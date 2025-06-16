# Changelog

All notable changes to this project will be documented in this file.

## [0.2.3] - 2025-06-16

### Added

* **Dataset Sampling for Testing:**
    * Added `--sample <percentage>` flag to `spikee test` to randomly sample a subset of the dataset (e.g., `--sample 0.15` for 15%).
    * Added `--sample-seed <value>` flag to control sampling reproducibility. Default: `42`. Use `"random"` for a random seed (printed to console).
    * Sampling works correctly with `--resume-file`, maintaining the same sample set when resuming interrupted tests.
    * Useful for testing with large datasets under time or API quota constraints.

* **New Seed Datasets:**
    * `seeds-in-the-wild-jailbreak-prompts`: Real-world jailbreak attempts from TrustAIRLab collected from Discord, Reddit, and other platforms (~1,400 prompts from December 2023). Includes fetch script to download from Hugging Face.
    * `seeds-simsonsun-high-quality-jailbreaks`: Contamination-free jailbreak prompts curated to avoid overlap with training data of popular jailbreak classifiers. Includes two options: Dataset 1 (67 high-quality prompts) and Dataset 2 (2,359 broader coverage prompts). Supports `--dataset 2` flag in fetch script.

### Fixed

* Progress bars now correctly show previous progress when resuming a test with `--resume-file`, instead of starting from zero.

## [0.2.0] - 2025-04-28

### Added

* **Dynamic Attack Framework:**
    * New `attacks/` directory for attack scripts.
    * `spikee test` command now supports `--attack <name>` and `--attack-iterations <N>` to run iterative attack strategies if standard attempts fail.
    * `attacks/sample_attack.py`: Template for creating custom attacks.
    * Built-in attacks: `best_of_n`, `random_suffix_search`, `anti_spotlighting`, `prompt_decomposition_llm`, `prompt_decomposition_dumb`.
* **Judge System for Success Evaluation:**
    * Replaced `--success-criteria` flag with a per-entry judge system.
    * Dataset entries now use `judge_name` (e.g., "canary", "regex", "llm_judge") and `judge_args` (e.g., canary string, regex pattern, LLM criteria) to define success.
    * New `judges/` directory for custom judge scripts.
    * `judges/sample_judge.py`: Template provided via `spikee init`.
    * Built-in judges: `canary`, `regex`. Example LLM judges in workspace.
* **Enhanced Dataset Generation:**
    * Added `payload` field to JSONL output (the raw jailbreak+instruction text).
    * Added `exclude_from_transformations_regex` field (list of regex strings) for finer control over plugin transformations.
    * Plugins can now return a `List[str]` to generate multiple variations per input.
* **New Seed Datasets:**
    * `seeds-wildguardmix-harmful`: For testing harmful content generation (requires fetching external dataset). Uses LLM judge.
    * `seeds-investment-advice`: For testing topical guardrails around financial advice. Includes benign and attack prompts.
    * Updated other seeds like `seeds-cybersec-2025-04`, `seeds-sysmsg-extraction-2025-04`.
* **Results Analysis Improvements:**
    * `spikee results analyze` now correctly handles and groups results from dynamic attacks.
    * Calculates and reports `Initial Success Rate` (without dynamic attack) and `Attack Improvement` (successes achieved only via dynamic attack).
    * Added `response_time` field to results JSONL. For dynamic attacks, this covers the full attack duration.
    * Added `--false-positive-checks <path.jsonl>` option to `spikee results analyze` for calculating precision, recall, F1, and accuracy using results from benign prompts.
* **CLI Enhancements:**
    * `spikee init` now creates `attacks/` and `judges/` directories.
    * `spikee init` supports `--include-builtin [all|plugins|judges|targets|attacks]` to copy built-in modules locally.
    * `spikee list` command now includes `attacks` and `judges`.
    * Added `--tag` option to `spikee generate` and `spikee test` to add custom suffixes to output filenames.
    * Added `--max-retries` flag to `spikee test` (default 3) for rate limit handling.
* **Plugin Interface:**
    * `transform` function in plugins now accepts an optional `exclude_patterns: List[str]` argument.

### Changed

* **Guardrail Target Logic:** Targets intended for guardrail testing must now return `True` if the attack **bypassed** the guardrail (attack successful) and `False` if the attack was **blocked** (attack failed). This standardizes the boolean interpretation across guardrail targets. Built-in guardrail targets have been updated. **This is a potential breaking change if using custom v0.1 guardrail targets.**
* **Success Criteria Deprecated:** Removed the `--success-criteria` flag from `spikee test`. Success is now managed via the Judge system.
* **Internal Refactoring:** Updated `tester.py` and `results.py` to support dynamic attacks and the judge system. `generator.py` updated for new dataset fields and multi-variation plugins.

### Fixed

* Improved handling of file paths and module loading for local vs. built-in components.
* Ensured unique IDs for dynamic attack result entries (`<original_id>-attack`).

## [0.1.0] - 2025-01-27

* Initial release.
* Features: Dataset generation (`spikee generate`), testing (`spikee test`), results analysis (`spikee results analyze`, `convert-to-excel`), basic workspace initialization (`spikee init`), listing components (`spikee list`).
* Support for plugins and targets (local and built-in).
* Success criteria based on `--success-criteria [canary|boolean]`.