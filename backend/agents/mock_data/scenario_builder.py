"""
Scenario Configuration Builder
Maps form data to scenario configurations for the MOCK_DATA_MINI_AGENT framework
"""

from typing import Dict, Any


# Scenario configurations for all 12 scenarios
SCENARIO_CONFIGS = {
    # Group A: Warm Product + Warm User (4 scenarios)
    'A1': {
        'scenario_id': 'A1',
        'group': 'warm_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 24,
        'main_product_reviews': 30,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 1,
        'main_user_similar_reviews': 4,
        'api_review_count': 30,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'A2': {
        'scenario_id': 'A2',
        'group': 'warm_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 24,
        'main_product_reviews': 30,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 1,
        'main_user_similar_reviews': 0,
        'api_review_count': 30,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'A3': {
        'scenario_id': 'A3',
        'group': 'warm_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 24,
        'main_product_reviews': 30,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 4,
        'api_review_count': 30,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'A4': {
        'scenario_id': 'A4',
        'group': 'warm_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 24,
        'main_product_reviews': 30,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 0,
        'api_review_count': 30,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },

    # Group B: Cold Product + Warm User (4 scenarios)
    'B1': {
        'scenario_id': 'B1',
        'group': 'cold_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 18,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 0,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 4,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'B2': {
        'scenario_id': 'B2',
        'group': 'cold_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 18,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 0,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 0,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'B3': {
        'scenario_id': 'B3',
        'group': 'cold_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 18,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 4,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'B4': {
        'scenario_id': 'B4',
        'group': 'cold_warm',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 18,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 4,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 0,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },

    # Group C: Cold Product + Cold User (4 scenarios)
    'C1': {
        'scenario_id': 'C1',
        'group': 'cold_cold',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 12,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 0,
        'main_user_similar_purchases': 0,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 2,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'C2': {
        'scenario_id': 'C2',
        'group': 'cold_cold',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 12,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 0,
        'main_user_similar_purchases': 0,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 0,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'C3': {
        'scenario_id': 'C3',
        'group': 'cold_cold',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 12,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 1,
        'main_user_similar_purchases': 0,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 0,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
    'C4': {
        'scenario_id': 'C4',
        'group': 'cold_cold',
        'similar_product_count': 6,
        'diverse_product_count': 4,
        'mock_user_count': 12,
        'main_product_reviews': 0,
        'similar_product_reviews': 18,
        'main_user_exact_purchases': 0,
        'main_user_similar_purchases': 2,
        'main_user_exact_reviews': 0,
        'main_user_similar_reviews': 0,
        'api_review_count': 0,
        'reviews_per_product': 18,
        'generate_embeddings': True,
    },
}


def determine_scenario_id(form_data: Dict[str, Any]) -> str:
    """
    Determine scenario ID based on form data

    Args:
        form_data: Form submission with fields:
            - productPurchased: 'exact' or 'similar'
            - userPurchasedExact: 'YES' or 'NO'
            - userPurchasedSimilar: 'YES' or 'NO'
            - userReviewedExact: 'YES' or 'NO'
            - userReviewedSimilar: 'YES' or 'NO'

    Returns:
        Scenario ID (A1-A4, B1-B4, C1-C4)
    """
    product_purchased = form_data.get('productPurchased', 'exact')
    user_purchased_exact = form_data.get('userPurchasedExact', 'NO')
    user_purchased_similar = form_data.get('userPurchasedSimilar', 'NO')
    user_reviewed_exact = form_data.get('userReviewedExact', 'NO')
    user_reviewed_similar = form_data.get('userReviewedSimilar', 'NO')

    # Determine product warmth
    is_warm_product = (product_purchased == 'exact')

    # Determine user warmth
    has_purchases = (user_purchased_exact == 'YES' or user_purchased_similar == 'YES')
    has_reviews = (user_reviewed_exact == 'YES' or user_reviewed_similar == 'YES')
    is_warm_user = has_purchases or has_reviews

    # Group A: Warm Product + Warm User
    if is_warm_product and is_warm_user:
        if user_reviewed_exact == 'YES' and user_reviewed_similar == 'YES':
            return 'A1'
        elif user_reviewed_exact == 'YES' and user_reviewed_similar == 'NO':
            return 'A2'
        elif user_reviewed_exact == 'NO' and user_reviewed_similar == 'YES':
            return 'A3'
        else:  # Both NO
            return 'A4'

    # Group B: Cold Product + Warm User
    elif not is_warm_product and is_warm_user:
        if user_purchased_exact == 'NO' and user_reviewed_similar == 'YES':
            return 'B1'
        elif user_purchased_exact == 'NO' and user_reviewed_similar == 'NO':
            return 'B2'
        elif user_purchased_exact == 'YES' and user_reviewed_similar == 'YES':
            return 'B3'
        else:  # userPurchasedExact=YES, userReviewedSimilar=NO
            return 'B4'

    # Group C: Cold Product + Cold User
    else:
        if user_reviewed_similar == 'YES':
            return 'C1'
        elif user_purchased_exact == 'NO' and user_purchased_similar == 'NO':
            return 'C2'
        elif user_purchased_exact == 'YES':
            return 'C3'
        else:  # userPurchasedSimilar=YES
            return 'C4'


def build_scenario_config(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build complete scenario configuration from form data

    Args:
        form_data: Form submission data

    Returns:
        Scenario configuration dictionary
    """
    scenario_id = determine_scenario_id(form_data)
    config = SCENARIO_CONFIGS[scenario_id].copy()

    # Add form data to config for reference
    config['form_data'] = form_data

    return config
