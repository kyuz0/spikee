import os
import re
import json
import time
import importlib
import random
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

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

def load_target_module(target_name):
    local_target_path = os.path.join(os.getcwd(), 'targets', f"{target_name}.py")
    if os.path.isfile(local_target_path):
        return load_module_from_path(local_target_path, target_name)
    try:
        return importlib.import_module(f"spikee.targets.{target_name}")
    except ModuleNotFoundError:
        raise ValueError(f"Target '{target_name}' not found locally or in spikee.targets/")

def load_plugin_by_name(plugin_name):
    local_plugin_path = Path(os.getcwd()) / "plugins" / f"{plugin_name}.py"
    if local_plugin_path.is_file():
        spec = importlib.util.spec_from_file_location(plugin_name, local_plugin_path)
        plugin_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin_module)
        return plugin_module
    try:
        return importlib.import_module(f"spikee.plugins.{plugin_name}")
    except ModuleNotFoundError:
        raise ValueError(f"Plugin '{plugin_name}' not found locally or in spikee.plugins")


def load_judge_module(judge_name):
    """
    Looks for `judges/{judge_name}.py` locally first,
    then fallback to something like `spikee.judges.{judge_name}`, if desired.
    """
    import importlib.util
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

def call_judge(entry, llm_output):
    judge_name = entry.get("judge_name", "canary")
    judge_args = entry.get("judge_args", "")
    llm_input = entry["text"]

    judge_module = load_judge_module(judge_name)
    return judge_module.judge(llm_input=llm_input, llm_output=llm_output, judge_args=judge_args)

def _do_single_request(entry, input_text, target_module, success_criteria, max_retries, 
                       throttle, attempt_num, adaptive_attack_plugin, adaptive_attack_iteration,
                       attempts_bar, global_lock):
    canary = entry.get("canary", "")
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

    base_long_id = entry["long_id"]
    if adaptive_attack_iteration == 0:
        final_long_id = base_long_id
    else:
        final_long_id = f"{base_long_id}-{adaptive_attack_plugin}-{adaptive_attack_iteration}"

    retries = 0
    success = False
    response_str = None
    error_message = None

    while retries < max_retries:
        try:
            response = target_module.process_input(input_text, system_message)
            success = False
            if success_criteria == 'boolean':
                # used for guardrails
                if isinstance(response, bool):
                    success = response
                    response = ''
                else:
                    raise ValueError("Expected boolean response.")
            else:
                # Evaluate with selected judge
                success = call_judge(entry, response)
            response_str = response if isinstance(response, str) else ""
            break
        except Exception as e:
            error_message = str(e)
            if "429" in error_message:
                if retries < max_retries - 1:
                    wait_time = random.randint(30, 120)
                    time.sleep(wait_time)
                    retries += 1
                    continue
                else:
                    pass
            break

    if throttle > 0:
        time.sleep(throttle)

    with global_lock:
        attempts_bar.update(1)

    result_dict = {
        "id": entry["id"],
        "long_id": final_long_id,
        "input": input_text,
        "response": response_str,
        "success": success,
        "attempts": attempt_num,
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
        "error": error_message,
        "adaptive_attack_plugin": adaptive_attack_plugin,
        "adaptive_attack_attempt": adaptive_attack_iteration,
    }
    return result_dict, success

def process_entry(entry, target_module, attempts, success_criteria='canary', max_retries=5, throttle=0,
                  adaptive_attack_plugin=None, adaptive_attack_iterations=0,
                  attempts_bar=None, global_lock=None):
    original_input = entry["text"]
    std_result = None
    success_found = False
    total_for_item = attempts  # standard pass
    if adaptive_attack_plugin:
        total_for_item += attempts * adaptive_attack_iterations

    done_for_item = 0

    for attempt_num in range(1, attempts + 1):
        std_result, success_now = _do_single_request(
            entry, original_input, target_module, success_criteria, max_retries,
            throttle, attempt_num, None, 0, attempts_bar, global_lock
        )
        done_for_item += 1
        if success_now:
            pad = total_for_item - done_for_item
            if pad > 0:
                with global_lock:
                    attempts_bar.update(pad)
            return std_result
    if not adaptive_attack_plugin:
        return std_result

    adapted_result = None
    for i in range(1, adaptive_attack_iterations + 1):
        adapted_input = adaptive_attack_plugin.transform(original_input)
        for attempt_num in range(1, attempts + 1):
            adapted_result, success_now = _do_single_request(
                entry, adapted_input, target_module, success_criteria, max_retries,
                throttle, attempt_num, adaptive_attack_plugin.__name__, i,
                attempts_bar, global_lock
            )
            done_for_item += 1
            if success_now:
                pad = total_for_item - done_for_item
                if pad > 0:
                    with global_lock:
                        attempts_bar.update(pad)
                return adapted_result
    return adapted_result

def test_dataset(args):
    target_name = args.target
    num_threads = args.threads
    dataset_file = args.dataset
    attempts = args.attempts
    success_criteria = args.success_criteria
    resume_file = args.resume_file
    throttle = args.throttle
    adaptive_plugin = None

    if args.adaptive_attack:
        adaptive_plugin = load_plugin_by_name(args.adaptive_attack)

    target_module = load_target_module(target_name)
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
    output_file = os.path.join(
        'results',
        f"results_{target_name}-{extract_dataset_name(dataset_file)}_{timestamp}.jsonl"
    )

    print(f"[Info] Testing {len(entries_to_process)} new entries (threads={num_threads}).")
    print(f"[Info] Output will be saved to: {output_file}")

    max_per_item = attempts
    if adaptive_plugin:
        max_per_item += attempts * args.adaptive_attack_iterations
    total_attempts_possible = len(entries_to_process) * max_per_item

    global_lock = threading.Lock()
    attempts_bar = tqdm(total=total_attempts_possible, desc="All attempts", position=1)
    entry_bar = tqdm(total=len(entries_to_process), desc="Processing entries", position=0)

    executor = ThreadPoolExecutor(max_workers=num_threads)
    future_to_entry = {
        executor.submit(
            process_entry,
            entry,
            target_module,
            attempts,
            success_criteria,
            3,
            throttle,
            adaptive_plugin,
            args.adaptive_attack_iterations,
            attempts_bar,
            global_lock
        ): entry
        for entry in entries_to_process
    }

    try:
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                result_dict = future.result()
                if result_dict:
                    results.append(result_dict)
            except Exception as e:
                print(f"[Error] Entry ID {entry['id']}: {e}")
            entry_bar.update(1)
    except KeyboardInterrupt:
        print("\n[Interrupt] CTRL+C pressed. Cancelling all pending work...")
        executor.shutdown(wait=False, cancel_futures=True)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    attempts_bar.close()
    entry_bar.close()

    write_jsonl_file(output_file, results)
    print(f"[Done] Testing finished. Results saved to {output_file}")
