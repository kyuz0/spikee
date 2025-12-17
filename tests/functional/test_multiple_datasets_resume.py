from .utils import run_generate_command, run_test_command, write_jsonl, read_jsonl


def test_multiple_datasets_independent_resume(run_spikee, workspace_dir):
    # 1. Generate 2 datasets
    dataset_path_a, _ = run_generate_command(
        run_spikee, workspace_dir, extra_args=["--tag", "A"]
    )
    dataset_path_b, _ = run_generate_command(
        run_spikee, workspace_dir, extra_args=["--tag", "B"]
    )

    entries_a = read_jsonl(dataset_path_a)
    entries_b = read_jsonl(dataset_path_b)

    # 2. Create partial results for Dataset A
    # Process 2 entries of A
    completed_entries = []
    for i in range(2):
        res = {
            "id": entries_a[i]["id"],
            "long_id": entries_a[i]["long_id"],
            "success": False,
            "attack_name": "None",
            "attempts": 1,
        }
        completed_entries.append(res)

    # Assume output filename structure: results_target_datasetname.jsonl
    # Actually, the auto-resume logic looks for matching files.
    # We need to construct a valid result file name so auto-resume finds it.
    # spikee uses `build_resource_name`.
    # Let's verify by running a small test OR assume standard naming.
    # Code: _build_target_name -> target-options
    # then build_resource_name("results", target_full, dataset_name)

    # Let's run a "fake" successful run to get the filename if we want to be safe,
    # but manually creating is faster if we know the pattern.
    # Pattern: results_{target}_{dataset_name}_{timestamp}.jsonl

    # Dataset A name
    ds_name_a = dataset_path_a.stem
    target_name = "always_success"

    # We create a dummy result file for A
    results_dir = workspace_dir / "results"
    results_dir.mkdir(exist_ok=True)

    resume_file_a = results_dir / f"results_{target_name}_{ds_name_a}_1234567890.jsonl"
    write_jsonl(resume_file_a, completed_entries)

    # Dataset B has NO results.

    dataset_rel_a = dataset_path_a.relative_to(workspace_dir)
    dataset_rel_b = dataset_path_b.relative_to(workspace_dir)

    # 3. Run test for BOTH datasets with auto-resume
    result = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_rel_a),
            "--dataset",
            str(dataset_rel_b),
            "--target",
            target_name,
            "--auto-resume",
        ],
    )

    # 4. Assertions
    stdout = result.stdout
    stderr = result.stderr

    print(f"DEBUG: Stdout:\n{stdout}")

    # Check if A resumed
    assert f"[Auto-Resume] Using latest: {resume_file_a.name}" in stdout

    # Check A processed roughly (total - 2) entries
    # The output usually says "[Info] Testing X new entries"
    # A has e.g. 5 entries, processed 2. Should test 3.
    # A has e.g. 5 entries, processed 2. Should test 3.

    # Check if B started fresh
    # B should process ALL entries
    # B should process ALL entries

    # We need to parse the stdout to distinguish A and B blocks?
    # Or just check for errors.

    if "Error" in stdout or "Error" in stderr:
        # If B tried to use A's resume file, it might mismatch IDs and handle it?
        # Or it might filter incorrectly.
        pass

    # Logic check:
    # If bug exists, when processing B, args.resume_file is set to resume_file_a.
    # _load_results_file loads completed_ids from resume_file_a.
    # It filters B entries using A's IDs.
    # Since IDs are usually UUIDs, they won't match.
    # So B will process ALL entries (safe?).
    # BUT, it might try to append result B to resume_file_a?
    # No, output_file is determined separately.
    # However, "already_done" count might be wrong?

    # Wait, the main issue is if B *had* a resume file, would it be ignored?
    # Or if A had one, would B be forced to use it?

    # Let's adjust exact test case to prove BUG.
    # Case: A has resume file. B simulates having NO resume file.
    # If args.resume_file leaks, B will load A's resume file.
    # IDs won't match. B processes all.
    # Effect is subtle unless we check logs.

    # Better Case: A has resume file. B has DIFFERENT resume file.
    # If args.resume_file leaks, B might ignore its own resume file?
    # No, _determine_resume_file checks args.resume_file FIRST.
    # So if args.resume_file is set (from A), it won't even look for B's file!
    # B will use A's file.

    # So, let's create a resume file for B too!
    ds_name_b = dataset_path_b.stem
    resume_file_b = results_dir / f"results_{target_name}_{ds_name_b}_9999999999.jsonl"
    completed_entries_b = []
    # Process 2 entries of B
    for i in range(2):
        res = {
            "id": entries_b[i]["id"],
            "long_id": entries_b[i]["long_id"],
            "success": False,
            "attack_name": "None",
            "attempts": 1,
        }
        completed_entries_b.append(res)
    write_jsonl(resume_file_b, completed_entries_b)

    # Run again with auto-resume.
    # Expected:
    # A uses resume_file_a.
    # B uses resume_file_b.

    # Actual (Buggy):
    # A uses resume_file_a. Sets args.resume_file = resume_file_a.
    # B check: _determine_resume_file sees args.resume_file set. Returns resume_file_a.
    # B uses resume_file_a!!

    result_bug = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_rel_a),
            "--dataset",
            str(dataset_rel_b),
            "--target",
            target_name,
            "--auto-resume",
        ],
    )

    stdout_bug = result_bug.stdout
    print(f"DEBUG: Stdout Bug Run:\n{stdout_bug}")

    # We should see "[Auto-Resume] Using latest: ...A..." followed by logic for A.
    # Then for B...
    # If validation fails, we might see it mistakenly saying using A for B.

    # We can check specific string occurrences.
    # Or check if "Using latest: ...B..." appears.
    # If bug exists, "Using latest: ...B..." will NOT appear because it reused A.

    assert f"Using latest: {resume_file_b.name}" in stdout_bug, (
        "Did not find auto-resume message for Dataset B. Likely reused Dataset A's resume file."
    )
