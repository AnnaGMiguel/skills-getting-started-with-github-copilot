"""
Test suite for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Check that we have activities
        assert len(activities) > 0
        assert isinstance(activities, dict)
        
        # Check specific activities exist
        assert "Basketball" in activities
        assert "Swimming" in activities
        assert "Art Club" in activities
    
    def test_activity_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check Basketball activity structure
        basketball = activities["Basketball"]
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
        assert isinstance(basketball["participants"], list)


class TestSignUp:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]
        
        # Verify the student was added
        activities = client.get("/activities").json()
        assert "newstudent@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_signup_duplicate_student(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Swimming/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Swimming/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/InvalidActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregistration"""
        email = "unregister@mergington.edu"
        
        # First, sign up
        client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Basketball/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify the student was removed
        activities = client.get("/activities").json()
        assert email not in activities["Basketball"]["participants"]
    
    def test_unregister_non_registered_student(self):
        """Test unregistration of student not registered"""
        response = client.delete(
            "/activities/Art Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_invalid_activity(self):
        """Test unregistration from non-existent activity"""
        response = client.delete(
            "/activities/InvalidActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_unregister_cycle(self):
        """Test complete signup and unregister cycle"""
        email = "integration@mergington.edu"
        activity = "Drama Club"
        
        # Get initial participant count
        initial = client.get("/activities").json()
        initial_count = len(initial[activity]["participants"])
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Verify participant added
        after_signup = client.get("/activities").json()
        assert len(after_signup[activity]["participants"]) == initial_count + 1
        assert email in after_signup[activity]["participants"]
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify participant removed
        after_unregister = client.get("/activities").json()
        assert len(after_unregister[activity]["participants"]) == initial_count
        assert email not in after_unregister[activity]["participants"]
    
    def test_multiple_signups_different_activities(self):
        """Test signing up for multiple activities"""
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Basketball", "Swimming", "Art Club"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]
