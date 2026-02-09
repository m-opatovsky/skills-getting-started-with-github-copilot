"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a clean state before each test"""
    # Store original state
    original = {k: {"participants": v["participants"].copy()} for k, v in activities.items()}
    yield
    # Restore original state after test
    for activity_name, data in original.items():
        activities[activity_name]["participants"] = data["participants"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client, reset_activities):
        """GET /activities should return 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client, reset_activities):
        """GET /activities should return a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_has_expected_activities(self, client, reset_activities):
        """GET /activities should return all activities"""
        response = client.get("/activities")
        activities_result = response.json()
        assert "Chess Club" in activities_result
        assert "Programming Class" in activities_result
        assert "Gym Class" in activities_result

    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Activity objects should have required fields"""
        response = client.get("/activities")
        activities_result = response.json()
        activity = activities_result["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_returns_200(self, client, reset_activities):
        """Successful signup should return 200"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 200

    def test_signup_adds_participant(self, client, reset_activities):
        """Signup should add participant to activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert "newstudent@mergington.edu" in chess_club["participants"]

    def test_signup_returns_success_message(self, client, reset_activities):
        """Signup should return success message"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Signing up twice should return 400 error"""
        email = "testuser@mergington.edu"
        
        # First signup succeeds
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup fails
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400

    def test_signup_duplicate_error_message(self, client, reset_activities):
        """Duplicate signup should return appropriate error message"""
        email = "testuser@mergington.edu"
        
        # First signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Second signup
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Signing up for non-existent activity should return 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 404

    def test_signup_nonexistent_activity_error_message(self, client, reset_activities):
        """Error for non-existent activity should have appropriate message"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert "not found" in response.json()["detail"].lower()


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_returns_200(self, client, reset_activities):
        """Successful unregister should return 200"""
        email = "testuser@mergington.edu"
        
        # Sign up first
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200

    def test_unregister_removes_participant(self, client, reset_activities):
        """Unregister should remove participant from activity"""
        email = "testuser@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert email not in chess_club["participants"]

    def test_unregister_returns_success_message(self, client, reset_activities):
        """Unregister should return success message"""
        email = "testuser@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Unregister
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert "Unregistered" in response.json()["message"]

    def test_unregister_not_registered_returns_404(self, client, reset_activities):
        """Unregistering someone not signed up should return 404"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Unregistering from non-existent activity should return 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 404


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_redirects_to_static(self, client):
        """GET / should redirect to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
