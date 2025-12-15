# Survey Sensei Database

PostgreSQL database schema with pgvector for Survey Sensei's AI-powered survey system.

## Overview

The database supports:
- Product catalog with vector embeddings
- User profiles with engagement metrics
- Transaction tracking
- Product reviews with sentiment analysis
- Survey sessions with agent contexts
- Survey event logging

## Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Wait for initialization (~2 minutes)
4. Save Project URL and API keys

### 2. Run Migrations

**Option A: Use Combined Migration (Recommended)**

1. Open Supabase SQL Editor
2. Copy entire contents of `backend/database/_combined_migrations.sql`
3. Paste and execute
4. Verify 6 tables created

**Option B: Run Individual Migrations**

Execute files in order from `backend/database/migrations/`:
1. `001_enable_extensions.sql`
2. `002_create_products_table.sql`
3. `003_create_users_table.sql`
4. `004_create_transactions_table.sql`
5. `005_create_reviews_table.sql`
6. `006_create_survey_sessions_table.sql`
7. `007_create_survey_details_table.sql`
8. `008_create_triggers.sql`
9. `009_enable_row_level_security.sql`

### 3. Verify Tables

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Expected tables:
- `products`
- `users`
- `transactions`
- `reviews`
- `survey_sessions`
- `survey_details`

## Database Schema

### Core Tables

#### 1. products

Product catalog from Amazon with vector embeddings.

**Key Columns:**
```sql
item_id VARCHAR(20) PRIMARY KEY           -- ASIN (Amazon ID)
title TEXT NOT NULL
brand VARCHAR(255)
description TEXT
photos JSONB                              -- Array of image URLs
price DECIMAL(12, 2)
star_rating DECIMAL(3, 2)                 -- 0.0-5.0
num_ratings INTEGER                       -- Total ratings from Amazon
review_count INTEGER DEFAULT 0            -- Actual reviews in our DB
category VARCHAR(50)                      -- Product category
embeddings vector(1536)                   -- OpenAI embeddings
is_mock BOOLEAN DEFAULT false             -- true = generated, false = from Amazon
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Indexes:**
- `idx_products_brand`
- `idx_products_star_rating`
- `idx_products_category`
- `idx_products_embeddings` (IVFFlat for vector search)
- `idx_products_is_mock`

#### 2. users

User profiles with demographics and engagement metrics.

**Key Columns:**
```sql
user_id UUID PRIMARY KEY
user_name VARCHAR(255) NOT NULL
email_id VARCHAR(255) UNIQUE NOT NULL
age INTEGER
base_location VARCHAR(255)                -- "City, State"
base_zip VARCHAR(20)
gender VARCHAR(50)                        -- Male, Female
embeddings vector(1536)                   -- User behavior embeddings
total_purchases INTEGER DEFAULT 0
total_reviews INTEGER DEFAULT 0
review_engagement_rate DECIMAL(4,3)       -- % of purchases reviewed
avg_review_rating DECIMAL(3,2)            -- Average star rating
sentiment_tendency VARCHAR(20)            -- positive, critical, balanced, polarized, neutral
engagement_level VARCHAR(30)              -- highly_engaged, moderately_engaged, passive_buyer, new_user
is_main_user BOOLEAN DEFAULT false        -- true = survey target, false = generated
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Indexes:**
- `idx_users_email`
- `idx_users_base_zip`
- `idx_users_embeddings` (IVFFlat)
- `idx_users_is_main_user`
- `idx_users_engagement_rate`
- `idx_users_engagement_level`
- `idx_users_sentiment`

#### 3. transactions

Purchase records linking users to products.

**Key Columns:**
```sql
transaction_id UUID PRIMARY KEY
item_id VARCHAR(20) REFERENCES products
user_id UUID REFERENCES users
order_date TIMESTAMP WITH TIME ZONE NOT NULL
delivery_date TIMESTAMP WITH TIME ZONE
expected_delivery_date TIMESTAMP WITH TIME ZONE
return_date TIMESTAMP WITH TIME ZONE
original_price DECIMAL(12, 2) NOT NULL
retail_price DECIMAL(12, 2) NOT NULL     -- Actual price paid
transaction_status VARCHAR(50)            -- pending, shipped, delivered, returned
is_mock BOOLEAN DEFAULT false
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Constraints:**
- `check_delivery_date`: delivery_date >= order_date
- `check_expected_delivery`: expected_delivery_date >= order_date
- `check_return_date`: return_date >= delivery_date
- `check_prices`: original_price >= retail_price AND retail_price > 0

**Indexes:**
- `idx_transactions_item_id`
- `idx_transactions_user_id`
- `idx_transactions_order_date`
- `idx_transactions_status`
- `idx_transactions_is_mock`

#### 4. reviews

Product reviews with embeddings and source tracking.

**Key Columns:**
```sql
review_id UUID PRIMARY KEY
item_id VARCHAR(20) REFERENCES products
user_id UUID REFERENCES users
transaction_id UUID REFERENCES transactions
timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
review_title VARCHAR(500)
review_text TEXT NOT NULL
review_stars INTEGER NOT NULL             -- 1-5
source VARCHAR(20) NOT NULL               -- 'rapidapi', 'agent_generated', 'user_survey'
manual_or_agent_generated VARCHAR(20)     -- 'manual', 'agent'
embeddings vector(1536)                   -- Review sentiment embeddings
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Source Tracking:**
- `source`: Where review came from
  - `rapidapi`: Scraped from Amazon
  - `agent_generated`: Created by MOCK_RVW_MINI_AGENT
  - `user_survey`: Submitted via survey flow
- `manual_or_agent_generated`: Content authorship
  - `manual`: Human-written text
  - `agent`: AI-generated text

**Constraints:**
- `check_review_stars`: review_stars BETWEEN 1 AND 5
- `check_source`: source IN ('rapidapi', 'agent_generated', 'user_survey')
- `check_manual_or_agent`: manual_or_agent_generated IN ('manual', 'agent')
- `unique_review_per_transaction`: One review per transaction

**Indexes:**
- `idx_reviews_item_id`
- `idx_reviews_user_id`
- `idx_reviews_transaction_id`
- `idx_reviews_stars`
- `idx_reviews_embeddings` (IVFFlat)
- `idx_reviews_source`
- `idx_reviews_manual_or_agent`

#### 5. survey_sessions

Survey session tracking with agent contexts and results.

**Key Columns:**
```sql
session_id UUID PRIMARY KEY
user_id UUID REFERENCES users
item_id VARCHAR(20) REFERENCES products
transaction_id UUID REFERENCES transactions
product_context JSONB                     -- ProductContextAgent output
customer_context JSONB                    -- CustomerContextAgent output
session_context JSONB                     -- Survey state + review gen inputs
questions_and_answers JSONB              -- Final Q&A pairs
review_options JSONB                      -- 3 generated review options
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**JSONB Field Details:**

`product_context`:
```json
{
  "key_features": ["..."],
  "major_concerns": ["..."],
  "pros": ["..."],
  "cons": ["..."],
  "common_use_cases": ["..."],
  "context_type": "direct_reviews | similar_products | description_only",
  "confidence_score": 0.85
}
```

`customer_context`:
```json
{
  "purchase_patterns": ["..."],
  "review_behavior": ["..."],
  "product_preferences": ["..."],
  "primary_concerns": ["..."],
  "expectations": ["..."],
  "pain_points": ["..."],
  "engagement_level": "highly_engaged",
  "sentiment_tendency": "positive",
  "review_engagement_rate": 0.75,
  "context_type": "exact_interaction | similar_products | demographics_only",
  "confidence_score": 0.92,
  "data_points_used": 15
}
```

`session_context` (populated at survey completion):
```json
{
  "answers": [...],
  "questions": [...],
  "conversation_history": [...],
  "review_generation_inputs": {
    "survey_responses": [...],
    "product_context": {...},
    "customer_context": {...},
    "product_title": "...",
    "user_reviews": [...]
  },
  "review_generated_at": "2025-01-15T12:34:56Z"
}
```

`questions_and_answers` (populated at survey completion):
```json
[
  {
    "question_number": 1,
    "question_text": "...",
    "answer": "...",
    "timestamp": "2025-01-15T12:30:00Z"
  }
]
```

`review_options` (populated at review generation):
```json
{
  "options": [
    {
      "review_title": "Outstanding Sound Quality and Comfort",
      "review_text": "...",
      "review_stars": 5,
      "tone": "enthusiastic",
      "highlights": ["sound quality", "comfort"]
    }
  ],
  "sentiment_band": "good | okay | bad"
}
```

**Indexes:**
- `idx_survey_sessions_user_id`
- `idx_survey_sessions_item_id`
- `idx_survey_sessions_transaction_id`

#### 6. survey_details

Event log for all survey interactions.

**Key Columns:**
```sql
session_id UUID REFERENCES survey_sessions
detail_id UUID PRIMARY KEY
event_type VARCHAR(50) NOT NULL
event_detail JSONB
created_at TIMESTAMP WITH TIME ZONE
```

**Event Types:**
- `question_generated`
- `answer_submitted`
- `answer_updated`
- `answer_skipped`
- `question_updated`
- `survey_incomplete`
- `survey_aborted`
- `survey_completed`

**Indexes:**
- `idx_survey_details_session_id`
- `idx_survey_details_event_type`
- `idx_survey_details_created_at`

### Table Relationships

```
products (ASIN)
    ↓ 1:N
transactions ← N:1 → users (UUID)
    ↓ 1:1
reviews

survey_sessions
    ├→ products (item_id)
    ├→ users (user_id)
    └→ transactions (transaction_id)

survey_details → survey_sessions
```

## Database Features

### Auto-Generated Fields

**Timestamps:**
- `created_at`: Set on insert
- `updated_at`: Auto-updated on change (via trigger)

**Review Count:**
- `products.review_count`: Auto-incremented/decremented (via trigger)

### Triggers

**update_updated_at_column()**
- Updates `updated_at` timestamp on all tables
- Triggered on UPDATE

**update_product_review_count()**
- Increments `products.review_count` on review insert
- Decrements on review delete

### Vector Functions

**match_products()**
```sql
match_products(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
```

Finds similar products using cosine similarity on embeddings.

**Usage:**
```sql
SELECT * FROM match_products(
  (SELECT embeddings FROM products WHERE item_id = 'B0DCJ5NMV2'),
  0.7,
  10
);
```

## Data Flow

### 1. Form Submission → Mock Data Generation

```
User fills form
    ↓
Frontend: POST /api/mock-data
    ↓
Backend: MOCK_DATA_MINI_AGENT
    ├→ Insert main product (is_mock=false)
    ├→ Generate similar products (is_mock=true)
    ├→ Insert main user (is_main_user=true)
    ├→ Generate mock users (is_main_user=false)
    ├→ Create transactions
    ├→ Generate reviews
    └→ Generate embeddings (OpenAI)
    ↓
Insert all data into Supabase
```

### 2. Survey Flow → Review Creation

```
User clicks "Start Survey"
    ↓
Backend: POST /api/survey/start
    ├→ Create survey_session
    ├→ ProductContextAgent → product_context
    ├→ CustomerContextAgent → customer_context
    └→ SurveyAgent → first question
    ↓
User answers questions (3-7 total)
    ↓
Backend: POST /api/survey/answer (repeated)
    ├→ Store answer in session_context
    ├→ SurveyAgent decides: continue or complete
    └→ If complete: save questions_and_answers
    ↓
User clicks "Generate Reviews"
    ↓
Backend: POST /api/survey/generate-reviews
    ├→ ReviewGenAgent creates 3 options
    ├→ Store in review_options
    └→ Update session_context with review_gen_inputs
    ↓
User selects review
    ↓
Backend: POST /api/survey/submit-review
    ├→ Retrieve from review_options
    └→ Insert into reviews (source='user_survey')
```

## Verification

### Check Tables

```sql
-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Check Data Counts

```sql
-- Count records
SELECT 'products' as table_name, COUNT(*) as count FROM products
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'survey_sessions', COUNT(*) FROM survey_sessions
UNION ALL
SELECT 'survey_details', COUNT(*) FROM survey_details;
```

### Check Embeddings

```sql
-- Verify embeddings populated
SELECT
  'products' as table_name,
  COUNT(*) as total,
  COUNT(embeddings) as with_embeddings,
  ROUND(100.0 * COUNT(embeddings) / COUNT(*), 2) as pct
FROM products
UNION ALL
SELECT
  'users',
  COUNT(*),
  COUNT(embeddings),
  ROUND(100.0 * COUNT(embeddings) / COUNT(*), 2)
FROM users
UNION ALL
SELECT
  'reviews',
  COUNT(*),
  COUNT(embeddings),
  ROUND(100.0 * COUNT(embeddings) / COUNT(*), 2)
FROM reviews;
```

### Check Recent Data

```sql
-- Recent survey sessions
SELECT
  session_id,
  user_id,
  item_id,
  product_context IS NOT NULL as has_product_ctx,
  customer_context IS NOT NULL as has_customer_ctx,
  questions_and_answers IS NOT NULL as has_qa,
  review_options IS NOT NULL as has_reviews,
  created_at
FROM survey_sessions
ORDER BY created_at DESC
LIMIT 5;
```

## Troubleshooting

### Tables Not Appearing

1. Check pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. Check Supabase logs:
   - Go to Project Settings → Database → Logs

3. Re-run migrations:
   - Execute `_combined_migrations.sql` again

### Embeddings Not Populated

1. Check OpenAI API key in backend `.env.local`
2. Verify embedding generation is enabled
3. Check backend logs for errors

### Constraint Violations

**Review stars:**
```sql
-- Must be 1-5
UPDATE reviews SET review_stars = 3 WHERE review_stars < 1 OR review_stars > 5;
```

**Review source:**
```sql
-- Must be 'rapidapi', 'agent_generated', or 'user_survey'
SELECT * FROM reviews WHERE source NOT IN ('rapidapi', 'agent_generated', 'user_survey');
```

### Vector Search Not Working

1. Verify pgvector extension:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

2. Check embeddings exist:
   ```sql
   SELECT COUNT(*) FROM products WHERE embeddings IS NOT NULL;
   ```

3. Test match_products function:
   ```sql
   SELECT * FROM match_products(
     (SELECT embeddings FROM products LIMIT 1),
     0.7,
     5
   );
   ```

## Row Level Security (RLS)

RLS policies are enabled but can be disabled for development:

```sql
-- Disable RLS (development only)
ALTER TABLE products DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE reviews DISABLE ROW LEVEL SECURITY;
ALTER TABLE survey_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE survey_details DISABLE ROW LEVEL SECURITY;
```

**WARNING:** Never disable RLS in production!

## File Structure

```
backend/database/
├── _combined_migrations.sql              # Master reset script (generated)
├── README.md                             # This file
├── supabase_client.py                    # Python database client
├── init/
│   └── apply_migrations.py               # Generates _combined_migrations.sql
└── migrations/
    ├── 001_enable_extensions.sql
    ├── 002_create_products_table.sql
    ├── 003_create_users_table.sql
    ├── 004_create_transactions_table.sql
    ├── 005_create_reviews_table.sql
    ├── 006_create_survey_sessions_table.sql
    ├── 007_create_survey_details_table.sql
    ├── 008_create_triggers.sql
    └── 009_enable_row_level_security.sql
```

## Regenerating Combined Migration

```bash
cd backend
python database/init/apply_migrations.py
```

This creates `backend/database/_combined_migrations.sql` with:
- DROP TABLE statements (master reset)
- All table creation
- Triggers and functions
- RLS policies

---

**Database Version**: 1.0.0
**PostgreSQL Version**: 15+
**Status**: Production Ready
