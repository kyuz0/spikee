from __future__ import annotations

import time
from pathlib import Path

from .utils import (
    extract_results_path,
    read_jsonl,
    run_generate_command,
    run_results_command,
    run_test_command,
)


def _create_judge_results(run_spikee, workspace_dir: Path):
    dataset_path = workspace_dir / "datasets" / "test_judge_dataset.jsonl"
    assert dataset_path.exists()

    result = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_path),
            "--target",
            "always_success",
            "--judge-options",
            "test_judge:mode=fail",
        ],
    )
    return extract_results_path(result.stdout, workspace_dir)


def test_spikee_results_analyze(run_spikee, workspace_dir):
    results_file = _create_judge_results(run_spikee, workspace_dir)

    analyze = run_results_command(
        run_spikee,
        workspace_dir,
        "analyze",
        ["--result-file", str(results_file)],
    )

    output = analyze.stdout
    assert "General Statistics" in output
    assert "Total Unique Entries" in output
    assert "Successful Attacks: 0" in output
    assert "Attack Success Rate" in output


def test_spikee_results_rejudge_with_options(run_spikee, workspace_dir):
    results_file = _create_judge_results(run_spikee, workspace_dir)

    existing = {
        path for path in results_file.parent.glob(f"{results_file.stem}-rejudge-*.jsonl")
    }

    rejudge = run_results_command(
        run_spikee,
        workspace_dir,
        "rejudge",
        [
            "--result-file",
            str(results_file),
            "--judge-options",
            "test_judge:mode=success",
        ],
    )
    assert "Re-judging the following file(s)" in rejudge.stdout

    # Identify new rejudge file
    timeout = time.time() + 5
    new_file = None
    while time.time() < timeout and new_file is None:
        candidates = {
            path
            for path in results_file.parent.glob(
                f"{results_file.stem}-rejudge-*.jsonl"
            )
        }
        new_candidates = candidates - existing
        if new_candidates:
            new_file = max(new_candidates, key=lambda p: p.stat().st_mtime)
        else:
            time.sleep(0.1)

    assert new_file and new_file.exists(), "Rejudge output file not created"

    rejudged_results = read_jsonl(new_file)
    assert rejudged_results
    assert all(entry["success"] for entry in rejudged_results)

    analyze = run_results_command(
        run_spikee,
        workspace_dir,
        "analyze",
        ["--result-file", str(new_file)],
    )
    output = analyze.stdout
    assert "Successful Attacks: 2" in output
