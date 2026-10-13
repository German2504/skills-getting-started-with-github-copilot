import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Test Club": {
            "description": "Test activity",
            "schedule": "Mondays, 3:00 PM - 4:00 PM",
            "max_participants": 5,
            "participants": ["existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "Test Club": {
            "description": "Test activity",
            "schedule": "Mondays, 3:00 PM - 4:00 PM",
            "max_participants": 5,
            "participants": ["existing@mergington.edu"],
        }
    }


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant_to_activity(client):
    response = client.post(
        "/activities/Test%20Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@mergington.edu for Test Club"
    }
    assert client.get("/activities").json()["Test Club"]["participants"] == [
        "existing@mergington.edu",
        "new@mergington.edu",
    ]


def test_signup_returns_400_for_existing_participant(client):
    response = client.post(
        "/activities/Test%20Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Missing%20Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_removes_existing_participant(client):
    response = client.delete(
        "/activities/Test%20Club/participants",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed existing@mergington.edu from Test Club"
    }
    assert client.get("/activities").json()["Test Club"]["participants"] == []


def test_remove_participant_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Missing%20Club/participants",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Test%20Club/participants",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
