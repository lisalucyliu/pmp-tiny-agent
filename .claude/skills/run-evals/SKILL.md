---
name: run-evals
description: Runs the Private Marketplace agent's test tasks and summarizes the results. Use when Lisa asks to run evals or tests, or after any change to the agent's system prompt, tools, or data.
argument-hint: "[number of runs per task, default 1]"
---

# Run evals

The tasks and checks live in `evals/tasks.json`. The runner is `evals/run_evals.py`. Each run is a fresh session, and each run makes about 2 calls to Claude with Lisa's API key.

## Steps

1. From the project folder, run the runner. If Lisa gave a number (for example `/run-evals 3`), pass it as `--runs`:
   ```
   .venv/bin/python evals/run_evals.py --runs <N>
   ```
   Without a number, leave out `--runs`. The runner exits with code 1 when any run fails. That's expected and isn't an error in the runner.

2. Show Lisa the summary table exactly as the runner printed it, including the transcripts path.

3. For each FAIL or ERROR, open the results file named in the summary and show the relevant part of the transcript:
   - the buyer and the question
   - the tool calls, in order, with their inputs
   - the part of the final answer that broke the check (quote it), or the full answer if it's short
   - which check failed and its detail
   Skip the passing runs.

4. End with a short, plain list of what failed. If a check is marked "(approximate)", say whether it looks like a real failure or a false alarm from the phrase list, and why.

## Rule

Never change the agent (`tiny_agent.py`), the data, the tasks, or the checks just to make a test pass. Report failures and ask Lisa what to do.
