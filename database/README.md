# Survey Sensei - Database Setup Guide

## Overview

This database schema is optimized for a **GenAI-powered agentic survey system**. The architecture supports dynamic, personalized survey generation based on user profiles, purchase history, and real-time sentiment analysis.

## Architecture Highlights

### Key GenAI Optimizations

1. **Vector Embeddings (pgvector)**
   - Product embeddings for semantic search
   - User profile embeddings for personalization
   - Review embeddings for sentiment clustering
   - Enables similarity search and recommendation systems

2. **Agentic Survey System**
   - `survey` table stores dynamically generated questions
   - `agent_reasoning` field provides explainability
   - `agent_confidence_score` for quality control
   - `correctly_anticipates_user_sentiment` for model improvement

3. **Session State Management**
   - `survey_sessions` tracks entire conversation flow
   - `session_context` (JSONB) stores agent memory
   - Enables multi-turn conversational surveys

## Database Schema

### Core Tables

#### 1. `products`
Stores product catalog with semantic embeddings.

**Key Fields:**
- `embeddings` (vector): For semantic product search
- `tags` (array): Multi-label categorization
- `pictures` (JSONB): Flexible image storage

#### 2. `users`
User profiles with demographic data for personalization.

**Key Fields:**
- `embeddings` (vector): User profile representation
- Demographics: age, location, credit_score, spending patterns

#### 3. `transactions`
Purchase and delivery tracking with computed fields.

**Key Features:**
- Auto-computed `discount_percentage`
- Constraint validation for dates and prices
- Status tracking (pending, delivered, returned)

#### 4. `reviews`
User-generated reviews with AI-enhanced metadata.

**Key Fields:**
- `embeddings` (vector): Review semantic representation
- `sentiment_score` (-1.0 to 1.0): AI-computed sentiment
- `toxicity_score` (0.0 to 1.0): Content moderation
- One review per transaction (enforced by constraint)

#### 5. `survey` ⭐ **Core Agentic System**
Dynamically generated survey questions with agent metadata.

**Key Fields:**
- `question` & `options_object`: Flexible question formats
- `selected_option` (TEXT): User's selected answer/option
- `agent_reasoning`: Explainability for each question
- `agent_confidence_score`: Quality metric
- `user_response` (JSONB): Stores actual answers with metadata
- `follow_up_trigger`: Enables conversational flow

#### 6. `survey_sessions` 🆕
Tracks complete survey sessions for analytics.

**Key Features:**
- Progress tracking (total vs answered questions)
- Agent performance metrics
- `session_context` (JSONB): Maintains conversation state

## Quick Setup (One Command)

### Option 1: Automated Migration Tool (Easiest)

```bash
# Run the Python migration tool
cd backend
conda activate survey-sensei
python ../database/init/apply_migrations.py
```

This will:
- Display all migration SQL
- Save combined SQL to `database/migrations/_combined_migrations.sql`
- Provide copy-paste instructions for Supabase SQL Editor

### Option 2: Using psql (Terminal)

```bash
# Get your database password from: Supabase Dashboard → Settings → Database
export PGPASSWORD='your-database-password'

# Run all migrations
cat database/migrations/*.sql | psql \
    -h db.tursagcbtccbzdyjavex.supabase.co \
    -p 5432 -U postgres -d postgres
```

Or use the provided script:
```bash
chmod +x database/init/run_migrations.sh
PGPASSWORD='your-password' ./database/init/run_migrations.sh
```

### Option 3: Manual SQL Editor

Copy and paste the contents of `database/migrations/_combined_migrations.sql` (auto-generated) or individual migration files into the Supabase SQL Editor:
- Go to: https://tursagcbtccbzdyjavex.supabase.co/project/default/sql/new
- Paste SQL and click "Run"

## Setup Instructions (Detailed)

### Prerequisites

1. **Supabase Account**: https://supabase.com
2. **pgvector Extension**: Required for embeddings (auto-installed via migrations)
3. **Conda Environment**: Uses `survey-sensei` environment (no separate requirements.txt needed)

### Folder Structure

```
database/
├── init/                    # Migration tools and scripts
│   ├── apply_migrations.py  # Python migration tool (recommended)
│   ├── run_migrations.py    # Alternative Python runner
│   └── run_migrations.sh    # Bash script for psql
├── migrations/              # SQL migration files (run in order)
│   ├── 001_enable_extensions.sql
│   ├── 002_create_products_table.sql
│   ├── 003_create_users_table.sql
│   ├── 004_create_transactions_table.sql
│   ├── 005_create_reviews_table.sql
│   ├── 006_create_survey_table.sql
│   ├── 007_create_survey_sessions_table.sql
│   ├── 008_create_triggers.sql
│   ├── 009_enable_row_level_security.sql
│   └── _combined_migrations.sql  # Auto-generated combined SQL
├── seed/                    # Sample data for testing
│   └── 001_sample_data.sql
├── functions/               # Custom PostgreSQL functions
│   └── match_products.sql
└── README.md               # This file
```

### Migration Files

Each migration is in a separate file for clarity and granular control:

1. **001_enable_extensions.sql** - PostgreSQL extensions (uuid-ossp, vector)
2. **002_create_products_table.sql** - Product catalog with embeddings
3. **003_create_users_table.sql** - User profiles and demographics
4. **004_create_transactions_table.sql** - Purchase tracking
5. **005_create_reviews_table.sql** - User reviews with sentiment
6. **006_create_survey_table.sql** - Survey questions and responses
7. **007_create_survey_sessions_table.sql** - Survey session tracking
8. **008_create_triggers.sql** - Auto-update triggers
9. **009_enable_row_level_security.sql** - RLS policies

### Step 3: Verify Installation

Run this query to verify all tables were created:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

Expected output:
- products
- reviews
- survey
- survey_sessions
- transactions
- users

### Step 4: Load Sample Data (Optional)

For development/testing, load sample data:

```sql
-- Copy contents of seed/001_sample_data.sql
```

### Step 5: Verify Row Level Security (RLS)

Check that RLS is enabled:

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

All tables should show `rowsecurity = true`.

## Database Features

### Auto-Timestamps

All tables automatically maintain:
- `created_at`: Set on insert
- `updated_at`: Auto-updated on modification

### Triggers

1. **Update Timestamps**: Auto-updates `updated_at` on all tables
2. **Review Count**: Auto-increments `products.review_count` when reviews are added/removed

### Constraints

- **Check Constraints**: Validate data ranges (ages, scores, dates)
- **Foreign Keys**: Enforce referential integrity with CASCADE deletes
- **Unique Constraints**: Prevent duplicate reviews per transaction

### Indexes

Performance-optimized indexes on:
- Foreign keys (for joins)
- Frequently queried fields (status, dates, platforms)
- Vector embeddings (IVFFlat for similarity search)
- JSONB fields (GIN indexes)

## Row Level Security (RLS)

### Current Policies

1. **Products**: Public read access (catalog browsing)
2. **Users**: Users can only view their own profile
3. **Transactions**: Users can only view their own purchases
4. **Reviews**: Users can view and create their own reviews
5. **Survey Questions**: Users can view their own surveys
6. **Sessions**: Users can view their own survey sessions

### Customizing RLS

For development, you may want to temporarily disable RLS:

```sql
ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
```

**⚠️ Warning**: Never disable RLS in production!

## Vector Embeddings Setup

### Dimension Size

Default: **1536** (OpenAI `text-embedding-ada-002`)

To use different embedding models:
- **OpenAI text-embedding-3-small**: 1536 dimensions
- **OpenAI text-embedding-3-large**: 3072 dimensions
- **Cohere embed-v3**: 1024 dimensions

Update the schema:

```sql
ALTER TABLE products
ALTER COLUMN embeddings TYPE vector(3072);
```

### Similarity Search Example

Find similar products:

```sql
SELECT item_id, title,
       1 - (embeddings <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM products
ORDER BY embeddings <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

## GenAI Integration Points

### 1. Product Embeddings
```python
# Generate on product creation
embedding = openai.Embedding.create(
    input=f"{product.title} {product.description}",
    model="text-embedding-ada-002"
)
```

### 2. User Profile Embeddings
```python
# Aggregate user preferences
user_profile = f"Age: {age}, Location: {location}, Interests: {tags}"
embedding = generate_embedding(user_profile)
```

### 3. Review Sentiment
```python
# Analyze review sentiment
sentiment = analyze_sentiment(review_text)  # -1.0 to 1.0
toxicity = moderate_content(review_text)    # 0.0 to 1.0
```

### 4. Dynamic Question Generation (Core Agentic System)
```python
# Agent generates contextual questions
question = agent.generate_question(
    user_profile=user_embeddings,
    product=product_data,
    transaction=transaction_data,
    previous_answers=session_context
)
```

## Schema Evolution

### Adding New Columns

```sql
ALTER TABLE products
ADD COLUMN new_field TEXT;
```

### Creating Migrations

For future schema changes, create numbered migration files in `database/migrations/`:

```bash
# Example: Adding a new column
database/migrations/010_add_user_preferences.sql
```

Best practices:
- Use sequential numbering (010, 011, 012...)
- One logical change per file
- Include descriptive names
- Run migration tool after creating: `python database/init/apply_migrations.py`

## Performance Optimization

### Index Tuning

Monitor query performance:

```sql
EXPLAIN ANALYZE
SELECT * FROM products WHERE source_platform = 'amazon';
```

### Vector Index Optimization

Adjust IVFFlat lists based on table size:

```sql
-- For larger datasets (>1M rows), increase lists
CREATE INDEX idx_products_embeddings
ON products USING ivfflat(embeddings vector_cosine_ops)
WITH (lists = 1000);
```

## Backup & Recovery

### Export Schema

```sql
pg_dump -h db.xxx.supabase.co -U postgres -s public > schema_backup.sql
```

### Export Data

```sql
pg_dump -h db.xxx.supabase.co -U postgres -a public > data_backup.sql
```

## Troubleshooting

### Common Issues

1. **pgvector extension not found**
   ```sql
   CREATE EXTENSION vector;
   ```

2. **RLS blocking queries**
   - Check authentication: `SELECT auth.uid();`
   - Review policies: `SELECT * FROM pg_policies;`

3. **Slow vector queries**
   - Ensure IVFFlat index is created
   - Increase `lists` parameter for larger datasets

## Next Steps (Phase 1-4)

- **Phase 1**: Frontend UI for survey interaction
- **Phase 2**: Agentic backend (LangGraph/LangChain agents)
- **Phase 3**: REST/GraphQL APIs
- **Phase 4**: Production deployment

## Connection Details

```env
SUPABASE_URL=https://tursagcbtccbzdyjavex.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
```

See `.env.example` for complete configuration.

## Support

For issues or questions:
1. Check Supabase logs: Project Settings → Database → Logs
2. Review table constraints: `\d+ table_name` in psql
3. Verify RLS policies: `SELECT * FROM pg_policies WHERE tablename = 'your_table';`

---

**Schema Version**: 1.0
**Last Updated**: 2025-01-08
**Optimized for**: GenAI Agentic Survey Systems
