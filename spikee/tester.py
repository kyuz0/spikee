import os
import re
import json
import time
import importlib
import random
import threading
import inspect
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class AdvancedTargetWrapper:
    """
    A wrapper for a target module's process_input method that incorporates both:
      - A loop for a given number of independent attempts (num_attempts), and
      - A retry strategy for handling 429 errors (max_retries) with throttling.
    
    This is designed to be passed to the attack() function so that each call to process_input()
    will try up to num_attempts times (each with up to max_retries on quota errors) before failing.
    
    Parameters:
      target_module: The original target module that provides process_input(input_text, system_message[, logprobs]).
      num_attempts (int): Number of independent attempts to call process_input per invocation.
      max_retries (int): Maximum number of retries per attempt (e.g. on 429 errors).
      throttle (float): Number of seconds to wait after a successful call.
    """
    def __init__(self, target_module, max_retries=3, throttle=0):
        self.target_module = target_module
        self.max_retries = max_retries
        self.throttle = throttle
        # Determine if the underlying process_input supports a 'logprobs' parameter.
        sig = inspect.signature(self.target_module.process_input)
        self.supports_logprobs = 'logprobs' in sig.parameters

    def process_input(self, input_text, system_message=None, logprobs=False):
        last_error = None
        # Loop over the specified number of independent attempts.
        
        retries = 0
        while retries < self.max_retries:
            try:
                # Call the underlying target_module's process_input.
                if self.supports_logprobs:
                    result = self.target_module.process_input(input_text, system_message, logprobs)
                else:
                    result = self.target_module.process_input(input_text, system_message)
                
                # If the result is a tuple (response, logprobs), unpack it.
                if isinstance(result, tuple) and len(result) == 2:
                    response, logprobs_value = result
                else:
                    # Legacy target: only a response is returned.
                    response = result
                    logprobs_value = None
                    
                if self.throttle > 0:
                    time.sleep(self.throttle)
                
                return response, logprobs_value
            except Exception as e:
                last_error = e
                # If error indicates a quota issue, wait a random interval and retry.
                if "429" in str(e) and retries < self.max_retries - 1:
                    wait_time = random.randint(30, 120)
                    time.sleep(wait_time)
                    retries += 1
                else:
                    break

        # If all attempts failed, raise the last encountered error.
        raise last_error if last_error else Exception("All attempts failed.")

def validate_tag(tag):
    """
    Validates that a tag is safe to use in a filename.
    
    Args:
        tag (str): The tag to validate
        
    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): True if tag is valid, False otherwise
            - error_message (str): Reason for validation failure or None if valid
    """
    if tag is None:
        return True, None
        
    # Check for empty string after stripping whitespace
    if len(tag.strip()) == 0:
        return False, "Tag cannot be empty or whitespace only"
    
    # Check length (reasonable max length for filename component)
    MAX_LENGTH = 50
    if len(tag) > MAX_LENGTH:
        return False, f"Tag exceeds maximum length of {MAX_LENGTH} characters"
    
    # Check for valid characters - alphanumeric, dash and underscore only
    pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    if not pattern.match(tag):
        return False, "Tag can only contain letters, numbers, dash (-) and underscore (_)"
    
    return True, None

def extract_dataset_name(file_name):
    file_name = os.path.basename(file_name)
    file_name = re.sub(r'^\d+-', '', file_name)
    file_name = re.sub(r'-dataset\.jsonl$', '', file_name)
    if file_name.startswith("seeds-"):
        file_name = file_name[len("seeds-"):]
    return file_name

def read_jsonl_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def write_jsonl_file(output_file, data):
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

def append_jsonl_entry(output_file, entry, file_lock):
    """Appends a single entry to a JSONL file in a thread-safe manner."""
    with file_lock:
        with open(output_file, 'a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

def check_canary_in_response(response, canary):
    if not canary:
        return False
    return canary in response

def load_module_from_path(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    raise ImportError(f"Could not load module {module_name} from {path}")

def load_target_module(target_name, max_retries, throttle):
    local_target_path = os.path.join(os.getcwd(), 'targets', f"{target_name}.py")
    if os.path.isfile(local_target_path):
        target_mod = load_module_from_path(local_target_path, target_name)
    else:
        try:
            target_mod = importlib.import_module(f"spikee.targets.{target_name}")
        except ModuleNotFoundError:
            raise ValueError(f"Target '{target_name}' not found locally or in spikee.targets/")
    
    # Wrap the target module with AdvancedTargetWrapper, 
    return AdvancedTargetWrapper(target_mod, max_retries=max_retries, throttle=throttle)

def load_attack_by_name(attack_name):
    """
    Loads an attack module from a new "attacks" folder or from built-in package data.
    """
    local_attack_path = Path(os.getcwd()) / "attacks" / f"{attack_name}.py"
    if local_attack_path.is_file():
        spec = importlib.util.spec_from_file_location(attack_name, local_attack_path)
        attack_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(attack_module)
        return attack_module
    try:
        return importlib.import_module(f"spikee.attacks.{attack_name}")
    except ModuleNotFoundError:
        raise ValueError(f"Attack '{attack_name}' not found locally or in spikee.attacks")

def load_judge_module(judge_name):
    """
    Looks for `judges/{judge_name}.py` locally first,
    then falls back to built-in judges.
    """
    from pathlib import Path
    local_path = Path(os.getcwd()) / "judges" / f"{judge_name}.py"
    if local_path.is_file():
        spec = importlib.util.spec_from_file_location(judge_name, local_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    try:
        return importlib.import_module(f"spikee.judges.{judge_name}")
    except ModuleNotFoundError:
        raise ValueError(f"Judge '{judge_name}' not found locally or built-in.")

def call_judge(entry, output):
    """
    Determines if the LLM output indicates a successful attack.
    
    If the output provided is a boolean that value is used to indicate success or failure. 
    This is used when testing LLM guardrail targets, which return True if the attack went 
    through the guardrail (attack successful) and False if the guardrail stopped it.
    
    In all other cases (i.e. when using a target LLM), the appropriate judge module
    for the attack is loaded and its judge() function is called.
    """
    if isinstance(output, bool):
        return output
      
    else:
        judge_name = entry.get("judge_name", "canary")
        judge_args = entry.get("judge_args", "")
        llm_input = entry["text"]
        judge_module = load_judge_module(judge_name)
        return judge_module.judge(llm_input=llm_input, llm_output=output, judge_args=judge_args)

def _do_single_request(entry, input_text, target_module, num_attempt,
                       attempts_bar, global_lock):
    """
    Executes one request against the target by calling its process_input() method.
    The target_module is assumed to be an instance of AdvancedTargetWrapper that
    already implements retries and throttling. 

    Parameters:
      entry (dict): The dataset entry.
      input_text (str): The prompt text.
      target_module: The wrapped target module.
      num_attempt: The current attempt number.
      attempts_bar (tqdm): Progress bar to update.
      global_lock (threading.Lock): Lock for safely updating the progress bar.

    Returns:
      tuple: (result_dict, success)
    """
    # Extract metadata from the entry.
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

    try:
        start_time = time.time()
        response, _ = target_module.process_input(input_text, system_message)
        end_time = time.time()
        response_time = end_time - start_time
        success = call_judge(entry, response)
        response_str = response if isinstance(response, str) else ""
        error_message = None
    except Exception as e:
        error_message = str(e)
        response_str = ""
        response_time = None
        success = False
        print("[Error] {}: {}".format(entry["id"], error_message))

    with global_lock:
        attempts_bar.update(1)

    result_dict = {
        "id": entry["id"],
        "long_id": entry["long_id"],
        "input": input_text,
        "response": response_str,
        "response_time": response_time,
        "success": success,
        "attempts": num_attempt,
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
        "attack_name": "None",
        "error": error_message
    }
    return result_dict, success

def process_entry(entry, target_module, attempts=1,
                  attack_module=None, attack_iterations=0,
                  attempts_bar=None, global_lock=None):
    """
    Processes one dataset entry.

    First, it performs a single standard attempt by calling _do_single_request().
    The final standard attempt result is recorded (with "attack_name": "None").
    If this attempt is unsuccessful and an attack module is provided,
    it then calls the attack() method and records its result as a separate entry.

    The target_module passed here is assumed to be wrapped (AdvancedTargetWrapper)
    and therefore already handles retries and multiple attempts.

    Returns:
      List[dict]: A list containing one or two result entries.
    """
    original_input = entry["text"]
    std_result = None
    std_success = False

    for attempt_num in range(1, attempts + 1):
        std_result, success_now = _do_single_request(
            entry, original_input, target_module, attempt_num,
            attempts_bar, global_lock
        )
        if success_now:
            std_success = True
            break

    results_list = [std_result]

    if std_success and attack_module:
        # Remove all the attempts that we are not going to do any longer as we are skipping the dynamic attacks 
        with global_lock:
            attempts_bar.total = attempts_bar.total - attack_iterations

    # If the standard attempt fail and an attack module is provided, run the dynamic attack.
    if (not std_success) and attack_module:
        try:
            start_time = time.time()
            attack_attempts, attack_success, attack_input, attack_response = attack_module.attack(
                entry, target_module, call_judge, attack_iterations, attempts_bar, global_lock
            )
            end_time = time.time()
            response_time = end_time - start_time

            attack_result = {
                "id": f"{entry['id']}-attack",
                "long_id": entry["long_id"] + "-" + attack_module.__name__,
                "input": attack_input,
                "response": attack_response,
                "response_time": response_time,
                "success": attack_success,
                "attempts": attack_attempts,
                "task_type": entry.get("task_type", None),
                "jailbreak_type": entry.get("jailbreak_type", None),
                "instruction_type": entry.get("instruction_type", None),
                "document_id": entry.get("document_id", None),
                "position": entry.get("position", None),
                "spotlighting_data_markers": entry.get("spotlighting_data_markers", None),
                "injection_delimiters": entry.get("injection_delimiters", None),
                "suffix_id": entry.get("suffix_id", None),
                "lang": entry.get("lang", 'en'),
                "system_message": entry.get("system_message", None),
                "plugin": entry.get("plugin", None),
                "error": None,
                "attack_name": attack_module.__name__
            }
            results_list.append(attack_result)
        except Exception as e:
            error_result = {
                "id": f"{entry['id']}-attack",
                "long_id": entry["long_id"] + "-" + attack_module.__name__ + "-ERROR",
                "input": original_input,
                "response": "",
                "success": False,
                "attempts": 1,
                "task_type": entry.get("task_type", None),
                "jailbreak_type": entry.get("jailbreak_type", None),
                "instruction_type": entry.get("instruction_type", None),
                "document_id": entry.get("document_id", None),
                "position": entry.get("position", None),
                "spotlighting_data_markers": entry.get("spotlighting_data_markers", None),
                "injection_delimiters": entry.get("injection_delimiters", None),
                "suffix_id": entry.get("suffix_id", None),
                "lang": entry.get("lang", 'en'),
                "system_message": entry.get("system_message", None),
                "plugin": entry.get("plugin", None),
                "error": str(e),
                "attack_name": attack_module.__name__
            }
            results_list.append(error_result)

    return results_list

def test_dataset(args):
    target_name = args.target
    num_threads = args.threads
    dataset_file = args.dataset
    attempts = args.attempts
    max_retries = args.max_retries
    resume_file = args.resume_file
    throttle = args.throttle

    tag = args.tag
    if tag:
        is_valid_tag, tag_error = validate_tag(tag)
        if not is_valid_tag:
            print(f"Error: Invalid tag: {tag_error}")
            return

    # Load attack module (if specified) from the new attacks folder.
    attack_module = None
    if hasattr(args, 'attack') and args.attack:
        attack_module = load_attack_by_name(args.attack)

    target_module = load_target_module(target_name, max_retries, throttle)
    
    dataset = read_jsonl_file(dataset_file)
    completed_ids = set()
    results = []

    if resume_file and os.path.exists(resume_file):
        existing_results = read_jsonl_file(resume_file)
        completed_ids = set(r['id'] for r in existing_results)
        results = existing_results
        print(f"[Resume] Found {len(completed_ids)} completed entries in {resume_file}.")

    entries_to_process = [e for e in dataset if e['id'] not in completed_ids]

    timestamp = int(time.time())
    os.makedirs('results', exist_ok=True)
    filename = f"results_{target_name}-{extract_dataset_name(dataset_file)}_{timestamp}"
    if tag: filename += f"_{tag}"
    
    output_file = os.path.join(
        'results',
        f"{filename}.jsonl"
    )

    # Initialize current output file
    os.makedirs('results', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in results:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

    print(f"[Info] Testing {len(entries_to_process)} new entries (threads={num_threads}).")
    print(f"[Info] Output will be saved to: {output_file}")

    # Calculate total attempts possible.
    max_per_item = attempts
    if attack_module:
        max_per_item += args.attack_iterations
    total_attempts_possible = len(entries_to_process) * max_per_item

    global_lock = threading.Lock()
    file_lock = threading.Lock()
    attempts_bar = tqdm(total=total_attempts_possible, desc="All attempts", position=1)
    entry_bar = tqdm(total=len(entries_to_process), desc="Processing entries", position=0)

    executor = ThreadPoolExecutor(max_workers=num_threads)
    future_to_entry = {
        executor.submit(
            process_entry,
            entry,
            target_module,
            attempts,
            attack_module,
            args.attack_iterations if attack_module else 0,
            attempts_bar,
            global_lock
        ): entry
        for entry in entries_to_process
    }

    success_count = 0  
    entry_bar.set_postfix(success=success_count)

    try:
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                result = future.result()
                if result:
                    # result can be a list of result entries
                    if isinstance(result, list):
                        for r in result:
                            if r.get("success"):
                                success_count += 1
                            append_jsonl_entry(output_file, r, file_lock) 
                        results.extend(result)
                    else:
                        if result.get("success"):
                            success_count += 1
                        append_jsonl_entry(output_file, result, file_lock)
                        results.append(result)
            except Exception as e:
                print(f"[Error] Entry ID {entry['id']}: {e}")
            
            # Update the entry progress bar with the current success count
            entry_bar.set_postfix(success=success_count)
            entry_bar.update(1)

    except KeyboardInterrupt:
        print("\n[Interrupt] CTRL+C pressed. Cancelling all pending work...")
        executor.shutdown(wait=False, cancel_futures=True)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    attempts_bar.close()
    entry_bar.close()

    print(f"[Done] Testing finished. Results saved to {output_file}")
