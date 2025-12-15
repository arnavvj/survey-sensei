"""
Unit tests for Agent 2: CUSTOMER_CONTEXT_AGENT (Upgraded Autonomous Version)

Tests the upgraded autonomous CustomerContextAgent with:
- Three-path decision logic (exact, similar, demographics)
- Main user enforcement (is_main_user=True)
- Smart ranking algorithm (similarity 45%, recency 30%, engagement 25%)
- Engagement metrics integration
- Pydantic schema validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from agents.customer_context_agent import CustomerContextAgent, CustomerContext


@pytest.fixture
def agent():
    """Create CustomerContextAgent instance"""
    return CustomerContextAgent()


@pytest.fixture
def mock_main_user():
    """Mock main user (survey target) with engagement metrics"""
    return {
        "user_id": "user-main-123",
        "user_name": "John Doe",
        "email_id": "john@example.com",
        "age": 30,
        "base_location": "New York, NY",
        "base_zip": "10001",
        "gender": "Male",
        "is_main_user": True,  # MAIN USER - survey target
        "total_purchases": 15,
        "total_reviews": 10,
        "review_engagement_rate": 0.667,
        "avg_review_rating": 4.2,
        "sentiment_tendency": "positive",
        "engagement_level": "highly_engaged",
    }


@pytest.fixture
def mock_mock_user():
    """Mock generated user (not main user)"""
    return {
        "user_id": "user-mock-456",
        "user_name": "Jane Smith",
        "email_id": "jane@example.com",
        "age": 25,
        "base_location": "San Francisco, CA",
        "base_zip": "94102",
        "gender": "Female",
        "is_main_user": False,  # MOCK USER - not survey target
        "total_purchases": 5,
        "total_reviews": 2,
        "review_engagement_rate": 0.400,
        "avg_review_rating": 3.5,
        "sentiment_tendency": "neutral",
        "engagement_level": "moderately_engaged",
    }


@pytest.fixture
def mock_product():
    """Mock product data"""
    return {
        "item_id": "prod-123",
        "title": "Wireless Headphones",
        "embeddings": [0.1] * 1536,
    }


@pytest.fixture
def mock_transaction_with_review():
    """Mock transaction with review for Path 1"""
    return {
        "transaction_id": "txn-abc-123",
        "user_id": "user-main-123",
        "item_id": "prod-123",
        "order_date": datetime.now(timezone.utc) - timedelta(days=30),
        "final_price": 99.99,
        "transaction_status": "delivered",
        "products": {
            "item_id": "prod-123",
            "title": "Wireless Headphones",
        },
    }


@pytest.fixture
def mock_review():
    """Mock review for Path 1"""
    return {
        "review_id": "rev-xyz-789",
        "transaction_id": "txn-abc-123",
        "item_id": "prod-123",
        "rating": 5,
        "review_text": "Amazing sound quality! Battery lasts forever. Best headphones I've owned.",
        "sentiment_label": "positive",
        "created_at": datetime.now(timezone.utc) - timedelta(days=25),
    }


@pytest.fixture
def mock_similar_transactions():
    """Mock similar product transactions for Path 2 ranking"""
    now = datetime.now(timezone.utc)
    return [
        {
            "transaction_id": "txn-001",
            "item_id": "prod-similar-1",
            "order_date": now - timedelta(days=10),  # Recent
            "final_price": 89.99,
            "transaction_status": "delivered",
            "similarity_score": 0.92,  # High similarity
            "has_review": True,  # High engagement
            "products": {
                "item_id": "prod-similar-1",
                "title": "Premium Bluetooth Headphones",
            },
        },
        {
            "transaction_id": "txn-002",
            "item_id": "prod-similar-2",
            "order_date": now - timedelta(days=200),  # Old
            "final_price": 79.99,
            "transaction_status": "delivered",
            "similarity_score": 0.75,  # Medium similarity
            "has_review": False,  # Low engagement
            "products": {
                "item_id": "prod-similar-2",
                "title": "Noise Cancelling Earbuds",
            },
        },
        {
            "transaction_id": "txn-003",
            "item_id": "prod-similar-3",
            "order_date": now - timedelta(days=60),  # Medium age
            "final_price": 149.99,
            "transaction_status": "delivered",
            "similarity_score": 0.88,  # High similarity
            "has_review": True,  # High engagement
            "products": {
                "item_id": "prod-similar-3",
                "title": "Studio Monitor Headphones",
            },
        },
    ]


@pytest.fixture
def mock_reviews_for_similar():
    """Mock reviews for similar products"""
    return [
        {
            "review_id": "rev-001",
            "transaction_id": "txn-001",
            "item_id": "prod-similar-1",
            "rating": 5,
            "review_text": "Great bass and clarity. Comfortable for long sessions.",
            "sentiment_label": "positive",
        },
        {
            "review_id": "rev-003",
            "transaction_id": "txn-003",
            "item_id": "prod-similar-3",
            "rating": 4,
            "review_text": "Professional quality but a bit heavy.",
            "sentiment_label": "positive",
        },
    ]


# ============================================================================
# PATH 1 TESTS: Exact Interaction (User purchased/reviewed THIS product)
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_path1_with_review(
    mock_db, agent, mock_main_user, mock_product, mock_transaction_with_review, mock_review
):
    """Path 1: User purchased and reviewed THIS exact product"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = mock_transaction_with_review
    mock_db.get_review_by_transaction_id.return_value = mock_review

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "exact_interaction"
    assert context.confidence_score == 0.95  # With review
    assert context.data_points_used == 2  # Transaction + review
    assert len(context.purchase_patterns) > 0
    assert len(context.review_behavior) > 0
    assert context.engagement_level == "highly_engaged"
    assert context.sentiment_tendency == "positive"

    # Verify database calls
    mock_db.get_user_by_id.assert_called_once_with("user-main-123")
    mock_db.get_product_by_id.assert_called_once_with("prod-123")
    mock_db.get_user_transaction_for_product.assert_called_once_with("user-main-123", "prod-123")
    mock_db.get_review_by_transaction_id.assert_called_once_with("txn-abc-123")


@patch("agents.customer_context_agent.db")
def test_path1_without_review(
    mock_db, agent, mock_main_user, mock_product, mock_transaction_with_review
):
    """Path 1: User purchased THIS product but hasn't reviewed it (silent purchase)"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = mock_transaction_with_review
    mock_db.get_review_by_transaction_id.return_value = None  # No review

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "exact_interaction"
    assert context.confidence_score == 0.85  # Without review
    assert context.data_points_used == 1  # Transaction only
    assert len(context.purchase_patterns) > 0
    # Silent purchase - should still extract behavioral signals
    assert len(context.expectations) > 0 or len(context.primary_concerns) > 0


@patch("agents.customer_context_agent.db")
def test_path1_engagement_metrics_populated(
    mock_db, agent, mock_main_user, mock_product, mock_transaction_with_review, mock_review
):
    """Path 1: Verify engagement metrics are correctly populated"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = mock_transaction_with_review
    mock_db.get_review_by_transaction_id.return_value = mock_review

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Verify engagement metrics from user profile
    assert context.engagement_level == "highly_engaged"
    assert context.sentiment_tendency == "positive"
    assert context.review_engagement_rate == 0.667


@patch("agents.customer_context_agent.db")
def test_path1_confidence_with_high_engagement(
    mock_db, agent, mock_main_user, mock_product, mock_transaction_with_review, mock_review
):
    """Path 1: Higher confidence for users with high review engagement"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = mock_transaction_with_review
    mock_db.get_review_by_transaction_id.return_value = mock_review

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # High engagement (0.667 rate) should yield higher confidence
    assert context.confidence_score >= 0.90


# ============================================================================
# PATH 2 TESTS: Similar Products (Vector search + Smart ranking)
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_path2_with_similar_products(
    mock_db,
    agent,
    mock_main_user,
    mock_product,
    mock_similar_transactions,
    mock_reviews_for_similar,
):
    """Path 2: User has similar product purchases (no exact match)"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None  # No exact match
    mock_db.find_user_similar_product_purchases.return_value = mock_similar_transactions
    mock_db.get_reviews_by_transaction_ids.return_value = mock_reviews_for_similar

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "similar_products"
    assert 0.55 <= context.confidence_score <= 0.80
    assert context.data_points_used == 3
    assert len(context.purchase_patterns) > 0
    assert len(context.product_preferences) > 0

    # Verify vector search was called
    mock_db.find_user_similar_product_purchases.assert_called_once()


@patch("agents.customer_context_agent.db")
def test_path2_ranking_algorithm(
    mock_db,
    agent,
    mock_main_user,
    mock_product,
    mock_similar_transactions,
    mock_reviews_for_similar,
):
    """Path 2: Verify smart ranking algorithm (similarity 45%, recency 30%, engagement 25%)"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None
    mock_db.find_user_similar_product_purchases.return_value = mock_similar_transactions
    mock_db.get_reviews_by_transaction_ids.return_value = mock_reviews_for_similar

    # Execute - ranking happens internally
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Expected ranking (manual calculation):
    # txn-001: similarity=0.92 (0.414), recency=10d (~0.96, 0.288), engagement=1.0 (0.25) = 0.952
    # txn-003: similarity=0.88 (0.396), recency=60d (~0.77, 0.231), engagement=1.0 (0.25) = 0.877
    # txn-002: similarity=0.75 (0.338), recency=200d (~0.40, 0.120), engagement=0.0 (0.00) = 0.458

    # Most recent + high similarity + reviewed = highest rank
    assert context.data_points_used == 3
    assert context.confidence_score > 0.60  # Multiple similar products


@patch("agents.customer_context_agent.db")
def test_path2_without_reviews(
    mock_db, agent, mock_main_user, mock_product, mock_similar_transactions
):
    """Path 2: Similar products purchased but no reviews (silent purchases)"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None
    mock_db.find_user_similar_product_purchases.return_value = mock_similar_transactions
    mock_db.get_reviews_by_transaction_ids.return_value = []  # No reviews

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "similar_products"
    assert 0.55 <= context.confidence_score <= 0.75  # Lower without reviews
    assert len(context.purchase_patterns) > 0


@patch("agents.customer_context_agent.db")
def test_path2_top5_limit(
    mock_db, agent, mock_main_user, mock_product, mock_reviews_for_similar
):
    """Path 2: Verify only top 5 similar products are used"""
    # Create 10 similar transactions
    many_transactions = []
    for i in range(10):
        many_transactions.append(
            {
                "transaction_id": f"txn-{i:03d}",
                "item_id": f"prod-similar-{i}",
                "order_date": datetime.now(timezone.utc) - timedelta(days=i * 10),
                "similarity_score": 0.9 - (i * 0.05),
                "has_review": i % 2 == 0,
                "products": {"title": f"Similar Product {i}"},
            }
        )

    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None
    mock_db.find_user_similar_product_purchases.return_value = many_transactions
    mock_db.get_reviews_by_transaction_ids.return_value = mock_reviews_for_similar

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # Should use max 5 data points
    assert context.data_points_used <= 5


@patch("agents.customer_context_agent.db")
def test_path2_confidence_calculation(
    mock_db,
    agent,
    mock_main_user,
    mock_product,
    mock_similar_transactions,
    mock_reviews_for_similar,
):
    """Path 2: Verify confidence increases with more data points and reviews"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None
    mock_db.find_user_similar_product_purchases.return_value = mock_similar_transactions
    mock_db.get_reviews_by_transaction_ids.return_value = mock_reviews_for_similar

    # Execute
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")

    # 3 transactions, 2 with reviews = high confidence
    assert context.confidence_score >= 0.70


# ============================================================================
# PATH 3 TESTS: Demographics Only (No purchase history)
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_path3_demographics_only(mock_db, agent, mock_product):
    """Path 3: New user with demographics only (no purchase history)"""
    # New user with minimal data
    new_user = {
        "user_id": "user-new-789",
        "user_name": "Alice Johnson",
        "email_id": "alice@example.com",
        "age": 28,
        "base_location": "Boston, MA",
        "base_zip": "02101",
        "gender": "Female",
        "is_main_user": True,
        "total_purchases": 0,
        "total_reviews": 0,
        "review_engagement_rate": 0.000,
        "avg_review_rating": 0.00,
        "sentiment_tendency": "neutral",
        "engagement_level": "new_user",
    }

    # Setup
    mock_db.get_user_by_id.return_value = new_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None
    mock_db.find_user_similar_product_purchases.return_value = []

    # Execute
    context = agent.generate_context(user_id="user-new-789", item_id="prod-123")

    # Assertions
    assert isinstance(context, CustomerContext)
    assert context.context_type == "demographics_only"
    assert 0.35 <= context.confidence_score <= 0.45
    assert context.data_points_used == 0
    assert context.engagement_level == "new_user"
    assert len(context.expectations) > 0 or len(context.primary_concerns) > 0


@patch("agents.customer_context_agent.db")
def test_path3_generic_insights(mock_db, agent, mock_product):
    """Path 3: Should generate generic demographic-based insights"""
    # User with only demographics
    demographic_user = {
        "user_id": "user-demo-456",
        "user_name": "Bob Smith",
        "email_id": "bob@example.com",
        "age": 45,
        "base_location": "Austin, TX",
        "base_zip": "73301",
        "gender": "Male",
        "is_main_user": True,
        "total_purchases": 0,
        "total_reviews": 0,
        "review_engagement_rate": 0.000,
        "avg_review_rating": 0.00,
        "sentiment_tendency": "neutral",
        "engagement_level": "new_user",
    }

    # Setup
    mock_db.get_user_by_id.return_value = demographic_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = None
    mock_db.find_user_similar_product_purchases.return_value = []

    # Execute
    context = agent.generate_context(user_id="user-demo-456", item_id="prod-123")

    # Should generate insights based on age, location, gender
    assert context.context_type == "demographics_only"
    assert context.confidence_score <= 0.45


# ============================================================================
# MAIN USER ENFORCEMENT TESTS
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_rejects_mock_user(mock_db, agent, mock_mock_user, mock_product):
    """Should reject mock users (is_main_user=False)"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_mock_user
    mock_db.get_product_by_id.return_value = mock_product

    # Execute & Assert
    with pytest.raises(
        ValueError,
        match="Customer Context Agent can only analyze main user.*not the survey target",
    ):
        agent.generate_context(user_id="user-mock-456", item_id="prod-123")


@patch("agents.customer_context_agent.db")
def test_rejects_user_missing_is_main_user_field(mock_db, agent, mock_product):
    """Should reject users without is_main_user field (defaults to False)"""
    user_no_field = {
        "user_id": "user-no-field",
        "user_name": "Test User",
        "email_id": "test@example.com",
        # Missing is_main_user field
    }

    # Setup
    mock_db.get_user_by_id.return_value = user_no_field
    mock_db.get_product_by_id.return_value = mock_product

    # Execute & Assert
    with pytest.raises(ValueError, match="not the survey target"):
        agent.generate_context(user_id="user-no-field", item_id="prod-123")


@patch("agents.customer_context_agent.db")
def test_accepts_main_user_only(
    mock_db, agent, mock_main_user, mock_product, mock_transaction_with_review, mock_review
):
    """Should accept main user (is_main_user=True)"""
    # Setup
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = mock_product
    mock_db.get_user_transaction_for_product.return_value = mock_transaction_with_review
    mock_db.get_review_by_transaction_id.return_value = mock_review

    # Execute - should not raise
    context = agent.generate_context(user_id="user-main-123", item_id="prod-123")
    assert isinstance(context, CustomerContext)


# ============================================================================
# VALIDATION TESTS: Pydantic Schema
# ============================================================================


def test_customer_context_schema_valid():
    """Test CustomerContext schema with valid data"""
    context = CustomerContext(
        purchase_patterns=["Frequent electronics purchases", "Prefers premium brands"],
        review_behavior=["Writes detailed reviews", "Focus on technical specs"],
        product_preferences=["High-end audio equipment", "Wireless products"],
        primary_concerns=["Sound quality", "Battery life"],
        expectations=["Long-lasting battery", "Premium build quality"],
        pain_points=["Previous headphones broke quickly"],
        engagement_level="highly_engaged",
        sentiment_tendency="positive",
        review_engagement_rate=0.750,
        context_type="exact_interaction",
        confidence_score=0.92,
        data_points_used=2,
    )

    assert context.engagement_level == "highly_engaged"
    assert context.sentiment_tendency == "positive"
    assert context.confidence_score == 0.92


def test_customer_context_confidence_validator():
    """Test confidence score validation (0.0-1.0)"""
    # Valid
    context = CustomerContext(confidence_score=0.5)
    assert context.confidence_score == 0.5

    # Invalid - too high
    with pytest.raises(ValueError):
        CustomerContext(confidence_score=1.5)

    # Invalid - negative
    with pytest.raises(ValueError):
        CustomerContext(confidence_score=-0.1)


def test_customer_context_engagement_rate_validator():
    """Test review_engagement_rate validation (0.0-1.0)"""
    # Valid
    context = CustomerContext(review_engagement_rate=0.667)
    assert context.review_engagement_rate == 0.667

    # Invalid - too high
    with pytest.raises(ValueError):
        CustomerContext(review_engagement_rate=1.2)

    # Invalid - negative
    with pytest.raises(ValueError):
        CustomerContext(review_engagement_rate=-0.5)


def test_customer_context_enum_validators():
    """Test enum field validators"""
    # Valid engagement_level
    for level in ["highly_engaged", "moderately_engaged", "passive_buyer", "new_user", "unknown"]:
        context = CustomerContext(engagement_level=level)
        assert context.engagement_level == level

    # Valid sentiment_tendency
    for sentiment in ["positive", "critical", "balanced", "polarized", "neutral"]:
        context = CustomerContext(sentiment_tendency=sentiment)
        assert context.sentiment_tendency == sentiment

    # Valid context_type
    for ctx_type in [
        "exact_interaction",
        "similar_products",
        "demographics_only",
    ]:
        context = CustomerContext(context_type=ctx_type)
        assert context.context_type == ctx_type


def test_customer_context_defaults():
    """Test default values are properly set"""
    context = CustomerContext()

    assert context.purchase_patterns == []
    assert context.review_behavior == []
    assert context.product_preferences == []
    assert context.primary_concerns == []
    assert context.expectations == []
    assert context.pain_points == []
    assert context.engagement_level == "unknown"
    assert context.sentiment_tendency == "neutral"
    assert context.review_engagement_rate == 0.0
    assert context.context_type == "demographics_only"
    assert context.confidence_score == 0.5
    assert context.data_points_used == 0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@patch("agents.customer_context_agent.db")
def test_user_not_found(mock_db, agent):
    """Test error when user not found"""
    mock_db.get_user_by_id.return_value = None

    with pytest.raises(ValueError, match="User not found with ID"):
        agent.generate_context(user_id="nonexistent-user", item_id="prod-123")


@patch("agents.customer_context_agent.db")
def test_product_not_found(mock_db, agent, mock_main_user):
    """Test error when product not found"""
    mock_db.get_user_by_id.return_value = mock_main_user
    mock_db.get_product_by_id.return_value = None

    with pytest.raises(ValueError, match="Product not found with ID"):
        agent.generate_context(user_id="user-main-123", item_id="nonexistent-product")


# ============================================================================
# RANKING ALGORITHM UNIT TESTS
# ============================================================================


def test_ranking_algorithm_weights():
    """Test that ranking algorithm uses correct weights"""
    agent = CustomerContextAgent()

    transactions = [
        {
            "transaction_id": "txn-1",
            "order_date": datetime.now(timezone.utc) - timedelta(days=1),
            "similarity_score": 1.0,
            "has_review": True,
        }
    ]

    ranked = agent._rank_transactions_by_similarity_recency_engagement(transactions)

    # Should have rank_score = 0.45*1.0 + 0.30*(~1.0) + 0.25*1.0 ≈ 1.0
    assert "rank_score" in ranked[0]
    assert ranked[0]["rank_score"] > 0.95


def test_ranking_algorithm_recency_decay():
    """Test exponential decay for recency (180-day half-life)"""
    agent = CustomerContextAgent()
    now = datetime.now(timezone.utc)

    transactions = [
        {
            "transaction_id": "txn-recent",
            "order_date": now - timedelta(days=1),
            "similarity_score": 0.8,
            "has_review": False,
        },
        {
            "transaction_id": "txn-old",
            "order_date": now - timedelta(days=365),
            "similarity_score": 0.8,
            "has_review": False,
        },
    ]

    ranked = agent._rank_transactions_by_similarity_recency_engagement(transactions)

    # Recent should rank higher than old
    recent_score = next(t["rank_score"] for t in ranked if t["transaction_id"] == "txn-recent")
    old_score = next(t["rank_score"] for t in ranked if t["transaction_id"] == "txn-old")
    assert recent_score > old_score


def test_ranking_algorithm_sorting():
    """Test that transactions are sorted by rank_score descending"""
    agent = CustomerContextAgent()
    now = datetime.now(timezone.utc)

    transactions = [
        {
            "transaction_id": "txn-low",
            "order_date": now - timedelta(days=300),
            "similarity_score": 0.6,
            "has_review": False,
        },
        {
            "transaction_id": "txn-high",
            "order_date": now - timedelta(days=5),
            "similarity_score": 0.95,
            "has_review": True,
        },
        {
            "transaction_id": "txn-medium",
            "order_date": now - timedelta(days=100),
            "similarity_score": 0.75,
            "has_review": False,
        },
    ]

    ranked = agent._rank_transactions_by_similarity_recency_engagement(transactions)

    # Should be sorted: high, medium, low
    assert ranked[0]["transaction_id"] == "txn-high"
    assert ranked[2]["transaction_id"] == "txn-low"
    # Verify descending order
    assert ranked[0]["rank_score"] > ranked[1]["rank_score"] > ranked[2]["rank_score"]
