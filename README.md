# spikee - Simple Prompt Injection Kit for Evaluation and Exploitation

Version: 0.2.2

```
   _____ _____ _____ _  ________ ______
  / ____|  __ \_   _| |/ /  ____|  ____|
 | (___ | |__) || | | ' /| |__  | |__   
  \___ \|  ___/ | | |  < |  __| |  __|  
  ____) | |    _| |_| . \| |____| |____
 |_____/|_|   |_____|_|\_\______|______|

```

Developed by Reversec Labs, `spikee` (Simple Prompt Injection Kit for Evaluation and Exploitation) assesses the resilience of LLMs, guardrails, and application pipelines against known prompt injection and jailbreak patterns. Rather than simply asking *if* a system is vulnerable, `spikee` helps determine *how easily* it can be compromised, gauging whether standard, off-the-shelf techniques are sufficient or if novel attacks are necessary.

---

## 1. Installation

### 1.1 PyPI Installation

```bash
pip install spikee
```

### 1.2 Local Installation (From Source)

```bash
git clone https://github.com/WithSecureLabs/spikee.git
cd spikee
python3 -m venv env
source env/bin/activate
pip install .
```

### 1.3 Local Inference Dependencies

For targets requiring local model inference:

```bash
pip install -r requirements-local-inference.txt
```

---

## 2. Usage

### 2.1 Initializing a Workspace

Creates local directories (`datasets/`, `plugins/`, `targets/`, `judges/`, `attacks/`, `results/`) and copies samples.

```bash
spikee init
```

**Options:**

* `--force`: Overwrite existing workspace files/directories.
* `--include-builtin [none|all|plugins|judges|targets|attacks]`: Copy built-in modules (specified types or 'all') into the local workspace for modification. Default is `none`. Useful if you want to understand how modules work and if you want to modify a built-in module.

---

### 2.2 Listing Available Components

Check local and built-in modules:

```bash
spikee list seeds       # Seed folders in ./datasets/
spikee list datasets    # Generated .jsonl files in ./datasets/
spikee list targets     # Target scripts (.py) in ./targets/ and built-in
spikee list plugins     # Plugin scripts (.py) in ./plugins/ and built-in
spikee list judges      # Judge scripts (.py) in ./judges/ and built-in
spikee list attacks     # Attack scripts (.py) in ./attacks/ and built-in
```

---

### 2.3 Environment Variables

Rename the `env-example` file in your workspace to `.env` and populate required API keys and other secrets for your use case. `spikee` loads this automatically.

```bash
# .env example
OPENAI_API_KEY=sk-...
AZURE_OPENAI_API_KEY=...
AWS_ACCESS_KEY_ID=...
# etc.
```

---

### 2.4 Generating a Dataset

`spikee generate` creates test datasets from seed files (`base_documents.jsonl`, `jailbreaks.jsonl`, `instructions.jsonl`).

**Basic Example:**

```bash
# Uses default seeds (datasets/seeds-mini-test)
# Injects payload at the end of documents
spikee generate
```

**Available Seed Datasets (in `./datasets/` after `spikee init`):**

* `seeds-mini-test`: A small set for quick testing and examples.
* `seeds-targeted-2024-12`: A diverse set focused on common web exploits (XSS, data exfil) and manipulation.
* `seeds-cybersec-2025-04`: Updated cybersecurity-focused dataset with newer techniques.
* `seeds-sysmsg-extraction-2025-04`: Seeds specifically designed to test system prompt extraction vulnerabilities.
* `seeds-llm-mailbox`: Example seeds tailored for testing an email summarization feature (from the v0.1 tutorial).
* `seeds-investment-advice`: Seeds containing prompts related to financial/investment advice, useful for testing topical guardrails. Includes benign prompts in `base_documents.jsonl` (for false positive checks) and attack prompts in `standalone_attacks.jsonl`.
* `seeds-wildguardmix-harmful`: Seeds for testing harmful content generation. Requires running a fetch script to download the actual prompts from Hugging Face (see the `README.md` within that seed folder). Uses an LLM judge by default.

**Examples using Key Options:**

* **Specify Seed Folder & Injection Positions:**
    ```bash
    spikee generate --seed-folder datasets/seeds-cybersec-2025-04 --positions start end
    ```

* **Custom Injection Delimiters:** Inject payloads wrapped in parentheses or Markdown code blocks.
    ```bash
    # Note the use of $'...' for bash to interpret \n correctly
    spikee generate --injection-delimiters $'(INJECTION_PAYLOAD)',$'\n```\nINJECTION_PAYLOAD\n```\n'
    ```

* **Custom Spotlighting Data Markers:** Wrap documents in `<data>` tags for summarization/QnA tasks.
    ```bash
    spikee generate --spotlighting-data-markers $'\n<data>\nDOCUMENT\n</data>\n'
    ```

* **Include Standalone Attacks (e.g., for topical guardrails):**
    ```bash
    spikee generate --seed-folder datasets/seeds-investment-advice \
                    --standalone-attacks datasets/seeds-investment-advice/standalone_attacks.jsonl \
                    --format document
    ```

* **Apply Plugins:** Use the `1337` and `base64` plugins for obfuscation.
    ```bash
    spikee generate --plugins 1337 base64
    ```

* **Filter by Language and Type:** Generate only English data exfiltration and XSS attacks.
    ```bash
    spikee generate --languages en --instruction-filter data-exfil-markdown,xss
    ```

* **Burp Suite Format:** Output payloads suitable for Burp Intruder.
    ```bash
    spikee generate --format burp
    ```

**All Options:**

* `--seed-folder <path>`: Specify seed folder path.
* `--positions [start|middle|end]`: Payload injection position(s). Default: `end`. Ignored if document has `placeholder`.
* `--injection-delimiters '<delim1>','<delim2>'`: Comma-separated payload wrappers (use `INJECTION_PAYLOAD`).
* `--spotlighting-data-markers '<marker1>','<marker2>'`: Comma-separated document wrappers for QnA/Summarization (use `DOCUMENT`). Default: `'\nDOCUMENT\n'`.
* `--standalone-attacks <path.jsonl>`: Include direct attacks from a JSONL file.
* `--plugins <name1> <name2>`: Apply transformations from `plugins/` scripts.
* `--format [full-prompt|document|burp]`: Output format. Default: `full-prompt`.
* `--include-system-message`: Add system messages from `system_messages.toml`.
* `--include-suffixes`: Add suffixes from `adv_suffixes.jsonl`.
* `--match-languages`: Only combine items with matching `lang` fields.
* `--languages <lang1>,<lang2>`: Filter items by language code.
* `--instruction-filter <type1>,<type2>`: Filter by `instruction_type`.
* `--jailbreak-filter <type1>,<type2>`: Filter by `jailbreak_type`.
* `--tag <string>`: Append tag to output filename.

**Dataset JSONL Fields (v0.2):**

Generated `.jsonl` files now include:

* `payload`: The raw text combining the jailbreak and instruction before injection.
* `exclude_from_transformations_regex`: (Optional list of strings) Regex patterns defining parts of the `payload` that plugins should *not* modify.
* `judge_name`: (String) Name of the judge script (`judges/` or built-in) used to determine success. Default: `"canary"`.
* `judge_args`: (String) Arguments passed to the judge function (e.g., the canary string for the `canary` judge, or a regex pattern for the `regex` judge).

---

### 2.5 Testing a Target

`spikee test` evaluates a dataset against a target LLM or guardrail.

**Basic Test:**

```bash
# Requires dataset/example.jsonl and targets/openai_gpt4o.py (or built-in)
# Assumes OPENAI_API_KEY is in .env
spikee test --dataset datasets/example.jsonl \
            --target openai_gpt4o \
            --threads 4
```

**Key Options:**

* `--dataset <path.jsonl>`: Path to the generated dataset.
* `--target <name>`: Name of the target script (`targets/` or built-in).
* `--threads <N>`: Number of concurrent threads (default: 4).
* `--attempts <N>`: Number of standard attempts per dataset entry before trying dynamic attacks (default: 1).
* `--max-retries <N>`: Max retries on API rate limit errors (e.g., 429) per attempt (default: 3).
* `--throttle <seconds>`: Delay between requests per thread (default: 0).
* `--resume-file <path.jsonl>`: Continue a previously interrupted test run.
* `--attack <name>`: **(New in v0.2)** Name of a dynamic attack script (`attacks/` or built-in) to run if standard attempts fail.
* `--attack-iterations <N>`: **(New in v0.2)** Maximum iterations for the dynamic attack script (default: 100).
* `--tag <string>`: Append a custom tag to the results filename.

**Success Determination (v0.2):**

Success is now determined by **Judges**, specified via `judge_name` and `judge_args` in the dataset. The old `--success-criteria` flag is removed. See the Judges sub-guide for details.

**Testing Guardrails:**

Guardrail targets should return a boolean:

* `True`: Attack **bypassed** the guardrail (considered a **success** for `spikee`).
* `False`: Attack was **blocked** by the guardrail (considered a **failure** for `spikee`).

Example:

```bash
# az_prompt_shields target implements this boolean logic
spikee test --dataset datasets/example.jsonl --target az_prompt_shields
```

**Dynamic Attacks:**

If standard attempts fail, use `--attack` to employ iterative strategies:

```bash
# Try the best_of_n attack for up to 50 iterations if standard attempt fails
spikee test --dataset datasets/example.jsonl \
            --target openai_gpt4o \
            --attack best_of_n \
            --attack-iterations 50
```

See the Dynamic Attacks sub-guide for more.

---

### 2.6 Results Analysis and Conversion

Use `spikee results` to analyze or convert test output (`results/*.jsonl`).

**Analyze Results:**

```bash
spikee results analyze --result-file results/results_openai_gpt4o_...jsonl
```

* Provides summary statistics, success rates, and breakdowns by various factors (jailbreak type, instruction type, etc.).
* If dynamic attacks were used, shows overall success vs. initial success and attack improvement.
* `--output-format html`: Generate an HTML report.
* `--false-positive-checks <path.jsonl>`: **(New in v0.2)** Provide results from a run using benign prompts to calculate precision, recall, F1, and accuracy metrics (useful for guardrail evaluation).

**Convert to Excel:**

```bash
spikee results convert-to-excel --result-file results/results_openai_gpt4o_...jsonl
```

Generates an `.xlsx` file from the results JSONL.

---

### 2.7 Understanding Plugins vs. Dynamic Attacks

* **Plugins (`--plugins`)**:
    * Apply **static transformations** during `spikee generate`.
    * Each generated variation is tested independently by `spikee test`.
    * Goal: Test effectiveness of specific, known obfuscation techniques.
    * Example: Use `base64` plugin to see if base64-encoded payloads bypass defenses.

* **Dynamic Attacks (`--attack`)**:
    * Apply **iterative strategies** during `spikee test` if standard attempts fail.
    * An attack script runs sequentially, trying variations until one succeeds or iterations run out.
    * Goal: Find *any* successful variation, potentially using adaptive logic.
    * Example: Use `best_of_n` attack to randomly mutate payloads until one bypasses the target.

Plugins act *before* testing; Attacks act *during* testing (if needed).

---

### 2.8 Migrating from v0.1 / Using Old Tutorial

Key changes from v0.1:

1.  **Success Criteria -> Judges:** The `--success-criteria` flag is gone. Success is now defined per-entry in the dataset via `judge_name` and `judge_args`. Old datasets using `canary` will likely need updating or use the default `canary` judge implicitly.
2.  **Guardrail Logic:** Target scripts for guardrails now return `True` if the attack *succeeded* (bypassed) and `False` if it *failed* (was blocked). This might be the reverse of previous implicit logic.
3.  **Dynamic Attacks:** The `--attack` and `--attack-iterations` flags are new for running iterative attack strategies.
4.  **Dataset Fields:** New fields like `payload`, `exclude_from_transformations_regex`, `judge_name`, `judge_args` are used in generated datasets.

The core concepts of the v0.1 tutorial (creating custom datasets, using Burp, creating custom targets) still apply, but command flags and result interpretation have evolved.

---

## 3. Contributing

Contributions (bug fixes, new targets, plugins, attacks, judges, dataset seeds) are welcome via GitHub pull requests.

---

### Questions or Feedback?

* File issues on [GitHub](https://github.com/WithSecureLabs/spikee).