# Guide to Seed Datasets

Spikee comes with a variety of built-in seed datasets, each designed for a specific testing purpose. These seeds are located in the `datasets/` directory after you run `spikee init`. You can list them at any time with `spikee list seeds`.

This guide provides an overview of each available seed folder.

---

### `seeds-cybersec-2025-04`
*   **Purpose:** A general-purpose dataset for testing prompt injection. It focuses on common attack goals seen in web application security, such as data exfiltration, cross-site scripting (XSS), and resource exhaustion.

### `seeds-in-the-wild-jailbreak-prompts`
*   **Purpose:** Contains approximately 1,400 real-world jailbreak prompts collected from public sources like Discord and Reddit (filtered from the TrustAIRLab dataset). Ideal for testing a target's resilience against known, publicly available jailbreaks.
*   **Note:** This dataset requires you to run a fetch script to download the prompts. See the `README.md` inside the seed folder for instructions. It uses an LLM judge by default.

### `seeds-simsonsun-high-quality-jailbreaks`
*   **Purpose:** A high-quality set of contamination-free jailbreak prompts, specifically curated to avoid overlap with the training data of many common safety classifiers.
*   **Note:** This dataset requires you to run a fetch script. See the `README.md` inside the seed folder.

### `seeds-wildguardmix-harmful`
*   **Purpose:** A dataset for testing harmful content generation. The prompts are sourced from the WildGuard-Mix dataset.
*   **Note:** This dataset requires you to run a fetch script. See the `README.md` inside the seed folder. It uses an LLM judge by default.

### `seeds-wildguardmix-harmful-fp`
*   **Purpose:** A companion dataset to `seeds-wildguardmix-harmful`, containing benign (harmless) prompts. This dataset is intended for use with the `--false-positive-checks` flag to measure how often a guardrail incorrectly blocks legitimate prompts when evaluating harmful content filters.

### `seeds-investment-advice`
*   **Purpose:** Designed to test topical guardrails that are supposed to block personal financial or investment advice. It includes both malicious instructions and standalone attack prompts.

### `seeds-investment-advice-fp`
*   **Purpose:** A companion dataset to `seeds-investment-advice`, containing benign (harmless) queries about financial topics. This dataset is intended for use with the `--false-positive-checks` flag to measure how often a guardrail incorrectly blocks legitimate prompts.

### `seeds-sysmsg-extraction-2025-04`
*   **Purpose:** Specifically designed to test for system prompt extraction. The instructions and judges are tailored to detect if the target model leaks its own system prompt or initial instructions.

### `seeds-llm-mailbox`
*   **Purpose:** An example seed tailored for testing an email summarization feature. The documents are sample emails, and the instructions are designed to test for vulnerabilities in that specific context. See the associated [blog post](https://labs.reversec.com/posts/2025/01/spikee-testing-llm-applications-for-prompt-injection) for a detailed walkthrough.

---

### Utility Seeds

### `seeds-mini-test`
*   **Purpose:** A very small set of examples for quick, functional testing of Spikee itself. Use this to verify your setup or to test a new custom target or plugin without running a large number of tests.

### `seeds-empty`
*   **Purpose:** An empty template folder. It contains empty `documents.jsonl`, `jailbreaks.jsonl`, and `instructions.jsonl` files. This is the recommended starting point when creating a new dataset from scratch, especially for standalone attacks.

### `zzz_LEGACY_seeds-targeted-2024-12`
*   **Purpose:** A legacy dataset that has been superseded by `seeds-cybersec-2025-04`. It is kept for backward compatibility.