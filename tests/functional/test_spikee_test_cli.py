from __future__ import annotations

import pytest

from .utils import extract_results_path, read_jsonl, run_generate_command, run_test_command


def _attack_base_name(entry):
    attack_name = entry.get("attack_name")
    if not attack_name:
        return None
    return attack_name.split(".")[-1]


@pytest.mark.parametrize(
    "target_name,expected_success", [("always_refuse", False), ("always_success", True)]
)
def test_spikee_test_targets(run_spikee, workspace_dir, target_name, expected_success):
    dataset_path, _ = run_generate_command(run_spikee, workspace_dir)
    dataset_rel = dataset_path.relative_to(workspace_dir)

    result = run_test_command(
        run_spikee,
        workspace_dir,
        ["--dataset", str(dataset_rel), "--target", target_name],
    )

    results_file = extract_results_path(result.stdout, workspace_dir)
    results = read_jsonl(results_file)
    assert results, "No results recorded by spikee test"
    assert all(entry["success"] == expected_success for entry in results)


def test_spikee_test_runs_attack_when_base_fails(run_spikee, workspace_dir):
    dataset_path, _ = run_generate_command(run_spikee, workspace_dir)
    dataset_rel = dataset_path.relative_to(workspace_dir)

    result = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_rel),
            "--target",
            "always_refuse",
            "--attack",
            "mock_attack",
            "--attack-iterations",
            "5",
        ],
    )

    results_file = extract_results_path(result.stdout, workspace_dir)
    results = read_jsonl(results_file)
    assert results

    base_results = [entry for entry in results if entry.get("attack_name") == "None"]
    attack_results = [
        entry for entry in results if _attack_base_name(entry) == "mock_attack"
    ]

    assert len(base_results) == len(attack_results)
    for attack_entry in attack_results:
        attempts = attack_entry["attempts"]
        assert attempts == 5
        assert not attack_entry["success"]


def test_spikee_test_skips_attack_when_base_succeeds(run_spikee, workspace_dir):
    dataset_path, _ = run_generate_command(run_spikee, workspace_dir)
    dataset_rel = dataset_path.relative_to(workspace_dir)

    result = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_rel),
            "--target",
            "always_success",
            "--attack",
            "mock_attack",
            "--attack-iterations",
            "5",
        ],
    )

    results_file = extract_results_path(result.stdout, workspace_dir)
    results = read_jsonl(results_file)
    assert results

    base_results = [entry for entry in results if entry.get("attack_name") == "None"]
    attack_results = [
        entry for entry in results if _attack_base_name(entry) == "mock_attack"
    ]

    assert base_results
    assert all(entry["success"] for entry in base_results)
    assert not attack_results


def test_spikee_test_partial_success_target(run_spikee, workspace_dir):
    dataset_path, _ = run_generate_command(run_spikee, workspace_dir)
    dataset_rel = dataset_path.relative_to(workspace_dir)

    result = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_rel),
            "--target",
            "partial_success",
            "--attack",
            "mock_attack",
            "--attack-iterations",
            "5",
        ],
    )

    results_file = extract_results_path(result.stdout, workspace_dir)
    results = read_jsonl(results_file)
    assert results

    base_results = [entry for entry in results if entry.get("attack_name") == "None"]
    attack_results = [
        entry for entry in results if _attack_base_name(entry) == "mock_attack"
    ]

    assert len(base_results) > 0
    successes = [entry for entry in base_results if entry["success"]]
    failures = [entry for entry in base_results if not entry["success"]]
    assert successes
    assert failures
    assert attack_results
    assert len(attack_results) == len(failures)
    assert all(entry["attempts"] == 5 for entry in attack_results)
    assert all(not entry["success"] for entry in attack_results)


@pytest.mark.parametrize(
    "attack_name",
    [
        "anti_spotlighting",
        "best_of_n",
        "prompt_decomposition",
    ],
)
def test_spikee_test_builtin_attacks(run_spikee, workspace_dir, attack_name):
    dataset_path, _ = run_generate_command(run_spikee, workspace_dir)
    dataset_rel = dataset_path.relative_to(workspace_dir)

    result = run_test_command(
        run_spikee,
        workspace_dir,
        [
            "--dataset",
            str(dataset_rel),
            "--target",
            "always_refuse",
            "--attack",
            attack_name,
            "--attack-iterations",
            "4",
        ],
    )

    results_file = extract_results_path(result.stdout, workspace_dir)
    results = read_jsonl(results_file)
    assert results

    attack_results = [
        entry for entry in results if _attack_base_name(entry) == attack_name
    ]
    assert attack_results

    for entry in attack_results:
        assert 1 <= entry["attempts"] <= 4
        assert not entry["success"]
