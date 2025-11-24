# Survey Sensei Backend - Complete Setup Guide

## Phase 2: AI-Powered Survey Generation Backend

This guide will help you set up and run the backend agentic framework.

---

## Prerequisites

✅ **Completed Phase 1**: Frontend form and mock data generation
✅ **Python 3.11+** installed
✅ **OpenAI API Key** (you mentioned you created one)
✅ **Supabase Project** with Phase 1 database schema
✅ **Git** for version control

---

## Quick Start (5 Minutes)

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Environment File

```bash
# Copy the example
cp .env.example .env

# Edit .env with your credentials
# Windows: notepad .env
# Mac/Linux: nano .env
```

Add your credentials to `.env`:

```env
# Supabase (from your frontend/.env.local)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# OpenAI (the key you just created)
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Application
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### Step 3: Install Dependencies

**Option A: Using the start script (recommended)**

Windows:
```bash
start.bat
```

Mac/Linux:
```bash
chmod +x start.sh
./start.sh
```

**Option B: Manual installation**

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py
```

### Step 4: Set Up Database Function

1. Go to your Supabase project dashboard
2. Click "SQL Editor" in the sidebar
3. Click "New Query"
4. Copy the contents of `database/functions/match_products.sql`
5. Paste and click "Run"

This creates the vector similarity search function.

### Step 5: Verify Backend is Running

Open your browser and visit:
- http://localhost:8000 (health check)
- http://localhost:8000/docs (interactive API documentation)

You should see:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development"
}
```

---

## Understanding the Three-Agent System

### 🤖 Agent 1: PRODUCT_CONTEXT_AGENT

**Purpose**: Analyze product to extract insights

**File**: `agents/product_context_agent.py`

**Workflow**:
```
Has product been reviewed?
├─ Yes → Extract from product's reviews
│        - Major concerns from reviewers
│        - Highlighted features
│        - Pros and cons
│        - Common use cases
│
└─ No  → Similar products reviewed?
         ├─ Yes → Use similar products' reviews
         │        - Find top 5 similar products (embedding search)
         │        - Aggregate their review insights
         │
         └─ No  → Use product description only
                  - Infer likely concerns
                  - Generate plausible pros/cons
```

**Output**: ProductContext with confidence score

### 🤖 Agent 2: CUSTOMER_CONTEXT_AGENT

**Purpose**: Analyze user to understand expectations

**File**: `agents/customer_context_agent.py`

**Workflow**:
```
Has user purchased similar products?
├─ Yes → Has user reviewed them?
│        ├─ Yes → Extract from user's review history
│        │        - User's concerns/expectations
│        │        - Purchase motivations
│        │        - Pain points
│        │
│        └─ No  → Derive from purchase history
│                 - What they bought
│                 - Price sensitivity
│                 - Category preferences
│
└─ No  → Use demographic profile
         - Age, location, gender
         - Generic expectations for cohort
```

**Output**: CustomerContext with user segment

### 🤖 Agent 3: SURVEY_AND_REVIEW_AGENT

**Purpose**: Orchestrate survey and generate reviews

**File**: `agents/survey_and_review_agent.py`

**Workflow** (Stateful LangGraph):
```
1. START SURVEY
   │
   ├─> Invoke Agent 1 (parallel)
   ├─> Invoke Agent 2 (parallel)
   │
   ↓
2. GENERATE INITIAL QUESTIONS (3 questions)
   - Based on product + customer context
   - Personalized to user and product
   │
   ↓
3. PRESENT QUESTION → GET ANSWER
   - Show question with 4-6 options
   - User selects one
   - Record in conversation history
   │
   ↓
4. ADAPTIVE QUESTIONING
   - Generate 2 follow-up questions
   - Based on previous answers
   - Explore interesting angles
   │
   ↓
5. REPEAT (total 5-10 questions)
   │
   ↓
6. GENERATE REVIEW OPTIONS (3 options)
   - Option 1: Enthusiastic tone
   - Option 2: Balanced tone
   - Option 3: Critical/honest tone
   - Each with appropriate star rating
   │
   ↓
7. SAVE SELECTED REVIEW
   - User picks one
   - Save to database
   - Mark session complete
```

**Key Features**:
- ✅ Stateful (remembers conversation)
- ✅ Adaptive (questions change based on answers)
- ✅ Handles navigation (user can go back)
- ✅ Guardrails (stays on topic)
- ✅ Natural language reviews

---

## API Integration Flow

### Frontend → Backend Communication

```
Frontend (Next.js)
    │
    │ POST /api/survey/start
    ↓
Frontend API Route (/app/api/survey/start/route.ts)
    │
    │ Proxy request
    ↓
Backend FastAPI (/api/survey/start)
    │
    │ Invoke agents
    ↓
Agent 3 → Agent 1 + Agent 2
    │
    │ Return first question
    ↓
Frontend UI (display question)
    │
    │ User answers
    ↓
Frontend API Route (/app/api/survey/answer/route.ts)
    │
    ↓
Backend (/api/survey/answer)
    │
    │ Process answer, next question
    ↓
... repeat until survey complete ...
    │
    ↓
Backend returns review options
    │
    ↓
Frontend displays review options
    │
    │ User selects
    ↓
Backend saves review (/api/survey/review)
    │
    ↓
Session complete! 🎉
```

---

## Testing the Backend

### 1. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development"
}
```

### 2. Test Start Survey (with real data)

```bash
curl -X POST http://localhost:8000/api/survey/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid-from-db",
    "item_id": "product-uuid-from-db",
    "form_data": {
      "productUrl": "https://amazon.com/...",
      "hasReviews": "yes",
      "userPersona": {
        "name": "John Doe",
        "email": "john@example.com",
        "age": "25",
        "location": "New York"
      },
      "userHasPurchasedSimilar": "yes"
    }
  }'
```

Expected:
```json
{
  "session_id": "generated-uuid",
  "question": {
    "question_text": "What was your primary reason for considering this product?",
    "options": [
      "Price and value",
      "Brand reputation",
      "Specific features",
      "Reviews and ratings",
      "Recommendation from friend",
      "Other"
    ],
    "reasoning": "Understanding purchase motivation helps personalize the survey..."
  },
  "question_number": 1,
  "total_questions": 3
}
```

### 3. Interactive API Testing

Visit http://localhost:8000/docs

You'll see Swagger UI with all endpoints. You can:
- Test each endpoint interactively
- See request/response schemas
- Try different parameters

---

## Configuration Options

Edit `config.py` to customize:

```python
# OpenAI Model (cost vs quality trade-off)
openai_model: str = "gpt-4o-mini"  # or "gpt-4o" for better quality

# Temperature (creativity vs consistency)
openai_temperature: float = 0.7  # 0.0-1.0

# Survey Length
initial_questions_count: int = 3  # First batch
min_survey_questions: int = 5      # Minimum total
max_survey_questions: int = 10     # Maximum total

# Review Options
review_options_count: int = 3  # Number of review choices

# Vector Search
similarity_threshold: float = 0.7  # 0.0-1.0 (higher = stricter)
max_similar_products: int = 5
max_user_history: int = 10
```

---

## Common Issues & Solutions

### Issue 1: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'langchain'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue 2: Supabase Connection Failed

**Error**: `Could not connect to Supabase`

**Solution**:
- Verify `SUPABASE_URL` in `.env`
- Ensure you're using **SERVICE_ROLE_KEY** (not anon key)
- Check network connectivity

### Issue 3: OpenAI API Error

**Error**: `OpenAI API error: Invalid API key`

**Solution**:
- Verify API key starts with `sk-proj-`
- Check billing status at platform.openai.com
- Ensure key has correct permissions

### Issue 4: Vector Search Not Working

**Error**: `Function match_products does not exist`

**Solution**:
- Run `database/functions/match_products.sql` in Supabase SQL Editor
- Verify pgvector extension is enabled
- Check Supabase logs for errors

---

## Cost Estimation

### OpenAI API Costs (GPT-4o-mini)

**Per Survey**:
- Input: ~2,000 tokens (contexts + questions)
- Output: ~1,500 tokens (questions + reviews)
- Cost: **~$0.001** (less than 1 cent)

**Monthly Estimates**:
- 100 surveys: ~$0.10
- 1,000 surveys: ~$1.00
- 10,000 surveys: ~$10.00

**Embeddings** (text-embedding-3-small):
- Minimal cost (~$0.00001 per product)

---

## Next Steps

Now that your backend is set up:

1. ✅ **Verify backend is running** (http://localhost:8000)
2. ⏳ **Add backend URL to frontend `.env.local`**:
   ```env
   BACKEND_URL=http://localhost:8000
   ```
3. ⏳ **Update frontend to call survey APIs** (Phase 2 Part 2)
4. ⏳ **Test complete flow** end-to-end
5. ⏳ **Fine-tune agent prompts** based on results
6. ⏳ **Deploy backend** to Railway/Render

---

## Development Workflow

### Running in Development

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Both should be running for full functionality.

### Making Changes to Agents

1. Edit agent file (e.g., `agents/product_context_agent.py`)
2. Backend auto-reloads (if using `--reload` flag)
3. Test via `/docs` or frontend
4. Iterate on prompts

### Debugging

Check backend logs in terminal:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Errors will appear with full stack traces.

---

## Support Resources

- **LangChain Docs**: https://python.langchain.com/docs/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **OpenAI API Docs**: https://platform.openai.com/docs/
- **Supabase Docs**: https://supabase.com/docs

---

## Summary

You've successfully created:
- ✅ 3 AI agents (Product, Customer, Survey)
- ✅ FastAPI backend with RESTful APIs
- ✅ Vector similarity search
- ✅ Stateful survey orchestration
- ✅ Natural language review generation
- ✅ Complete documentation

**Your backend is ready for Phase 2 integration!** 🎉
