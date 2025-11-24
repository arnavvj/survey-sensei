## Survey Sensei Backend - Phase 2

AI-powered survey generation and review creation backend using LangChain and LangGraph.

## Architecture

### Three-Agent System

1. **Agent 1: PRODUCT_CONTEXT_AGENT** (Stateless LangChain)
   - Analyzes product reviews and descriptions
   - Extracts concerns, features, pros/cons
   - Handles cold start scenarios with similar product analysis

2. **Agent 2: CUSTOMER_CONTEXT_AGENT** (Stateless LangChain)
   - Analyzes user purchase and review history
   - Identifies user concerns and expectations
   - Segments users by behavior patterns

3. **Agent 3: SURVEY_AND_REVIEW_AGENT** (Stateful LangGraph)
   - Orchestrates Agent 1 and 2
   - Generates adaptive survey questions
   - Creates natural language review options
   - Manages conversation state

## Setup Instructions

### 1. Install Python Dependencies

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
- Better dependency management for complex packages (LangChain, sentence-transformers)
- Reproducible across all platforms (Windows, Linux, macOS)
- Recommended for both development and deployment
- Single source of truth for all dependencies

### 2. Configure Environment Variables

Create `.env.local` file:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your credentials:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI
OPENAI_API_KEY=sk-proj-your-openai-key

# Application
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### 3. Set Up Database Function

Execute the SQL function in your Supabase SQL Editor:

```bash
# The function is located at:
database/functions/match_products.sql
```

This creates the `match_products()` function for vector similarity search.

### 4. Start the Backend Server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --port 8000
```

The server will start at `http://localhost:8000`

### 5. Verify Installation

Visit `http://localhost:8000/docs` to see the interactive API documentation (Swagger UI).

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development"
}
```

## API Endpoints

### POST /api/survey/start
Start a new survey session

**Request:**
```json
{
  "user_id": "uuid",
  "item_id": "uuid",
  "form_data": {
    "productUrl": "...",
    "hasReviews": "yes",
    "userPersona": {...},
    ...
  }
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "question": {
    "question_text": "...",
    "options": ["...", "..."],
    "reasoning": "..."
  },
  "question_number": 1,
  "total_questions": 3
}
```

### POST /api/survey/answer
Submit an answer and get next question

**Request:**
```json
{
  "session_id": "uuid",
  "answer": "Selected option text"
}
```

**Response (continued):**
```json
{
  "session_id": "uuid",
  "status": "continue",
  "question": {...},
  "question_number": 2,
  "total_questions": 5
}
```

**Response (completed):**
```json
{
  "session_id": "uuid",
  "status": "completed",
  "review_options": [
    {
      "review_text": "...",
      "rating": 5,
      "sentiment": "positive",
      "tone": "enthusiastic"
    },
    ...
  ]
}
```

### POST /api/survey/review
Submit selected review

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
  "review": {...}
}
```

## Project Structure

```
backend/
├── agents/
│   ├── __init__.py
│   ├── product_context_agent.py     # Agent 1: Product analysis
│   ├── customer_context_agent.py    # Agent 2: Customer analysis
│   └── survey_and_review_agent.py   # Agent 3: Survey orchestration
├── database/
│   ├── __init__.py
│   └── supabase_client.py            # Database operations
├── utils/
│   ├── __init__.py
│   └── embeddings.py                 # OpenAI embeddings
├── config.py                          # Configuration management
├── main.py                            # FastAPI application
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
└── README.md                          # This file
```

## Agent Workflows

### Agent 1: Product Context

```
Product has reviews?
  Yes → Extract from reviews
  No  → Similar products reviewed?
          Yes → Use similar product reviews
          No  → Use product description only
```

### Agent 2: Customer Context

```
User purchased similar?
  Yes → User reviewed them?
          Yes → Extract from user's reviews
          No  → Derive from purchase history
  No  → Use demographic profile
```

### Agent 3: Survey Flow

```
1. Invoke Agent 1 + Agent 2 (parallel)
2. Generate initial 3 questions
3. Present question → Get answer
4. Generate 2 follow-up questions
5. Present question → Get answer
6. Repeat until 5-10 questions total
7. Generate 3 review options
8. Save selected review
```

## Configuration

Edit `config.py` to adjust:

- **OpenAI Model**: `gpt-4o-mini` (default, cost-effective) or `gpt-4o`
- **Temperature**: `0.7` (creativity vs consistency)
- **Survey Length**: `5-10` questions (min/max)
- **Review Options**: `3` options to choose from
- **Similarity Threshold**: `0.7` for vector search

## Development Tips

### Testing Individual Agents

```python
# Test Agent 1
from agents import product_context_agent

context = product_context_agent.generate_context(
    product_url="https://amazon.com/...",
    has_reviews=True,
    form_data={...}
)
print(context)
```

```python
# Test Agent 2
from agents import customer_context_agent

context = customer_context_agent.generate_context(
    user_email="user@example.com",
    product_url="https://amazon.com/...",
    has_purchased_similar=True,
    form_data={...}
)
print(context)
```

### Monitoring Costs

Track OpenAI API usage at [platform.openai.com/usage](https://platform.openai.com/usage)

**Estimated costs** (GPT-4o-mini):
- Survey generation: ~$0.001 per survey
- 100 surveys/month: ~$0.10

## Troubleshooting

### ImportError: No module named 'langchain'
```bash
pip install -r requirements.txt
```

### Supabase connection failed
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`
- Check network connectivity to Supabase
- Ensure service role key (not anon key) is used

### OpenAI API errors
- Verify `OPENAI_API_KEY` is correct (starts with `sk-proj-`)
- Check billing and usage limits at OpenAI dashboard
- Ensure sufficient credits available

### Vector search not working
- Run the `match_products.sql` function in Supabase SQL Editor
- Verify pgvector extension is enabled
- Check that product embeddings exist in database

## Testing

### Quick Start

Run all unit tests (fast, no API key needed):

**Windows**:
```bash
run_tests.bat
```

**Linux/Mac**:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

Run with integration tests (requires OpenAI API key):

**Windows**:
```bash
run_tests.bat --integration
```

**Linux/Mac**:
```bash
./run_tests.sh --integration
```

### Test Coverage

The backend includes comprehensive tests:

- ✅ **Agent 1 Tests**: Product context generation (all 3 scenarios)
- ✅ **Agent 2 Tests**: Customer context generation (all 4 scenarios)
- ✅ **API Tests**: All endpoints with error handling
- ✅ **Integration Tests**: Real OpenAI API workflow

**Test Structure**:
```
backend/
├── tests/
│   ├── test_product_context_agent.py    # Agent 1 (25+ tests)
│   ├── test_customer_context_agent.py   # Agent 2 (20+ tests)
│   └── test_api_endpoints.py            # APIs (15+ tests)
├── conftest.py                           # Shared fixtures
├── pytest.ini                            # Configuration
└── run_tests.{sh,bat}                    # Test runners
```

### Manual Testing

```bash
# Run specific test file
pytest tests/test_product_context_agent.py

# Run specific test
pytest tests/test_api_endpoints.py::test_start_survey_success

# Verbose output
pytest -vv

# With coverage report
pytest --cov=agents --cov-report=html
```

### Test Categories

**Unit Tests** (Fast, ~5s):
- Mocked dependencies (no API calls)
- Test agent logic in isolation
- 90%+ code coverage

**Integration Tests** (Slow, ~45s):
- Real OpenAI API calls
- End-to-end workflows
- Requires `--run-integration` flag

**Performance**:
| Test Suite | Tests | Time | Coverage |
|------------|-------|------|----------|
| Unit | 25+ | ~5s | 90%+ |
| Integration | 5+ | ~45s | 95%+ |
| API | 15+ | ~10s | 85%+ |

### Viewing Coverage

After running tests, open the HTML report:

```bash
# Generated at:
htmlcov/index.html
```

### Writing Tests

Example test structure:

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_data():
    return {"key": "value"}

@patch('agents.product_context_agent.db')
def test_my_feature(mock_db, mock_data):
    # Arrange
    mock_db.get_product.return_value = mock_data

    # Act
    result = agent.generate_context(...)

    # Assert
    assert result.context_type == "expected"
    mock_db.get_product.assert_called_once()
```

### Troubleshooting Tests

**Import errors**:
```bash
# Install in development mode
pip install -e .
```

**Integration test failures**:
- Check `OPENAI_API_KEY` in `.env`
- Verify API key is valid
- Ensure sufficient credits

**Slow tests**:
```bash
# Skip integration tests
pytest  # (default, no --run-integration)

# Run in parallel
pip install pytest-xdist
pytest -n 4
```

## Conda Environment Management

### Quick Commands

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

### Adding New Dependencies

**Conda packages:**
```bash
conda install -c conda-forge package-name
# Then add to environment.yml under dependencies
```

**Pip packages:**
```bash
pip install package-name
# Then add to environment.yml under pip: section
```

### Troubleshooting Conda

**Environment already exists:**
```bash
conda env remove -n survey-sensei
conda env create -f environment.yml
```

**Slow environment creation:**
```bash
# Use faster solver
conda install -c conda-forge mamba
mamba env create -f environment.yml
```

**Package conflicts:**
```bash
# Update with libmamba solver
conda env update -f environment.yml --prune --solver=libmamba
```

## Next Steps

1. ✅ Backend agents created
2. ✅ Comprehensive test suite added
3. ⏳ Test with real data from Phase 1
4. ⏳ Integrate with frontend Survey UI
5. ⏳ Fine-tune prompts based on results
6. ⏳ Deploy to production (Railway/Render)

## Support

For issues or questions, check:
- [LangChain Docs](https://python.langchain.com/docs/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pytest Docs](https://docs.pytest.org/)
- [Conda Docs](https://docs.conda.io/)
