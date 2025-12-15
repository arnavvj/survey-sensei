# Survey Sensei Backend

AI-powered survey generation and review creation using LangChain agents and FastAPI.

## Overview

The backend orchestrates three specialized LangChain agents to create personalized surveys and generate authentic product reviews based on user context.

### Three-Agent Architecture

**1. ProductContextAgent** (Stateless)
- Analyzes product reviews, descriptions, and ratings
- Extracts key features, concerns, pros/cons
- Handles cold start with similar product analysis
- Uses vector similarity search (pgvector)

**2. CustomerContextAgent** (Stateless)
- Analyzes user purchase history and review patterns
- Identifies customer concerns and expectations
- Segments users by engagement metrics
- Leverages similar product purchases via embeddings

**3. SurveyAgent** (Stateful LangGraph)
- Orchestrates ProductContext and CustomerContext agents
- Generates adaptive survey questions (3-7 questions)
- Manages conversation state and flow
- Routes to ReviewGenAgent upon completion

**4. ReviewGenAgent** (Stateless)
- Synthesizes survey responses into review options
- Generates 3 review alternatives with different tones
- Creates review titles, text, star ratings
- Classifies sentiment (good/okay/bad)

## Quick Setup

### 1. Install Dependencies

**Using Conda (Required)**

```bash
cd backend

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate survey-sensei
```

**Why Conda?**
- Isolated Python 3.11 environment
- Better dependency management for LangChain and ML packages
- Reproducible across platforms
- Single source of truth for all dependencies

### 2. Configure Environment

Create `.env.local` file:

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key

# OpenAI
OPENAI_API_KEY=sk-proj-your-openai-key

# Application
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### 3. Start Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --port 8000
```

Server starts at `http://localhost:8000`

### 4. Verify Installation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

Test health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

## API Endpoints

### POST /api/survey/start

Start a new survey session.

**Request:**
```json
{
  "user_id": "uuid",
  "item_id": "ASIN",
  "transaction_id": "uuid"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "question": {
    "question_text": "How would you describe your experience with this product?",
    "options": ["Excellent", "Good", "Average", "Poor"],
    "question_type": "multiple_choice"
  },
  "question_number": 1,
  "total_questions_so_far": 1
}
```

**What Happens:**
1. Creates survey session in database
2. Invokes ProductContextAgent (analyzes product)
3. Invokes CustomerContextAgent (analyzes user)
4. SurveyAgent generates first question
5. Returns question to user

### POST /api/survey/answer

Submit answer and get next question.

**Request:**
```json
{
  "session_id": "uuid",
  "answer": "Excellent"
}
```

**Response (continued):**
```json
{
  "session_id": "uuid",
  "status": "continue",
  "question": {
    "question_text": "What specific features stood out to you?",
    "options": ["Battery life", "Sound quality", "Build quality", "Price"],
    "question_type": "multiple_choice"
  },
  "question_number": 2,
  "total_questions_so_far": 2
}
```

**Response (completed):**
```json
{
  "session_id": "uuid",
  "status": "completed",
  "message": "Survey completed! Proceeding to review generation.",
  "total_questions": 5
}
```

**What Happens:**
1. Stores answer in survey state
2. SurveyAgent decides: continue or complete
3. If continue: generates next question
4. If complete: saves Q&A to database

### POST /api/survey/generate-reviews

Generate review options from survey responses.

**Request:**
```json
{
  "session_id": "uuid"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "status": "reviews_generated",
  "reviews": [
    {
      "review_title": "Outstanding Sound Quality and Comfort",
      "review_text": "I've been using these headphones for a month...",
      "review_stars": 5,
      "tone": "enthusiastic",
      "highlights": ["sound quality", "comfort", "battery life"],
      "sentiment_band": "good"
    },
    {
      "review_title": "Good Headphones with Minor Issues",
      "review_text": "Overall satisfied but the noise cancellation could be better...",
      "review_stars": 4,
      "tone": "balanced",
      "highlights": ["value", "comfort"],
      "sentiment_band": "okay"
    },
    {
      "review_title": "Decent but Overpriced",
      "review_text": "Expected more for the price point...",
      "review_stars": 3,
      "tone": "critical",
      "highlights": ["price", "features"],
      "sentiment_band": "okay"
    }
  ],
  "sentiment_band": "good"
}
```

**What Happens:**
1. Retrieves survey state from database
2. ReviewGenAgent synthesizes responses
3. Generates 3 review options
4. Stores review_options in survey_sessions table
5. Returns reviews to user

### POST /api/survey/submit-review

Save selected review to database.

**Request:**
```json
{
  "session_id": "uuid",
  "selected_review_index": 0
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "status": "review_saved",
  "review_id": "uuid",
  "message": "Review saved successfully!"
}
```

**What Happens:**
1. Retrieves selected review from review_options
2. Inserts into reviews table with source='user_survey'
3. Marks survey session as complete

## Agent Details

### ProductContextAgent

**Autonomous operation** - queries database directly without form_data dependency.

**Three-Path Decision Logic:**

```
1. Check product.review_count from database
   ↓
2. Path Selection:

   Path 1: Product has reviews (review_count > 0)
   → Use: Main product reviews + product description
   → Confidence: 0.70-0.95

   Path 2: No reviews BUT similar products have reviews
   → Use: Similar product reviews + product description
   → Vector similarity search (threshold: 0.7)
   → Confidence: 0.55-0.80

   Path 3: No reviews anywhere
   → Use: Product description/stats only
   → Confidence: 0.40-0.50
```

**Output Schema:**
```python
class ProductContext(BaseModel):
    key_features: List[str]        # Top product features
    major_concerns: List[str]      # Customer concerns
    pros: List[str]                # Product advantages
    cons: List[str]                # Product disadvantages
    common_use_cases: List[str]    # Typical usage scenarios
    context_type: str              # "direct_reviews" | "similar_products" | "description_only"
    confidence_score: float        # 0.0-1.0
```

**Review Ranking (Path 1):**
- Recency: 50% (exponential decay, 180-day half-life)
- Quality: 40% (text length)
- Diversity: 10% (star rating mix)

**Review Ranking (Path 2):**
- Similarity: 40% (vector similarity score)
- Recency: 35% (exponential decay)
- Quality: 20% (text length)
- Diversity: 5% (star rating mix)

### CustomerContextAgent

**Autonomous operation** - queries database directly for user_id and item_id.

**Three-Path Decision Logic:**

```
1. Check user's transaction history for THIS product
   ↓
2. Path Selection:

   Path 1: Exact Interaction
   → User purchased/reviewed THIS product
   → Confidence: 0.85-0.95

   Path 2: Similar Products
   → User has similar product purchases (vector search)
   → Smart ranking: Similarity (45%), Recency (30%), Engagement (25%)
   → Confidence: 0.55-0.80

   Path 3: Demographics Only
   → No purchase history
   → Confidence: 0.35-0.45
```

**Output Schema:**
```python
class CustomerContext(BaseModel):
    purchase_patterns: List[str]        # Observable behaviors
    review_behavior: List[str]          # Review patterns
    product_preferences: List[str]      # Category preferences
    primary_concerns: List[str]         # Top 3-5 concerns
    expectations: List[str]             # What user expects
    pain_points: List[str]              # Recurring frustrations
    engagement_level: str               # highly_engaged | moderately_engaged | passive_buyer | new_user
    sentiment_tendency: str             # positive | critical | balanced | polarized | neutral
    review_engagement_rate: float       # 0.0-1.0
    context_type: str                   # "exact_interaction" | "similar_products" | "demographics_only"
    confidence_score: float             # 0.0-1.0
    data_points_used: int               # Number of transactions analyzed
```

### SurveyAgent

**Stateful LangGraph agent** - manages multi-turn conversation.

**Workflow:**
```
1. Invoke ProductContextAgent + CustomerContextAgent (parallel)
2. Generate initial question based on contexts
3. Present question → Await user response
4. Process answer → Update state
5. Decide: Continue (generate next question) or Complete
6. Repeat until 3-7 questions total
7. Mark survey as complete
```

**State Management:**
- In-memory cache during survey
- Saved to database on completion
- Retrieved from database for review generation

### ReviewGenAgent

**Autonomous generation** - creates review options from survey responses.

**Input:**
- Survey responses (Q&A pairs)
- Product context
- Customer context
- User's existing reviews (for writing style)
- Product title

**Output:**
```python
class ReviewOptions(BaseModel):
    reviews: List[ReviewOption]    # 3 review options
    sentiment_band: str            # "good" | "okay" | "bad"

class ReviewOption(BaseModel):
    review_title: str              # 5-10 word title
    review_text: str               # 50-150 word review
    review_stars: int              # 1-5
    tone: str                      # enthusiastic | balanced | critical
    highlights: List[str]          # Key points emphasized
```

**Review Generation Strategy:**
1. Analyzes survey sentiment
2. Creates 3 variations (enthusiastic, balanced, critical)
3. Ensures authenticity (mimics user's writing style)
4. Incorporates specific details from survey
5. Assigns appropriate star ratings

## Project Structure

```
backend/
├── agents/
│   ├── product_context_agent.py      # Agent 1: Product analysis
│   ├── customer_context_agent.py     # Agent 2: Customer analysis
│   ├── survey_agent.py               # Agent 3: Survey orchestration
│   └── review_gen_agent.py           # Agent 4: Review generation
├── database/
│   ├── supabase_client.py            # Database operations
│   ├── migrations/                   # SQL migration files
│   │   ├── 001_enable_extensions.sql
│   │   ├── 002_create_products_table.sql
│   │   ├── 003_create_users_table.sql
│   │   ├── 004_create_transactions_table.sql
│   │   ├── 005_create_reviews_table.sql
│   │   ├── 006_create_survey_sessions_table.sql
│   │   ├── 007_create_survey_details_table.sql
│   │   ├── 008_create_triggers.sql
│   │   └── 009_enable_row_level_security.sql
│   └── _combined_migrations.sql      # Generated master reset script
├── integrations/
│   └── rapidapi_client.py            # Amazon product scraper
├── utils/
│   └── embeddings.py                 # OpenAI embedding generation
├── config.py                         # Configuration
├── main.py                           # FastAPI application
├── environment.yml                   # Conda dependencies
└── README.md                         # This file
```

## Configuration

Edit `config.py` to adjust settings:

```python
# OpenAI Settings
OPENAI_MODEL = "gpt-4o-mini"     # Cost-effective model
TEMPERATURE = 0.7                 # Creativity balance

# Survey Settings
MIN_QUESTIONS = 3
MAX_QUESTIONS = 7
REVIEW_OPTIONS = 3

# Vector Search
SIMILARITY_THRESHOLD = 0.7        # Cosine similarity threshold
```

## Testing

### Run All Tests

**Windows:**
```bash
run_tests.bat
```

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Run Specific Tests

```bash
# Product Context Agent (48 tests)
pytest tests/test_product_context_agent.py

# Customer Context Agent (20+ tests)
pytest tests/test_customer_context_agent.py

# API Endpoints (15+ tests)
pytest tests/test_api_endpoints.py

# Verbose output
pytest -vv

# With coverage
pytest --cov=agents --cov-report=html
```

### Test Coverage

| Test Suite | Tests | Time | Coverage |
|------------|-------|------|----------|
| ProductContextAgent | 48 | ~5s | 95%+ |
| CustomerContextAgent | 20+ | ~3s | 90%+ |
| SurveyAgent | 15+ | ~4s | 85%+ |
| API Endpoints | 15+ | ~10s | 85%+ |

### Integration Tests

Run with real OpenAI API calls:

```bash
# Windows
run_tests.bat --integration

# Linux/Mac
./run_tests.sh --integration
```

**Note**: Requires valid `OPENAI_API_KEY` in `.env.local`

## Development Commands

```bash
# Start server
python main.py

# Run tests
pytest

# Run specific test
pytest tests/test_product_context_agent.py::test_path1_direct_reviews

# Generate coverage report
pytest --cov=agents --cov-report=html

# View coverage
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

## Conda Environment Management

```bash
# Create environment
conda env create -f environment.yml

# Activate environment
conda activate survey-sensei

# Update environment after changes
conda env update -f environment.yml --prune

# List all packages
conda list

# Export environment
conda env export > environment-backup.yml

# Remove environment
conda deactivate
conda env remove -n survey-sensei
```

### Adding Dependencies

**Conda packages:**
```bash
conda install -c conda-forge package-name
# Add to environment.yml under dependencies
```

**Pip packages:**
```bash
pip install package-name
# Add to environment.yml under pip: section
```

## Troubleshooting

### ImportError: No module named 'langchain'

```bash
conda activate survey-sensei
pip install -r requirements.txt
```

### Supabase Connection Failed

- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env.local`
- Ensure service role key (not anon key) is used
- Check Supabase project is not paused

### OpenAI API Errors

- Verify `OPENAI_API_KEY` starts with `sk-proj-`
- Check billing at [OpenAI dashboard](https://platform.openai.com/usage)
- Ensure sufficient credits available

### Vector Search Not Working

- Verify pgvector extension enabled in Supabase
- Check product embeddings exist in database:
  ```sql
  SELECT COUNT(*) FROM products WHERE embeddings IS NOT NULL;
  ```

### Tests Failing

**Import errors:**
```bash
pip install -e .
```

**Integration test failures:**
- Check `OPENAI_API_KEY` in `.env.local`
- Verify API key is valid
- Ensure sufficient credits

## Cost Estimation

Using GPT-4o-mini:

| Operation | Cost per Request | Notes |
|-----------|-----------------|-------|
| Survey generation | ~$0.001 | ProductContext + CustomerContext + SurveyAgent |
| Review generation | ~$0.0005 | ReviewGenAgent |
| **Total per survey** | **~$0.0015** | Complete flow |
| 100 surveys/month | ~$0.15 | Very cost-effective |
| 1,000 surveys/month | ~$1.50 | Production scale |

Monitor usage at [platform.openai.com/usage](https://platform.openai.com/usage)

## Resources

- [LangChain Docs](https://python.langchain.com/docs/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pytest Docs](https://docs.pytest.org/)
- [Conda Docs](https://docs.conda.io/)

---

**Backend Version**: 1.0.0
**Python Version**: 3.11+
**Status**: Production Ready
