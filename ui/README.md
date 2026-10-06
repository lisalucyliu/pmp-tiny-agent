# Test page

A static Cloudscape page that shows one sample conversation with the buyer agent. It's a test page for the design review loop and an early step toward Demo 2. Concept prototype, not affiliated with AWS. All data is fictional.

The conversation is copied from a real eval run: `evals/results/2026-10-05_143027.json`, task `1-riley-watchtail-database`, run 1. There are no API calls.

## How to run

In a separate terminal tab, from the `~/pmp-tiny-agent/ui` folder:

```
npm run dev
```

Then open the URL it prints. The page shows the search in progress for 2 seconds, then the answer.

To hold the page on the in-progress state (for screenshots), add `?state=searching` to the URL.

## Known gaps for Demo 2

Found by the design review on 2026-10-05. Lisa decided to leave these for Demo 2.

- **States:** the page has the in-progress and answered states only. It has no empty state (no conversation yet) and no error state (search failed).
- **Messy cases:** there is one tidy conversation. Demo 2 should cover zero results, long product and vendor names, Sam with requests off, and answers that use more than one tool.
- **Bare URLs:** the answer shows product links as raw URLs, because the agent writes them that way. On phone they break mid-URL. Fix this in the agent's system prompt so it links product names instead, then update the page.
