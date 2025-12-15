# Survey Sensei Frontend

Next.js 14 application with progressive form, survey interface, and review selection UI.

## Overview

The frontend provides a complete user experience from product selection through survey completion to review submission. Built with Next.js 14 App Router, TypeScript, and Tailwind CSS.

## Features

- **Progressive Form**: 5-step intake with conditional logic
- **Amazon Product Scraping**: RapidAPI integration with fallback
- **Diverse User Personas**: 48 diverse names with round-robin gender alternation
- **Interactive Survey UI**: Real-time question-answer flow
- **Review Selection**: Choose from 3 AI-generated review options
- **Responsive Design**: Works on all screen sizes

## Quick Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key

# OpenAI (for persona generation)
OPENAI_API_KEY=sk-proj-your-openai-key

# RapidAPI (optional but recommended)
RAPIDAPI_KEY=your-rapidapi-key

# Application
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Application starts at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── api/
│   │   ├── scrape/route.ts           # Amazon product scraper
│   │   ├── mock-data/route.ts        # Mock data generation
│   │   └── generate-persona/route.ts # User persona generation
│   ├── globals.css                   # Global styles
│   ├── layout.tsx                    # Root layout
│   └── page.tsx                      # Main application
├── components/
│   └── form/
│       ├── ProductUrlField.tsx       # Field 1: Amazon URL
│       ├── ReviewStatusField.tsx     # Field 2: Has reviews?
│       ├── SentimentSpreadField.tsx  # Field 3: Sentiment sliders
│       ├── SimilarProductsField.tsx  # Field 4: Similar products?
│       ├── UserPersonaField.tsx      # Field 5: User profile
│       └── SubmissionSummary.tsx     # Post-submit summary
├── lib/
│   ├── supabase.ts                   # Supabase client
│   ├── types.ts                      # TypeScript types
│   └── utils.ts                      # Utility functions
└── README.md                         # This file
```

## Application Flow

### 1. Form Submission (5 Steps)

**Step 1: Product URL**
- Enter Amazon product URL
- Click "Fetch Product Info"
- System scrapes product via RapidAPI
- Displays: title, price, images, rating

**Step 2: Review Status**
- Select: "Yes, it has reviews" or "No reviews"
- Determines next field (sentiment spread vs similar products)

**Step 3a: Sentiment Spread** (if has reviews)
- Adjust sliders: Good (%), Neutral (%), Bad (%)
- Must total 100%
- Determines mock review distribution

**Step 3b: Similar Products** (if no reviews)
- Select: "Yes" or "No"
- Determines if similar products generated

**Step 4: User Persona**
- Auto-generated with diverse demographics
- Click "Regenerate" for new persona (alternates gender)
- Contains: Name, Email, Age, Gender, Location

**Step 5: Purchase History**
- Has purchase history? "Yes" or "No"
- Bought exact product? "Yes" or "No"
- Submit → Generates mock data

### 2. Mock Data Generation

**What Gets Created:**
- Main product + similar products (if applicable)
- Main user + 20-100 mock users
- Purchase transactions with realistic dates
- Product reviews with sentiment distribution
- All data inserted into Supabase

**Data Summary Displayed:**
- Product count
- User count
- Transaction count
- Review count
- Scenario description

### 3. Survey Execution

**Start Survey:**
- Click "Start Survey" button
- Backend invokes ProductContext and CustomerContext agents
- First question generated and displayed

**Answer Questions:**
- Read question
- Select from multiple choice options
- Click "Submit Answer"
- Next question appears (3-7 questions total)

**Survey Completion:**
- After final question, survey marked complete
- "Generate Reviews" button appears

### 4. Review Generation

**Generate Options:**
- Click "Generate Reviews"
- ReviewGenAgent creates 3 review alternatives
- Each review includes: title, text, star rating, tone

**Review Display:**
- Overall sentiment indicator (Good/Okay/Bad)
- 3 review cards with different tones:
  - Enthusiastic (usually 4-5 stars)
  - Balanced (usually 3-4 stars)
  - Critical (usually 2-3 stars)

**Select and Submit:**
- Click "Select This Review" on preferred option
- Review saved to database with source='user_survey'
- Success message displayed

## API Endpoints

### POST /api/scrape

Scrapes Amazon product data.

**Request:**
```json
{
  "url": "https://www.amazon.com/dp/B0DCJ5NMV2"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://...",
    "title": "Product Name",
    "price": 279.99,
    "images": ["url1", "url2"],
    "description": "...",
    "brand": "Brand Name",
    "rating": 4.7,
    "reviewCount": 12847,
    "platform": "amazon"
  }
}
```

### POST /api/mock-data

Generates mock data for testing.

**Request:** Complete form data object

**Response:**
```json
{
  "success": true,
  "summary": {
    "products": 6,
    "users": 53,
    "transactions": 78,
    "reviews": 45,
    "scenario": "Product has 45 reviews with 60% positive..."
  }
}
```

### POST /api/generate-persona

Generates diverse user persona.

**Request:**
```json
{
  "lastGender": "Female"
}
```

**Response:**
```json
{
  "success": true,
  "persona": {
    "name": "Hiroshi Tanaka",
    "email": "hiroshi.tanaka.8234@example.com",
    "age": 42,
    "city": "Seattle",
    "state": "Washington",
    "zip": "98101",
    "gender": "Male",
    "location": "Seattle, Washington"
  }
}
```

**Features:**
- 48 diverse names (24 male, 24 female)
- Round-robin gender alternation on "Regenerate"
- Names from USA, India, China, Middle East, Japan, Europe, Latin America

## Key Features

### Diverse User Personas

**48 Curated Names:**
- Equal male/female distribution (24 each)
- Multiple ethnicities and cultural backgrounds
- Realistic email generation
- US cities and ZIP codes
- Age range: 18-75

**Round-Robin Alternation:**
- First generation: Random gender
- Subsequent regenerations: Alternates gender
- Example: Female → Male → Female → Male

**Implementation:**
```typescript
// Client sends last gender to API
fetch('/api/generate-persona', {
  method: 'POST',
  body: JSON.stringify({ lastGender })
})

// API alternates gender
gender = lastGender === 'Male' ? 'Female' : 'Male'
```

### Amazon Product Scraping

**ASIN Extraction:**
Supports all Amazon URL formats:
```
/dp/ASIN
/gp/product/ASIN
/ASIN/ref=...
?asin=ASIN
amzn.to/ASIN
```

**RapidAPI Integration:**
- Primary: RapidAPI Real-Time Amazon Data API
- Fallback: Direct scraping (may be blocked)
- Mock: Use URL ending with "mock" for instant testing

### Form Validation

**URL Validation:**
- Must be valid URL
- Amazon domain required
- ASIN extracted and verified

**Sentiment Validation:**
- Good + Neutral + Bad must equal 100%
- Real-time total calculation
- Visual feedback (green/yellow/red)

**Email Validation:**
- Valid email format
- Auto-generated from name

**ZIP Validation:**
- 5-digit format
- Auto-generated for personas

## Development Commands

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

# Clean build artifacts
rm -rf .next node_modules
npm install
```

## Testing

### Test Amazon URLs

```
https://www.amazon.com/dp/B0DCJ5NMV2
https://www.amazon.com/dp/B09XS7JWHH
```

### Test with Mock Data

```
http://localhost:3000?url=mock
```

Or enter "mock" in the product URL field.

### Verify Database

After form submission:

```sql
-- Check inserted data
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM reviews;

-- Check main user
SELECT * FROM users WHERE is_main_user = true ORDER BY created_at DESC LIMIT 1;

-- Check main product
SELECT * FROM products WHERE is_mock = false ORDER BY created_at DESC LIMIT 1;
```

## Troubleshooting

### Build Errors

```bash
rm -rf node_modules .next
npm install
npm run dev
```

### Type Errors

```bash
npm run type-check
```

Fix errors shown, then rebuild.

### RapidAPI Not Working

1. Verify `RAPIDAPI_KEY` in `.env.local`
2. Check API key at [RapidAPI Dashboard](https://rapidapi.com/developer/apps)
3. Ensure free tier limits not exceeded (100 requests/month)
4. Restart dev server: `npm run dev`

### Product Scraping Fails

1. Try mock URL: enter "mock" in product field
2. Check Amazon URL format (must contain ASIN)
3. Verify RapidAPI key configured
4. Check browser console for error details (F12)

### Port 3000 in Use

**Windows:**
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
lsof -ti:3000 | xargs kill -9
```

**Or use different port:**
```bash
npm run dev -- -p 3001
```

### Environment Variables Not Loading

1. Ensure `.env.local` exists in frontend directory
2. Restart dev server completely
3. Check file name (must be exactly `.env.local`)
4. Verify no spaces in variable names

### Persona Generation Stuck

1. Check OpenAI API key in `.env.local`
2. Verify API key valid at [OpenAI Platform](https://platform.openai.com/api-keys)
3. Fallback will activate if API fails (uses local name list)

## Design System

### Colors

```css
/* Primary (Blue) */
--primary-600: #0284c7
--primary-900: #0c4a6e

/* Status */
--success: #10b981 (Green)
--warning: #f59e0b (Yellow)
--error: #ef4444 (Red)

/* Sentiment */
--good: #10b981 (Green)
--neutral: #f59e0b (Yellow)
--bad: #ef4444 (Red)
```

### Components

**Buttons:**
```css
.btn-primary     /* Blue background, white text */
.btn-secondary   /* Gray background, gray text */
```

**Inputs:**
```css
.input           /* White background, gray border */
```

**Cards:**
```css
.card            /* White background, shadow, rounded */
```

### Animations

```css
/* Fade in */
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide in */
@keyframes slide-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Amazon scrape (RapidAPI) | 1-3s | Faster than direct scraping |
| Mock data generation | 2-5s | Depends on data volume |
| Persona generation | 1-2s | OpenAI API call |
| UI transitions | 0.5s | Smooth animations |

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Supabase JS Client](https://supabase.com/docs/reference/javascript)

---

**Frontend Version**: 1.0.0
**Framework**: Next.js 14.2+
**Status**: Production Ready
