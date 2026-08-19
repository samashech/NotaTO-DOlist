import os
import sys

from fastapi.testclient import TestClient

# Add backend to path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Deadline Guardian AI API"}

def test_analyze_risk_mocked(monkeypatch):
    # Mock the genai client response
    class MockResponse:
        def __init__(self, text):
            self.text = text
            
    class MockModels:
        def generate_content(self, model, contents, config=None):
            return MockResponse('{"risk_score": 75, "recommendation": "Mocked rec", "breakdown": ["Step 1", "Step 2"]}')
            
    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()

    # We need to monkeypatch genai.Client in main.py
    import main
    monkeypatch.setattr(main.genai, "Client", MockClient)

    payload = {
        "id": "123",
        "title": "Test Task",
        "description": "A task for testing",
        "due_date": "2026-10-10T10:00:00",
        "estimated_hours": 2.0,
        "status": "pending",
        "priority": "high",
        "blocked_sites": []
    }
    
    response = client.post("/api/analyze_risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 75
    assert data["recommendation"] == "Mocked rec"
    assert len(data["breakdown"]) == 2

def test_interrogation_chat_mocked(monkeypatch):
    class MockResponse:
        def __init__(self, text):
            self.text = text
            
    class MockModels:
        def generate_content(self, model, contents, config=None):
            return MockResponse('{"action": "RESCHEDULE_TASK", "task": {"due_date": "2026-12-01T12:00:00", "estimated_hours": 3.0}}')
            
    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()

    import main
    monkeypatch.setattr(main.genai, "Client", MockClient)

    payload = {
        "messages": [
            {"role": "user", "content": "I failed my task"}
        ]
    }
    
    response = client.post("/api/interrogation_chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "RESCHEDULE_TASK" in data["reply"]
