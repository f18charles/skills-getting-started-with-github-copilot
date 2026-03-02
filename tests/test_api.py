import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_global


def _quote(component: str) -> str:
    return urllib.parse.quote(component, safe="")


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities_global)
    # ensure a clean copy before each test
    activities_global.clear()
    activities_global.update(copy.deepcopy(original))
    yield
    # restore original after test
    activities_global.clear()
    activities_global.update(copy.deepcopy(original))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_get_activities(client):
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_duplicate(client):
    email = "test.user@mergington.edu"
    activity = "Chess Club"
    path = f"/activities/{_quote(activity)}/signup"

    r1 = client.post(path, params={"email": email})
    assert r1.status_code == 200
    assert "Signed up" in r1.json().get("message", "")

    # second attempt should be rejected
    r2 = client.post(path, params={"email": email})
    assert r2.status_code == 400
    assert r2.json().get("detail") == "Student already signed up"


def test_unregister_success_and_not_found(client):
    # use an existing participant
    activity = "Chess Club"
    existing = "michael@mergington.edu"
    path = f"/activities/{_quote(activity)}/participants"

    # delete existing
    r = client.delete(path, params={"email": existing})
    assert r.status_code == 200
    assert f"Removed {existing}" in r.json().get("message", "")

    # deleting someone not registered returns 404
    r2 = client.delete(path, params={"email": "noone@x.com"})
    assert r2.status_code == 404
    assert r2.json().get("detail") == "Student not registered"
