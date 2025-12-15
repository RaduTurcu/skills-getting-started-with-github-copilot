import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities_state():
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original)


@pytest.fixture()
def client():
    return TestClient(app)


def test_get_activities_returns_cache_control_no_store(client: TestClient):
    response = client.get("/activities")
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    body = response.json()
    assert isinstance(body, dict)
    assert "Chess Club" in body


def test_signup_adds_participant_and_is_visible_in_activities(client: TestClient):
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200

    activities_response = client.get("/activities")
    assert activities_response.status_code == 200
    body = activities_response.json()
    assert email in body[activity_name]["participants"]


def test_signup_duplicate_returns_400(client: TestClient):
    email = "dupe@mergington.edu"
    activity_name = "Programming Class"

    first = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert first.status_code == 200

    second = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert second.status_code == 400


def test_signup_unknown_activity_returns_404(client: TestClient):
    response = client.post("/activities/Does%20Not%20Exist/signup", params={"email": "x@mergington.edu"})
    assert response.status_code == 404


def test_unregister_removes_participant(client: TestClient):
    email = "remove-me@mergington.edu"
    activity_name = "Science Club"

    signup = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert signup.status_code == 200

    unregister = client.delete(f"/activities/{activity_name}/participants", params={"email": email})
    assert unregister.status_code == 200

    activities_response = client.get("/activities")
    assert activities_response.status_code == 200
    body = activities_response.json()
    assert email not in body[activity_name]["participants"]


def test_unregister_missing_participant_returns_404(client: TestClient):
    response = client.delete(
        "/activities/Art%20Studio/participants",
        params={"email": "not-signed-up@mergington.edu"},
    )
    assert response.status_code == 404
