# Interpreting Spikee Results

The `spikee results analyze` command provides statistics about a test run. Understanding these metrics is key to evaluating target resilience.

## Core Metrics

* **Total Unique Entries:** The number of distinct test cases processed (original prompts, potentially including variations from plugins). Each original prompt and its associated dynamic attack attempts (if any) count as one unique entry for overall success rate calculation.
* **Successful Attacks (Total):** Number of unique entries where *at least one* attempt (standard or dynamic) succeeded according to the defined judge.
* **Failed Attacks:** Number of unique entries where *all* attempts failed and no errors occurred.
* **Errors:** Number of unique entries where *all* attempts resulted in an error (e.g., API errors, timeouts). Note: An entry counts as an error *only if all attempts resulted in error*. If some attempts error but one succeeds or fails normally, it's not counted here.
* **Total Attempts:** The sum of all individual requests made to the target across all entries and iterations (standard + dynamic). This reflects the total workload/cost.
* **Attack Success Rate (Overall):** `(Successful Attacks / Total Unique Entries) * 100`. The primary metric for overall vulnerability.

## Dynamic Attack Metrics (If `--attack` was used)

These metrics appear only if a dynamic attack was run.

* **Initially Successful:** Number of unique entries that succeeded during the *standard* attempts (`--attempts`) before any dynamic attack script was invoked.
* **Only Successful with Dynamic Attack:** Number of unique entries that *only* succeeded during the dynamic attack phase (`--attack-iterations`), after failing the standard attempts.
* **Attack Success Rate (Without Dynamic Attack):** `(Initially Successful / Total Unique Entries) * 100`. Shows baseline vulnerability to the static payloads in the dataset.
* **Attack Success Rate (Improvement from Dynamic Attack):** `(Only Successful with Dynamic Attack / Total Unique Entries) * 100`. Quantifies the additional risk uncovered by the dynamic attack strategy.
* **Dynamic Attack Statistics Table:** Shows per-attack-type success rates:
    * `Attack Type`: Name of the attack script used.
    * `Total`: How many unique entries *invoked* this dynamic attack script (i.e., failed standard attempts).
    * `Successes`: How many times this script ultimately *achieved success*.
    * `Attempts`: Total *iterations* run by this script across all entries it was invoked for (sum of the first element returned by the `attack` function).
    * `Success Rate`: `(Successes / Total) * 100`. How effective this specific attack strategy was *when it was needed*.

## False Positive Analysis Metrics (If `--false-positive-checks` was used)

These metrics evaluate how well a *guardrail* target distinguishes between malicious attacks and benign prompts. Requires running `spikee test` on both an attack dataset (`results.jsonl`) and a benign dataset (`benign_results.jsonl`), then analyzing with `--false-positive-checks benign_results.jsonl`. Remember the guardrail logic: `True` means bypassed/allowed, `False` means blocked.

* **Confusion Matrix:**
    * **True Positives (TP):** Attacks correctly **blocked** by the guardrail. (Attack run: result `False`).
    * **False Negatives (FN):** Attacks incorrectly **allowed** (bypassed) by the guardrail. (Attack run: result `True`). These are successful attacks.
    * **True Negatives (TN):** Benign prompts correctly **allowed** by the guardrail. (Benign run: result `True`).
    * **False Positives (FP):** Benign prompts incorrectly **blocked** by the guardrail. (Benign run: result `False`).
* **Performance Metrics:**
    * **Precision:** `TP / (TP + FP)`. Of all prompts the guardrail *blocked*, what fraction were *actual attacks*? High precision means few benign prompts are blocked unnecessarily.
    * **Recall (Sensitivity):** `TP / (TP + FN)`. Of all *actual attacks* presented, what fraction did the guardrail *block*? High recall means the guardrail catches most attacks.
    * **F1 Score:** `2 * (Precision * Recall) / (Precision + Recall)`. Harmonic mean, balancing Precision and Recall. Useful for overall performance assessment.
    * **Accuracy:** `(TP + TN) / (TP + TN + FP + FN)`. Overall percentage of prompts (both attack and benign) classified correctly. Can be misleading if the dataset is imbalanced (e.g., far more attacks than benign prompts).

## Breakdown Tables

The `analyze` command provides tables breaking down success rates by various factors (Jailbreak Type, Instruction Type, Plugin, Language, Position, etc.). The table structure adapts based on whether dynamic attacks were run.

* **Columns (With Dynamic Attacks):**
    * `Factor Value`: (e.g., Jailbreak Type 'dan', Plugin '1337')
    * `Total`: Number of unique entries with this factor.
    * `All Successes`: Total successes (standard + dynamic).
    * `Initial Successes`: Successes from standard attempts only.
    * `Attack-Only Successes`: Successes from dynamic attacks only.
    * `Attempts`: Total target calls for entries with this factor.
    * `Success Rate`: Overall success rate for this factor.
    * `Initial Rate`: Baseline success rate for this factor.
    * `Attack Improvement`: Added success rate from dynamic attacks for this factor.
* **Columns (Without Dynamic Attacks):**
    * `Factor Value`, `Total`, `Successes`, `Attempts`, `Success Rate`.

These tables help identify which types of attacks, instructions, languages, or plugins are more or less effective against the target. Use the sort order (default: highest overall success rate first) to quickly see the most impactful factors.

## Combination Tables (Top 10 / Bottom 10)

These tables show the success rates for specific *combinations* of Jailbreak Type, Instruction Type, Language, Suffix ID, and Plugin. They help identify particularly potent or weak combinations of attack elements. Interpretation is similar to the breakdown tables, considering all relevant columns based on whether dynamic attacks were run.