from tests.conftest import ACADEMIC, OTHER_SUPERVISOR, STUDENT, SUPERVISOR, submit


def review(client, eid, headers=SUPERVISOR, **body):
    return client.post(f"/v1/entries/{eid}/reviews", json=body or {"decision": "approved"}, headers=headers)


def test_supervisor_approves(client):
    eid = submit(client).json()["id"]
    r = review(client, eid)
    assert r.status_code == 201 and r.json()["decision"] == "approved" and r.json()["reviewer_id"] == "cs-1"
    assert client.get(f"/v1/entries/{eid}", headers=STUDENT).json()["status"] == "approved"


# --- business rule 2: approved entries cannot be edited -> 409
def test_approved_entry_cannot_be_edited(client):
    eid = submit(client).json()["id"]
    review(client, eid)
    r = client.put(f"/v1/entries/{eid}", json={"tasks": "Changed", "hours": 10}, headers=STUDENT)
    assert r.status_code == 409 and r.json()["error"]["code"] == "entry_locked"


# --- business rule 3: only the assigned company supervisor can review -> 403
def test_unassigned_supervisor_cannot_review(client):
    eid = submit(client).json()["id"]
    r = review(client, eid, headers=OTHER_SUPERVISOR)
    assert r.status_code == 403 and r.json()["error"]["code"] == "not_assigned_supervisor"
    assert client.get(f"/v1/entries/{eid}", headers=STUDENT).json()["status"] == "pending"


def test_rejection_needs_a_comment(client):
    eid = submit(client).json()["id"]
    r = review(client, eid, decision="rejected")
    assert r.status_code == 422 and r.json()["error"]["code"] == "comment_required"


def test_rejected_entry_can_be_revised_and_goes_back_to_pending(client):
    eid = submit(client).json()["id"]
    assert review(client, eid, decision="rejected", comment="Too vague").status_code == 201
    assert client.get(f"/v1/entries/{eid}", headers=STUDENT).json()["status"] == "rejected"
    r = client.put(f"/v1/entries/{eid}", json={"tasks": "Detailed tasks", "hours": 36}, headers=STUDENT)
    assert r.status_code == 200 and r.json()["status"] == "pending"


def test_only_a_pending_entry_can_be_reviewed(client):
    eid = submit(client).json()["id"]
    review(client, eid)
    r = review(client, eid)
    assert r.status_code == 409 and r.json()["error"]["code"] == "entry_not_pending"


def test_review_of_unknown_entry_is_404(client):
    assert review(client, "nope").status_code == 404


def test_invalid_decision_is_422(client):
    eid = submit(client).json()["id"]
    assert review(client, eid, decision="maybe").status_code == 422


def test_review_history(client):
    eid = submit(client).json()["id"]
    review(client, eid, decision="rejected", comment="Add details")
    client.put(f"/v1/entries/{eid}", json={"tasks": "More", "hours": 30}, headers=STUDENT)
    review(client, eid)
    history = client.get(f"/v1/entries/{eid}/reviews", headers=STUDENT).json()
    assert [h["decision"] for h in history] == ["rejected", "approved"]


def test_progress_for_the_academic_supervisor(client):
    ids = [submit(client, week=w).json()["id"] for w in (1, 2, 3)]
    review(client, ids[0])
    review(client, ids[1], decision="rejected", comment="Missing hours")
    p = client.get("/v1/placements/P1/progress", headers=ACADEMIC).json()
    assert p["total_weeks"] == 4 and p["submitted"] == 3
    assert (p["approved"], p["rejected"], p["pending"]) == (1, 1, 1)
    assert p["completion_percent"] == 25.0
    assert p["comments"] == [{"week": 2, "decision": "rejected", "comment": "Missing hours", "reviewer_id": "cs-1"}]