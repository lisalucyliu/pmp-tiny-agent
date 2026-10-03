# Tiny Marketplace Agent

A small concept prototype of an AI agent that helps buyers find and request software in a company's private software catalog.

This is my own design concept, inspired by AWS Marketplace's Private Marketplace feature. It is not affiliated with or endorsed by AWS. All vendor names, product names, and buyer data in this project are fictional, made up for this prototype.

## What it is

The agent runs in a terminal. A buyer logs in (there are two fictional sample buyers to choose from), then asks questions like "do you have a VPN?" or "can I get this approved?" Claude searches a fake product catalog, checks whether the buyer's company allows software requests, and can send a request to a fake admin inbox for products that aren't approved yet.

This project exists to learn how an agent built on the Claude API actually works underneath: the loop where Claude asks to use a tool, your own code runs it, and the result goes back to Claude so it can keep reasoning or give a final answer.

## How it works

Claude has three tools it can call. It decides when to call them based on what the buyer asks; your code is the one that actually runs them and decides what's allowed.

- **search_products**: looks up products by name, vendor, or what they do, and tolerates small typos. Every result includes the product's approval status for the buyer's company and a link to its page. The top of the results also says whether the buyer's company allows requests at all.
- **check_request_settings**: checks whether request submission is turned on for the buyer's company. Claude is told to only call this when the buyer asks about requests directly, since search results already carry that information.
- **submit_request**: sends a request to a fake admin inbox file for one product. Claude always asks the buyer to confirm first.

A few rules are enforced by the code itself, not left up to Claude to remember:

- Who is logged in, their account ID, and whether their company allows requests are tracked by the program, not by Claude. Claude never sees the buyer record directly, only what a tool tells it.
- If requests are turned off for a buyer's company, the code refuses to save a request no matter what Claude asks for, and returns a message telling Claude to point the buyer to their administrator instead.
- If a product has been declined and blocked by an administrator, the code refuses to save a new request for it.
- If a product is already approved, the code skips straight to telling the buyer that, instead of filing a pointless request.
- Every request the code does save gets the buyer's real account ID, company, and a timestamp added automatically. Claude can never fill in those fields itself.

## How to run it

You'll need Python 3 and your own Anthropic API key.

1. Create a virtual environment and activate it:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Create a file named `.env` in the project folder with this line, and put your own key after the equals sign:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```
4. Run the agent:
   ```
   python tiny_agent.py
   ```

## Example conversation

```
Who's logging in?
  1. Riley (Engineering experience)
  2. Sam (Finance experience)
Enter a number: 1

You: do you have a VPN?

Agent: I found two VPN options in your Engineering experience. Tunnelport
Access Server (BYOL), a self-hosted business VPN on EC2, is approved:
https://example.com/marketplace/prod-wtvfcarn. Meshwire, secure networking
that replaces legacy VPNs, is not approved:
https://example.com/marketplace/prod-rqccxbpo. The difference is self-hosted
on your own EC2 instance versus a SaaS network. Product requests are
enabled, so I can submit Meshwire for your administrator's review if you'd
prefer that one.
```
