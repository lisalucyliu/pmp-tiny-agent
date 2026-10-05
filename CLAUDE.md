# pmp-tiny-agent
Concept prototype of an AI agent that helps buyers find and request software in a company's private catalog. Inspired by AWS Marketplace's Private Marketplace. Not affiliated with AWS.

# How to run
- In a separate terminal tab, from the ~/pmp-tiny-agent folder: source .venv/bin/activate, then python tiny_agent.py
- Choose buyer 1 (Riley, requests on) or 2 (Sam, requests off).
- Restart the agent after any change to code or data.
- To run the evals, from the ~/pmp-tiny-agent folder: .venv/bin/python evals/run_evals.py (add --runs 3 to run each task 3 times), or use /run-evals in Claude Code. Tasks and checks are in evals/tasks.json.

# Project rules
- All vendor and product names are fictional. Never add real company names.
- Rules that must always hold go in code, not only in the system prompt or tool descriptions.
- Tool descriptions are design decisions. When you change one, show me the before and after.
- The agent has three tools: search_products, check_request_settings, submit_request. Ask before adding or removing a tool.
- The agent never purchases. It links to product pages.
- Reset data/admin_requests.json to [] before committing.

# Testing
- Test each task in a fresh session, as both Riley and Sam.
