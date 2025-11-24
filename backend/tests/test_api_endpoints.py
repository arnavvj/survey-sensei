"""
Integration tests for FastAPI endpoints
Tests the complete API workflow
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_form_data():
    """Mock form submission data"""
    return {
        "user_id": "user-123",
        "item_id": "prod-123",
        "form_data": {
            "productUrl": "https://amazon.com/test",
            "hasReviews": "yes",
            "userPersona": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": "30",
                "location": "New York",
            },
            "userHasPurchasedSimilar": "yes",
        },
    }


# ============================================================================
# Health Check Tests
# ============================================================================


def test_root_endpoint(client):
    """Test root endpoint returns health status"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_endpoint(client):
    """Test dedicated health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"


# ============================================================================
# Survey Start Tests
# ============================================================================


@patch("main.survey_agent.start_survey")
def test_start_survey_success(mock_start_survey, client, mock_form_data):
    """Test successful survey start"""
    # Mock agent response
    mock_start_survey.return_value = {
        "session_id": "session-123",
        "question": {
            "question_text": "What feature is most important to you?",
            "options": ["Price", "Quality", "Features", "Brand"],
            "reasoning": "Understanding priorities",
        },
        "question_number": 1,
        "total_questions": 3,
    }

    response = client.post("/api/survey/start", json=mock_form_data)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"] == "session-123"
    assert "question" in data
    assert data["question_number"] == 1
    assert len(data["question"]["options"]) == 4


@patch("main.survey_agent.start_survey")
def test_start_survey_validation_error(mock_start_survey, client):
    """Test validation error when missing required fields"""
    invalid_data = {
        "user_id": "user-123",
        # Missing item_id and form_data
    }

    response = client.post("/api/survey/start", json=invalid_data)
    assert response.status_code == 422  # Validation error


@patch("main.survey_agent.start_survey")
def test_start_survey_agent_error(mock_start_survey, client, mock_form_data):
    """Test error handling when agent fails"""
    mock_start_survey.side_effect = Exception("Agent failed")

    response = client.post("/api/survey/start", json=mock_form_data)
    assert response.status_code == 500
    assert "Failed to start survey" in response.json()["detail"]


# ============================================================================
# Submit Answer Tests
# ============================================================================


@patch("main.survey_agent.submit_answer")
def test_submit_answer_continue(mock_submit_answer, client):
    """Test submitting answer and receiving next question"""
    mock_submit_answer.return_value = {
        "session_id": "session-123",
        "question": {
            "question_text": "How important is warranty?",
            "options": ["Very important", "Somewhat", "Not important"],
        },
        "question_number": 2,
        "total_questions": 5,
    }

    request_data = {
        "session_id": "session-123",
        "answer": "Price",
    }

    response = client.post("/api/survey/answer", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "continue"
    assert data["question_number"] == 2
    assert "question" in data


@patch("main.survey_agent.submit_answer")
def test_submit_answer_completed(mock_submit_answer, client):
    """Test survey completion with review options"""
    mock_submit_answer.return_value = {
        "session_id": "session-123",
        "status": "completed",
        "review_options": [
            {
                "review_text": "Great product! Highly recommend.",
                "rating": 5,
                "sentiment": "positive",
                "tone": "enthusiastic",
            },
            {
                "review_text": "Decent product, meets expectations.",
                "rating": 4,
                "sentiment": "neutral",
                "tone": "balanced",
            },
            {
                "review_text": "Could be better for the price.",
                "rating": 3,
                "sentiment": "negative",
                "tone": "critical",
            },
        ],
    }

    request_data = {
        "session_id": "session-123",
        "answer": "Very important",
    }

    response = client.post("/api/survey/answer", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["review_options"]) == 3
    assert all("review_text" in opt for opt in data["review_options"])


# ============================================================================
# Submit Review Tests
# ============================================================================


@patch("main.survey_agent.submit_review")
def test_submit_review_success(mock_submit_review, client):
    """Test successful review submission"""
    mock_submit_review.return_value = {
        "session_id": "session-123",
        "status": "review_saved",
        "review": {
            "review_text": "Great product!",
            "rating": 5,
            "sentiment": "positive",
        },
    }

    request_data = {
        "session_id": "session-123",
        "selected_review_index": 0,
    }

    response = client.post("/api/survey/review", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "review_saved"
    assert "review" in data


# ============================================================================
# Session Retrieval Tests
# ============================================================================


@patch("main.db.get_survey_session")
def test_get_survey_session(mock_get_session, client):
    """Test retrieving survey session details"""
    mock_get_session.return_value = {
        "session_id": "session-123",
        "user_id": "user-123",
        "item_id": "prod-123",
        "state": "active",
        "conversation_history": [],
    }

    response = client.get("/api/survey/session/session-123")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "session-123"


@patch("main.db.get_survey_session")
def test_get_survey_session_not_found(mock_get_session, client):
    """Test 404 when session not found"""
    mock_get_session.return_value = None

    response = client.get("/api/survey/session/nonexistent")

    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


@patch("main.db.get_session_questions")
def test_get_session_questions(mock_get_questions, client):
    """Test retrieving all questions for a session"""
    mock_get_questions.return_value = [
        {
            "question_id": "q1",
            "question_text": "Test question 1",
            "selected_option": "Answer 1",
        },
        {
            "question_id": "q2",
            "question_text": "Test question 2",
            "selected_option": "Answer 2",
        },
    ]

    response = client.get("/api/survey/questions/session-123")

    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) == 2


# ============================================================================
# CORS Tests
# ============================================================================


def test_cors_headers(client):
    """Test CORS headers are properly set"""
    response = client.options(
        "/api/survey/start",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_invalid_json(client):
    """Test handling of invalid JSON"""
    response = client.post(
        "/api/survey/start",
        data="invalid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_method_not_allowed(client):
    """Test handling of wrong HTTP method"""
    response = client.get("/api/survey/start")  # Should be POST
    assert response.status_code == 405


# ============================================================================
# Integration Test (Full Workflow)
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    not pytest.config.getoption("--run-integration"),
    reason="Requires --run-integration flag",
)
@patch("main.db")
@patch("main.survey_agent")
def test_complete_survey_workflow(mock_agent, mock_db, client, mock_form_data):
    """Test complete survey workflow from start to review submission"""
    # Mock agent responses
    mock_agent.start_survey.return_value = {
        "session_id": "session-123",
        "question": {"question_text": "Q1", "options": ["A", "B"]},
        "question_number": 1,
        "total_questions": 2,
    }

    mock_agent.submit_answer.side_effect = [
        {
            "session_id": "session-123",
            "question": {"question_text": "Q2", "options": ["C", "D"]},
            "question_number": 2,
            "total_questions": 2,
        },
        {
            "session_id": "session-123",
            "status": "completed",
            "review_options": [
                {"review_text": "Great!", "rating": 5, "sentiment": "positive"}
            ],
        },
    ]

    mock_agent.submit_review.return_value = {
        "session_id": "session-123",
        "status": "review_saved",
        "review": {"review_text": "Great!", "rating": 5},
    }

    # 1. Start survey
    response1 = client.post("/api/survey/start", json=mock_form_data)
    assert response1.status_code == 200
    session_id = response1.json()["session_id"]

    # 2. Answer first question
    response2 = client.post(
        "/api/survey/answer", json={"session_id": session_id, "answer": "A"}
    )
    assert response2.status_code == 200

    # 3. Answer second question (survey completes)
    response3 = client.post(
        "/api/survey/answer", json={"session_id": session_id, "answer": "C"}
    )
    assert response3.status_code == 200
    assert response3.json()["status"] == "completed"

    # 4. Submit selected review
    response4 = client.post(
        "/api/survey/review",
        json={"session_id": session_id, "selected_review_index": 0},
    )
    assert response4.status_code == 200
    assert response4.json()["status"] == "review_saved"
