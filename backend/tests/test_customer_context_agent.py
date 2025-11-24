"""
Unit tests for Agent 2: CUSTOMER_CONTEXT_AGENT
Tests all scenarios: review history, purchase history, demographics, persona-only
"""

import pytest
from unittest.mock import Mock, patch
from agents.customer_context_agent import CustomerContextAgent, CustomerContext


@pytest.fixture
def agent():
    """Create CustomerContextAgent instance"""
    return CustomerContextAgent()


@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "user_id": "user-123",
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "location": "New York, NY",
        "gender": "Male",
        "income_level": "median",
    }


@pytest.fixture
def mock_product():
    """Mock product data"""
    return {
        "item_id": "prod-123",
        "title": "Test Product",
        "embedding": [0.1] * 1536,
    }


@pytest.fixture
def mock_user_reviews():
    """Mock user review history"""
    return [
        {
            "item_id": "prod-456",
            "rating": 5,
            "review_text": "Great product! Love the quality.",
            "sentiment_label": "positive",
            "products": {"title": "Previous Product 1"},
        },
        {
            "item_id": "prod-789",
            "rating": 3,
            "review_text": "It's okay, but could be better.",
            "sentiment_label": "neutral",
            "products": {"title": "Previous Product 2"},
        },
    ]


@pytest.fixture
def mock_transactions():
    """Mock user transaction history"""
    return [
        {
            "item_id": "prod-456",
            "final_price": 99.99,
            "transaction_status": "delivered",
            "similarity_score": 0.85,
            "products": {"title": "Similar Product 1"},
        }
    ]


# ============================================================================
# Test Scenario 1: User Has Review History
# ============================================================================


@patch("agents.customer_context_agent.embedding_service")
@patch("agents.customer_context_agent.db")
def test_generate_context_with_review_history(
    mock_db,
    mock_embedding_service,
    agent,
    mock_user,
    mock_product,
    mock_user_reviews,
    mock_transactions,
):
    """Test context generation from user's review history"""
    # Setup mocks
    mock_db.get_user_by_email.return_value = mock_user
    mock_db.get_product_by_url.return_value = mock_product
    mock_embedding_service.generate_embedding.return_value = [0.1] * 1536
    mock_db.find_user_similar_product_purchases.return_value = mock_transactions
    mock_db.get_user_reviews.return_value = mock_user_reviews

    form_data = {"userHasPurchasedSimilar": "yes"}

    # Execute
    context = agent.generate_context(
        user_email="john@example.com",
        product_url="https://amazon.com/test",
        has_purchased_similar=True,
        form_data=form_data,
    )

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "review_history"
    assert context.confidence_score >= 0.6
    assert len(context.major_concerns) > 0
    assert len(context.expectations) > 0
    assert len(context.purchase_motivations) > 0

    # Verify database calls
    mock_db.get_user_by_email.assert_called_once_with("john@example.com")
    mock_db.get_user_reviews.assert_called_once()


# ============================================================================
# Test Scenario 2: Purchase History Only (No Reviews)
# ============================================================================


@patch("agents.customer_context_agent.embedding_service")
@patch("agents.customer_context_agent.db")
def test_generate_context_purchase_history_only(
    mock_db,
    mock_embedding_service,
    agent,
    mock_user,
    mock_product,
    mock_transactions,
):
    """Test context from purchase history without reviews"""
    # Setup mocks
    mock_db.get_user_by_email.return_value = mock_user
    mock_db.get_product_by_url.return_value = mock_product
    mock_embedding_service.generate_embedding.return_value = [0.1] * 1536
    mock_db.find_user_similar_product_purchases.return_value = mock_transactions
    mock_db.get_user_reviews.return_value = [
        {"item_id": "other-prod"}  # No reviews for similar products
    ]

    # Execute
    context = agent.generate_context(
        user_email="john@example.com",
        product_url="https://amazon.com/test",
        has_purchased_similar=True,
        form_data={"userHasPurchasedSimilar": "yes"},
    )

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "purchase_history"
    assert 0.5 <= context.confidence_score <= 0.7


# ============================================================================
# Test Scenario 3: Demographics Only
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_generate_context_demographics_only(mock_db, agent, mock_user, mock_product):
    """Test context generation from demographics only"""
    # Setup mocks
    mock_db.get_user_by_email.return_value = mock_user
    mock_db.get_product_by_url.return_value = mock_product
    mock_db.find_user_similar_product_purchases.return_value = []

    # Execute
    context = agent.generate_context(
        user_email="john@example.com",
        product_url="https://amazon.com/test",
        has_purchased_similar=False,
        form_data={"userHasPurchasedSimilar": "no"},
    )

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "demographic"
    assert context.confidence_score == 0.5
    assert len(context.user_segment) > 0


# ============================================================================
# Test Scenario 4: New User (Persona Only)
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_generate_context_persona_only(mock_db, agent, mock_product):
    """Test context generation for new user from form persona"""
    # Setup mocks
    mock_db.get_user_by_email.return_value = None  # User not found
    mock_db.get_product_by_url.return_value = mock_product

    form_data = {
        "userPersona": {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": "25",
            "location": "San Francisco",
        },
        "userHasPurchasedSimilar": "no",
    }

    # Execute
    context = agent.generate_context(
        user_email="jane@example.com",
        product_url="https://amazon.com/test",
        has_purchased_similar=False,
        form_data=form_data,
    )

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "demographic"
    assert context.confidence_score == 0.3  # Low confidence


# ============================================================================
# Test Error Handling
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_generate_context_product_not_found(mock_db, agent, mock_user):
    """Test error when product not found"""
    mock_db.get_user_by_email.return_value = mock_user
    mock_db.get_product_by_url.return_value = None

    with pytest.raises(ValueError, match="Product not found"):
        agent.generate_context(
            user_email="john@example.com",
            product_url="https://amazon.com/nonexistent",
            has_purchased_similar=False,
            form_data={},
        )


# ============================================================================
# Test Output Structure
# ============================================================================


def test_customer_context_schema():
    """Test CustomerContext Pydantic model validation"""
    context = CustomerContext(
        major_concerns=["Price", "Quality"],
        expectations=["Fast delivery", "Good support"],
        purchase_motivations=["Reviews", "Brand"],
        pain_points=["Slow shipping"],
        user_segment="budget_conscious",
        context_type="review_history",
        confidence_score=0.75,
    )

    assert context.major_concerns == ["Price", "Quality"]
    assert context.user_segment == "budget_conscious"
    assert context.context_type == "review_history"
    assert 0.0 <= context.confidence_score <= 1.0


def test_customer_context_valid_user_segments():
    """Test different valid user segments"""
    segments = [
        "budget_conscious",
        "quality_seeker",
        "feature_focused",
        "brand_loyal",
    ]

    for segment in segments:
        context = CustomerContext(
            major_concerns=["Test"],
            expectations=["Test"],
            purchase_motivations=["Test"],
            pain_points=["Test"],
            user_segment=segment,
            context_type="demographic",
            confidence_score=0.5,
        )
        assert context.user_segment == segment


# ============================================================================
# Integration Test
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    not pytest.config.getoption("--run-integration"),
    reason="Requires --run-integration flag",
)
@patch("agents.customer_context_agent.embedding_service")
@patch("agents.customer_context_agent.db")
def test_full_integration_with_real_llm(
    mock_db,
    mock_embedding_service,
    agent,
    mock_user,
    mock_product,
    mock_user_reviews,
    mock_transactions,
):
    """Integration test with real OpenAI API"""
    mock_db.get_user_by_email.return_value = mock_user
    mock_db.get_product_by_url.return_value = mock_product
    mock_embedding_service.generate_embedding.return_value = [0.1] * 1536
    mock_db.find_user_similar_product_purchases.return_value = mock_transactions
    mock_db.get_user_reviews.return_value = mock_user_reviews

    context = agent.generate_context(
        user_email="john@example.com",
        product_url="https://amazon.com/test",
        has_purchased_similar=True,
        form_data={"userHasPurchasedSimilar": "yes"},
    )

    # Verify structure and meaningful content
    assert isinstance(context, CustomerContext)
    assert context.context_type in ["review_history", "purchase_history"]
    assert all(len(item) > 5 for item in context.major_concerns)
