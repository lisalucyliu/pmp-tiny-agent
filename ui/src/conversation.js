// Copied from a real eval run.
// Source: evals/results/2026-10-05_143027.json, task 1-riley-watchtail-database, run 1.
// All vendor and product names are fictional.

export const buyer = {
  name: 'Riley',
  experience: 'Engineering',
};

export const question = 'I need to buy a database product from Watchtail for my team.';

// The run's only tool call: search_products(query="Watchtail")
export const activity = [
  {
    id: 'search-1',
    tool: 'search_products',
    inProgressLabel: 'Searching catalog',
    doneLabel: 'Searched catalog',
    query: 'Watchtail',
  },
];

export const answer =
  "Watchtail doesn't sell a database, but two of its products include database monitoring. " +
  'Watchtail Pro (for smaller teams) is approved for your experience: https://example.com/marketplace/prod-blkffdyr. ' +
  'Watchtail Enterprise (for large companies) is not approved: https://example.com/marketplace/prod-egiccoxd. ' +
  'Watchtail has 2 other products, and Sentrypoint Security sells a managed service that runs on Watchtail. ' +
  'Do you need database monitoring, or a database to store data?';
