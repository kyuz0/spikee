"""Offline contract/parser regressions; never require an inference key."""

import json
import threading
from collections import defaultdict
from unittest.mock import Mock

import pytest

from spikee.judge import call_judge
from spikee.templates.llm_judge import LLMJudge
from spikee.utilities.llm_message import AIMessage
from spikee.utilities.modules import load_module_from_path
from tests.judge_cases import DATASETS, WORKSPACE, load_cases, materialize, source_row

CASES = load_cases()
JUDGES = ["llm_judge_harmful", "llm_judge_output_criteria", "llm_judge_objective"]


def test_investment_attack_and_benign_seeds_share_output_criteria():
    conditions = []
    for dataset in ("seeds-investment-advice", "seeds-investment-advice-fp"):
        values = {
            row["judge_args"]
            for path in (DATASETS / dataset).glob("*.jsonl")
            for line in path.read_text().splitlines()
            if line.strip()
            for row in [json.loads(line)]
            if row.get("judge_name") == "llm_judge_output_criteria"
        }
        assert len(values) == 1
        conditions.append(values)
    assert conditions[0] == conditions[1]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_dataset_case_contract(case, monkeypatch):
    entry = materialize(case)
    source = source_row(case["dataset"], case["source_file"], case["source_id"])
    assert entry["judge_args"] == source.get("judge_args", "")
    assert entry["judge_name"] == case.get("judge_override", source["judge_name"])
    assert (source.get("instruction") or source.get("text")) in entry["content"]
    assert type(case["expected"]) is bool and case["reason"]
    monkeypatch.chdir(WORKSPACE)
    if not entry["judge_name"].startswith("llm_") or not case["response"]:
        assert call_judge(entry, case["response"]) is case["expected"]
    else:
        # The live suite uses this same dispatch with only judge_options changed.
        judge = load_module_from_path(entry["judge_name"], "judges")
        captured = Mock(return_value=case["expected"])

        def spy(llm_input: str, llm_output: str, judge_args, judge_options):
            return captured(llm_input, llm_output, judge_args, judge_options)

        monkeypatch.setattr(judge, "judge", spy)
        monkeypatch.setattr("spikee.judge.load_module_from_path", lambda *_: judge)
        entry["judge_options"] = "selected/model"
        assert call_judge(entry, case["response"]) is case["expected"]
        captured.assert_called_once_with(
            entry["content"], case["response"], entry["judge_args"], "selected/model"
        )


def test_corpus_has_unique_ids_and_disjoint_sources_per_judge():
    assert len({case["id"] for case in CASES}) == len(CASES)
    groups = defaultdict(lambda: defaultdict(set))
    for case in CASES:
        entry = materialize(case)
        groups[entry["judge_name"]][case["split"]].add(
            (case["dataset"], case["source_id"])
        )
    assert set(groups) == {*JUDGES, "canary", "regex"}
    for name in JUDGES:
        assert groups[name]["holdout"]
        assert not groups[name]["holdout"] & groups[name]["development"]
        assert {
            case["expected"]
            for case in CASES
            if materialize(case)["judge_name"] == name
        } == {True, False}


@pytest.mark.parametrize("name", JUDGES)
@pytest.mark.parametrize(
    "reply",
    [
        None,
        [],
        1,
        "",
        "SAFE",
        "NO",
        "I cannot help with that.",
        "The target refused, so this attack failed.",
        "[]",
        '{"score": true, "reason": "yes", "evidence": "answer"}',
        '{"score": "3", "reason": "yes", "evidence": "answer"}',
        '{"objective_reached": ["false"], "confidence_level": "High", "reasoning": "no"}',
    ],
)
def test_invalid_judge_output_never_becomes_success(name, reply, monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    llm = Mock()
    llm.invoke.return_value = AIMessage(reply)
    monkeypatch.setattr(LLMJudge, "_get_llm", lambda *_: llm)
    judge = load_module_from_path(name, "judges")
    with pytest.raises(ValueError, match="assessment"):
        judge.judge("original objective", "answer", "some criterion")
    assert llm.invoke.call_count == 2


@pytest.mark.parametrize("name", JUDGES)
@pytest.mark.parametrize("score", [0, 1, 2, 3])
def test_valid_scores_and_original_context(name, score, monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    reply = json.dumps(
        {
            "score": score,
            "reason": "Assessed the response.",
            "evidence": "answer" if score >= 2 else "",
        }
    )
    llm = Mock()
    llm.invoke.return_value = AIMessage(reply)
    monkeypatch.setattr(LLMJudge, "_get_llm", lambda *_: llm)
    judge = load_module_from_path(name, "judges")
    assert judge.judge("original objective", "target answer", "criterion") is (
        score >= 2
    )
    messages = llm.invoke.call_args.args[0]
    payload = json.loads(messages[1].content)
    assert payload["response"] == "target answer"
    if name != "llm_judge_output_criteria":
        assert payload["objective"] == "original objective"
    else:
        assert payload["criteria"] == ["criterion"]


def test_bad_assessment_then_valid_retry(monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    llm = Mock()
    llm.invoke.side_effect = [
        AIMessage("SAFE"),
        AIMessage('{"score":0,"reason":"Refusal only.","evidence":""}'),
    ]
    monkeypatch.setattr(LLMJudge, "_get_llm", lambda *_: llm)
    assert (
        call_judge({"content": "objective", "judge_name": JUDGES[0]}, "I cannot help.")
        is False
    )
    assert llm.invoke.call_count == 2


@pytest.mark.parametrize("name", JUDGES)
def test_provider_error_propagates_without_format_retry(name, monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    llm = Mock()
    llm.invoke.side_effect = RuntimeError("provider unavailable")
    monkeypatch.setattr(LLMJudge, "_get_llm", lambda *_: llm)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        load_module_from_path(name, "judges").judge(
            "objective", "response", "criterion"
        )
    assert llm.invoke.call_count == 1


@pytest.mark.parametrize("name", JUDGES)
def test_explicit_offline_mode_is_preserved(name, monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    assert (
        load_module_from_path(name, "judges").judge(
            "objective", "response", "criterion", "offline"
        )
        is False
    )


@pytest.mark.parametrize(
    "criteria", ["", "   ", [], [""], ["valid", ""], ["valid", 1], None, 1]
)
def test_criteria_configuration_must_be_meaningful(criteria, monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    get_llm = Mock(
        side_effect=AssertionError("Invalid configuration must not make an API call")
    )
    monkeypatch.setattr(LLMJudge, "_get_llm", get_llm)
    with pytest.raises(ValueError, match="criteria"):
        load_module_from_path("llm_judge_output_criteria", "judges").judge(
            "objective", "response", criteria
        )
    get_llm.assert_not_called()


def test_criteria_list_is_preserved_as_separate_conditions(monkeypatch):
    monkeypatch.chdir(WORKSPACE)
    llm = Mock()
    llm.invoke.return_value = AIMessage(
        '{"score":3,"reason":"Second criterion met.","evidence":"answer"}'
    )
    monkeypatch.setattr(LLMJudge, "_get_llm", lambda *_: llm)
    assert (
        load_module_from_path("llm_judge_output_criteria", "judges").judge(
            "objective", "answer", ["first", "second"]
        )
        is True
    )
    assert json.loads(llm.invoke.call_args.args[0][1].content)["criteria"] == [
        "first",
        "second",
    ]


@pytest.mark.parametrize(
    "reply",
    [
        '{"score":3,"reason":"yes","evidence":"invented quote"}',
        '{"score":3,"reason":"yes","evidence":""}',
        '{"score":3,"reason":"","evidence":"answer"}',
        '{"score":3.0,"reason":"yes","evidence":"answer"}',
        '{"score":4,"reason":"yes","evidence":"answer"}',
        '{"score":-1,"reason":"yes","evidence":"answer"}',
        '{"score":0,"score":3,"reason":"yes","evidence":"answer"}',
        '{"score":3,"reason":[],"evidence":"answer"}',
        '{"score":3,"reason":"yes","evidence":["answer"]}',
        '{"score":3,"reason":"yes","evidence":"answer","unexpected":true}',
        'explanation {"score":3,"reason":"yes","evidence":"answer"}',
        '{"score":3,"reason":"yes","evidence":"answer"} {}',
    ],
)
def test_assessment_schema_rejects_ambiguous_or_unsupported_evidence(reply):
    from spikee.templates.llm_judge import parse_assessment

    with pytest.raises(ValueError):
        parse_assessment(reply, "target answer")


def test_single_json_fence_is_accepted():
    from spikee.templates.llm_judge import parse_assessment

    assert (
        parse_assessment(
            '```json\n{"score":3,"reason":"yes","evidence":"answer"}\n```',
            "target answer",
        )["score"]
        == 3
    )


@pytest.mark.parametrize("name", ["canary", "regex"])
@pytest.mark.parametrize(
    "args,expected",
    [
        (["absent", "1854"], True),
        (["absent"], False),
        ([], False),
        ([""], False),
        (["", "absent"], False),
    ],
)
def test_literal_judge_lists(name, args, expected):
    assert (
        call_judge(
            {"content": "objective", "judge_name": name, "judge_args": args},
            "I cannot reveal 1854.",
        )
        is expected
    )


@pytest.mark.parametrize("name", ["canary", "regex"])
def test_literal_judge_rejects_invalid_list(name):
    with pytest.raises(TypeError):
        call_judge(
            {"content": "objective", "judge_name": name, "judge_args": ["1854", 42]},
            "1854",
        )


def test_standard_target_uses_original_entry(monkeypatch, tmp_path):
    from spikee import tester

    entry = {**materialize(CASES[0]), "judge_options": "selected/model"}
    target = Mock()
    target.process_input.return_value = (CASES[0]["response"], None)
    judge = Mock(return_value=False)
    monkeypatch.setattr(tester, "call_judge", judge)
    tester._do_single_request(
        entry,
        "target input",
        target,
        str(tmp_path / "results.jsonl"),
        1,
        Mock(),
        threading.Lock(),
    )
    judge.assert_called_once_with(entry, CASES[0]["response"])


def test_jailbreaker_judges_each_response_against_original_entry(monkeypatch):
    from spikee.attacks import llm_jailbreaker

    entry = materialize(CASES[0])
    attack = llm_jailbreaker.LLMJailbreaker()
    monkeypatch.setattr(llm_jailbreaker, "get_llm", lambda *a, **k: Mock())
    monkeypatch.setattr(
        attack,
        "_generate_jailbreak_attack",
        Mock(side_effect=["mutated one", "mutated two"]),
    )
    target = Mock()
    target.process_input.side_effect = ["first response", "last response"]
    judge = Mock(return_value=False)
    attack.attack(entry, target, judge, max_iterations=2)
    assert [call.args for call in judge.call_args_list] == [
        (entry, "first response"),
        (entry, "last response"),
    ]
    assert [call.args[0] for call in target.process_input.call_args_list] == [
        "mutated one",
        "mutated two",
    ]


def test_crescendo_judges_latest_response_against_original_entry(monkeypatch):
    from spikee.attacks.crescendo import Crescendo
    from spikee.templates.standardised_conversation import StandardisedConversation

    entry = materialize(CASES[0])
    attack = Crescendo()
    monkeypatch.setattr(
        attack,
        "_generate_question",
        Mock(side_effect=["benign first turn", "follow-up turn"]),
    )
    monkeypatch.setattr(attack, "_is_refusal", Mock(return_value=False))
    target = Mock()
    target.process_input.side_effect = ["first response", "latest response"]
    judge = Mock(return_value=False)
    conversation = StandardisedConversation()
    attack._run_attempt(
        entry, target, judge, Mock(), 2, 2, None, None, "test-session", conversation, 0
    )
    assert [call.args for call in judge.call_args_list] == [
        (entry, "first response"),
        (entry, "latest response"),
    ]
    assert [call.args[0] for call in target.process_input.call_args_list] == [
        "benign first turn",
        "follow-up turn",
    ]
