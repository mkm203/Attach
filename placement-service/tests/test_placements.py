PLACEMENT = {"student_id": "stu-1", "student_name": "Clarisse Ngo", "company_name": "Douala Tech SARL",
             "company_city": "Douala", "company_supervisor_id": "cs-1", "academic_supervisor_id": "as-1",
             "start_date": "2026-09-07", "end_date": "2026-11-29"}


def make(client, **changes):
    return client.post("/v1/placements", json={**PLACEMENT, **changes})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "placement"}


def test_create_and_get(client):
    r = make(client)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "open" and body["total_weeks"] == 12
    assert client.get(f"/v1/placements/{body['id']}").json() == body


def test_unknown_placement_is_404_with_error_schema(client):
    r = client.get("/v1/placements/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "placement_not_found"


def test_dates_must_be_ordered_and_inside_term(client):
    assert make(client, end_date="2026-09-01", start_date="2026-09-07").status_code == 422
    r = make(client, start_date="2026-01-05")
    assert r.status_code == 422 and r.json()["error"]["code"] == "outside_term"


def test_missing_field_is_422_with_details(client):
    r = client.post("/v1/placements", json={"student_id": "x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error" and r.json()["error"]["details"]


def test_list_filters_and_pages(client):
    for i in range(3):
        make(client, student_id=f"stu-{i}")
    page = client.get("/v1/placements?page=1&page_size=2").json()
    assert page["total"] == 3 and len(page["items"]) == 2
    assert client.get("/v1/placements?student_id=stu-1").json()["total"] == 1
    assert client.get("/v1/placements?status=closed").json()["total"] == 0
    assert client.get("/v1/placements?page_size=500").status_code == 422


def test_update_supervisors(client):
    pid = make(client).json()["id"]
    r = client.put(f"/v1/placements/{pid}", json={"company_supervisor_id": "cs-9", "academic_supervisor_id": "as-9"})
    assert r.status_code == 200 and r.json()["company_supervisor_id"] == "cs-9"


def test_close_records_evaluation_and_locks(client):
    pid = make(client).json()["id"]
    r = client.post(f"/v1/placements/{pid}/close", json={"score": 16, "comment": "Reliable."})
    assert r.status_code == 200 and r.json()["status"] == "closed" and r.json()["final_score"] == 16
    again = client.post(f"/v1/placements/{pid}/close", json={"score": 10, "comment": "x"})
    assert again.status_code == 409
    upd = client.put(f"/v1/placements/{pid}", json={"company_supervisor_id": "a", "academic_supervisor_id": "b"})
    assert upd.status_code == 409


def test_score_out_of_range_is_422(client):
    pid = make(client).json()["id"]
    assert client.post(f"/v1/placements/{pid}/close", json={"score": 25, "comment": "x"}).status_code == 422