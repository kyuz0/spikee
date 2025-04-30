# Writing Dynamic Attack Scripts

Dynamic attacks provide an iterative way to test targets when standard payloads fail. They are executed by `spikee test --attack <name>` if the initial `--attempts` do not succeed.

## Structure

An attack script must be placed in the `attacks/` directory (local workspace or built-in) and contain a function named `attack`.

**Signature:**

```python
import threading # For bar_lock
from typing import Tuple, Optional, Dict, Any

# Define your attack logic function (can be in the same file or imported)
def generate_next_attack_variation(base_payload, iteration_num):
    # Example: Append iteration number
    # Replace this with your actual attack variation generation logic
    return f"{base_payload} [ATTACK_VAR_{iteration_num}]"

def attack(
    entry: Dict[str, Any],
    target_module: Any, # Wrapped target module (handles retries/throttling)
    call_judge: callable,
    max_iterations: int,
    attempts_bar: Optional[object] = None, # tqdm progress bar instance
    bar_lock: Optional[threading.Lock] = None # Lock for thread-safe bar updates
) -> Tuple[int, bool, str, str]:
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

    last_payload = original_text # Fallback value
    last_response = ""
    success_flag = False

    # 2. Loop up to max_iterations.
    for i in range(1, max_iterations + 1):
        # 3. Generate the next attack variation based on 'payload_to_modify'.
        current_variation = generate_next_attack_variation(payload_to_modify, i) # Your logic here

        # 4. Construct the full input text for the target.
        # If 'payload' exists in the entry, substitute the modified payload back into the original text structure.
        # Otherwise, the 'current_variation' is the full text to send.
        if entry.get("payload"):
            idx = original_text.find(entry["payload"])
            if idx != -1:
                current_input = original_text[:idx] + current_variation + original_text[idx+len(entry["payload"]):]
            else: # Fallback if payload wasn't found (shouldn't happen ideally)
                 current_input = current_variation # Or maybe error out?
        else:
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

**Key Points:**

1.  **Location:** Store custom attacks in `./attacks/your_attack_name.py`.
2.  **Function Name:** Must be `attack`.
3.  **Parameters:** Receives the dataset `entry`, the wrapped `target_module`, the `call_judge` function, `max_iterations`, and optional progress bar components (`attempts_bar`, `bar_lock`).
4.  **Target Interaction:** Call `target_module.process_input()`. The wrapper handles retries/throttling for *each individual call*. Your script controls the *iteration* logic.
5.  **Success Check:** Use `call_judge(entry, response)` to determine if an iteration succeeded.
6.  **Iteration Limit:** Your main loop *must not* exceed `max_iterations`.
7.  **Progress Bar:** Update `attempts_bar` *inside* the `bar_lock` context manager for each iteration attempted. If breaking early on success, adjust `attempts_bar.total` to reflect skipped iterations accurately.
8.  **Return Value:** Return a tuple `(iterations_attempted, success_flag, last_payload, last_response)`.
9.  **Payload vs. Text:** Decide whether your attack modifies the `entry['payload']` (recommended) and substitutes it back into `entry['text']`, or modifies `entry['text']` directly. Using `payload` allows the attack to focus on the malicious part.
10. **State:** Attack functions should ideally be stateless between entries, relying only on the `entry` data for context. If state is needed *within* an attack sequence for a single entry, manage it within the `attack` function's scope.