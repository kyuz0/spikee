import os
import re
import json
import time
import importlib
import random

from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_dataset_name(file_name):
    # Remove the directory path if present
    file_name = os.path.basename(file_name)
    
    # Remove the timestamp at the beginning
    file_name = re.sub(r'^\d+-', '', file_name)
    
    # Remove the '-dataset.jsonl' suffix
    file_name = re.sub(r'-dataset\.jsonl$', '', file_name)
    
    # If the string starts with "seeds-", remove it
    if file_name.startswith("seeds-"):
        file_name = file_name[len("seeds-"):]  # Remove "seeds-"
    
    return file_name

def load_target_module(target_name):
    """
    Dynamically loads the target's Python module from targets/ folder.
    Each target must implement 'process_input(input_text, system_message)'.
    """
    try:
        module = importlib.import_module(f'targets.{target_name}')
        return module
    except ModuleNotFoundError:
        raise ValueError(f"Target '{target_name}' not found. "
                         f"Ensure there's a corresponding module in targets/ directory.")

def read_jsonl_file(file_path):
    """Reads a JSONL file into a list of dicts."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def write_jsonl_file(output_file, data):
    """Writes a list of dicts to JSONL file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

def check_canary_in_response(response, canary):
    """Checks if a canary string is present in the model's response."""
    if not canary:
        return False
    return canary in response

def load_target_module(target_name):
    """
    For the target name, try local first, then package.
    """
    # 1) local
    local_target_path = os.path.join(os.getcwd(), 'targets', f"{target_name}.py")
    if os.path.isfile(local_target_path):
        return load_module_from_path(local_target_path, target_name)
    
    # 2) built-in
    try:
        module = importlib.import_module(f"spikee.targets.{target_name}")
        return module
    except ModuleNotFoundError:
        raise ValueError(f"Target '{target_name}' not found locally or in spikee.targets/")

def load_module_from_path(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    else:
        raise ImportError(f"Could not load module {module_name} from {path}")    
    if not canary:
        return False
    return canary in response

def process_entry(
    entry,
    target_module,
    attempts,
    success_criteria='canary',
    max_retries=5,
    throttle=0
):
    """
    Sends one dataset entry to the target module, optionally retrying on rate-limit errors.
    Returns a dict with the result details.
    """

    input_text = entry["text"]
    canary = entry.get("canary", "")
    attempt_count = 0
    last_result = None

    # Extra metadata
    task_type = entry.get("task_type", None)
    jailbreak_type = entry.get("jailbreak_type", None)
    instruction_type = entry.get("instruction_type", None)
    document_id = entry.get("document_id", None)
    position = entry.get("position", None)
    spotlighting_data_markers = entry.get("spotlighting_data_markers", None)
    injection_delimiters = entry.get("injection_delimiters", None)
    suffix_id = entry.get("suffix_id", None)
    lang = entry.get("lang", 'en')
    system_message = entry.get("system_message", None)
    plugin = entry.get("plugin", None)

    for attempt in range(1, attempts + 1):
        attempt_count = attempt
        retries = 0
        while retries < max_retries:
            try:
                # This is where the target LLM or guardrail is invoked.
                response = target_module.process_input(input_text, system_message)

                if success_criteria == 'canary':
                    success = check_canary_in_response(response, canary)
                elif success_criteria == 'boolean':
                    # Some guardrails return True/False
                    if isinstance(response, bool):
                        success = response
                        response = ''  # or "blocked" / "allowed" as needed
                    else:
                        raise ValueError("Expected boolean response from the target module.")
                else:
                    raise ValueError(f"Unknown success criteria: {success_criteria}")

                result = {
                    "id": entry["id"],
                    "long_id": entry["long_id"],
                    "input": input_text,
                    "response": response if isinstance(response, str) else "",
                    "success": success,
                    "attempts": attempt_count,
                    "task_type": task_type,
                    "jailbreak_type": jailbreak_type,
                    "instruction_type": instruction_type,
                    "document_id": document_id,
                    "position": position,
                    "spotlighting_data_markers": spotlighting_data_markers,
                    "injection_delimiters": injection_delimiters,
                    "suffix_id": suffix_id,
                    "lang": lang,
                    "system_message": system_message,
                    "plugin": plugin,
                    "error": None
                }

                # Throttle if requested
                if throttle > 0:
                    time.sleep(throttle)

                # If the canary was found or boolean was True, return immediately
                if success:
                    return result
                else:
                    # If we didn't succeed, we'll continue to next attempt
                    last_result = result
                break

            except Exception as e:
                error_message = str(e)
                # Typical handling for a 429 or rate-limit type error
                if "429" in error_message:
                    # Exponential backoff or random sleep to handle rate-limit
                    if retries < max_retries - 1:
                        wait_time = random.randint(30, 120)
                        print(f"[Rate limit error] Retrying in {wait_time}s (Attempt {retries+1}/{max_retries})")
                        time.sleep(wait_time)
                        retries += 1
                        continue
                    else:
                        print("[Rate limit error] Max retries reached.")
                else:
                    print(f"[Error] Entry ID {entry['id']}: {error_message}")

                result = {
                    "id": entry["id"],
                    "long_id": entry["long_id"],
                    "input": input_text,
                    "response": None,
                    "success": False,
                    "attempts": attempt_count,
                    "task_type": task_type,
                    "jailbreak_type": jailbreak_type,
                    "instruction_type": instruction_type,
                    "document_id": document_id,
                    "position": position,
                    "spotlighting_data_markers": spotlighting_data_markers,
                    "injection_delimiters": injection_delimiters,
                    "suffix_id": suffix_id,
                    "lang": lang,
                    "system_message": system_message,
                    "plugin": plugin,
                    "error": error_message
                }
                last_result = result
                break

        # If we want to throttle between attempts:
        if throttle > 0:
            time.sleep(throttle)

    # If we exhausted attempts or never succeeded, return the last result
    if last_result:
        return last_result
    else:
        # Fallback if something went wrong very early
        return {
            "id": entry["id"],
            "long_id": entry["long_id"],
            "input": input_text,
            "response": None,
            "success": False,
            "attempts": attempt_count,
            "task_type": task_type,
            "jailbreak_type": jailbreak_type,
            "instruction_type": instruction_type,
            "document_id": document_id,
            "position": position,
            "spotlighting_data_markers": spotlighting_data_markers,
            "injection_delimiters": injection_delimiters,
            "suffix_id": suffix_id,
            "lang": lang,
            "system_message": system_message,
            "plugin": plugin,
            "error": "No response received"
        }

def test_dataset(args):
    """
    Main test routine:
      - Loads target from targets/{target_name}.py
      - Reads dataset
      - Tests each entry in parallel threads
      - Allows resuming from a partial results file (via --resume-file)
      - Immediately cancels all threads & saves partial results if CTRL+C is pressed
    """

    target_name = args.target
    num_threads = args.threads
    dataset_file = args.dataset
    attempts = args.attempts
    success_criteria = args.success_criteria
    resume_file = args.resume_file
    throttle = args.throttle

    # Load target plugin (LLM or guardrail)
    target_module = load_target_module(target_name)

    # Load the dataset, index by ID for convenience
    dataset = read_jsonl_file(dataset_file)
    dataset_entries = {entry['id']: entry for entry in dataset}

    # If resuming, read existing partial results
    completed_ids = set()
    results = []
    if resume_file and os.path.exists(resume_file):
        existing_results = read_jsonl_file(resume_file)
        completed_ids = set(r['id'] for r in existing_results)
        results = existing_results
        print(f"[Resume] Found {len(completed_ids)} completed entries in {resume_file}.")

    # Filter out entries already completed
    entries_to_process = [e for e in dataset if e['id'] not in completed_ids]

    # Prepare output filename
    timestamp = int(time.time())
    os.makedirs('results', exist_ok=True)
    output_file = os.path.join(
        'results',
        f"results_{target_name}-{extract_dataset_name(dataset_file)}_{timestamp}.jsonl"
    )

    print(f"[Info] Testing {len(entries_to_process)} new entries (threads={num_threads}).")
    print(f"[Info] Output will be saved to: {output_file}")

    # Use a ThreadPoolExecutor for parallel processing
    executor = ThreadPoolExecutor(max_workers=num_threads)

    # Submit tasks: each future is mapped to a dataset entry
    future_to_entry = {
        executor.submit(
            process_entry,
            entry,
            target_module,
            attempts,
            success_criteria,
            max_retries=3,   # example
            throttle=throttle
        ): entry
        for entry in entries_to_process
    }

    try:
        with tqdm(total=len(future_to_entry), desc="Processing entries") as pbar:
            for future in as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    result_entry = future.result()
                    if result_entry:
                        results.append(result_entry)
                except Exception as e:
                    # Catch any errors not handled inside process_entry
                    print(f"[Error] Entry ID {entry['id']}: {e}")

                pbar.update(1)

    except KeyboardInterrupt:
        print("\n[Interrupt] CTRL+C pressed. Cancelling all pending work...")
        # Cancel all running & pending futures immediately
        executor.shutdown(wait=False, cancel_futures=True)

        # We do NOT re-collect from any incomplete tasks — so partial results only
        # The for-loop ends here, so we skip uncompleted tasks
    finally:
        # Ensure the executor is shut down, even if normal completion
        executor.shutdown(wait=False, cancel_futures=True)
    
    # Write out the partial or full results we have so far
    write_jsonl_file(output_file, results)
    print(f"[Done] Testing finished (partial or complete). Results saved to {output_file}")
