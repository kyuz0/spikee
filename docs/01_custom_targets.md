# Creating Custom Targets

Targets in **Spikee** are Python scripts that define how `spikee test` sends prompts and processes responses. They can call any API, local or remote LLM, or apply guardrail logic.

## Structure

Place your target module in:

```
./targets/your_target_name.py
```

### Required Function

Each file **must** define:

```python
from typing import Union, Tuple, Optional
import os
from dotenv import load_dotenv

# Optional: Load .env for API keys
# load_dotenv()

def process_input(
    input_text: str,
    system_message: Optional[str] = None,
    target_options: Optional[str] = None,
    logprobs: bool = False
) -> Union[str, bool, Tuple[str, Optional[dict]]]:
    """
    Process the input and return a result.

    Args:
        input_text: prompt from Spikee.
        system_message: optional context message.
        target_options: agnostic string passed at runtime (often a model/deployment key). May be ignored if unused.
        logprobs: hint for returning log-prob data (ignore if unsupported).

    Returns:
        str: LLM response text.
        bool: for guardrail targets: True if attack bypassed (success), False if blocked (failure).
        Tuple[str, Optional[dict]]: (response, logprobs data) if requested/supported.
    """
    # --- Implementation ---
    # 1. Resolve and validate `target_options` if used.
    # 3. Build messages using input_text and system_message.
    # 4. Call API or LLM; catch and log exceptions.
    # 5. Return text or boolean or (text, logprobs).
    
    # Example stub:
    response_text = f"Processed: {input_text[:50]}..."
    return response_text
```

* `input_text`: the prompt from Spikee.
* `system_message`: optional system/context message.
* **`target_options`**: a **string** passed at runtime—often used to choose a model or deployment, but you can ignore it entirely if not needed.
* `logprobs`: hint for log-prob support; return `(text, logprobs)` if handling, else ignore.

## `target_options` Guidance

* **Optional**: targets that don’t need runtime configuration can skip using `target_options`.
* **Common use**: select among multiple models.

## Return Types

* **LLM targets**: return `str`, or `(str, dict)` if providing log-prob details.
* **Guardrail targets**: return `bool` (`True` means attack **bypassed**, `False` means **blocked**).

## Error Handling

* If you validate `target_options`, **raise** on invalid values; do **not** silently fallback.
* Wrap API/LLM calls in `try/except`, log the error, and re-raise so Spikee’s retry logic (`--max-retries`) applies.

## Example

```python
# ./targets/my_api_target.py
import os
import requests
from dotenv import load_dotenv
from typing import Optional, Tuple

load_dotenv()
API_ENDPOINT = os.getenv("MY_API_ENDPOINT")
API_KEY      = os.getenv("MY_API_KEY")


def process_input(
    input_text: str,
    system_message: Optional[str] = None,
    target_options: Optional[str] = None,
    logprobs: bool = False
) -> str:
    # Ignoring target_options in this simple example
    if not API_ENDPOINT or not API_KEY:
        raise ValueError("Missing API credentials in .env")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"prompt": input_text}
    if system_message:
        payload["system_prompt"] = system_message

    try:
        resp = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("completion", "")
    except Exception as e:
        print(f"Error calling API: {e}")
        raise
```

With this pattern, your target can remain flexible: parse or ignore `target_options` as you see fit, or use it to drive runtime behavior without duplicating code.
