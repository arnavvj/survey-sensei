-- Sample Data for Survey Sensei
-- Use this for development and testing

-- =====================================================
-- Sample Products
-- =====================================================
INSERT INTO products (item_id, source_platform, product_url, title, brand, description, pictures, tags, version_number) VALUES
(
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    'amazon',
    'https://amazon.com/dp/B08N5WRWNW',
    'Sony WH-1000XM4 Wireless Noise Canceling Headphones',
    'Sony',
    'Industry-leading noise canceling with Dual Noise Sensor technology. Next-level music with Edge-AI, co-developed with Sony Music Studios Tokyo.',
    '["https://example.com/sony-headphones-1.jpg", "https://example.com/sony-headphones-2.jpg"]'::jsonb,
    ARRAY['electronics', 'audio', 'headphones', 'wireless', 'noise-canceling'],
    1
),
(
    '550e8400-e29b-41d4-a716-446655440002'::uuid,
    'amazon',
    'https://amazon.com/dp/B07XJ8C8F5',
    'Apple AirPods Pro (2nd Generation)',
    'Apple',
    'Active Noise Cancellation, Adaptive Transparency, Personalized Spatial Audio with dynamic head tracking',
    '["https://example.com/airpods-1.jpg", "https://example.com/airpods-2.jpg"]'::jsonb,
    ARRAY['electronics', 'audio', 'earbuds', 'wireless', 'apple'],
    1
),
(
    '550e8400-e29b-41d4-a716-446655440003'::uuid,
    'amazon',
    'https://amazon.com/dp/B0863TXGM3',
    'Logitech MX Master 3S Wireless Mouse',
    'Logitech',
    'Performance Wireless Mouse with Ultra-fast Scrolling, Ergonomic, 8K DPI, Track on Glass, Quiet Clicks',
    '["https://example.com/logitech-mouse-1.jpg"]'::jsonb,
    ARRAY['electronics', 'computer-accessories', 'mouse', 'wireless'],
    1
);

-- =====================================================
-- Sample Users
-- =====================================================
INSERT INTO users (user_id, user_name, email_id, age, base_location, base_zip, gender, credit_score, avg_monthly_expenses) VALUES
(
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    'John Doe',
    'john.doe@example.com',
    32,
    'San Francisco, CA',
    '94102',
    'Male',
    750,
    3500.00
),
(
    '650e8400-e29b-41d4-a716-446655440002'::uuid,
    'Sarah Johnson',
    'sarah.j@example.com',
    28,
    'Austin, TX',
    '73301',
    'Female',
    720,
    2800.00
),
(
    '650e8400-e29b-41d4-a716-446655440003'::uuid,
    'Mike Chen',
    'mike.chen@example.com',
    35,
    'Seattle, WA',
    '98101',
    'Male',
    680,
    4200.00
);

-- =====================================================
-- Sample Transactions
-- =====================================================
INSERT INTO transactions (transaction_id, item_id, user_id, order_date, delivery_date, expected_delivery_date, original_price, retail_price, transaction_status) VALUES
(
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '2024-10-15 14:30:00+00',
    '2024-10-18 09:15:00+00',
    '2024-10-20 23:59:59+00',
    349.99,
    279.99,
    'delivered'
),
(
    '750e8400-e29b-41d4-a716-446655440002'::uuid,
    '550e8400-e29b-41d4-a716-446655440002'::uuid,
    '650e8400-e29b-41d4-a716-446655440002'::uuid,
    '2024-10-20 10:00:00+00',
    '2024-10-22 14:30:00+00',
    '2024-10-25 23:59:59+00',
    249.99,
    199.99,
    'delivered'
),
(
    '750e8400-e29b-41d4-a716-446655440003'::uuid,
    '550e8400-e29b-41d4-a716-446655440003'::uuid,
    '650e8400-e29b-41d4-a716-446655440003'::uuid,
    '2024-11-01 16:45:00+00',
    '2024-11-03 11:20:00+00',
    '2024-11-05 23:59:59+00',
    99.99,
    89.99,
    'delivered'
);

-- =====================================================
-- Sample Reviews
-- =====================================================
INSERT INTO reviews (review_id, item_id, user_id, transaction_id, timestamp, review_title, review_text, review_stars, manual_or_agent_generated) VALUES
(
    '850e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '2024-10-19 15:00:00+00',
    'Best noise canceling headphones!',
    'These headphones are absolutely amazing. The noise canceling is incredible - I use them daily for work calls and the sound quality is top-notch. Battery life easily lasts 2 days of heavy use.',
    5,
    'manual'
),
(
    '850e8400-e29b-41d4-a716-446655440002'::uuid,
    '550e8400-e29b-41d4-a716-446655440002'::uuid,
    '650e8400-e29b-41d4-a716-446655440002'::uuid,
    '750e8400-e29b-41d4-a716-446655440002'::uuid,
    '2024-10-23 18:30:00+00',
    'Great but expensive',
    'Sound quality is excellent and they fit perfectly in my ears. Noise cancellation works well on flights. Only complaint is the price - a bit steep compared to alternatives.',
    4,
    'manual'
);

-- =====================================================
-- Sample Survey Session
-- =====================================================
INSERT INTO survey_sessions (session_id, user_id, transaction_id, is_completed, total_questions, answered_questions, average_confidence_score) VALUES
(
    '950e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    true,
    5,
    5,
    0.92
);

-- =====================================================
-- Sample Survey Questions (SURVEY)
-- =====================================================
INSERT INTO survey (
    scenario_id,
    item_id,
    user_id,
    transaction_id,
    survey_id,
    question_id,
    question_number,
    question,
    options_object,
    selected_option,
    correctly_anticipates_user_sentiment
) VALUES
(
    '950e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '850e8400-e29b-41d4-a716-446655440001'::uuid,
    'a50e8400-e29b-41d4-a716-446655440001'::uuid,
    1,
    'The product description mentions "industry-leading noise canceling with Dual Noise Sensor technology." How well did the noise cancellation meet your expectations in real-world use?',
    '{"type": "multiple_choice", "options": ["Exceeded my expectations - blocks out almost all ambient noise", "Met my expectations - effectively reduces most background sounds", "Somewhat below expectations - noticeable but not as effective as advertised", "Did not meet expectations - minimal noise reduction"], "allow_multiple": false}'::jsonb,
    'Exceeded my expectations - blocks out almost all ambient noise',
    true
),
(
    '950e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '850e8400-e29b-41d4-a716-446655440001'::uuid,
    'a50e8400-e29b-41d4-a716-446655440002'::uuid,
    2,
    'The headphones claim to deliver "next-level music with Edge-AI" technology. Did you notice any difference in sound quality compared to other headphones you''ve used?',
    '{"type": "multiple_choice", "options": ["Yes, significantly better audio quality with noticeable clarity and depth", "Yes, slightly better but the difference is subtle", "About the same as other premium headphones", "No difference or worse than my previous headphones"], "allow_multiple": false}'::jsonb,
    'Yes, significantly better audio quality with noticeable clarity and depth',
    true
),
(
    '950e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '850e8400-e29b-41d4-a716-446655440001'::uuid,
    'a50e8400-e29b-41d4-a716-446655440003'::uuid,
    3,
    'How would you describe the battery life during your typical daily use?',
    '{"type": "multiple_choice", "options": ["Lasts 2+ days on a single charge", "Lasts a full day with moderate to heavy use", "Needs charging after 6-8 hours of use", "Needs charging multiple times per day"], "allow_multiple": false}'::jsonb,
    'Lasts 2+ days on a single charge',
    true
),
(
    '950e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '850e8400-e29b-41d4-a716-446655440001'::uuid,
    'a50e8400-e29b-41d4-a716-446655440004'::uuid,
    4,
    'Thinking about comfort during extended listening sessions, how do the headphones feel after wearing them for 2-3 hours?',
    '{"type": "multiple_choice", "options": ["Extremely comfortable - barely notice I''m wearing them", "Comfortable - minor ear fatigue but manageable", "Somewhat uncomfortable - need breaks after prolonged use", "Uncomfortable - ear pain or pressure headaches"], "allow_multiple": false}'::jsonb,
    'Extremely comfortable - barely notice I''m wearing them',
    true
),
(
    '950e8400-e29b-41d4-a716-446655440001'::uuid,
    '550e8400-e29b-41d4-a716-446655440001'::uuid,
    '650e8400-e29b-41d4-a716-446655440001'::uuid,
    '750e8400-e29b-41d4-a716-446655440001'::uuid,
    '850e8400-e29b-41d4-a716-446655440001'::uuid,
    'a50e8400-e29b-41d4-a716-446655440005'::uuid,
    5,
    'Overall, how would you rate your satisfaction with this purchase?',
    '{"type": "rating", "min": 1, "max": 5, "labels": {"1": "Very Dissatisfied", "2": "Dissatisfied", "3": "Neutral", "4": "Satisfied", "5": "Very Satisfied"}}'::jsonb,
    '5',
    true
);

-- =====================================================
-- Update review count for products
-- (Trigger should handle this, but just in case)
-- =====================================================
UPDATE products SET review_count = (
    SELECT COUNT(*) FROM reviews WHERE reviews.item_id = products.item_id
);
