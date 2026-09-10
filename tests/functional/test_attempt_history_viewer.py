"""Candidate evidence stays nested under a single result in the viewer."""

from copy import deepcopy

import pytest
from werkzeug.datastructures import MultiDict

from spikee.templates.standardised_conversation import StandardisedConversation
from spikee.utilities.files import read_jsonl_file, write_jsonl_file
from spikee.viewer.app import create_app
from spikee.viewer.blueprints import _cache
from spikee.viewer.blueprints import results as viewer_results
from spikee.viewer.blueprints._forms import TestForm as RunForm


@pytest.fixture
def history_viewer(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    (tmp_path / "datasets").mkdir()
    history = [
        {
            "input": "candidate prompt <script>alert('input')</script>",
            "response": "candidate response <img src=x onerror=alert('response')>",
            "success": False,
        },
        {
            "input": ["structured input", {"text": "another part"}],
            "response": {"text": "unjudged response"},
            "success": None,
        },
        {
            "input": "error candidate",
            "response": "response before judge error",
            "error": "judge failed <script>alert('error')</script>",
        },
        {"input": "successful candidate", "response": "done", "success": True},
    ]
    row = {
        "id": "42-attack",
        "long_id": "dataset-entry-best_of_n",
        "input": "successful candidate",
        "response": "done",
        "success": True,
        "attempts": 4,
        "attack_name": "best_of_n",
        "judge_name": "canary",
        "judge_args": "done",
        "attempt_history": history,
    }
    path = tmp_path / "results" / "results_history.jsonl"
    write_jsonl_file(path, [row])
    monkeypatch.setattr(_cache, "warm_cache", lambda: None)
    monkeypatch.setattr(viewer_results, "loaded_files", {"history": path})
    app = create_app(db_path=str(tmp_path / "jobs.sqlite"))
    app.config["TESTING"] = True
    return app.test_client(), path, row


def test_candidate_history_detail_is_escaped_and_summary_stays_compact(history_viewer):
    client, _path, _row = history_viewer
    response = client.get("/results/entries?result_file=history")
    assert response.status_code == 200
    assert b"Attempt history: 4 recorded candidates" in response.data
    assert b"#attempt-history" in response.data
    assert b"candidate prompt" not in response.data

    response = client.get("/results/entry/history-42-attack?result_file=history")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="attempt-history"' in html
    for marker in (
        "Candidate 1",
        "Candidate 4",
        "FAILED",
        "SUCCESS",
        "UNJUDGED",
        "ERROR",
        "structured input",
        "unjudged response",
        "response before judge error",
        "candidate prompt &lt;script&gt;",
        "candidate response &lt;img",
        "judge failed &lt;script&gt;",
    ):
        assert marker in html
    assert "<script>alert(" not in html
    assert "<img src=x" not in html
    assert html.count("Toggle Success") == 1
    assert html.count(">Re-judge<") == 1


def test_rejudge_and_toggle_change_only_the_result(history_viewer, monkeypatch):
    client, path, row = history_viewer
    original_history = deepcopy(row["attempt_history"])
    judged = []

    def judge(entry, response):
        judged.append((entry["id"], response))
        return False

    monkeypatch.setattr(viewer_results, "call_judge", judge)
    route = "/results/entry/history-42-attack"
    response = client.post(f"{route}/rejudge?result_file=history")
    assert response.status_code == 302
    assert judged == [("42-attack", "done")]
    updated = read_jsonl_file(path)
    assert len(updated) == 1
    assert updated[0]["success"] is False
    assert updated[0]["attempts"] == 4
    assert updated[0]["attempt_history"] == original_history
    response = client.post(f"{route}/toggle?result_file=history")
    assert response.status_code == 302
    updated = read_jsonl_file(path)
    assert updated[0]["success"] is True
    assert updated[0]["attempt_history"] == original_history


@pytest.mark.parametrize("format", ["representative", "conversation", "expanded"])
def test_existing_result_formats_still_render(history_viewer, format):
    client, path, row = history_viewer
    del row["attempt_history"]
    if format == "conversation":
        conversation = StandardisedConversation("conversation objective")
        conversation.add_message(0, {"response": "preserved conversation branch"})
        row["conversation"] = str(conversation)
    elif format == "expanded":
        row.update(
            id="42-attack-1",
            attack_attempt=1,
            attack_parent_id=42,
            attack_result_format="attempt",
        )
    write_jsonl_file(path, [row])
    response = client.get(f"/results/entry/history-{row['id']}?result_file=history")
    assert response.status_code == 200
    assert b'id="attempt-history"' not in response.data
    if format == "conversation":
        assert b"Attack Conversation Trace" in response.data
        assert b"preserved conversation branch" in response.data
    elif format == "expanded":
        assert b"Attack Attempt" in response.data


def test_test_form_ignores_saved_retention_flag(history_viewer):
    client, _path, _row = history_viewer
    form = MultiDict(
        {
            "target": "mock",
            "datasets": "example.jsonl",
            "attack": "best_of_n",
            "attack_return_all_attempts": "on",
        }
    )
    args = RunForm.from_form(form).to_cli_args()
    assert args[:3] == ["test", "--target", "mock"]
    assert "--attack" in args
    assert "--attack-return-all-attempts" not in args
    with client.session_transaction() as session:
        session["test_settings"] = dict(form)
    response = client.get("/test/run")
    assert response.status_code == 200
    assert b"attack_return_all_attempts" not in response.data
