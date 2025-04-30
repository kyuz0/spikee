# Spikee Documentation - Table of Contents

Index of detailed guides for Spikee v0.2+.

1.  **[Creating Custom Targets](./01_custom_targets.md)**
    * Structure and implementation of target scripts (`targets/`) for interacting with LLMs, APIs, or guardrails. Covers the `process_input` function, API key handling, error management, and expected return values (string, boolean, or tuple).

2.  **[Developing Custom Plugins](./02_custom_plugins.md)**
    * Structure and implementation of plugin scripts (`plugins/`) for static payload transformation during dataset generation. Covers the `transform` function, handling `exclude_patterns`, and returning single vs. multiple variations.

3.  **[Writing Dynamic Attack Scripts](./03_dynamic_attacks.md)**
    * Structure and implementation of dynamic attack scripts (`attacks/`). Details the `attack` function, interacting with the wrapped target module, using `call_judge`, respecting `max_iterations`, and progress bar updates.

4.  **[Understanding and Using Judges](./04_judges.md)**
    * Explanation of the judge system for attack success evaluation. Covers built-in judges (`canary`, `regex`), creating custom judges (`judges/`), and the role of `judge_name` and `judge_args` in datasets. Includes notes on LLM-based judges.

5.  **[Interpreting Spikee Results](./05_interpreting_results.md)**
    * Guide to understanding the output of `spikee results analyze`. Explains core metrics, dynamic attack statistics (initial vs. attack-only success), false positive analysis metrics (Precision, Recall, F1, Accuracy), and breakdown/combination tables.

6.  **[Generating Custom Datasets with an LLM](./06_llm_dataset_generation.md)**
    * Methods for using LLMs to generate use-case specific datasets. Covers creating `standalone_attacks.jsonl` directly and generating custom `instructions.jsonl` for use with existing seeds. Includes example prompts and emphasizes manual review.

7.  **[Testing Guardrails](./07_guardrail_testing.md)**
    * Workflow for evaluating guardrails using attack and benign datasets. Explains target configuration (boolean return value), running tests, and using `--false-positive-checks` for comprehensive analysis (Precision, Recall, etc.).