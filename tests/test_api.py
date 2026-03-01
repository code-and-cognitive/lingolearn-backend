"""Integration tests for LingoLearn API"""
import pytest
from fastapi.testclient import TestClient
from src.api import app


client = TestClient(app)

# Get API token from environment or use default for testing
TEST_API_TOKEN = "test-token"


def get_auth_headers():
    """Get authorization headers for testing"""
    return {"Authorization": f"Bearer {TEST_API_TOKEN}"}


class TestHealth:
    """Health check tests"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "online"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "LingoLearn API" in response.json()["name"]


class TestAuthentication:
    """Authentication tests"""
    
    def test_missing_auth_header(self):
        """Test missing authorization header"""
        response = client.get("/status")
        assert response.status_code == 401
    
    def test_invalid_token(self):
        """Test invalid token"""
        response = client.get(
            "/status",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


class TestLessons:
    """Lesson generation tests"""
    
    @pytest.mark.skip(reason="Requires Google API key")
    def test_generate_lesson(self):
        """Test lesson generation"""
        payload = {
            "level": "A1.1",
            "native_lang": "English",
            "target_lang": "French",
            "num_questions": 5
        }
        
        response = client.post(
            "/api/v1/lessons/generate",
            json=payload,
            headers=get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) > 0


class TestUsers:
    """User management tests"""
    
    @pytest.mark.skip(reason="Requires proper setup")
    def test_create_user(self):
        """Test user creation"""
        payload = {
            "name": "Test User",
            "email": "test@example.com",
            "native_lang": "English",
            "target_lang": "French"
        }
        
        response = client.post(
            "/api/v1/users",
            json=payload,
            headers=get_auth_headers()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"


# Example test usage with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
