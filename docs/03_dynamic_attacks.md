# Writing Dynamic Attack Scripts

Dynamic attacks provide an iterative way to test targets when standard payloads fail. They are executed by `spikee test --attack <name>` if the initial samples i nthe dataset do not succeed.

## Structure

An attack script must be placed in the `attacks/` directory (local workspace or built-in) and contain a function named `attack`.

**Basic Signature:**

```python
import threading # For bar_lock
from typing import Tuple, Optional, Dict, Any

def attack(
    entry: Dict[str, Any],
    target_module: Any,
    call_judge: callable,
    max_iterations: int,
    attempts_bar: Optional[object] = None,
    bar_lock: Optional[threading.Lock] = None
) -> Tuple[int, bool, str, str]:
```

**Signature with Options Support:**

```python
from typing import List

def get_available_option_values() -> List[str]:
    """
    Return supported attack options; first option is default.
    
    Returns:
        List[str]: List of supported option strings. The first option is considered
                  the default and will be highlighted when listing attacks.
    """
    return [
        "mode=dumb",     # Default option (first in list)
        "mode=advanced",
        "strategy=aggressive",
        "strategy=stealth"
    ]

def attack(
    entry: Dict[str, Any],
    target_module: Any,
    call_judge: callable,
    max_iterations: int,
    attempts_bar: Optional[object] = None,
    bar_lock: Optional[threading.Lock] = None,
    attack_option: Optional[str] = None
) -> Tuple[int, bool, str, str]:
```

## Attack Options

Attacks can optionally support configuration options by implementing `get_available_option_values()` and accepting an `attack_option` parameter in their `attack()` function.

**Usage:**
```bash
# Use default options
spikee test --attack prompt_decomposition --attack-iterations 50

# Specify attack options
spikee test --attack prompt_decomposition --attack-iterations 25 --attack-options "mode=gpt4o-mini"

# Use local model
spikee test --attack my_custom_attack --attack-iterations 100 --attack-options "strategy=stealth"
```

**Option Format:**
- Single option string (e.g., `"mode=advanced"`, `"strategy=aggressive"`)
- No complex parsing needed unlike plugins (attacks are singular)

## Implementation Example

```python
    """
    Executes a dynamic attack strategy.

    Args:
        entry (Dict[str, Any]): The dataset entry dictionary. Access fields like
            'text', 'payload', 'system_message', 'judge_name', 'judge_args',
            'exclude_from_transformations_regex'.
        target_module (Any): The *wrapped* target module instance. Call its
            `process_input(text, system_message, logprobs=...)` method. This
            wrapper already handles retries and throttling per call.
        call_judge (callable): Function to evaluate success. Call as
            `success = call_judge(entry, response)`.
        max_iterations (int): Maximum number of attack iterations allowed for this entry.
            Your loop must respect this limit.
        attempts_bar (tqdm, optional): Progress bar for total attempts across all entries.
            Update using `with bar_lock: attempts_bar.update(1)`.
        bar_lock (threading.Lock, optional): Lock to safely update the shared progress bar.
        attack_option (str, optional): Configuration option passed via --attack-options.

    Returns:
        Tuple[int, bool, str, str]:
            - iterations_attempted (int): How many iterations were actually run.
            - success_flag (bool): True if any iteration succeeded, False otherwise.
            - last_payload (str): The input text used in the final iteration.
            - last_response (str): The response from the target in the final iteration.
    """
    # --- Implementation ---
    # 1. Get necessary info from 'entry' (e.g., original text, payload).
    original_text = entry.get("text", "")
    # Use 'payload' if available, otherwise use the full 'text' as the base for modification
    payload_to_modify = entry.get("payload", original_text)
    system_message = entry.get("system_message", None)

    # Understanding payload vs. full text:
    # - 'text' is the complete prompt that will be sent to the target
    # - 'payload' (if present) is just the malicious part that was injected
    # - If you have a payload, modify it and substitute back into the full text
    # - If no payload, treat the entire text as the thing to modify
    
    last_payload = original_text # Fallback value
    last_response = ""
    success_flag = False

    # 2. Loop up to max_iterations.
    for i in range(1, max_iterations + 1):
        # 3. Generate the next attack variation based on 'payload_to_modify'.
        current_variation = generate_next_attack_variation(payload_to_modify, i) # Your logic here

        # 4. Construct the full input text for the target.
        # If 'payload' exists, substitute the modified payload back into the original text.
        # This preserves the document structure while only modifying the malicious part.
        if entry.get("payload") and entry["payload"] in original_text:
            current_input = original_text.replace(entry["payload"], current_variation)
        else:
            # No payload field, so treat the variation as the complete text to send
            current_input = current_variation

        last_payload = current_input

        # 5. Call the target module. Use try/except for robustness.
        try:
            # Target module wrapper handles retries per call.
            # Request logprobs=False unless your attack specifically needs them.
            response, logprobs_value = target_module.process_input(current_input, system_message, logprobs=False)
            # Ensure response is a string for the judge and final return value
            last_response = response if isinstance(response, str) else str(response)

            # 6. Evaluate success using call_judge.
            success_flag = call_judge(entry, last_response)

        except Exception as e:
            last_response = f"Error during attack iteration {i}: {e}"
            success_flag = False
            # Log the error, decide if you want to continue or break
            # print(f"[Attack Error] Entry {entry.get('id', 'N/A')}, Iteration {i}: {e}")
            # break # Optional: stop attack on error

        # 7. Update the shared progress bar safely for each iteration attempt.
        if attempts_bar and bar_lock:
            with bar_lock:
                attempts_bar.update(1)

        # 8. If successful, break the loop and return early.
        if success_flag:
             # Adjust total attempts in the progress bar if stopping early
             if attempts_bar and bar_lock:
                  with bar_lock:
                      remaining_iterations = max_iterations - i
                      if attempts_bar.total and attempts_bar.total > remaining_iterations: # Prevent negative total
                          attempts_bar.total -= remaining_iterations
                      # Avoid setting total below current count if something went wrong
                      elif attempts_bar.total and attempts_bar.total <= attempts_bar.n:
                           attempts_bar.total = attempts_bar.n
             return i, True, last_payload, last_response

        # Optional: Add a small delay between iterations if needed by the attack logic or target API
        # import time
        # time.sleep(0.1)

    # 9. If loop finishes without success, return the final state after max_iterations.
    return max_iterations, False, last_payload, last_response

```

## Attack Options (Advanced)

Attacks can optionally support configuration options by implementing `get_available_option_values()` and using the `attack_option` parameter.

**Usage:**
```bash
# Basic usage (no options)
spikee test --attack my_attack --attack-iterations 50

# With options
spikee test --attack prompt_decomposition --attack-options "mode=gpt4o-mini"
```

**Implementation:**
```python
from typing import List

def get_available_option_values() -> List[str]:
    """Return supported options; first option is default."""
    return ["mode=dumb", "mode=advanced"]

def attack(..., attack_option: Optional[str] = None):
    # Parse attack_option if needed
    mode = "dumb"  # default
    if attack_option and attack_option.startswith("mode="):
        mode = attack_option.replace("mode=", "")
    
    # Use mode in your attack logic
    # ...
```

**Key Points:**

1.  **Location:** Store custom attacks in `./attacks/your_attack_name.py`.
2.  **Function Name:** Must be `attack`.
3.  **Parameters:** Receives the dataset `entry`, wrapped `target_module`, `call_judge` function, `max_iterations`, and optional progress bar components.
4.  **Target Interaction:** Call `target_module.process_input()`. The wrapper handles retries/throttling for *each individual call*. Your script controls the *iteration* logic.
5.  **Success Check:** Use `call_judge(entry, response)` to determine if an iteration succeeded.
6.  **Iteration Limit:** Your main loop *must not* exceed `max_iterations`.
7.  **Progress Bar:** Update `attempts_bar` *inside* the `bar_lock` context manager for each iteration attempted. If breaking early on success, adjust `attempts_bar.total` to reflect skipped iterations accurately.
8.  **Return Value:** Return a tuple `(iterations_attempted, success_flag, last_payload, last_response)`.
9.  **Payload vs. Text:** Decide whether your attack modifies the `entry['payload']` (recommended) and substitutes it back into `entry['text']`, or modifies `entry['text']` directly. Using `payload` allows the attack to focus on the malicious part.
10. **State:** Attack functions should ideally be stateless between entries, relying only on the `entry` data for context. If state is needed *within* an attack sequence for a single entry, manage it within the `attack` function's scope.
11. **Options:** Attacks can optionally accept an `attack_option` parameter for configuration. Implement `get_available_option_values()` to define supported options.