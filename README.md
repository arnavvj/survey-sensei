# Survey Sensei

**AI-Powered Personalized Survey Generation with Context-Aware Review Creation**

Survey Sensei is a production-ready application that generates hyper-personalized survey questions based on user purchase history, product analytics, and customer behavior using LangChain agents and vector embeddings.

## Features

- **Context-Aware Survey Generation**: LangChain agents analyze product and customer context to create targeted questions
- **Adaptive Question Flow**: Dynamic survey that adjusts based on user responses
- **Intelligent Review Creation**: Generates authentic review options from survey answers
- **Vector Embeddings**: Semantic search using pgvector (1536-dim OpenAI embeddings)
- **Amazon Product Integration**: RapidAPI-powered product scraping
- **Mock Data Generation**: Realistic synthetic data for testing and demonstrations

## Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router) + TypeScript
- **Styling**: Tailwind CSS
- **Database**: Supabase JS Client
- **APIs**: RapidAPI, OpenAI

### Backend
- **Framework**: FastAPI + Python 3.11+
- **AI/ML**: LangChain, OpenAI GPT-4o-mini
- **Database**: Supabase Client

### Database
- **Platform**: Supabase (PostgreSQL 15+)
- **Extensions**: pgvector (1536-dimensional embeddings)
- **Features**: Row Level Security, Triggers, Indexes

## Quick Start

### Prerequisites

1. **Node.js 18+** - [Download](https://nodejs.org/)
2. **Python 3.11+** - [Download](https://www.python.org/downloads/)
3. **Conda** - [Download](https://docs.conda.io/en/latest/miniconda.html)
4. **Supabase Account** - [Sign up](https://supabase.com) (free tier)
5. **OpenAI API Key** - [Get key](https://platform.openai.com/api-keys)
6. **RapidAPI Key** (optional) - [Subscribe](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data) (free tier: 100 requests/month)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/your-username/survey-sensei.git
cd survey-sensei
```

#### 2. Database Setup

**Create Supabase Project:**
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for project to initialize (~2 minutes)
3. Save your Project URL and API keys

**Run Database Migrations:**
1. Open Supabase SQL Editor in your project
2. Copy entire contents of `backend/database/_combined_migrations.sql`
3. Paste and execute in SQL Editor
4. Verify 6 tables created: `products`, `users`, `transactions`, `reviews`, `survey_sessions`, `survey_details`

**Get Supabase Credentials:**
- Go to: **Project Settings** → **API**
- **Project URL**: Copy the full URL (format: `https://xxxxx.supabase.co`)
- **Anon Key**: Find `anon` `public` key (starts with `eyJhbGc...`)
- **Service Role Key**: Find `service_role` `secret` key (starts with `eyJhbGc...`)

#### 3. Backend Setup

```bash
cd backend

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate survey-sensei

# Create environment file
cp .env.local.example .env.local
```

**Configure Backend Environment (`backend/.env.local`):**

```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key-here

# OpenAI
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Application
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

**Start Backend Server:**

```bash
python main.py
```

Backend will start at `http://localhost:8000`

Verify installation at `http://localhost:8000/docs` (Swagger UI)

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
```

**Configure Frontend Environment (`frontend/.env.local`):**

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key-here

# OpenAI (for persona generation)
OPENAI_API_KEY=sk-proj-your-openai-key-here

# RapidAPI (optional but recommended)
RAPIDAPI_KEY=your-rapidapi-key-here

# Application
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Start Frontend Server:**

```bash
npm run dev
```

Frontend will start at `http://localhost:3000`

#### 5. Verify Installation

**Test Complete Flow:**
1. Open `http://localhost:3000`
2. Paste Amazon URL: `https://www.amazon.com/dp/B0DCJ5NMV2`
3. Click "Fetch Product Info"
4. Complete all form fields
5. Submit form → Mock data generation
6. Start survey → Answer questions
7. Generate review → Select and submit

**Check Backend Health:**
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

## Application Flow

### 1. Product Data Collection
- User enters Amazon product URL
- System scrapes product details via RapidAPI
- Product data stored in database

### 2. Survey Configuration
- User answers 5 setup questions:
  1. Product has reviews? (Yes/No)
  2. Sentiment spread (Good/Neutral/Bad %) OR Similar products exist?
  3. User persona (auto-generated, can regenerate)
  4. User has purchase history? (Yes/No)
  5. User bought exact product? (Yes/No)

### 3. Mock Data Generation
- MOCK_DATA_MINI_AGENT generates:
  - Similar products (if applicable)
  - User personas (20-100 users)
  - Purchase transactions (realistic patterns)
  - Product reviews (with sentiment distribution)
- All data inserted into Supabase

### 4. Survey Execution
- ProductContextAgent analyzes product reviews/descriptions
- CustomerContextAgent analyzes user purchase history
- SurveyAgent generates contextual questions
- User answers 3-7 questions adaptively

### 5. Review Generation
- ReviewGenAgent synthesizes survey responses
- Generates 3 review options with different tones
- User selects preferred review
- Review saved to database

## Project Structure

```
survey-sensei/
├── backend/
│   ├── agents/
│   │   ├── product_context_agent.py      # Analyzes product data
│   │   ├── customer_context_agent.py     # Analyzes customer behavior
│   │   ├── survey_agent.py               # Generates questions
│   │   └── review_gen_agent.py           # Creates review options
│   ├── database/
│   │   ├── supabase_client.py            # Database operations
│   │   ├── migrations/                   # SQL migration files
│   │   └── _combined_migrations.sql      # Master reset script
│   ├── integrations/
│   │   └── rapidapi_client.py            # Amazon product scraper
│   ├── config.py                         # Configuration
│   ├── main.py                           # FastAPI application
│   └── environment.yml                   # Conda dependencies
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── scrape/route.ts           # Product scraping API
│   │   │   ├── mock-data/route.ts        # Mock data generation
│   │   │   └── generate-persona/route.ts # User persona generation
│   │   └── page.tsx                      # Main UI (form + survey + review)
│   ├── components/
│   │   └── form/                         # Form field components
│   └── lib/
│       ├── supabase.ts                   # Supabase client
│       ├── types.ts                      # TypeScript definitions
│       └── utils.ts                      # Utility functions
└── README.md                             # This file
```

## Database Schema

### Core Tables

**products** - Product catalog
- Primary key: `item_id` (ASIN)
- Contains: title, brand, price, photos, ratings
- Embeddings: 1536-dim vectors for similarity search

**users** - User profiles
- Primary key: `user_id` (UUID)
- Contains: name, email, demographics, engagement metrics
- Embeddings: User behavior vectors

**transactions** - Purchase records
- Links users to products
- Contains: order dates, prices, status
- Tracks delivery and returns

**reviews** - Product reviews
- Links to transactions
- Contains: title, text, star rating
- Tracks source: RapidAPI vs agent-generated vs user-submitted
- Embeddings: Review sentiment vectors

**survey_sessions** - Survey tracking
- Contains: product_context, customer_context, session_context
- Stores: questions_and_answers, review_options
- Tracks entire survey lifecycle

**survey_details** - Event log
- Tracks: question_generated, answer_submitted, survey_completed
- Enables analytics and reconstruction

## API Endpoints

### Backend Endpoints

**POST /api/survey/start**
- Starts new survey session
- Invokes Product and Customer Context Agents
- Returns first question

**POST /api/survey/answer**
- Submits answer and gets next question
- Adapts questions based on responses
- Returns survey status and next question

**POST /api/survey/generate-reviews**
- Generates 3 review options from survey responses
- Returns reviews with titles, text, stars, sentiment

**POST /api/survey/submit-review**
- Saves selected review to database
- Marks survey session as complete

### Frontend Endpoints

**POST /api/scrape**
- Scrapes Amazon product data
- Uses RapidAPI with fallback to direct scraping

**POST /api/mock-data**
- Generates mock data for testing
- Creates products, users, transactions, reviews

**POST /api/generate-persona**
- Generates diverse user personas
- Round-robin gender alternation

## Configuration

### Backend Configuration (`backend/config.py`)

```python
# OpenAI Settings
OPENAI_MODEL = "gpt-4o-mini"  # Cost-effective
TEMPERATURE = 0.7              # Balanced creativity

# Survey Settings
MIN_QUESTIONS = 3
MAX_QUESTIONS = 7
REVIEW_OPTIONS = 3

# Vector Search
SIMILARITY_THRESHOLD = 0.7
```

### Frontend Configuration

- **Form Fields**: 5 progressive fields with conditional logic
- **UI States**: Multi-pane interface (form → summary → survey → review)
- **Animations**: Smooth transitions (500ms duration)

## Testing

### Test with Mock Data

For development without API calls, use `mock` URLs:

```
http://localhost:3000?url=mock
```

### Test Amazon URLs

```
https://www.amazon.com/dp/B0DCJ5NMV2
https://www.amazon.com/dp/B09XS7JWHH
```

### Database Verification

```sql
-- Check data counts
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM reviews;

-- Check survey sessions
SELECT session_id, created_at FROM survey_sessions ORDER BY created_at DESC LIMIT 5;

-- Verify embeddings
SELECT item_id, title, embeddings IS NOT NULL as has_embedding FROM products LIMIT 5;
```

## Troubleshooting

### Backend Won't Start

**Issue**: Import errors or missing dependencies
**Solution**:
```bash
conda env remove -n survey-sensei
conda env create -f environment.yml
conda activate survey-sensei
```

### Frontend Build Errors

**Issue**: Type errors or missing modules
**Solution**:
```bash
rm -rf node_modules .next
npm install
npm run dev
```

### Database Connection Failed

**Issue**: Invalid Supabase credentials
**Solution**:
- Verify `SUPABASE_URL` and keys in `.env.local`
- Ensure service role key (not anon key) is used in backend
- Check Supabase project is not paused

### OpenAI API Errors

**Issue**: Invalid API key or insufficient credits
**Solution**:
- Verify API key starts with `sk-proj-`
- Check billing at [platform.openai.com/usage](https://platform.openai.com/usage)
- Ensure sufficient credits available

### RapidAPI Not Working

**Issue**: Product scraping fails
**Solution**:
- Add `RAPIDAPI_KEY` to frontend `.env.local`
- Verify API key at [RapidAPI dashboard](https://rapidapi.com/developer/apps)
- Check free tier limits (100 requests/month)

## Development Commands

### Backend

```bash
# Start server
python main.py

# Run tests
pytest

# Run specific test
pytest tests/test_product_context_agent.py

# Generate coverage report
pytest --cov=agents --cov-report=html
```

### Frontend

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type checking
npm run type-check
```

## Documentation

- **[Backend README](backend/README.md)**: Agent architecture, API reference, testing
- **[Frontend README](frontend/README.md)**: Component structure, UI states, form flow
- **[Database README](backend/database/README.md)**: Schema details, migrations, verification

## Contributing

This is a demonstration project showcasing AI agent architecture and full-stack development skills.

## License

MIT

---

**Version**: 1.0.0
**Status**: Production Ready
**Author**: Arnav Jeurkar
