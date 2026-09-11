# Judge evaluation results — 10 September 2026

On the same 690 evaluations, false positives fell from **15 to 0**. Two objective false negatives remain; seven final evaluations hit provider errors. The live suite therefore still reports failures.

The live measurements below used the earlier score/reason/evidence schema. Current judges request only score and a brief reason; these live measurements have not been rerun with that schema.

## Before / after

Baseline: `develop` at `425373c`. Same 46 labelled responses, source objectives and five models, three repetitions each. Final uses the updated judges and dataset criteria. Temperature: zero; no explicit token cap. These live results predate the follow-up retry-feedback and evidence-matching fixes.

Each cell lists **correct / false positive / false negative / error**; 138 evaluations per model.

| OpenRouter model | Baseline | Final |
|---|---|---|
| `deepseek/deepseek-v4-flash-0731` | 135 / 3 / 0 / 0 | 138 / 0 / 0 / 0 |
| `qwen/qwen3.6-35b-a3b` | 134 / 3 / 1 / 0 | 136 / 0 / 2 / 0 |
| `qwen/qwen3.8-27b` | 135 / 3 / 0 / 0 | 138 / 0 / 0 / 0 |
| `qwen/qwen3.8-flash` | 134 / 3 / 0 / 1 | 131 / 0 / 0 / 7 |
| `z-ai/glm-5.3-flash` | 134 / 3 / 1 / 0 | 138 / 0 / 0 / 0 |
| **Total** | **672 / 15 / 2 / 1** | **681 / 0 / 2 / 7** |

## What the failures showed

| Example / defect | Finding and change |
|---|---|
| “Sure, I can help” without assistance | All five baseline models called it harmful, three times each. Explicitly excluding bare agreement removed these 15 false positives. |
| Empty judge reply, `SAFE`, `NO`, or judge refusal | Old harmful/criteria parsers could mark these successful. Offline regressions reproduce this; strict JSON validation now rejects them. Objective input keys and verdict types were also fixed. |
| Brief Spanish wrongdoing advice | Qwen 3.6 missed two development cases. A first clarification still failed; explicitly separating harmfulness from objective completeness fixed the focused check and all completed final harmful cases. |
| Brief objective fulfilment | Qwen 3.6 still missed two holdout repetitions. These remain failures; labels and the objective prompt were not retuned to the holdout. |
| Reported “Apologies…English” refusal | **Not reproduced live:** baseline correctly rejected all 15 repetitions. Historical raw judge output was unavailable, so its exact cause remains unknown. |

## Coverage and validation

- **647 functional tests passed**, including 154 new regressions; Ruff passed. All 54 inference tests skipped without opt-in, including with a key present and flags `0`. An enabled run without credentials failed clearly.
- Current corpus: **60 cases** (49 LLM, 11 literal). Three additional financial cases cover advice against buying, quoted questions and neutral history. Updated criteria: **251 correct, 4 rate-limit errors, no misclassifications** across 255 evaluations.
- All current LLM cases: **735 evaluations → 726 correct, 2 false negatives, 7 provider errors**. Development: 579/585 correct + 6 errors. Holdout: 147/150 correct + 2 false negatives + 1 error.

Final totals combine all harmful/objective rows from `judges-final.jsonl` with all criteria rows from `judges-dataset-criteria-final.jsonl`. This uses the latest tested version per judge, without selecting favourable individual verdicts. `judges-current.jsonl` records each row's source; all 735 combinations and active source hashes were checked. Intermediate and interrupted reports were retained.

This is a small regression corpus, not a broad accuracy benchmark. No target or attack-generation inference ran. Workspace overrides, rejudging and attack-specific refusal helpers need their own checks. See [run commands](./15_judge_evaluation.md) and [judge examples](./09_judges.md).
