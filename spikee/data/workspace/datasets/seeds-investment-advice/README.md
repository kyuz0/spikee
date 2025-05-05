This example dataset can be used for testing topical guardrails aimed at blocking prompts/queries/instructions for an LLM system that attempt to elicit "personal investment/financial advice" queries.

```bash
spikee generate --seed-folder datasets/seeds-investment-advice --standalone-attacks datasets/seeds-investment-advice/standalone_attacks.jsonl --match-languages --include-system-message --format document 
```