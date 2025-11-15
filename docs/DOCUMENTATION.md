# Survey Sensei - Technical Documentation

Complete system architecture, database schema, API reference, and deployment guide.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [Amazon Product Integration](#amazon-product-integration)
4. [Phase Completion Status](#phase-completion-status)
5. [Development Workflow](#development-workflow)
6. [Production Deployment](#production-deployment)

---

## System Architecture

### High-Level Overview

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   FRONTEND      │◄────►│    BACKEND      │◄────►│    DATABASE     │
│  React/Next.js  │      │ Python/FastAPI  │      │   Supabase      │
│  Tailwind CSS   │      │   LangChain     │      │  PostgreSQL     │
│  Multi-Pane UI  │      │   Agents        │      │   pgvector      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                         │
         └────────────────────────┴─────────────────────────┘
                  RapidAPI (Amazon Product Data)
```

### Tech Stack

**Frontend (Phase 1)**:
- Next.js 14 (App Router) with TypeScript
- Tailwind CSS with custom design system
- Supabase JS Client
- RapidAPI integration

**Backend (Phase 2)**:
- Python 3.11+
- FastAPI
- LangChain / LangGraph
- OpenAI API / Anthropic Claude
- Sentence Transformers

**Database (Phase 0)**:
- Supabase (PostgreSQL 15+)
- pgvector extension (1536-dimensional embeddings)
- Row Level Security (RLS)
- Auto-updating triggers and indexes

**Deployment (Phase 4)**:
- Vercel (Frontend)
- Railway/Render (Backend)
- Supabase Cloud (Database)
- GitHub Actions (CI/CD)

### Key Features

- **Agentic AI Survey Generation**: LangChain agents analyze context and generate personalized questions
- **Vector Embeddings**: Semantic search using pgvector for products, users, and reviews
- **Progressive Form UI**: 7-field intake with conditional logic
- **Multi-Pane Retractable Interface**: 4 distinct UI states with smooth transitions
- **Amazon Product Integration**: RapidAPI-based scraping with intelligent ASIN extraction
- **Mock Data Agent**: Realistic synthetic data generator for simulation
- **Cold Start Handling**: Adapts to limited product/user history scenarios

---

## Database Schema

### Overview

6 tables optimized for GenAI-powered agentic survey systems with vector similarity search.

```
products (1) ─── (*) transactions ─── (*) users
    │                    │
    └──── (*) reviews ───┘
              │
              └──── (*) survey
                         │
                         └──── (*) survey_sessions
```

### Table Definitions

#### 1. products

Product catalog with semantic embeddings for similarity search.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `item_id` | UUID | Primary key (auto-generated) |
| `source_platform` | VARCHAR | Platform: "amazon", "walmart", "etsy", "ebay" |
| `product_url` | TEXT | Original product URL |
| `title` | TEXT | Product title |
| `brand` | VARCHAR | Brand name |
| `description` | TEXT | Full product description |
| `pictures` | JSONB | Array of image URLs |
| `review_count` | INTEGER | Auto-maintained via trigger |
| `average_rating` | DECIMAL(2,1) | Computed from reviews |
| `tags` | TEXT[] | Multi-label categorization |
| `embeddings` | vector(1536) | Semantic product representation |
| `created_at` | TIMESTAMP | Auto-set on insert |
| `updated_at` | TIMESTAMP | Auto-updated on modification |

**Indexes**:
- B-tree: `source_platform`, `brand`
- GIN: `tags`
- IVFFlat: `embeddings` (for cosine similarity)

**Example Query**:
```sql
-- Find similar products using cosine similarity
SELECT item_id, title,
       1 - (embeddings <=> $1::vector) AS similarity
FROM products
ORDER BY embeddings <=> $1::vector
LIMIT 10;
```

#### 2. users

User profiles with demographics for personalization.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `user_id` | UUID | Primary key |
| `user_name` | VARCHAR | Full name |
| `email_id` | VARCHAR UNIQUE | Email address |
| `age` | INTEGER | CHECK (18-120) |
| `base_location` | VARCHAR | City, State |
| `base_zip` | VARCHAR(10) | ZIP code |
| `gender` | VARCHAR | Male/Female/Other |
| `credit_score` | INTEGER | CHECK (300-850) |
| `avg_monthly_expenses` | DECIMAL(10,2) | Average spending |
| `last_active` | TIMESTAMP | Last activity timestamp |
| `embeddings` | vector(1536) | User profile representation |
| `created_at` | TIMESTAMP | Account creation |
| `updated_at` | TIMESTAMP | Last profile update |

**Indexes**:
- B-tree: `email_id`, `age`, `credit_score`, `last_active`
- IVFFlat: `embeddings`

**Example Query**:
```sql
-- Find similar users by demographics
SELECT user_id, user_name, age, base_location,
       1 - (embeddings <=> $1::vector) AS similarity
FROM users
WHERE age BETWEEN 25 AND 35
  AND credit_score > 700
ORDER BY embeddings <=> $1::vector
LIMIT 20;
```

#### 3. transactions

Purchase and delivery tracking with auto-computed fields.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `transaction_id` | UUID | Primary key |
| `item_id` | UUID | FK to products |
| `user_id` | UUID | FK to users |
| `order_date` | TIMESTAMP | When ordered |
| `delivery_date` | TIMESTAMP | When delivered (nullable) |
| `expected_delivery_date` | TIMESTAMP | Expected delivery |
| `return_date` | TIMESTAMP | Return date (nullable) |
| `original_price` | DECIMAL(10,2) | Original price |
| `retail_price` | DECIMAL(10,2) | Retail price (discounted) |
| `discount_percentage` | DECIMAL(5,2) | Auto-computed |
| `transaction_status` | VARCHAR | pending/delivered/returned/in_transit |
| `created_at` | TIMESTAMP | Transaction creation |
| `updated_at` | TIMESTAMP | Last update |

**Constraints**:
- `delivery_date >= order_date`
- `return_date >= delivery_date`
- `retail_price <= original_price`

**Auto-Computed**:
```sql
discount_percentage = ((original_price - retail_price) / original_price) * 100
```

**Indexes**:
- B-tree: `item_id`, `user_id`, `order_date`, `transaction_status`

**Example Query**:
```sql
-- User purchase history with reviews
SELECT t.transaction_id, p.title, t.order_date, t.retail_price,
       r.review_stars, r.review_text
FROM transactions t
JOIN products p ON t.item_id = p.item_id
LEFT JOIN reviews r ON t.transaction_id = r.transaction_id
WHERE t.user_id = $1
ORDER BY t.order_date DESC;
```

#### 4. reviews

User-generated reviews with AI sentiment analysis.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `review_id` | UUID | Primary key |
| `item_id` | UUID | FK to products |
| `user_id` | UUID | FK to users |
| `transaction_id` | UUID | FK to transactions (UNIQUE) |
| `timestamp` | TIMESTAMP | Review creation time |
| `review_title` | VARCHAR | Review headline |
| `review_text` | TEXT | Full review content |
| `review_stars` | INTEGER | CHECK (1-5) |
| `sentiment_score` | FLOAT | CHECK (-1.0 to 1.0) |
| `toxicity_score` | FLOAT | CHECK (0.0 to 1.0) |
| `manual_or_agent_generated` | VARCHAR | "manual" or "agent_generated" |
| `embeddings` | vector(1536) | Review semantic representation |
| `created_at` | TIMESTAMP | Review created |
| `updated_at` | TIMESTAMP | Review updated |

**Constraints**:
- One review per transaction (UNIQUE on `transaction_id`)
- Review must be for same user as transaction

**Triggers**:
- Auto-updates `products.review_count` on insert/delete

**Indexes**:
- B-tree: `item_id`, `user_id`, `transaction_id`, `review_stars`, `timestamp`
- IVFFlat: `embeddings`

**Example Query**:
```sql
-- Product average rating with sentiment
SELECT p.item_id, p.title,
       AVG(r.review_stars) AS avg_rating,
       AVG(r.sentiment_score) AS avg_sentiment,
       COUNT(r.review_id) AS review_count
FROM products p
LEFT JOIN reviews r ON p.item_id = r.item_id
GROUP BY p.item_id, p.title
HAVING COUNT(r.review_id) > 0;
```

#### 5. survey (Core Agentic System)

Dynamically generated survey questions with agent metadata and explainability.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `scenario_id` | UUID | Composite PK (with question_id) |
| `question_id` | UUID | Composite PK (with scenario_id) |
| `item_id` | UUID | FK to products (nullable) |
| `user_id` | UUID | FK to users |
| `transaction_id` | UUID | FK to transactions (nullable) |
| `survey_id` | UUID | Survey session identifier |
| `question_number` | INTEGER | Sequential question number |
| `question` | TEXT | Question text |
| `question_type` | TEXT | rating/multiple_choice/yes_no/open_ended |
| `options_object` | JSONB | Flexible question options |
| `selected_option` | TEXT | User's selected answer |
| `user_response` | JSONB | Answer with metadata |
| `agent_reasoning` | TEXT | Explainability for question |
| `agent_confidence_score` | FLOAT | CHECK (0.0-1.0) Quality metric |
| `follow_up_trigger` | BOOLEAN | Enable conversational flow |
| `correctly_anticipates_user_sentiment` | BOOLEAN | Model improvement flag |
| `created_at` | TIMESTAMP | Question generated |
| `updated_at` | TIMESTAMP | Answer updated |

**Indexes**:
- B-tree: `scenario_id`, `survey_id`, `user_id`, `item_id`, `question_number`
- GIN: `options_object`, `user_response`

**Example Query**:
```sql
-- Survey questions with high confidence
SELECT question_id, question, question_type,
       agent_confidence_score, agent_reasoning
FROM survey
WHERE survey_id = $1
  AND agent_confidence_score > 0.8
ORDER BY question_number;
```

#### 6. survey_sessions

Session tracking and analytics for complete survey flows.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `session_id` | UUID | Primary key |
| `scenario_id` | UUID | FK to survey |
| `user_id` | UUID | FK to users |
| `total_questions` | INTEGER | Total questions in survey |
| `answered_questions` | INTEGER | Questions answered so far |
| `is_completed` | BOOLEAN | Survey completion status |
| `session_context` | JSONB | Conversation state/memory |
| `started_at` | TIMESTAMP | Session start |
| `completed_at` | TIMESTAMP | Session completion (nullable) |
| `agent_metrics` | JSONB | Performance data |
| `created_at` | TIMESTAMP | Session created |
| `updated_at` | TIMESTAMP | Last activity |

**Indexes**:
- B-tree: `scenario_id`, `user_id`, `is_completed`, `started_at`
- GIN: `session_context`, `agent_metrics`

**Example Query**:
```sql
-- Active sessions with progress
SELECT session_id, user_id,
       answered_questions::FLOAT / total_questions * 100 AS progress_pct,
       started_at
FROM survey_sessions
WHERE is_completed = FALSE
  AND started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;
```

### Database Features

**Auto-Timestamps**:
- All tables maintain `created_at` (set on insert) and `updated_at` (auto-updated on modification)

**Triggers**:
1. `update_updated_at`: Auto-updates `updated_at` on all tables
2. `update_review_count`: Auto-maintains `products.review_count`

**Constraints**:
- Foreign keys with CASCADE deletes for referential integrity
- CHECK constraints for data validation (ages, scores, dates, ratings)
- UNIQUE constraints to prevent duplicates

**Row Level Security (RLS)**:
- Enabled on all tables
- Users can only view/modify their own data
- Public read access for product catalog

### Vector Embeddings

**Dimension**: 1536 (OpenAI `text-embedding-ada-002` compatible)

**Generation** (Current - Mock):
```typescript
function generateMockEmbedding(text: string): number[] {
  const seed = text.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const random = (n: number) => {
    const x = Math.sin(seed + n) * 10000
    return (x - Math.floor(x)) * 2 - 1  // Normalize to [-1, 1]
  }
  return Array.from({ length: 1536 }, (_, i) => random(i))
}
```

**Generation** (Production - OpenAI):
```python
import openai

def generate_embedding(text: str) -> list[float]:
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']
```

**Similarity Search**:
```sql
-- Cosine similarity (pgvector operator: <=>)
SELECT *, 1 - (embeddings <=> $1::vector) AS similarity
FROM products
ORDER BY embeddings <=> $1::vector
LIMIT 10;
```

---

## Amazon Product Integration

### Supported URL Formats

The scraper automatically extracts the ASIN (Amazon Standard Identification Number) from any Amazon URL format.

**Standard Formats**:
```
https://www.amazon.com/dp/B0DCJ5NMV2
https://www.amazon.com/gp/product/B0DCJ5NMV2
https://www.amazon.com/ASIN/B0DCJ5NMV2
```

**With Product Titles**:
```
https://www.amazon.com/Apple-iPhone-15-Pro-Titanium/dp/B0DCJ5NMV2
https://www.amazon.com/Sony-Headphones/dp/B09XS7JWHH?th=1&psc=1
```

**With Tracking Parameters**:
```
https://www.amazon.com/dp/B0DCJ5NMV2/ref=nav_signin
https://www.amazon.com/dp/B0DCJ5NMV2?ref=ppx_yo_dt_b_product_details
```

**Shortened Links**:
```
https://amzn.to/B0DCJ5NMV2
```

**International Domains**:
```
https://www.amazon.co.uk/dp/B0DCJ5NMV2
https://www.amazon.ca/dp/B0DCJ5NMV2
https://www.amazon.de/dp/B0DCJ5NMV2
```

### ASIN Extraction

**What is an ASIN?**
- Amazon Standard Identification Number
- Always exactly 10 alphanumeric characters
- Unique to each product on Amazon
- Example: `B0DCJ5NMV2`

**Regex Patterns**:
```typescript
const asinPatterns = [
  /\/dp\/([A-Z0-9]{10})/i,              // Standard /dp/ format
  /\/gp\/product\/([A-Z0-9]{10})/i,     // Alternative /gp/product/
  /\/([A-Z0-9]{10})\/ref=/i,            // ASIN before /ref=
  /[?&]asin=([A-Z0-9]{10})/i,           // Query parameter
  /amzn\.to\/([A-Z0-9]{10})/i,          // Shortened links
]
```

### RapidAPI Integration

**API Provider**: Real-Time Amazon Data by Letscrape

**Free Tier**:
- 100 requests/month
- No credit card required
- No expiration

**Setup**:
1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to [Real-Time Amazon Data API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data)
3. Copy API key from dashboard
4. Add to `.env.local`: `RAPIDAPI_KEY=your_api_key`

**Endpoints Used**:

1. **Product Details** (`GET /product-details`):
```typescript
const response = await fetch(
  `https://real-time-amazon-data.p.rapidapi.com/product-details?asin=${asin}&country=US`,
  {
    headers: {
      'X-RapidAPI-Key': RAPIDAPI_KEY,
      'X-RapidAPI-Host': 'real-time-amazon-data.p.rapidapi.com'
    }
  }
)
```

2. **Product Reviews** (`GET /product-reviews`):
```typescript
const response = await fetch(
  `https://real-time-amazon-data.p.rapidapi.com/product-reviews?asin=${asin}&country=US&sort_by=TOP_REVIEWS`,
  {
    headers: {
      'X-RapidAPI-Key': RAPIDAPI_KEY,
      'X-RapidAPI-Host': 'real-time-amazon-data.p.rapidapi.com'
    }
  }
)
```

**Conditional Review Fetching**:
- Reviews only fetched when user confirms product has reviews (Field 2 = "Yes")
- Saves 50% API calls when products have no reviews
- Each product scrape uses 1-2 API calls (details + reviews if needed)

**API Optimization**:
```
Without optimization: 100 requests/month = ~50 products
With optimization: 100 requests/month = ~50-100 products (depending on review ratio)
```

**Fallback Strategy**:
1. Try RapidAPI first (if configured)
2. Fall back to direct scraping (may be blocked)
3. Return mock data if both fail

### Alternative APIs

**ScraperAPI** (documented but not used):
- **Free Tier**: 5,000 requests/month
- **Pros**: Works with existing scraping code, handles anti-bot
- **Cons**: Adds 1-2s latency, rate limited
- **Use Case**: Backup option if RapidAPI fails

**Comparison**:
| Solution | Cost | Free Tier | Reliability | Setup Time |
|----------|------|-----------|-------------|------------|
| RapidAPI | Free/$10/mo | 100/mo | 95% | 5 min |
| ScraperAPI | Free/$49/mo | 5,000/mo | 95% | 5 min |
| Direct Scraping | Free | Unlimited | 30% | 0 min |

---

## Phase Completion Status

### ✅ Phase 0: Database (Complete)

**Delivered**:
- 6 tables with vector embeddings (1536-dim)
- Row Level Security policies (8 policies)
- Optimized indexes (20+ indexes: B-tree, GIN, IVFFlat)
- Auto-updating triggers (7 triggers)
- Sample data (3 products, 3 users, 3 transactions, 2 reviews)

**Files**:
- `database/migrations/001_initial_schema.sql` (complete migration)
- `database/seed/001_sample_data.sql` (sample data)
- `database/README.md` (setup guide)

**Metrics**:
- Total Indexes: 20+
- Total Triggers: 7
- Total Constraints: 15+
- RLS Policies: 8

### ✅ Phase 1 Part 1: Frontend Intake (Complete)

**Delivered**:
- 7-field progressive form with conditional logic
- Amazon product scraping via RapidAPI
- Conditional review fetching (API optimization)
- MOCK_DATA_AGENT for synthetic data generation
- Complete database integration (4 tables: products, users, transactions, reviews)
- Cold start scenario detection

**Components**:
- `ProductUrlField.tsx`: URL input + RapidAPI scraper
- `ReviewStatusField.tsx`: Yes/No with conditional review fetch
- `SentimentSpreadField.tsx`: Good/Neutral/Bad % sliders
- `SimilarProductsField.tsx`: Similar products reviewed?
- `UserPersonaField.tsx`: Auto-generated user personas
- `UserPurchaseHistoryField.tsx`: Purchase history?
- `UserExactProductField.tsx`: Bought this product?
- `SubmissionSummary.tsx`: Post-submit summary view

**API Endpoints**:
- `POST /api/scrape`: Amazon product scraper with conditional reviews
- `POST /api/mock-data`: MOCK_DATA_AGENT (generates synthetic data)

**Features**:
- ✅ RapidAPI integration with ASIN extraction
- ✅ Conditional review fetching
- ✅ Fallback to direct scraping
- ✅ Mock data on scraping failure
- ✅ Context-aware data generation
- ✅ Cold start detection
- ✅ Responsive design
- ✅ Type-safe (TypeScript + Zod)
- ✅ Database integration (batch operations)

**Performance**:
- Amazon scrape: 1-3s (with reviews: 2-5s)
- Mock data generation: 1-3s
- Database insertion: 0.5-2s
- Total submission: ~5-10s

### ✅ Phase 1 Part 2: Survey UI (Complete)

**Delivered**:
- Multi-pane retractable interface (4 UI states)
- Survey Sensei branding with gradient logo
- Simulation summary with compact stats
- Survey UI with 65/35 question/answer split
- Phase 2 integration placeholders
- Smooth animations and transitions (0.5s)

**UI States**:
1. **Form Filling**: Survey Sensei pane 100% width
2. **Submission Summary**: Survey Sensei 10% + Summary 90%
3. **Survey Pane Expanded**: Survey Sensei 90% + Summary 10%
4. **Survey UI**: Survey Sensei 10% + Stats 10% + Survey UI 80%

**Features**:
- ✅ Click-to-expand pane interactions
- ✅ Vertical text for minimized panes
- ✅ Compact stats view (products, users, transactions, reviews)
- ✅ Survey question placeholder (Phase 2 integration)
- ✅ Answer stack placeholder (65%/35% split)
- ✅ "Generate Product Review" button
- ✅ Smooth transitions (`transition-all duration-500`)

### 🔄 Phase 2: Agentic Backend (Planned)

**Goals**:
- FastAPI backend with LangChain/LangGraph
- OpenAI integration for embeddings and question generation
- Context analysis agent
- Question generation agent
- Sentiment analysis
- Embedding generation pipeline
- WebSocket support for real-time surveys

**Agent Architecture**:
```
Orchestrator Agent
  ├─ Context Agent: Fetch user/product/transaction data from Supabase
  ├─ Analysis Agent: Sentiment analysis + vector similarity search
  ├─ Question Agent: Generate contextual survey questions
  ├─ Validator Agent: Quality control + explainability
  └─ Response Agent: Process user answers + update context
```

**LangGraph State Machine**:
```
START → Fetch Context → Analyze Context → Generate Questions
     → Present to User → Await Response → Process Answer
     → Need Follow-up? (Yes: loop back | No: Generate Final Review) → END
```

**Tech Stack**:
- Python 3.11+
- FastAPI (async endpoints)
- LangChain (agent orchestration)
- LangGraph (state machine)
- OpenAI API (embeddings + completion)
- Anthropic Claude (alternative LLM)
- Supabase Python client
- Pydantic (validation)

### 🔄 Phase 3: API Integration (Planned)

**REST Endpoints**:
- Authentication: `POST /api/auth/login`, `POST /api/auth/signup`
- Products: `GET /api/products`, `GET /api/products/:id`
- Users: `GET /api/users/me`, `PUT /api/users/me`
- Transactions: `GET /api/transactions`
- Surveys: `POST /api/surveys/start`, `POST /api/surveys/:id/answer`, `POST /api/surveys/:id/complete`
- Reviews: `GET /api/reviews`, `POST /api/reviews`

**WebSocket**:
- `WS /ws/survey/:session_id`: Real-time survey question streaming

**Security**:
- JWT authentication (Supabase Auth)
- Rate limiting (Redis-based)
- Input validation (Pydantic schemas)
- CORS configuration
- SQL injection prevention
- XSS protection

**Documentation**:
- OpenAPI/Swagger specification
- Interactive API docs (FastAPI auto-generated)
- Code examples (Python, JavaScript)
- Authentication guide

### 🔄 Phase 4: Deployment (Planned)

**Infrastructure**:
- **Frontend**: Vercel (auto-scaling, edge network, CDN)
- **Backend**: Railway/Render (auto-scaling, health checks)
- **Database**: Supabase Cloud (connection pooling, backups)
- **Caching**: Redis (response caching, session storage)
- **Monitoring**: Sentry (error tracking), Supabase Analytics

**CI/CD**:
- GitHub Actions workflows
- Automated testing (unit, integration, E2E)
- Linting checks (ESLint, Black)
- Build verification
- Automated deployments (preview + production)

**Monitoring**:
- Error tracking (Sentry)
- API usage analytics
- Database performance monitoring
- Uptime monitoring (99.9% SLA)
- User analytics (PostHog/Mixpanel)

**Testing**:
- Unit tests (>80% coverage)
- Integration tests (API endpoints)
- E2E tests (Playwright/Cypress)
- Load testing (k6)
- Security audit

---

## Development Workflow

### Local Development

**Prerequisites**:
- Node.js 18+
- Python 3.11+ (for Phase 2)
- Supabase account
- RapidAPI key (optional but recommended)

**Frontend Setup**:
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with Supabase + RapidAPI credentials
npm run dev  # http://localhost:3000
```

**Backend Setup** (Phase 2):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Supabase + OpenAI credentials
uvicorn main:app --reload  # http://localhost:8000
```

**Database Setup**:
1. Create Supabase project at [supabase.com](https://supabase.com)
2. Open SQL Editor
3. Execute `database/migrations/001_initial_schema.sql`
4. (Optional) Execute `database/seed/001_sample_data.sql`
5. Verify tables in Table Editor

**Environment Variables**:

Frontend (`.env.local`):
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
NEXT_PUBLIC_APP_URL=http://localhost:3000
RAPIDAPI_KEY=xxx  # Optional
```

Backend (`.env` - Phase 2):
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
OPENAI_API_KEY=xxx
```

---

## Production Deployment

### Phase 4: Scaling Strategy

**MVP (< 10k users)**:
- Single Supabase instance
- Vercel serverless functions
- No caching layer needed
- **Cost**: ~$0-50/month

**Growth (10k-100k users)**:
- Supabase read replicas
- Redis caching layer (response + session caching)
- Background job queue (Celery + Redis)
- CDN for static assets
- **Cost**: ~$100-500/month

**Scale (100k-1M users)**:
- Database sharding by region
- Microservices architecture (split backend into services)
- Dedicated LLM inference server
- Auto-scaling backend instances
- **Cost**: ~$500-2,000/month

**Enterprise (1M+ users)**:
- Multi-region deployment
- Custom vector database (Pinecone/Weaviate)
- Event-driven architecture (Apache Kafka)
- Edge computing (Cloudflare Workers)
- **Cost**: Custom pricing

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| API response time | < 200ms (p95) | Excluding LLM calls |
| Survey generation | < 2s (cold), < 500ms (warm) | With caching |
| Database queries | < 50ms | With proper indexing |
| Uptime | 99.9% SLA | ~8.7 hours downtime/year |
| Concurrent users | 10k+ | Auto-scaling enabled |

### Cost Optimization

**Embedding Caching**:
- Cache embeddings for frequently accessed products/users
- Reduces OpenAI API calls by 80-90%
- Redis TTL: 24 hours

**Batch Processing**:
- Batch embedding generation (100 items at once)
- Background jobs for non-urgent tasks
- Reduces API overhead

**Supabase Connection Pooling**:
- PgBouncer for connection pooling
- Max connections: 100-500 (based on tier)
- Prevents connection exhaustion

**Serverless Auto-Scaling**:
- Vercel: Pay-per-request (no idle costs)
- Railway: Pay for actual usage
- Scales to zero during low traffic

### Deployment Checklist

**Frontend (Vercel)**:
- [ ] Deploy to Vercel
- [ ] Configure custom domain
- [ ] Set environment variables
- [ ] Enable preview deployments
- [ ] Configure CDN settings

**Backend (Railway/Render)**:
- [ ] Deploy to Railway
- [ ] Configure environment variables
- [ ] Set up auto-scaling rules
- [ ] Configure health checks
- [ ] Set up logging (CloudWatch/Papertrail)

**Database (Supabase)**:
- [ ] Verify production project
- [ ] Run migrations
- [ ] Configure backups (daily automated)
- [ ] Set up monitoring
- [ ] Optimize performance (indexes, connection pooling)

**CI/CD (GitHub Actions)**:
- [ ] Create workflow files
- [ ] Configure automated testing
- [ ] Set up linting checks
- [ ] Enable build verification
- [ ] Configure automated deployments

**Monitoring**:
- [ ] Set up Sentry for error tracking
- [ ] Configure Supabase analytics
- [ ] Set up uptime monitoring (UptimeRobot)
- [ ] Create performance dashboard
- [ ] Enable user analytics

---

**Documentation Version**: 2.0
**Last Updated**: 2025-11-12
**Overall Progress**: Phase 1 Complete (40%), Phase 2 Planning
