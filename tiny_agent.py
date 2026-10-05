"""
A tiny terminal agent powered by Claude: a Private Marketplace buyer agent.

All catalog, buyer, and request data here is fictional, for learning
purposes only.

The buyer helps a logged-in buyer search a software catalog, check whether
their Private Marketplace experience allows procurement requests, and send
a request to their administrator for products that aren't approved yet.

This file is still the same basic "agent loop" as before:
  1. Send the conversation so far to Claude.
  2. If Claude's reply says "I want to use a tool", run that tool locally
     and send the result back as part of the conversation.
  3. Repeat step 1-2 until Claude replies with plain text instead of a
     tool request.
  4. Show that text to the user and wait for their next message.

Who's logged in, their account ID, their experience, and whether requests
are enabled for them are all tracked by this code, never by Claude. Claude
only ever sees the result of a tool call, never the buyer record itself.
"""

import difflib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("No API key found. Set ANTHROPIC_API_KEY in .env first.")

client = anthropic.Anthropic()
MODEL = "claude-opus-5"

DATA_DIR = Path(__file__).parent / "data"
CATALOG_PATH = DATA_DIR / "catalog.json"
BUYERS_PATH = DATA_DIR / "buyers.json"
ADMIN_REQUESTS_PATH = DATA_DIR / "admin_requests.json"

SYSTEM_PROMPT = (
    "Respond in plain text only, formatted for a terminal with no Markdown "
    "rendering. Write in full sentences and paragraphs. Do not use bold "
    "(**), headers (#), or list markers of any kind, including -, *, and "
    "numbered lists like '1.'. Do not use em dashes (—); use a comma or "
    "period instead."
    "\n\n"
    "You help buyers find software in their company's Private Marketplace. "
    "Answer the buyer's specific question first, then offer next steps. "
    "You cannot purchase anything. When a "
    "product is approved, give the buyer its product page link so they can "
    "view purchase options and subscribe themselves. If a product is "
    "retired, say so and name its replacement."
    "\n\n"
    "Never offer to submit a request unless a tool result in this "
    "conversation shows requests are enabled. Only describe products using "
    "facts from tool results; do not add your own labels or opinions about "
    "a product."
    "\n\n"
    "Before you submit a request for a specific product, ask once if the "
    "buyer wants to add "
    "a note for their administrator, and mention that they can also add a "
    "PO number if they have one. Both are optional. Accept no without "
    "asking again. Never say that a reason or note is required."
    "\n\n"
    "Be concise. Answer the buyer's question in the first sentence. "
    "Describe only the products that fit the question, in one short line "
    "each. Summarize the rest as a count, for example \"Watchtail has 3 "
    "other products.\" Keep answers to about 5 short sentences unless the "
    "buyer asks for more."
    "\n\n"
    "For an approved product, write the name followed by its link, for "
    "example \"Watchtail Pro is approved for your experience: <link>\". Do "
    "not add phrases like \"you can go to its product page.\" For a "
    "product that is not approved, include its link so the buyer can share "
    "it with their administrator."
    "\n\n"
    "When two products are similar, state the difference in one short "
    "phrase and let the buyer choose. Do not recommend one unless the "
    "buyer has told you what they need."
    "\n\n"
    "Example of the expected length and style:\n"
    "Buyer: I need to buy a database product from Watchtail for my team.\n"
    "Agent: Watchtail doesn't sell a database, but two of its products "
    "include database monitoring. Watchtail Pro (for smaller teams) is "
    "approved for your experience: <link>. Watchtail Enterprise (for large "
    "companies) is not approved: <link>. Watchtail has 2 other products, "
    "and Sentrypoint Security sells a managed service that runs on "
    "Watchtail. Do you need database monitoring, or a database to store "
    "data?"
    "\n\n"
    "When requests are disabled, your first sentence must do two things: "
    "say that requests are off, and answer the buyer's actual question. "
    "Then tell the buyer to contact their administrator. Give only what "
    "fits the question, with one or two relevant product links, and tell "
    "the buyer to include those links in their message to the "
    "administrator. Offer to check what is already approved. When you "
    "share the docs page, describe it only as explaining how requests "
    "work. Do not describe what else is on it."
    "\n\n"
    "Example of the expected response when requests are disabled:\n"
    "Buyer: I need to buy a database product from Watchtail for my team.\n"
    "Agent: Product requests are off for your Finance experience, and "
    "Watchtail doesn't sell a database, but two of its products include "
    "database monitoring: Watchtail Pro <link> and Watchtail Enterprise "
    "<link>. Contact your administrator and include these links in your "
    "message. This page explains how requests work: <docs link>. Want me "
    "to check what's already approved for Finance?"
)

# Set once, at login, in main(). Never changed by anything Claude does.
CURRENT_BUYER = None
CATALOG = None


# ---- Buyer login and catalog loading (plain code, no Claude involved) ----


def load_buyers() -> list:
    return json.loads(BUYERS_PATH.read_text())


def load_catalog() -> list:
    return json.loads(CATALOG_PATH.read_text())


def choose_buyer(buyers: list) -> dict:
    print("Who's logging in?")
    for i, buyer in enumerate(buyers, start=1):
        print(f"  {i}. {buyer['name']} ({buyer['experience']} experience)")
    while True:
        choice = input("Enter a number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(buyers):
            return buyers[int(choice) - 1]
        print(f"Enter a number from 1 to {len(buyers)}.")


# ---- Tool definitions: Claude reads these to decide when and how to call each one ----

TOOLS = [
    {
        "name": "search_products",
        "description": (
            "Searches the company's full software catalog by product name, "
            "vendor, or what the product does. Each result shows the "
            "product name, vendor, type, a one-line description, its "
            "approval status in the buyer's experience, and a link to the "
            "product page. Use this for any question about a product, "
            "including vague or misspelled requests. If the buyer names a "
            "vendor, show all of that vendor's products. Note that a "
            "product can include a vendor's name but be sold by a "
            "different vendor; always report the actual vendor. Set "
            "approved_only to true only when the buyer wants approved "
            "alternatives. Searching a vendor name returns all of that "
            "vendor's products. Do not search again for a narrower "
            "version of the same query, because the first results "
            "already include those products. Search again only if the "
            "buyer asks about something different, or if the results "
            "say more products matched than were shown."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for: a product name, vendor, or what it does.",
                },
                "approved_only": {
                    "type": "boolean",
                    "description": "Only show products already approved for this buyer. Default false.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_request_settings",
        "description": (
            "Checks if product requests are enabled for the buyer's "
            "Private Marketplace experience. Only use this if the buyer "
            "asks about requests without searching for a product first. "
            "search_products results already include the request status, "
            "so do not call this tool after a search."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "submit_request",
        "description": (
            "Sends a request to the buyer's Private Marketplace "
            "administrator to approve one product for purchase. Use this "
            "only when search_products shows the product is not approved "
            "and check_request_settings shows requests are enabled. Always "
            "ask the buyer to confirm before you call this tool. Do not "
            "use this tool if the product is already approved, or if "
            "requests are disabled. In those cases, tell the buyer. If "
            "they want alternatives, use search_products with the "
            "approved-only filter. This tool does not approve or purchase "
            "the product. Only the administrator can approve it. After you "
            "submit, tell the buyer that the administrator will review the "
            "request, and do not suggest that approval is likely. If the "
            "tool returns blocked, the administrator has declined this "
            "product and blocked new requests for it. Tell the buyer, and "
            "offer to search for approved alternatives."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": (
                        "The product_id from a search_products result. "
                        "Never guess this from the product name."
                    ),
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "An optional note from the buyer to their "
                        "administrator, in their own words. Leave empty if "
                        "the buyer has none."
                    ),
                },
                "po_number": {
                    "type": "string",
                    "description": "A purchase order number, if the buyer gives one.",
                },
            },
            "required": ["product_id"],
        },
    },
]

STATUS_LABELS = {"A": "approved", "N": "not approved", "D": "declined and blocked"}


def _fuzzy_contains(haystack: str, needle: str) -> bool:
    """True if every word in `needle` either appears in `haystack`, or is
    close enough to a word in `haystack` to tolerate a small typo."""
    if needle in haystack:
        return True
    haystack_words = haystack.split()
    for word in needle.split():
        if word in haystack_words:
            continue
        if len(word) < 3:
            return False
        if not difflib.get_close_matches(word, haystack_words, n=1, cutoff=0.8):
            return False
    return True


def search_products(query: str, approved_only: bool = False) -> str:
    query_lower = query.lower()
    matches = []
    for product in CATALOG:
        haystack = f"{product['name']} {product['vendor']} {product['description']}".lower()
        if not _fuzzy_contains(haystack, query_lower):
            continue
        status = product["approval"][CURRENT_BUYER["experience"]]
        if approved_only and status != "A":
            continue
        matches.append(product)

    header = requests_status_message()

    if not matches:
        return (
            f'{header}\nNo products matched "{query}". Ask the buyer for a '
            "different name or what the product does, then search again."
        )

    shown = matches[:5]
    lines = [header]
    for product in shown:
        status = product["approval"][CURRENT_BUYER["experience"]]
        lines.append(
            f"- {product['name']} by {product['vendor']} ({product['type']}). "
            f"{product['description']} "
            f"Status in {CURRENT_BUYER['experience']}: {STATUS_LABELS[status]}. "
            f"product_id: {product['product_id']}. Link: {product['link']}"
        )
    remainder = len(matches) - len(shown)
    if remainder > 0:
        lines.append(f"...and {remainder} more matched but are not shown.")
    return "\n".join(lines)


REQUESTS_DOCS_LINK = (
    "https://docs.aws.amazon.com/marketplace/latest/buyerguide/"
    "requesting-products-for-procurement.html"
)


def requests_status_message() -> str:
    """The shared enabled/disabled line used by both search_products and
    check_request_settings, so they always say the same thing."""
    experience = CURRENT_BUYER["experience"]
    if CURRENT_BUYER["requests_enabled"]:
        return f"Product requests are enabled for the {experience} experience."
    return (
        f"Product requests are disabled for the {experience} experience. "
        "Do not offer to submit a request. Do not call submit_request. "
        "Tell the buyer to contact their "
        "administrator directly, and give them one or two relevant product "
        "links to include in their message. Share this page, which explains how "
        f"requests work: {REQUESTS_DOCS_LINK}"
    )


def check_request_settings() -> str:
    return requests_status_message()


def submit_request(product_id: str, reason: str = "", po_number: str = "") -> str:
    experience = CURRENT_BUYER["experience"]
    product = next((p for p in CATALOG if p["product_id"] == product_id), None)
    if product is None:
        return (
            f"Request not submitted. No product found with product_id "
            f"{product_id}. Use search_products to find the correct product_id."
        )

    # Checked after the product lookup so the message can name the product
    # and give the buyer its link to send to their administrator.
    if not CURRENT_BUYER["requests_enabled"]:
        return (
            f"Request not submitted. Product requests are disabled for the "
            f"{experience} experience. Do not call submit_request again. Tell "
            f"the buyer to contact their administrator directly about "
            f"{product['name']}, and include this link in their message: "
            f"{product['link']} Share this page, which explains how requests "
            f"work: {REQUESTS_DOCS_LINK} If the buyer wants alternatives, offer "
            "to use search_products with approved_only set to true."
        )

    status = product["approval"][experience]
    if status == "D":
        return (
            f"Request not submitted. The administrator declined "
            f"{product['name']} for the {experience} experience and blocked "
            "new requests for it. Do not call submit_request again for this "
            "product. Tell the buyer, and offer to search for approved "
            "alternatives."
        )
    if status == "A":
        return (
            f"{product['name']} is already approved in the {experience} "
            f"experience. No request needed. Link: {product['link']}"
        )

    record = {
        "product_id": product["product_id"],
        "product_name": product["name"],
        "account_id": CURRENT_BUYER["account_id"],
        "experience": CURRENT_BUYER["experience"],
        "buyer_name": CURRENT_BUYER["name"],
        "reason": reason,
        "po_number": po_number,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    requests = json.loads(ADMIN_REQUESTS_PATH.read_text()) if ADMIN_REQUESTS_PATH.exists() else []
    requests.append(record)
    ADMIN_REQUESTS_PATH.write_text(json.dumps(requests, indent=2) + "\n")

    return (
        f"Request submitted for {product['name']} (product_id "
        f"{product['product_id']}) under account {CURRENT_BUYER['account_id']} "
        f"in the {CURRENT_BUYER['experience']} experience."
    )


def run_tool(name: str, tool_input: dict) -> str:
    if name == "search_products":
        return search_products(tool_input["query"], tool_input.get("approved_only", False))
    if name == "check_request_settings":
        return check_request_settings()
    if name == "submit_request":
        return submit_request(
            tool_input["product_id"],
            tool_input.get("reason", ""),
            tool_input.get("po_number", ""),
        )
    return f"Unknown tool: {name}"


def format_args(tool_input: dict) -> str:
    parts = []
    for key, value in tool_input.items():
        parts.append(f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}")
    return ", ".join(parts)


def run_agent(messages: list) -> str:
    """Keep talking to Claude, running any tools it asks for, until it
    gives a final text answer. `messages` is updated in place so the
    conversation carries over to the next turn."""
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            print("[answer] no more tools needed")
            return next(
                (block.text for block in response.content if block.type == "text"),
                "",
            )

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_tool(block.name, block.input)
                print(f"[tool] {block.name}({format_args(block.input)}) → {result}")
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        messages.append({"role": "user", "content": tool_results})


def main():
    global CURRENT_BUYER, CATALOG
    CATALOG = load_catalog()
    CURRENT_BUYER = choose_buyer(load_buyers())
    print(
        f"\nLogged in as {CURRENT_BUYER['name']} "
        f"({CURRENT_BUYER['experience']} experience).\n"
    )
    print(
        "Private Marketplace buyer agent ready. All data is fictional. "
        "Try: \"do you have a VPN?\". Type 'quit' to exit.\n"
    )
    messages = []
    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        reply = run_agent(messages)
        print(f"\nAgent: {reply}\n")


if __name__ == "__main__":
    main()
