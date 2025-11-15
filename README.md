# Survey Sensei

AI-powered survey builder that adapts questions to each user's unique experience.

## Overview

Survey Sensei is a GenAI-powered hyper-custom survey application demonstrating expertise in building agentic backend systems. The platform generates personalized survey questions based on user purchase history, product details, and sentiment analysis using vector embeddings and LangChain agents.

## Key Features

- **Agentic AI Survey Generation**: LangChain/LangGraph agents analyze context and generate personalized questions
- **Vector Embeddings**: Semantic search using pgvector (1536-dim OpenAI-compatible)
- **Progressive Form UI**: 7-field intake with conditional logic and multi-pane retractable interface
- **Amazon Product Integration**: RapidAPI-based scraper with intelligent ASIN extraction
- **Mock Data Agent**: Realistic synthetic data generator for simulation
- **Cold Start Handling**: Adapts to scenarios with limited product/user history

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0: Database | ✅ Complete | PostgreSQL schema with pgvector, RLS, and triggers |
| Phase 1 Part 1: Frontend Intake | ✅ Complete | Progressive form + MOCK_DATA_AGENT |
| Phase 1 Part 2: Survey UI | ✅ Complete | Multi-pane retractable UI with survey interface |
| Phase 2: Agentic Backend | 🔄 Planned | LangChain agents for question generation |
| Phase 3: API Integration | 🔄 Planned | REST + WebSocket endpoints |
| Phase 4: Deployment | 🔄 Planned | Vercel + Railway production setup |

## Tech Stack

### Frontend
- Next.js 14 (App Router) with TypeScript
- Tailwind CSS with custom design system
- Supabase JS Client
- RapidAPI integration for Amazon data

### Backend (Phase 2)
- Python 3.11+
- FastAPI
- LangChain / LangGraph
- OpenAI API / Anthropic
- Sentence Transformers

### Database
- Supabase (PostgreSQL 15+)
- pgvector extension (1536-dimensional embeddings)
- Row Level Security (RLS)
- Auto-updating triggers and indexes

## Running Locally

### Prerequisites
- Node.js 18+
- Supabase account (free tier)
- RapidAPI key (optional, 100 free requests/month)

### Step 1: Database Setup

1. **Create Supabase Project**
   - Visit [supabase.com](https://supabase.com) and create a new project
   - Save your project URL and API keys for Step 2

2. **Run Database Migration**
   - Open Supabase SQL Editor in your project
   - Copy entire contents of `database/migrations/001_initial_schema.sql`
   - Paste and execute in SQL Editor
   - Verify 6 tables created: `products`, `users`, `transactions`, `reviews`, `survey`, `survey_sessions`

3. **Get Your Supabase Keys** ⚠️ Save These for Step 2!
   - Go to: **Project Settings** → **API**

   **Value 1: Project URL**
   - Find section: **Project URL**
   - Copy the full URL (format: `https://xxxxx.supabase.co`)

   **Value 2: Anon Key (Public)**
   - Find section: **Project API keys**
   - Look for row labeled `anon` `public`
   - Click "Copy" or "Reveal" to get the key (starts with `eyJhbGc...`)

   **Value 3: Service Role Key (Secret)**
   - Find row labeled `service_role` `secret`
   - Click "Copy" or "Reveal" to get the key (starts with `eyJhbGc...`)
   - ⚠️ **IMPORTANT**: This is sensitive! Keep it secret, never commit to git

### Step 2: Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Create Environment File**
   ```bash
   cp .env.local.example .env.local
   ```

3. **Add Supabase Credentials** (from Step 1.3)

   Open `frontend/.env.local` in your text editor and replace ALL placeholder values:

   ```env
   # Replace these 3 values with YOUR Supabase credentials from Step 1.3:
   NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co    # Paste Value 1
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key-here         # Paste Value 2
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key-here     # Paste Value 3
   ```

   **Example (with fake keys):**
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
   ```

   ⚠️ **Important**: Replace ALL `your-*` placeholders with real values!

4. **[OPTIONAL] Add RapidAPI Key** (Highly Recommended)

   Without this, Amazon may block product scraping. RapidAPI offers FREE 100 requests/month.

   **Quick Setup (2 minutes):**
   1. Sign up at [rapidapi.com](https://rapidapi.com/)
   2. Go to [Real-Time Amazon Data API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-amazon-data)
   3. Click "Subscribe to Test" → Select **"Basic" (FREE)**
   4. Find "Code Snippets" section and copy your API key (labeled `x-rapidapi-key`)
   5. Add to `frontend/.env.local`:
      ```env
      RAPIDAPI_KEY=your-actual-rapidapi-key-here
      ```

5. **Verify Your `.env.local`**

   Final file should look like this (with YOUR actual keys):
   ```env
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

   # RapidAPI (optional but recommended)
   RAPIDAPI_KEY=abc123xyz789def456

   # OpenAI (not needed for Phase 1)
   OPENAI_API_KEY=your_openai_api_key_here

   # Application Configuration
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```

   ✅ All placeholders replaced with real values
   ❌ No "your-project-id" or "your-anon-public-key-here" remaining

6. **Run Development Server**
   ```bash
   npm run dev
   ```

   Wait for: `Ready on http://localhost:3000`

7. **Open Application**
   - Navigate to [http://localhost:3000](http://localhost:3000)
   - Test with: `https://www.amazon.com/dp/B0DCJ5NMV2`

### Verification Checklist

After setup, verify everything works:

- [ ] Server starts without errors (`npm run dev`)
- [ ] Application loads at http://localhost:3000
- [ ] Paste Amazon URL and click "Fetch" → Product data appears
- [ ] Complete form and click "Submit" → Summary appears
- [ ] Check Supabase Table Editor → See new data in `products`, `users`, `transactions`, `reviews` tables

### Testing with Mock Data

For development and testing without making real API calls, simply enter a URL ending with `mock`:

**Quick Start:**
1. Open the application at `http://localhost:3000`
2. In the "Amazon Product URL" field, type: `mock`
3. Click "Fetch Product Info"
4. Done! Instant mock data loads ✨

**Supported mock URLs:**
- `mock` (simplest)
- `https://www.amazon.com/mock`
- `https://www.amazon.com/test/mock`
- Any URL ending with `/mock`

**Mock data includes:**
- Product: "Premium Wireless Headphones with Noise Cancellation"
- Price: $149.99
- Rating: 4.5/5 (1,247 reviews)
- 3 detailed customer reviews (with verified badges)
- 3 colorful product images

**Why use mock data?**
- ✅ No API key required
- ✅ Instant response (no network delay)
- ✅ Consistent data for reproducible tests
- ✅ Works offline
- ✅ Doesn't consume RapidAPI quota
- ✅ Perfect for demos and development

**Testing scenarios:**
- **Quick UI Testing**: Use `mock` to rapidly test form flow and navigation
- **Database Verification**: Confirm mock data inserts correctly into Supabase
- **Offline Development**: Continue working without internet
- **CI/CD Testing**: Automated tests without external API dependencies
- **Demos**: Show the app instantly to stakeholders

**Note:** Regular Amazon URLs (not ending with "mock") will fetch real product data using RapidAPI or direct scraping.

**Advanced testing options:**
```bash
# API endpoint testing (cURL)
curl -X POST http://localhost:3000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "mock"}'

# Browser console testing
fetch('/api/scrape', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'mock' })
}).then(r => r.json()).then(console.log)
```

## Application Architecture

### Database Schema (6 Tables)

1. **products**: Product catalog with semantic embeddings
2. **users**: User profiles with demographics and purchase patterns
3. **transactions**: Purchase and delivery tracking with auto-computed discounts
4. **reviews**: Sentiment analysis with toxicity detection
5. **survey**: Agentic question generation with explainability metadata
6. **survey_sessions**: Conversation state tracking for multi-turn surveys

### Multi-Pane UI States

The application features a sophisticated retractable UI system:

**State 1**: Form filling (before submit)
- Survey Sensei pane: 100% width

**State 2**: After submission
- Survey Sensei pane: 10% width (minimized, clickable)
- Simulation Summary: 90% width

**State 3**: Survey pane expanded
- Survey Sensei pane: 90% width (click to expand)
- Simulation Summary: 10% width (minimized with vertical text)

**State 4**: Survey UI (3-pane layout)
- Survey Sensei: 10% width
- Summary Stats: 10% width (compact view)
- Survey UI: 80% width (65% questions / 35% answer stack)

### Form Flow (7 Fields)

1. **Amazon Product URL**: Scrape with intelligent ASIN extraction
2. **Review Status**: Yes/No (triggers conditional logic)
3. **Sentiment Spread** (if Yes): Good/Neutral/Bad % sliders
4. **Similar Products** (if No): Yes/No
5. **User Persona**: Auto-generated (name, email, age, location, demographics)
6. **Purchase History**: Yes/No
7. **Exact Product**: Yes/No
8. **Submit**: Generate mock data + transition to summary

## Current Features

### ✅ Phase 1 Part 1: Form Intake (Complete)
- Progressive 7-field form with conditional logic
- Amazon product scraping via RapidAPI
- Conditional review fetching (API optimization)
- MOCK_DATA_AGENT for synthetic data generation
- Complete database integration (4 tables)
- Cold start scenario detection

### ✅ Phase 1 Part 2: Survey UI (Complete)
- Multi-pane retractable interface
- Survey Sensei branding with gradient logo
- Simulation summary with compact stats
- Survey UI with 65/35 question/answer split
- Phase 2 integration placeholders
- Smooth animations and transitions

### 🔄 Recent Improvements

**API Optimization**:
- Conditional review fetching saves 50% API calls
- Reviews only fetched when user confirms product has reviews
- Smart ASIN extraction supports all Amazon URL formats

**Database Completeness**:
- Vector embeddings (1536-dim) populated for products, users, reviews
- Transaction delivery dates and return dates
- User last_active timestamps
- All schema columns fully populated

**UX Enhancements**:
- Improved Survey Sensei logo with gradient styling
- Simulation summary relocated to sidebar
- Multi-state pane transitions with click interactions
- Loading states and visual feedback

## Key Implementation Details

### MOCK_DATA_AGENT Logic

1. **Product Generation**
   - Main scraped product
   - 5-10 similar variants (if applicable)
   - 8-15 user-specific products (if purchase history)
   - Price variations: ±30% of base price

2. **User Generation**
   - Main user persona from form
   - 20-50 review authors
   - 50-100 similar product purchasers (if applicable)
   - Realistic demographics and spending patterns

3. **Transaction Generation**
   - 1-3 transactions per user
   - Varied statuses: delivered (70%), returned (10%), in_transit (20%)
   - Realistic dates: 1-365 days ago
   - Auto-computed discounts

4. **Review Generation**
   - Based on sentiment spread
   - Natural language review text
   - Star ratings aligned with sentiment
   - Timestamps within 60 days

### Embedding Generation

Currently uses deterministic pseudo-random embeddings for demo purposes:

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

**For Production**: Replace with OpenAI embeddings API (`text-embedding-ada-002`)

## Development Commands

```bash
# Frontend
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript validation

# Backend (Phase 2)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload  # Start FastAPI server
```

## Testing

### Verified Amazon URLs
```
https://www.amazon.com/dp/B0DCJ5NMV2
https://www.amazon.com/dp/B09XS7JWHH
```

### Database Verification
```sql
SELECT COUNT(*) FROM products;      -- Should increase after submission
SELECT COUNT(*) FROM users;         -- Should increase after submission
SELECT COUNT(*) FROM transactions;  -- Should increase after submission
SELECT COUNT(*) FROM reviews;       -- Should increase if reviews enabled
```

### UI Testing Checklist
- [ ] Form progresses through all 7 fields
- [ ] Product data fetches correctly
- [ ] Conditional logic works (Fields 3 vs 4)
- [ ] Submission generates mock data
- [ ] Panel transitions work smoothly
- [ ] Survey pane expands/collapses on click
- [ ] Summary pane expands/collapses on click
- [ ] Survey UI displays correctly in 3-pane layout

## Troubleshooting

### "RapidAPI not configured"
- Add `RAPIDAPI_KEY` to `.env.local`
- Restart dev server
- App will fall back to direct scraping (may be blocked)

### "Could not extract ASIN from URL"
- Ensure URL is from Amazon product page (not search/category)
- URL should contain `/dp/` or `/gp/product/` with 10-character ASIN
- Example: `https://www.amazon.com/dp/B0DCJ5NMV2`

### Database Insertion Errors
- Verify Supabase credentials in `.env.local`
- Ensure database schema is deployed
- Check Supabase dashboard for error logs

### Port 3000 Already in Use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use different port
npm run dev -- -p 3001
```

## Production Roadmap

### Phase 2: Agentic Backend (Planned)

**Infrastructure**:
- FastAPI backend with LangChain/LangGraph
- OpenAI integration for embeddings and question generation
- WebSocket support for real-time surveys

**Agent Architecture**:
```
Orchestrator Agent
  ├─ Context Agent: Fetch user/product/transaction data
  ├─ Analysis Agent: Sentiment + vector similarity search
  ├─ Question Agent: Generate contextual questions
  ├─ Validator Agent: Quality control and explainability
  └─ Response Agent: Process user answers and update context
```

**LangGraph Workflow**:
```
START → Fetch Context → Analyze Context → Generate Questions
     → Present to User → Await Response → Process Answer
     → Need Follow-up? (Yes: loop | No: Generate Review) → END
```

### Phase 3: API Integration (Planned)

**REST Endpoints**:
- Authentication: `POST /api/auth/login`, `POST /api/auth/signup`
- Products: `GET /api/products`, `GET /api/products/:id`
- Surveys: `POST /api/surveys/start`, `POST /api/surveys/:id/answer`
- Reviews: `GET /api/reviews`, `POST /api/reviews`

**WebSocket**:
- `WS /ws/survey/:session_id`: Real-time question streaming

**Security**:
- JWT authentication
- Rate limiting (Redis-based)
- Input validation (Pydantic schemas)
- CORS configuration

### Phase 4: Deployment & Scaling (Planned)

**Infrastructure**:
- **Frontend**: Vercel (auto-scaling, CDN)
- **Backend**: Railway/Render (auto-scaling, health checks)
- **Database**: Supabase Cloud (connection pooling, backups)
- **Caching**: Redis (embedded response caching)
- **Monitoring**: Sentry (error tracking), Supabase Analytics

**Scaling Strategy**:

**MVP (< 10k users)**:
- Single Supabase instance
- Vercel serverless functions
- No caching layer needed

**Growth (10k-100k users)**:
- Supabase read replicas
- Redis caching layer
- Background job queue (Celery)
- CDN for static assets

**Scale (100k-1M users)**:
- Database sharding by region
- Microservices architecture
- Dedicated LLM inference server
- Auto-scaling backend instances

**Enterprise (1M+ users)**:
- Multi-region deployment
- Custom vector database (Pinecone/Weaviate)
- Event-driven architecture (Kafka)
- Edge computing (Cloudflare Workers)

**Performance Targets**:
- API response time: < 200ms (p95)
- Survey generation: < 2s (cold start), < 500ms (warm)
- Database queries: < 50ms (with proper indexing)
- Uptime: 99.9% SLA

**Cost Optimization**:
- Embedding caching (reduce OpenAI API calls)
- Batch processing for background jobs
- Supabase connection pooling
- Serverless auto-scaling (pay-per-use)

## Documentation

- **[Database Setup](database/README.md)**: Schema details, migrations, and optimization
- **[Frontend Guide](frontend/README.md)**: Component architecture and development
- **[Technical Docs](docs/DOCUMENTATION.md)**: System architecture and API reference

## What Didn't Work (Archive)

### Scraper Evolution

**Attempt 1: Multi-Platform Cheerio Scraper**
- **Issue**: Required Cheerio dependency, inconsistent HTML parsing across platforms
- **Why Failed**: Walmart/Etsy/eBay actively block scrapers, maintenance overhead too high
- **Lesson**: Focus on single platform (Amazon) with API-based approach

**Attempt 2: Direct Amazon Scraping**
- **Issue**: Amazon blocks direct requests ~70% of the time
- **Why Failed**: Unreliable for production, poor UX with frequent failures
- **Solution**: Switched to RapidAPI with graceful fallback

**Attempt 3: ScraperAPI Integration**
- **Issue**: Free tier limited to 5,000 requests/month, requires external service
- **Why Not Used**: RapidAPI offers cleaner JSON responses with same free tier limits
- **Alternative**: Kept as documented option in case RapidAPI fails

### UI Iterations

**Attempt 1: Vertical Stacked Layout**
- **Issue**: Form and summary competed for vertical space
- **Why Failed**: Required excessive scrolling, poor information hierarchy
- **Solution**: Horizontal panel transition (10% / 90%)

**Attempt 2: Modal-Based Summary**
- **Issue**: Summary hidden behind modal, required extra clicks
- **Why Failed**: Broke user flow, felt disjointed
- **Solution**: Integrated side-by-side panels with smooth transitions

**Attempt 3: Always-Visible Sidebar**
- **Issue**: Form felt cramped, especially on mobile
- **Why Failed**: Reduced form usability on smaller screens
- **Solution**: Minimized sidebar (10%) only after submission

### Database Attempts

**Attempt 1: Manual Embedding Generation**
- **Issue**: Planned to generate real embeddings immediately
- **Why Deferred**: OpenAI API costs during development, complexity
- **Current**: Using deterministic mock embeddings for Phase 1
- **Future**: Will integrate real embeddings in Phase 2

**Attempt 2: Separate Review Sentiment Table**
- **Issue**: Initially planned separate `review_sentiment` table
- **Why Failed**: Over-normalization, added query complexity
- **Solution**: Embedded sentiment_score and toxicity_score directly in reviews table

## License

MIT

---

**Current Version**: 1.2.0
**Last Updated**: 2025-11-12
**Contributors**: Arnav Jeurkar
**Status**: Phase 1 Complete, Phase 2 Planning
