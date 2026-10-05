"""
Runs the Private Marketplace agent's test tasks and checks the results.

Each run is a fresh session: a new, empty conversation, logged in as the
task's buyer. The agent code in tiny_agent.py is used as-is.

Usage, from the project folder:
  .venv/bin/python evals/run_evals.py            # every task, once
  .venv/bin/python evals/run_evals.py --runs 3   # every task, 3 times
  .venv/bin/python evals/run_evals.py --task 2   # tasks whose id starts with "2"

Full transcripts are saved to evals/results/<timestamp>.json.
"""

import argparse
import contextlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path

EVALS_DIR = Path(__file__).parent
PROJECT_DIR = EVALS_DIR.parent
TASKS_PATH = EVALS_DIR / "tasks.json"
RESULTS_DIR = EVALS_DIR / "results"

sys.path.insert(0, str(PROJECT_DIR))
import tiny_agent  # noqa: E402


# ---- Running one session ----


def to_plain(content):
    """Turn message content (which may hold SDK objects) into plain JSON data."""
    if isinstance(content, str):
        return content
    return [block.model_dump() if hasattr(block, "model_dump") else block for block in content]


def extract_tool_calls(messages: list) -> list:
    """List every tool call in order, with its input and the result the agent got back."""
    results_by_id = {}
    for message in messages:
        if message["role"] == "user" and isinstance(message["content"], list):
            for block in message["content"]:
                if block.get("type") == "tool_result":
                    results_by_id[block["tool_use_id"]] = block["content"]
    calls = []
    for message in messages:
        if message["role"] == "assistant":
            for block in message["content"]:
                if block["type"] == "tool_use":
                    calls.append({
                        "name": block["name"],
                        "input": block["input"],
                        "result": results_by_id.get(block["id"]),
                    })
    return calls


def run_session(buyer: dict, question: str) -> dict:
    """Ask one question as one buyer in a brand-new conversation."""
    tiny_agent.CATALOG = tiny_agent.load_catalog()
    tiny_agent.CURRENT_BUYER = buyer

    # Keep the admin requests file exactly as it was, even if the agent
    # calls submit_request during the test.
    requests_path = tiny_agent.ADMIN_REQUESTS_PATH
    saved_requests = requests_path.read_text() if requests_path.exists() else None

    messages = [{"role": "user", "content": question}]
    console = io.StringIO()
    new_requests = []
    try:
        with contextlib.redirect_stdout(console):
            answer = tiny_agent.run_agent(messages)
    finally:
        # Note any requests the agent saved, before putting the file back.
        before = json.loads(saved_requests) if saved_requests else []
        after = json.loads(requests_path.read_text()) if requests_path.exists() else []
        new_requests = after[len(before):]
        if saved_requests is None:
            requests_path.unlink(missing_ok=True)
        else:
            requests_path.write_text(saved_requests)

    plain_messages = [{"role": m["role"], "content": to_plain(m["content"])} for m in messages]
    return {
        "answer": answer,
        "tool_calls": extract_tool_calls(plain_messages),
        "new_requests": new_requests,
        "console_output": console.getvalue(),
        "messages": plain_messages,
    }


# ---- Checks ----


def run_check(check: dict, session: dict, catalog: list, offer_phrases: list) -> dict:
    """Returns {"label", "passed", "detail"} for one check."""
    answer = session["answer"]
    tool_names = [call["name"] for call in session["tool_calls"]]
    kind = check["type"]

    if kind == "tools_exactly":
        label = f"tools exactly [{', '.join(check['tools'])}]"
        passed = tool_names == check["tools"]
        detail = f"got [{', '.join(tool_names)}]"

    elif kind == "has_product_link":
        product = next(p for p in catalog if p["name"] == check["product"])
        label = f"has {check['product']} link"
        passed = product["link"] in answer
        detail = f"looked for {product['link']}"

    elif kind == "has_text":
        # "text" is one string; "texts" passes if any one of them appears.
        texts = check.get("texts", [check.get("text")])
        label = f"has {check.get('label', ' or '.join(repr(t) for t in texts))}"
        haystack = answer.lower() if check.get("ignore_case") else answer
        needles = [t.lower() for t in texts] if check.get("ignore_case") else texts
        passed = any(n in haystack for n in needles)
        detail = f"looked for {' or '.join(texts)}"
        if check.get("ignore_case"):
            detail += " (ignoring case)"

    elif kind == "no_request_saved":
        label = "no request saved"
        saved = session["new_requests"]
        passed = not saved
        detail = "saved " + ", ".join(r["product_name"] for r in saved) if saved else "none saved"

    elif kind == "tool_not_called":
        label = f"{check['tool']} not called"
        passed = check["tool"] not in tool_names
        detail = f"got [{', '.join(tool_names)}]"

    elif kind == "no_request_offer":
        label = "no request-offer phrases"
        found = [phrase for phrase in offer_phrases if phrase in answer.lower()]
        passed = not found
        detail = "found " + ", ".join(f'"{p}"' for p in found) if found else "none found"

    elif kind == "max_product_links":
        label = f"at most {check['max']} product link(s)"
        links = [p["link"] for p in catalog if p["link"] in answer]
        passed = len(links) <= check["max"]
        detail = f"found {len(links)}: {', '.join(links)}" if links else "found 0"

    else:
        raise ValueError(f"Unknown check type: {kind}")

    if check.get("approximate"):
        label += " (approximate)"
    return {"label": label, "passed": passed, "detail": detail}


# ---- Main ----


def main():
    parser = argparse.ArgumentParser(description="Run the agent's test tasks.")
    parser.add_argument("--runs", type=int, default=1, help="How many times to run each task (default 1).")
    parser.add_argument("--task", help="Only run tasks whose id starts with this text.")
    args = parser.parse_args()

    spec = json.loads(TASKS_PATH.read_text())
    tasks = spec["tasks"]
    if args.task:
        tasks = [t for t in tasks if t["id"].startswith(args.task)]
        if not tasks:
            sys.exit(f'No task id starts with "{args.task}".')
    offer_phrases = [p.lower() for p in spec.get("request_offer_phrases", [])]
    buyers = {b["name"]: b for b in tiny_agent.load_buyers()}
    catalog = tiny_agent.load_catalog()

    started = datetime.now()
    records = []
    for task in tasks:
        for run in range(1, args.runs + 1):
            print(f"Running {task['id']} (run {run} of {args.runs})...", file=sys.stderr)
            record = {"task_id": task["id"], "run": run, "buyer": task["buyer"], "question": task["question"]}
            try:
                session = run_session(buyers[task["buyer"]], task["question"])
                checks = [run_check(c, session, catalog, offer_phrases) for c in task["checks"]]
                record.update(session)
                record["checks"] = checks
                record["result"] = "PASS" if all(c["passed"] for c in checks) else "FAIL"
            except Exception as error:  # Keep going so one API error doesn't stop the batch.
                record["result"] = "ERROR"
                record["error"] = f"{type(error).__name__}: {error}"
            records.append(record)

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"{started.strftime('%Y-%m-%d_%H%M%S')}.json"
    results_path.write_text(json.dumps({
        "started_at": started.isoformat(timespec="seconds"),
        "model": tiny_agent.MODEL,
        "runs_per_task": args.runs,
        "results": records,
    }, indent=2) + "\n")

    # Summary
    id_width = max(len(r["task_id"]) for r in records)
    print()
    print(f"{'Task':<{id_width}}  Run  Result  Tools  Failed checks")
    for r in records:
        tools = str(len(r.get("tool_calls", []))) if r["result"] != "ERROR" else "-"
        if r["result"] == "ERROR":
            failed = r["error"]
        else:
            failed = "; ".join(f"{c['label']}: {c['detail']}" for c in r["checks"] if not c["passed"])
        print(f"{r['task_id']:<{id_width}}  {r['run']:>3}  {r['result']:<6}  {tools:>5}  {failed}")

    if args.runs > 1:
        print()
        for task in tasks:
            task_records = [r for r in records if r["task_id"] == task["id"]]
            passed = sum(r["result"] == "PASS" for r in task_records)
            print(f"{task['id']}: {passed}/{len(task_records)} passed")

    total_passed = sum(r["result"] == "PASS" for r in records)
    print()
    print(f"{total_passed} of {len(records)} runs passed. Transcripts: {results_path.relative_to(PROJECT_DIR)}")
    sys.exit(0 if total_passed == len(records) else 1)


if __name__ == "__main__":
    main()
