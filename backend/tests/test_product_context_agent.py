"""
Unit tests for Agent 1: PRODUCT_CONTEXT_AGENT
Tests all three scenarios: direct reviews, similar products, generic
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.product_context_agent import ProductContextAgent, ProductContext


@pytest.fixture
def agent():
    """Create ProductContextAgent instance"""
    return ProductContextAgent()


@pytest.fixture
def mock_product_with_reviews():
    """Mock product data with reviews"""
    return {
        "item_id": "prod-123",
        "title": "Test Product",
        "description": "Test Description",
        "category": "Electronics",
        "price": 99.99,
        "brand": "TestBrand",
        "embedding": [0.1] * 1536,
    }


@pytest.fixture
def mock_reviews():
    """Mock review data"""
    return [
        {
            "review_id": "rev-1",
            "rating": 5,
            "review_text": "Great product! Works perfectly.",
        },
        {
            "review_id": "rev-2",
            "rating": 4,
            "review_text": "Good quality but a bit expensive.",
        },
        {
            "review_id": "rev-3",
            "rating": 2,
            "review_text": "Disappointed with the battery life.",
        },
    ]


@pytest.fixture
def mock_form_data():
    """Mock form submission data"""
    return {
        "productUrl": "https://amazon.com/test",
        "hasReviews": "yes",
        "hasSimilarProductsReviewed": "no",
    }


# ============================================================================
# Test Scenario 1: Product Has Reviews
# ============================================================================


@patch("agents.product_context_agent.db")
def test_generate_context_with_direct_reviews(
    mock_db, agent, mock_product_with_reviews, mock_reviews, mock_form_data
):
    """Test context generation when product has reviews"""
    # Setup mocks
    mock_db.get_product_by_url.return_value = mock_product_with_reviews
    mock_db.get_product_reviews.return_value = mock_reviews

    # Execute
    context = agent.generate_context(
        product_url="https://amazon.com/test",
        has_reviews=True,
        form_data=mock_form_data,
    )

    # Assertions
    assert isinstance(context, ProductContext)
    assert context.context_type == "direct_reviews"
    assert context.confidence_score > 0.6
    assert len(context.major_concerns) > 0
    assert len(context.key_features) > 0
    assert len(context.pros) > 0
    assert len(context.cons) > 0

    # Verify database calls
    mock_db.get_product_by_url.assert_called_once_with("https://amazon.com/test")
    mock_db.get_product_reviews.assert_called_once()


@patch("agents.product_context_agent.db")
def test_generate_context_no_reviews_found(
    mock_db, agent, mock_product_with_reviews, mock_form_data
):
    """Test fallback to generic when no reviews found despite hasReviews=true"""
    # Setup mocks
    mock_db.get_product_by_url.return_value = mock_product_with_reviews
    mock_db.get_product_reviews.return_value = []  # No reviews

    # Execute
    context = agent.generate_context(
        product_url="https://amazon.com/test",
        has_reviews=True,
        form_data=mock_form_data,
    )

    # Assertions
    assert isinstance(context, ProductContext)
    assert context.context_type == "generic"  # Fallback
    assert context.confidence_score == 0.4


# ============================================================================
# Test Scenario 2: Similar Products Have Reviews
# ============================================================================


@patch("agents.product_context_agent.embedding_service")
@patch("agents.product_context_agent.db")
def test_generate_context_with_similar_products(
    mock_db, mock_embedding_service, agent, mock_product_with_reviews
):
    """Test context generation using similar products"""
    # Setup mocks
    mock_product = {**mock_product_with_reviews, "embedding": None}
    mock_db.get_product_by_url.return_value = mock_product
    mock_embedding_service.generate_embedding.return_value = [0.1] * 1536

    similar_products = [
        {
            "title": "Similar Product 1",
            "similarity": 0.85,
            "reviews": [
                {"rating": 5, "review_text": "Excellent similar product!"}
            ],
        }
    ]
    mock_db.get_similar_products_with_reviews.return_value = similar_products

    form_data = {
        "productUrl": "https://amazon.com/test",
        "hasReviews": "no",
        "hasSimilarProductsReviewed": "yes",
    }

    # Execute
    context = agent.generate_context(
        product_url="https://amazon.com/test",
        has_reviews=False,
        form_data=form_data,
    )

    # Assertions
    assert isinstance(context, ProductContext)
    assert context.context_type == "similar_products"
    assert 0.5 <= context.confidence_score <= 0.75

    # Verify embedding generation
    mock_embedding_service.generate_embedding.assert_called_once()


# ============================================================================
# Test Scenario 3: Generic (Cold Start)
# ============================================================================


@patch("agents.product_context_agent.db")
def test_generate_context_generic_cold_start(
    mock_db, agent, mock_product_with_reviews
):
    """Test generic context generation for cold start"""
    # Setup mocks
    mock_db.get_product_by_url.return_value = mock_product_with_reviews
    mock_db.get_similar_products_with_reviews.return_value = []

    form_data = {
        "productUrl": "https://amazon.com/test",
        "hasReviews": "no",
        "hasSimilarProductsReviewed": "no",
    }

    # Execute
    context = agent.generate_context(
        product_url="https://amazon.com/test",
        has_reviews=False,
        form_data=form_data,
    )

    # Assertions
    assert isinstance(context, ProductContext)
    assert context.context_type == "generic"
    assert context.confidence_score == 0.4  # Low confidence
    assert len(context.major_concerns) > 0
    assert len(context.key_features) > 0


# ============================================================================
# Test Error Handling
# ============================================================================


@patch("agents.product_context_agent.db")
def test_generate_context_product_not_found(mock_db, agent, mock_form_data):
    """Test error handling when product not found"""
    mock_db.get_product_by_url.return_value = None

    with pytest.raises(ValueError, match="Product not found"):
        agent.generate_context(
            product_url="https://amazon.com/nonexistent",
            has_reviews=True,
            form_data=mock_form_data,
        )


# ============================================================================
# Test Output Structure
# ============================================================================


def test_product_context_schema():
    """Test ProductContext Pydantic model validation"""
    context = ProductContext(
        major_concerns=["Battery life", "Price"],
        key_features=["Fast charging", "Waterproof"],
        pros=["Durable", "Good design"],
        cons=["Expensive", "Heavy"],
        common_use_cases=["Travel", "Work"],
        context_type="direct_reviews",
        confidence_score=0.85,
    )

    assert context.major_concerns == ["Battery life", "Price"]
    assert context.context_type == "direct_reviews"
    assert 0.0 <= context.confidence_score <= 1.0


def test_product_context_invalid_confidence():
    """Test validation of confidence score range"""
    with pytest.raises(ValueError):
        ProductContext(
            major_concerns=["Test"],
            key_features=["Test"],
            pros=["Test"],
            cons=["Test"],
            common_use_cases=["Test"],
            context_type="direct_reviews",
            confidence_score=1.5,  # Invalid: > 1.0
        )


# ============================================================================
# Integration Test (requires OpenAI API key)
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(
    not pytest.config.getoption("--run-integration"),
    reason="Requires --run-integration flag",
)
@patch("agents.product_context_agent.db")
def test_full_integration_with_real_llm(
    mock_db, agent, mock_product_with_reviews, mock_reviews
):
    """Integration test with real OpenAI API (requires API key)"""
    mock_db.get_product_by_url.return_value = mock_product_with_reviews
    mock_db.get_product_reviews.return_value = mock_reviews

    context = agent.generate_context(
        product_url="https://amazon.com/test",
        has_reviews=True,
        form_data={"hasReviews": "yes"},
    )

    # Verify structure
    assert isinstance(context, ProductContext)
    assert context.context_type == "direct_reviews"
    # With real API, we expect meaningful content
    assert all(len(item) > 10 for item in context.major_concerns)
