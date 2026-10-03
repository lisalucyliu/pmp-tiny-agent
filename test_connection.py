"""
Tiny connectivity test for the Claude API.

Run this after putting your key in .env to confirm everything is wired up
correctly, before building anything more complex.
"""

import os
import sys

from dotenv import load_dotenv
import anthropic

# Load ANTHROPIC_API_KEY from the .env file in this folder into the environment.
load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit(
        "No API key found. Open .env and set ANTHROPIC_API_KEY=your-key-here, "
        "then run this script again."
    )

# The client automatically picks up ANTHROPIC_API_KEY from the environment.
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=256,
    messages=[{"role": "user", "content": "Say hello"}],
)

# response.content is a list of blocks (usually just one text block for a
# simple reply like this).
for block in response.content:
    if block.type == "text":
        print(block.text)
