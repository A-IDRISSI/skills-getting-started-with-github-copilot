from copy import deepcopy

import pytest

from src.app import activities


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)
    page = client.get(expected_location)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert "Mergington High School" in page.text


def test_list_activities_returns_current_data_without_mutation(client):
    # Arrange
    expected = deepcopy(activities)
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")
    result = response.json()

    # Assert
    assert response.status_code == 200
    assert result == expected
    assert result
    for name, details in result.items():
        assert isinstance(name, str)
        assert required_fields <= details.keys()
        assert isinstance(details["description"], str)
        assert isinstance(details["schedule"], str)
        assert isinstance(details["max_participants"], int)
        assert isinstance(details["participants"], list)
        assert all(isinstance(email, str) for email in details["participants"])
    assert activities == expected


@pytest.mark.parametrize("email", ["new@mergington.edu", "new+chess@mergington.edu"])
def test_signup_adds_only_selected_participant(client, email):
    # Arrange
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].append(email)

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})
    listing = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert listing.status_code == 200
    assert listing.json() == expected
    assert activities == expected
    assert activities["Chess Club"]["participants"].count(email) == 1


@pytest.mark.parametrize(
    ("activity", "email", "status", "detail"),
    [
        ("Chess%20Club", "michael@mergington.edu", 400,
         "Student already signed up for this activity"),
        ("Unknown", "new@mergington.edu", 404, "Activity not found"),
    ],
)
def test_signup_rejects_invalid_registration(client, activity, email, status, detail):
    # Arrange
    expected = deepcopy(activities)

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert activities == expected


@pytest.mark.parametrize(
    ("method", "action"), [("POST", "signup"), ("DELETE", "unregister")]
)
def test_registration_requires_email(client, method, action):
    # Arrange
    expected = deepcopy(activities)
    url = f"/activities/Chess%20Club/{action}"

    # Act
    response = client.request(method, url)

    # Assert
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"] and error["type"] == "missing"
        for error in response.json()["detail"]
    )
    assert activities == expected


def test_unregister_removes_only_selected_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].remove(email)

    # Act
    response = client.delete(
        "/activities/Chess%20Club/unregister", params={"email": email}
    )
    listing = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert listing.status_code == 200
    assert listing.json() == expected
    assert activities == expected


@pytest.mark.parametrize(
    ("activity", "email", "status", "detail"),
    [
        ("Unknown", "michael@mergington.edu", 404, "Activity not found"),
        ("Chess%20Club", "unknown@example.com", 400,
         "Student is not signed up for this activity"),
    ],
)
def test_unregister_rejects_invalid_registration(client, activity, email, status, detail):
    # Arrange
    expected = deepcopy(activities)

    # Act
    response = client.delete(
        f"/activities/{activity}/unregister", params={"email": email}
    )

    # Assert
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert activities == expected


def test_unregister_final_participant_leaves_empty_activity(client):
    # Arrange
    email = "last+art@mergington.edu"
    activities["Art Club"]["participants"] = [email]
    expected = deepcopy(activities)
    expected["Art Club"]["participants"] = []

    # Act
    response = client.delete(
        "/activities/Art%20Club/unregister", params={"email": email}
    )
    listing = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Art Club"}
    assert listing.status_code == 200
    assert listing.json() == expected
    assert activities == expected


def test_participant_can_sign_up_again_after_unregistering(client):
    # Arrange
    email = "returning+art@mergington.edu"
    params = {"email": email}
    expected_empty = deepcopy(activities)
    expected_registered = deepcopy(activities)
    expected_registered["Art Club"]["participants"].append(email)

    # Act
    first_signup = client.post("/activities/Art%20Club/signup", params=params)
    first_listing = client.get("/activities")
    unregister = client.delete("/activities/Art%20Club/unregister", params=params)
    empty_listing = client.get("/activities")
    second_signup = client.post("/activities/Art%20Club/signup", params=params)
    final_listing = client.get("/activities")

    # Assert
    for response in (first_signup, second_signup):
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for Art Club"}
    assert unregister.status_code == 200
    assert unregister.json() == {"message": f"Unregistered {email} from Art Club"}
    for response in (first_listing, empty_listing, final_listing):
        assert response.status_code == 200
    assert first_listing.json() == expected_registered
    assert empty_listing.json() == expected_empty
    assert final_listing.json() == expected_registered
    assert activities == expected_registered
