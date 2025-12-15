"""
Unit tests for Product Context Agent (Agent 1)
Tests all 3 generation paths and edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.product_context_agent import ProductContextAgent, ProductContext


class TestProductContextAgent:
    """Test suite for ProductContextAgent"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return ProductContextAgent()

    @pytest.fixture
    def mock_product_with_reviews(self):
        """Mock product that has reviews"""
        return {
            "item_id": "B09YW8BZDP",
            "title": "Sony WH-1000XM5 Wireless Headphones",
            "brand": "Sony",
            "description": "Premium noise-canceling headphones with 30-hour battery life",
            "price": 399.99,
            "star_rating": 4.7,
            "num_ratings": 15234,
            "review_count": 1523,  # HAS REVIEWS
            "category": "Electronics",
            "embeddings": [0.1] * 1536  # Mock embedding
        }

    @pytest.fixture
    def mock_product_without_reviews(self):
        """Mock product with no reviews"""
        return {
            "item_id": "B0NEWPRODUCT",
            "title": "New Wireless Earbuds",
            "brand": "TechBrand",
            "description": "Latest generation wireless earbuds with ANC",
            "price": 149.99,
            "star_rating": 0.0,
            "num_ratings": 0,
            "review_count": 0,  # NO REVIEWS
            "category": "Electronics",
            "embeddings": [0.2] * 1536
        }

    @pytest.fixture
    def mock_reviews(self):
        """Mock reviews data"""
        return [
            {
                "review_id": "r1",
                "review_stars": 5,
                "review_text": "Amazing sound quality and battery life is excellent. Noise cancellation works perfectly on flights."
            },
            {
                "review_id": "r2",
                "review_stars": 4,
                "review_text": "Great headphones but a bit expensive. Comfortable for long wear."
            },
            {
                "review_id": "r3",
                "review_stars": 5,
                "review_text": "Best headphones I've owned. Perfect for gym and travel."
            },
            {
                "review_id": "r4",
                "review_stars": 3,
                "review_text": "Good sound but Bluetooth sometimes drops connection."
            },
        ] * 10  # 40 reviews total

    @pytest.fixture
    def mock_similar_products(self):
        """Mock similar products with reviews"""
        return [
            {
                "item_id": "B08SIMILAR1",
                "title": "Bose QuietComfort 45",
                "brand": "Bose",
                "review_count": 823,
                "similarity": 0.85,
                "reviews": [
                    {
                        "review_stars": 5,
                        "review_text": "Excellent noise cancellation and comfortable fit."
                    },
                    {
                        "review_stars": 4,
                        "review_text": "Great for travel but pricey."
                    }
                ] * 5
            },
            {
                "item_id": "B08SIMILAR2",
                "title": "Apple AirPods Max",
                "brand": "Apple",
                "review_count": 1234,
                "similarity": 0.78,
                "reviews": [
                    {
                        "review_stars": 5,
                        "review_text": "Premium sound quality and build."
                    },
                    {
                        "review_stars": 3,
                        "review_text": "Too heavy for long wear."
                    }
                ] * 5
            }
        ]

    @pytest.fixture
    def mock_llm_response_path1(self):
        """Mock LLM response for Path 1 (direct reviews)"""
        return Mock(
            content="""{
                "key_features": ["30-hour battery life", "Premium noise cancellation", "Comfortable design"],
                "major_concerns": ["Price point", "Bluetooth connectivity", "Weight"],
                "pros": ["Excellent sound quality", "Long battery life", "Comfortable for extended wear"],
                "cons": ["Expensive", "Occasional Bluetooth drops", "Limited color options"],
                "common_use_cases": ["Air travel", "Gym workouts", "Work from home", "Commuting"],
                "context_type": "direct_reviews",
                "confidence_score": 0.85
            }"""
        )

    @pytest.fixture
    def mock_llm_response_path2(self):
        """Mock LLM response for Path 2 (similar products)"""
        return Mock(
            content="""{
                "key_features": ["Active noise cancellation", "Wireless connectivity", "Long battery"],
                "major_concerns": ["Audio quality", "Comfort", "Price"],
                "pros": ["Category-leading features", "Similar to top-rated products"],
                "cons": ["New product - no user feedback", "Price comparable to competitors"],
                "common_use_cases": ["Travel", "Work", "Exercise"],
                "context_type": "similar_products",
                "confidence_score": 0.65
            }"""
        )

    @pytest.fixture
    def mock_llm_response_path3(self):
        """Mock LLM response for Path 3 (description only)"""
        return Mock(
            content="""{
                "key_features": ["Wireless design", "Noise cancellation"],
                "major_concerns": ["Battery life", "Build quality"],
                "pros": ["Modern features", "Competitive pricing"],
                "cons": ["No user reviews", "Uncertain performance"],
                "common_use_cases": ["General audio use"],
                "context_type": "generic",
                "confidence_score": 0.45
            }"""
        )

    # ============================================================================
    # TEST PATH 1: Product with Direct Reviews
    # ============================================================================

    @patch('agents.product_context_agent.db')
    def test_path1_direct_reviews_success(
        self,
        mock_db,
        agent,
        mock_product_with_reviews,
        mock_reviews,
        mock_llm_response_path1
    ):
        """Test Path 1: Product has reviews - successful generation"""
        # Setup mocks
        mock_db.get_product_by_id.return_value = mock_product_with_reviews
        mock_db.get_product_reviews.return_value = mock_reviews

        # Mock LLM response
        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response_path1):
            context = agent.generate_context("B09YW8BZDP")

        # Assertions
        assert isinstance(context, ProductContext)
        assert context.context_type == "direct_reviews"
        assert 0.70 <= context.confidence_score <= 0.95
        assert len(context.key_features) > 0
        assert len(context.major_concerns) > 0
        assert len(context.pros) > 0
        assert len(context.cons) > 0

        # Verify database calls
        mock_db.get_product_by_id.assert_called_once_with("B09YW8BZDP")
        mock_db.get_product_reviews.assert_called_once_with("B09YW8BZDP", limit=50)

    @patch('agents.product_context_agent.db')
    def test_path1_high_confidence_many_reviews(
        self,
        mock_db,
        agent,
        mock_product_with_reviews,
        mock_reviews
    ):
        """Test Path 1: High confidence with many reviews"""
        mock_db.get_product_by_id.return_value = mock_product_with_reviews
        mock_db.get_product_reviews.return_value = mock_reviews * 3  # 120 reviews

        mock_llm_response = Mock(content='{"key_features": [], "major_concerns": [], "pros": [], "cons": [], "common_use_cases": []}')

        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response):
            context = agent.generate_context("B09YW8BZDP")

        # With 120 reviews, confidence should be at max (0.95)
        assert context.confidence_score == 0.95

    @patch('agents.product_context_agent.db')
    def test_path1_fallback_when_reviews_deleted(
        self,
        mock_db,
        agent,
        mock_product_with_reviews
    ):
        """Test Path 1: Fallback when reviews are deleted after count check"""
        # Product says it has reviews, but fetch returns empty
        mock_db.get_product_by_id.return_value = mock_product_with_reviews
        mock_db.get_product_reviews.return_value = []  # Reviews deleted
        mock_db.find_similar_products.return_value = []

        mock_llm_response = Mock(content='{"key_features": [], "major_concerns": [], "pros": [], "cons": [], "common_use_cases": []}')

        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response):
            context = agent.generate_context("B09YW8BZDP")

        # Should fallback to description-only
        assert context.context_type == "generic"
        assert 0.40 <= context.confidence_score <= 0.50

    # ============================================================================
    # TEST PATH 2: Similar Products with Reviews
    # ============================================================================

    @patch('agents.product_context_agent.db')
    def test_path2_similar_products_success(
        self,
        mock_db,
        agent,
        mock_product_without_reviews,
        mock_similar_products,
        mock_llm_response_path2
    ):
        """Test Path 2: No direct reviews but similar products have reviews"""
        # Setup mocks
        mock_db.get_product_by_id.return_value = mock_product_without_reviews
        mock_db.find_similar_products.return_value = mock_similar_products
        mock_db.get_product_reviews.side_effect = lambda item_id, limit: (
            mock_similar_products[0]["reviews"] if item_id == "B08SIMILAR1"
            else mock_similar_products[1]["reviews"]
        )

        # Mock LLM response
        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response_path2):
            context = agent.generate_context("B0NEWPRODUCT")

        # Assertions
        assert isinstance(context, ProductContext)
        assert context.context_type == "similar_products"
        assert 0.55 <= context.confidence_score <= 0.80
        assert len(context.key_features) > 0

        # Verify vector search was called
        mock_db.find_similar_products.assert_called_once()

    @patch('agents.product_context_agent.db')
    def test_path2_confidence_calculation(
        self,
        mock_db,
        agent,
        mock_product_without_reviews,
        mock_similar_products
    ):
        """Test Path 2: Confidence score calculation based on similar products count"""
        mock_db.get_product_by_id.return_value = mock_product_without_reviews
        mock_db.find_similar_products.return_value = mock_similar_products
        mock_db.get_product_reviews.side_effect = lambda item_id, limit: (
            mock_similar_products[0]["reviews"] if item_id == "B08SIMILAR1"
            else mock_similar_products[1]["reviews"]
        )

        mock_llm_response = Mock(content='{"key_features": [], "major_concerns": [], "pros": [], "cons": [], "common_use_cases": []}')

        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response):
            context = agent.generate_context("B0NEWPRODUCT")

        # Confidence should be based on 2 similar products + reviews
        assert context.confidence_score >= 0.55
        assert context.confidence_score <= 0.80

    # ============================================================================
    # TEST PATH 3: No Reviews Available (Description Only)
    # ============================================================================

    @patch('agents.product_context_agent.db')
    def test_path3_description_only(
        self,
        mock_db,
        agent,
        mock_product_without_reviews,
        mock_llm_response_path3
    ):
        """Test Path 3: No reviews anywhere - use description only"""
        # Setup mocks - no reviews, no similar products
        mock_db.get_product_by_id.return_value = mock_product_without_reviews
        mock_db.find_similar_products.return_value = []  # No similar products

        # Mock LLM response
        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response_path3):
            context = agent.generate_context("B0NEWPRODUCT")

        # Assertions
        assert isinstance(context, ProductContext)
        assert context.context_type == "generic"
        assert 0.40 <= context.confidence_score <= 0.50

    @patch('agents.product_context_agent.db')
    def test_path3_confidence_with_full_product_data(
        self,
        mock_db,
        agent,
        mock_product_without_reviews
    ):
        """Test Path 3: Higher confidence when product has full data"""
        # Product with description, price, rating
        full_product = {**mock_product_without_reviews}
        mock_db.get_product_by_id.return_value = full_product
        mock_db.find_similar_products.return_value = []

        mock_llm_response = Mock(content='{"key_features": [], "major_concerns": [], "pros": [], "cons": [], "common_use_cases": []}')

        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response):
            context = agent.generate_context("B0NEWPRODUCT")

        # Should have bonuses for description, price, star_rating
        assert context.confidence_score == 0.50  # 0.40 + 0.05 + 0.02 + 0.03

    @patch('agents.product_context_agent.db')
    def test_path3_confidence_minimal_data(
        self,
        mock_db,
        agent
    ):
        """Test Path 3: Lowest confidence with minimal product data"""
        minimal_product = {
            "item_id": "B0MINIMAL",
            "title": "Basic Product",
            "brand": "Unknown",
            "description": "Short",  # Too short for bonus
            "price": None,
            "star_rating": None,
            "review_count": 0,
            "embeddings": [0.1] * 1536
        }
        mock_db.get_product_by_id.return_value = minimal_product
        mock_db.find_similar_products.return_value = []

        mock_llm_response = Mock(content='{"key_features": [], "major_concerns": [], "pros": [], "cons": [], "common_use_cases": []}')

        with patch.object(agent.llm, 'invoke', return_value=mock_llm_response):
            context = agent.generate_context("B0MINIMAL")

        # Minimal data should give base confidence only
        assert context.confidence_score == 0.40

    # ============================================================================
    # TEST ERROR HANDLING
    # ============================================================================

    @patch('agents.product_context_agent.db')
    def test_product_not_found_raises_error(self, mock_db, agent):
        """Test that ValueError is raised when product doesn't exist"""
        mock_db.get_product_by_id.return_value = None

        with pytest.raises(ValueError, match="Product not found"):
            agent.generate_context("INVALID_ID")

    @patch('agents.product_context_agent.db')
    def test_llm_parse_error_returns_fallback(
        self,
        mock_db,
        agent,
        mock_product_with_reviews,
        mock_reviews
    ):
        """Test that LLM parse errors return fallback context"""
        mock_db.get_product_by_id.return_value = mock_product_with_reviews
        mock_db.get_product_reviews.return_value = mock_reviews

        # Mock invalid JSON response
        invalid_response = Mock(content="This is not valid JSON!")

        with patch.object(agent.llm, 'invoke', return_value=invalid_response):
            context = agent.generate_context("B09YW8BZDP")

        # Should return fallback context
        assert context.context_type == "direct_reviews"
        assert context.confidence_score == 0.3  # Fallback confidence
        assert "Unable to analyze" in context.key_features[0]

    @patch('agents.product_context_agent.db')
    def test_markdown_wrapped_json_parsing(
        self,
        mock_db,
        agent,
        mock_product_with_reviews,
        mock_reviews
    ):
        """Test that markdown-wrapped JSON is correctly parsed"""
        mock_db.get_product_by_id.return_value = mock_product_with_reviews
        mock_db.get_product_reviews.return_value = mock_reviews

        # Mock response with markdown wrapper
        markdown_response = Mock(content="""```json
{
    "key_features": ["Feature 1"],
    "major_concerns": ["Concern 1"],
    "pros": ["Pro 1"],
    "cons": ["Con 1"],
    "common_use_cases": ["Use 1"]
}
```""")

        with patch.object(agent.llm, 'invoke', return_value=markdown_response):
            context = agent.generate_context("B09YW8BZDP")

        # Should successfully parse despite markdown wrapper
        assert context.key_features == ["Feature 1"]
        assert context.major_concerns == ["Concern 1"]

    # ============================================================================
    # TEST HELPER METHODS
    # ============================================================================

    def test_get_or_generate_embedding_existing(self, agent):
        """Test embedding retrieval when already exists"""
        product = {
            "embeddings": [0.5] * 1536
        }
        embedding = agent._get_or_generate_embedding(product)
        assert len(embedding) == 1536
        assert embedding[0] == 0.5

    def test_get_or_generate_embedding_json_string(self, agent):
        """Test embedding retrieval from JSON string"""
        import json
        product = {
            "embeddings": json.dumps([0.3] * 1536)
        }
        embedding = agent._get_or_generate_embedding(product)
        assert len(embedding) == 1536
        assert embedding[0] == 0.3

    @patch('agents.product_context_agent.embedding_service')
    def test_get_or_generate_embedding_generate_new(self, mock_embedding_service, agent):
        """Test embedding generation when missing"""
        product = {
            "title": "Test Product",
            "description": "Test Description",
            "embeddings": None
        }
        mock_embedding_service.generate_embedding.return_value = [0.7] * 1536

        embedding = agent._get_or_generate_embedding(product)

        mock_embedding_service.generate_embedding.assert_called_once_with("Test Product Test Description")
        assert len(embedding) == 1536

    def test_build_product_stats_full_data(self, agent):
        """Test product stats building with full data"""
        product = {
            "price": 399.99,
            "star_rating": 4.7,
            "num_ratings": 15234,
            "category": "Electronics"
        }
        stats = agent._build_product_stats(product)

        assert "$399.99" in stats
        assert "4.7/5.0" in stats
        assert "15,234" in stats
        assert "Electronics" in stats

    def test_build_product_stats_minimal_data(self, agent):
        """Test product stats building with minimal data"""
        product = {}
        stats = agent._build_product_stats(product)
        assert stats == "No additional statistics available"

    # ============================================================================
    # TEST CONFIDENCE SCORE CALCULATIONS
    # ============================================================================

    def test_calculate_confidence_direct_few_reviews(self, agent):
        """Test confidence calculation with few reviews"""
        confidence = agent._calculate_confidence_direct(10)
        assert confidence == 0.80  # 0.70 + (10/100)

    def test_calculate_confidence_direct_many_reviews(self, agent):
        """Test confidence calculation with many reviews (capped)"""
        confidence = agent._calculate_confidence_direct(50)
        assert confidence == 0.95  # Capped at 0.95

    def test_calculate_confidence_similar_medium(self, agent):
        """Test confidence calculation for similar products path"""
        confidence = agent._calculate_confidence_similar(num_similar=3, num_reviews=20)
        assert 0.55 <= confidence <= 0.80

    def test_calculate_confidence_similar_max(self, agent):
        """Test confidence calculation maxes at 0.80"""
        confidence = agent._calculate_confidence_similar(num_similar=10, num_reviews=200)
        assert confidence == 0.80  # Capped

    def test_calculate_confidence_generic_full_data(self, agent):
        """Test generic confidence with full product data"""
        product = {
            "description": "A" * 100,  # Long description
            "price": 99.99,
            "star_rating": 4.5
        }
        confidence = agent._calculate_confidence_generic(product)
        assert confidence == 0.50  # 0.40 + 0.05 + 0.02 + 0.03

    def test_calculate_confidence_generic_no_data(self, agent):
        """Test generic confidence with minimal data"""
        product = {"description": "Short"}
        confidence = agent._calculate_confidence_generic(product)
        assert confidence == 0.40  # Base only

    # ============================================================================
    # TEST PYDANTIC VALIDATION
    # ============================================================================

    def test_product_context_validation_success(self):
        """Test ProductContext validation with valid data"""
        context = ProductContext(
            key_features=["Feature 1"],
            major_concerns=["Concern 1"],
            pros=["Pro 1"],
            cons=["Con 1"],
            common_use_cases=["Use 1"],
            context_type="direct_reviews",
            confidence_score=0.85
        )
        assert context.confidence_score == 0.85
        assert context.context_type == "direct_reviews"

    def test_product_context_confidence_validation(self):
        """Test that confidence score is validated"""
        with pytest.raises(ValueError, match="Confidence score must be between"):
            ProductContext(
                key_features=[],
                major_concerns=[],
                pros=[],
                cons=[],
                common_use_cases=[],
                context_type="generic",
                confidence_score=1.5  # Invalid: > 1.0
            )

    def test_product_context_type_validation(self):
        """Test that context_type is validated"""
        with pytest.raises(ValueError, match="context_type must be one of"):
            ProductContext(
                key_features=[],
                major_concerns=[],
                pros=[],
                cons=[],
                common_use_cases=[],
                context_type="invalid_type",  # Invalid type
                confidence_score=0.5
            )

    def test_product_context_confidence_rounding(self):
        """Test that confidence score is rounded to 2 decimals"""
        context = ProductContext(
            key_features=[],
            major_concerns=[],
            pros=[],
            cons=[],
            common_use_cases=[],
            context_type="generic",
            confidence_score=0.123456789
        )
        assert context.confidence_score == 0.12  # Rounded

    # ============================================================================
    # TEST INTEGRATION SCENARIOS
    # ============================================================================

    @patch('agents.product_context_agent.db')
    def test_similar_products_filter_excludes_main_product(
        self,
        mock_db,
        agent,
        mock_product_without_reviews
    ):
        """Test that similar products search excludes the main product itself"""
        # Mock similar products that includes the main product
        similar_with_self = [
            {"item_id": "B0NEWPRODUCT", "review_count": 0},  # Main product (should be excluded)
            {"item_id": "B08SIMILAR1", "review_count": 100}
        ]

        mock_db.get_product_by_id.return_value = mock_product_without_reviews
        mock_db.find_similar_products.return_value = similar_with_self
        mock_db.get_product_reviews.return_value = [{"review_stars": 5, "review_text": "Great!"}] * 10

        similar = agent._find_similar_products_with_reviews(mock_product_without_reviews)

        # Should exclude the main product
        assert len(similar) == 1
        assert similar[0]["item_id"] == "B08SIMILAR1"

    @patch('agents.product_context_agent.db')
    def test_similar_products_filter_excludes_no_reviews(
        self,
        mock_db,
        agent,
        mock_product_without_reviews
    ):
        """Test that similar products with no reviews are excluded"""
        similar_mixed = [
            {"item_id": "B08SIM1", "review_count": 100},  # Has reviews
            {"item_id": "B08SIM2", "review_count": 0},    # No reviews (exclude)
            {"item_id": "B08SIM3", "review_count": 50}    # Has reviews
        ]

        mock_db.get_product_by_id.return_value = mock_product_without_reviews
        mock_db.find_similar_products.return_value = similar_mixed
        mock_db.get_product_reviews.return_value = [{"review_stars": 5, "review_text": "Good"}] * 10

        similar = agent._find_similar_products_with_reviews(mock_product_without_reviews)

        # Should only include products with reviews
        assert len(similar) == 2
        assert all(p["review_count"] > 0 for p in similar)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
