# spikee - Simple Prompt Injection Kit for Evaluation and Exploitation

Version: 0.1

```
   _____ _____ _____ _  ________ ______ 
  / ____|  __ \_   _| |/ /  ____|  ____|
 | (___ | |__) || | | ' /| |__  | |__   
  \___ \|  ___/ | | |  < |  __| |  __|  
  ____) | |    _| |_| . \| |____| |____ 
 |_____/|_|   |_____|_|\_\______|______|
                                        
spikee - Simple Prompt Injection Kit for Evaluation and Exploitation
```

[spikee.ai](https://spikee.ai/) is a *Simple Prompt Injection Kit for Evaluation and Exploitation* developed by WithSecure Consulting. It provides a comprehensive toolset for generating datasets and testing standalone LLMs, guardrails, and full LLM application pipelines for their susceptibility to known prompt injection patterns.

---

## 1. Installation

### 1.1 PyPI Installation (Recommended)

You can install **spikee** directly from PyPI:

```bash
pip install spikee
```

Once installed, the `spikee` command should be available in your terminal (assuming your Python/Scripts path is on the system `PATH`).

### 1.2 Local Installation (From Source)

If you prefer to install locally from the cloned repository:

1. Clone the repository:
   ```bash
   git clone https://github.com/WithSecureLabs/spikee.git
   cd spikee
   ```
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. Install spikee and its dependencies:
   ```bash
   pip install .
   ```

### 1.3 Local Inference

Optionally, if you're planning on using targets that require local inference:

```bash
pip install -r requirements-local-inference.txt
```

---

## 2. Usage

### 2.1 Initializing a Workspace

Before generating or testing datasets, you’ll want a **local workspace** with directories for `datasets/`, `plugins/`, `targets/`, and `results/`. Run:

```bash
spikee init
```

**What this does**:

- Creates `datasets/`, `results/`, `targets/`, `plugins/` in your current directory.
- Copies a sample `.env-example` for storing API keys.
- Copies a sample plugin (`sample_plugin.py`), a sample target (`sample_target.py`), and default seeds (`seeds-mini-test`, `seeds-targeted-2024-12`).
- Use `--force` to overwrite existing folders/files.

---

### 2.2 Listing Seeds, Datasets, Targets, and Plugins

After your workspace is set up, you can view what’s available locally (and built-in for targets/plugins) using the `list` command:

```bash
spikee list seeds
spikee list datasets
spikee list targets
spikee list plugins
```

- **`spikee list seeds`**: Shows seed folders in `datasets/` containing a `base_documents.jsonl`.
- **`spikee list datasets`**: Lists generated `.jsonl` files in the **top-level** of `datasets/` (not subfolders).
- **`spikee list targets`**: Lists local `.py` files under `targets/`, plus built-in targets shipped with spikee.
- **`spikee list plugins`**: Lists local `.py` files in `plugins/`, plus built-in plugins shipped with spikee.

Use these commands any time to check which assets you have before proceeding with generation or testing.

---

### 2.3 Environment Variables

Many targets (e.g., Azure, AWS, OpenAI) require API keys. You can place them in a `.env` file (copied from `env-example`) and store it in your workspace:

```
AZURE_OPENAI_API_KEY=...
OPENAI_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
...
```

When you run any `spikee` command, the `.env` file is automatically loaded so your environment variables become available to the underlying LLM or guardrail modules.

---

### 2.4 Generating a Dataset

The `generate` subcommand creates datasets tailored for testing prompt injection. These datasets can include various combinations of documents, jailbreaks, and instructions.

#### Simple Example

```bash
spikee generate --positions start middle end
```

*What this does:*

- Combines base documents, jailbreaks, and instructions from `datasets/seeds-mini-test` by default (you can change seeds with `--seed-folder`).
- Inserts payloads at the **start**, **middle**, and **end** of the documents (default is just **end**).
- Produces a `.jsonl` dataset in `datasets/`.

#### Injection Delimiters

To test LLM/guardrail handling of structured formats:

```bash
spikee generate --injection-delimiters $'\nINJECTION_PAYLOAD\n',$'(INJECTION_PAYLOAD)'
```

#### Spotlighting Data Markers

Wrap your document in tags (or any custom delimiter) to see if LLMs parse them correctly:

```bash
spikee generate --spotlighting-data-markers $'\n<data>\nDOCUMENT\n</data>\n'
```

#### Standalone Attacks

Inject pure malicious prompts unlinked to any base document:

```bash
spikee generate --standalone-attacks datasets/seeds-mini-test/standalone_attacks.jsonl
```

#### Plugins

Apply transformations or obfuscations to your attacks, e.g.:

```bash
spikee generate --plugins 1337
```

---

### 2.5 Testing a Target

The `test` subcommand evaluates a dataset against an LLM or guardrail target.

1. **Create a `.env` file** to hold your API keys (OpenAI, Azure, etc.).
2. **Run**:

   ```bash
   spikee test --dataset datasets/1732025823-seeds-mini-full-dataset.jsonl \
               --target az_gpt4_turbo \
               --success-criteria canary \
               --threads 4
   ```

   - **`--target az_gpt4_turbo`**: Looks for local `targets/az_gpt4_turbo.py`; if missing, uses a built-in target.
   - **`--success-criteria canary`**: Checks if the dataset’s “canary word” appears in the LLM’s response.  
     For guardrails, you may use `boolean` (True/False).

3. **Interrupt & Resume**  
   - Press `CTRL+C` to stop mid-test.  
   - Results are saved in `results/`.  
   - Resume later:

     ```bash
     spikee test --dataset datasets/... --target ... --resume-file results/results_xxx.jsonl
     ```

---

### 2.6 Results Analysis and Conversion

Use the `results` subcommand to analyze or convert your output.

#### Analyze

```bash
spikee results analyze --result-file results/test_results.jsonl
```

- Summarizes success rates, jailbreak/instruction breakdown, etc.
- Generate an HTML report:

  ```bash
  spikee results analyze --result-file results/test_results.jsonl --output-format html
  ```

#### Convert to Excel

```bash
spikee results convert-to-excel --result-file results/test_results.jsonl
```

Generates `test_results.xlsx` for easy spreadsheet viewing.

---

## 3. Contributing

We welcome contributions to **spikee**! Here are a few ways you can help:

- **Bug Fixes**: Submit fixes or improvements for issues you find.  
- **Expand the Dataset**: Add new jailbreaks, instructions (e.g., low-resource languages, glitch tokens), or other creative attacks.  
- **New Targets**: Add support for more LLMs or guardrails (AWS Bedrock, Azure, local inference, etc.).  
- **Burp Extension**: Integrate **spikee** into security testing workflows by creating a Burp Suite extension.

Simply fork the repo, make your changes, and submit a pull request. Thanks for contributing!

---

### Questions or Feedback?

- Visit [spikee.ai](https://spikee.ai/) for more info and examples.
- File issues or feature requests on [GitHub](https://github.com/WithSecureLabs/spikee).

**Enjoy testing and keep your prompts safe!**