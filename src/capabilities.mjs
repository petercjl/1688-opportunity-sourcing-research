export const capabilities = [
  {
    "id": "build_search_plan",
    "command": "1688-opportunity-sourcing-research script build_search_plan.py",
    "access": "local"
  },
  {
    "id": "collect_results",
    "command": "1688-opportunity-sourcing-research script collect_results.py",
    "access": "network-read"
  },
  {
    "id": "prepare_evidence",
    "command": "1688-opportunity-sourcing-research script prepare_evidence.py",
    "access": "local"
  },
  {
    "id": "prepare_image_review",
    "command": "1688-opportunity-sourcing-research script prepare_image_review.py",
    "access": "local"
  },
  {
    "id": "build_outputs",
    "command": "1688-opportunity-sourcing-research script build_outputs.py",
    "access": "local"
  },
  {
    "id": "discover_runtime",
    "command": "1688-opportunity-sourcing-research script discover_runtime.py",
    "access": "local"
  }
];
