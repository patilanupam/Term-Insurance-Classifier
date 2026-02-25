<div align="center">

# 🛡️ Term Insurance Classifier

### AI-powered term insurance comparison & recommendation engine for India

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-7.x-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.x-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Gemini](https://img.shields.io/badge/Gemini_AI-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com)

</div>

---

## 📖 What Is This?

> **Analogy:** Think of this as a **smart insurance broker** who works 24/7.  
> - Every day it visits comparison websites and collects the latest plan data.  
> - When you tell it your age, budget and coverage needs, it hands all that data to a financial expert (Gemini AI).  
> - The expert reads everything, ranks the plans from best to worst *specifically for you*, and explains the reasoning in plain English.

---

## 🗂️ Project Structure

```
term_insurance_Classifier/
│
├── 🐍 backend/                    ← Python (FastAPI) server
│   ├── main.py                    ← API routes (entry point)
│   ├── database.py                ← Database models & connection
│   ├── gemini_Classifier.py         ← Google Gemini AI integration
│   ├── requirements.txt           ← Python dependencies
│   ├── .env                       ← 🔑 Your Gemini API key (not committed)
│   ├── .env.example               ← Template for .env
│   └── scraper/
│       ├── bankbazaar.py          ← ✅ Primary scraper (reliable HTML)
│       ├── policybazaar.py        ← Optional scraper (may be blocked)
│       ├── insurancedekho.py      ← Optional scraper (may be blocked)
│       ├── scheduler.py           ← Auto-refresh every 24 hours
│       └── seed_data.py           ← 10 fallback plans (always available)
│
└── ⚛️  frontend/                   ← React (Vite) web app
    └── src/
        ├── App.jsx                ← Root component + tab navigation
        └── components/
            ├── UserInputForm.jsx  ← Age, budget, CSR slider form
            ├── AIRecommendation.jsx ← Gemini result banner
            ├── PlanCard.jsx       ← Individual plan result card
            ├── ManagePlans.jsx    ← Plan table with add/edit/delete
            └── PlanFormModal.jsx  ← Add/edit plan modal form
```

---

## 🏗️ Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              React Frontend  (port 5173)                │   │
│  │                                                         │   │
│  │  [🔍 Classifier Tab]          [📋 Manage Plans Tab]       │   │
│  │   UserInputForm               ManagePlans               │   │
│  │       ↓                      (add/edit/delete)          │   │
│  │   AIRecommendation                                       │   │
│  │   PlanCard × N                                          │   │
│  └──────────────────┬──────────────────────────────────────┘   │
└─────────────────────│───────────────────────────────────────────┘
                      │  HTTP (proxied by Vite dev server)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend  (port 8000)                  │
│                                                                 │
│   POST /api/recommend ──→ gemini_Classifier.py ──→ Gemini AI ─┐  │
│   GET  /api/plans     ──→ database.py (SQLite)               │  │
│   POST /api/plans     ──→ Create plan manually               │  │
│   PUT  /api/plans/:id ──→ Update plan                        │  │
│   DELETE /api/plans/:id → Delete plan                        │  │
│   POST /api/scrape    ──→ run_scrape_job() [background]      │  │
│                                                 ↓            │  │
│                                          Ranked JSON ◄───────┘  │
│                                                                 │
│   ┌──────────────────────────────────────────────────┐         │
│   │           APScheduler (every 24h)                │         │
│   │   bankbazaar.py ──→ requests + BeautifulSoup     │         │
│   │   policybazaar.py ──→ Playwright (optional)      │         │
│   │   insurancedekho.py ──→ Playwright (optional)   │         │
│   │         ↓ upsert                                 │         │
│   │   SQLite DB (insurance.db)                       │         │
│   └──────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Google Gemini 2.5 Flash                       │
│                                                                 │
│   Input:  user profile + list of eligible plans (JSON)         │
│   Output: ranked plans with scores, pros/cons, summary         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 How a Recommendation Is Generated (Step by Step)

```
Step 1: User fills form
        Age=30, Cover=₹1Cr, Budget=₹12,000/yr, Term=30yr, CSR≥97%
                    ↓
Step 2: Frontend sends POST /api/recommend
                    ↓
Step 3: Backend loads all plans from SQLite DB
                    ↓
Step 4: Filter plans where age_min ≤ 30 ≤ age_max
                    ↓
Step 5: Build Gemini prompt:
        "Given these 10 plans and a user aged 30 wanting ₹1Cr cover
         with ₹12k budget... rank them and explain."
                    ↓
Step 6: Gemini returns structured JSON with:
        - overall_summary
        - top_pick
        - ranked_plans[] with score, reason, pros, cons
                    ↓
Step 7: Frontend renders AIRecommendation + PlanCard for each plan
```

---

## 🕷️ How Scraping Works

```
Scraper Priority Order:
─────────────────────────────────────────────────────────────
1️⃣  BankBazaar (PRIMARY — always works)
    └── Plain HTTP request → BeautifulSoup parses HTML table
    └── Extracts: provider, plan name, CSR% live from the page
    └── No browser needed, no JavaScript execution

2️⃣  PolicyBazaar (OPTIONAL — often blocked by anti-bot)
    └── Playwright headless Chromium → waits for JS to load
    └── Extracts plan cards from DOM

3️⃣  InsuranceDekho (OPTIONAL — often blocked by anti-bot)
    └── Same Playwright approach

4️⃣  Seed Data (FALLBACK — always guaranteed)
    └── 10 hardcoded real plans always loaded on first startup
    └── Used if all scrapers fail
─────────────────────────────────────────────────────────────
```

> 💡 **Why BankBazaar?** PolicyBazaar and InsuranceDekho render their pages
> with React/JavaScript in the browser — there's no plan data in the raw HTML.
> BankBazaar uses server-side rendering, so the plan comparison table comes
> back in plain HTML that any HTTP client can read.

---

## 🧠 Gemini AI Integration

```python
# What we send to Gemini (simplified):
{
  "user": { "age": 30, "sum_assured": 100, "premium_budget": 12000, ... },
  "plans": [
    { "plan_name": "Smart Secure Plus", "provider": "Max Life",
      "claim_settlement_ratio": 99.65, "premium_annual": 8100, ... },
    ...
  ]
}

# What Gemini returns:
{
  "overall_summary": "Max Life Smart Secure Plus is ideal for...",
  "top_pick": "Smart Secure Plus by Max Life",
  "ranked_plans": [
    { "rank": 1, "score": 96, "pros": [...], "cons": [...], "reason": "..." },
    ...
  ]
}
```

> 🤖 **Model fallback chain:** If one model hits quota, the Classifier
> automatically tries: `gemini-2.5-flash-lite` → `gemini-2.5-flash` →
> `gemini-2.0-flash` → `gemini-flash-latest` → rule-based ranking

---

## 🗄️ Database Schema

```sql
TABLE insurance_plans
─────────────────────────────────────────────────────────────
 id                    INTEGER  PRIMARY KEY
 plan_name             TEXT     e.g. "Click 2 Protect Super"
 provider              TEXT     e.g. "HDFC Life"
 source                TEXT     "bankbazaar" | "manual" | "seed"
 sum_assured_min       FLOAT    minimum cover in Lakhs (₹)
 sum_assured_max       FLOAT    maximum cover in Lakhs (₹)
 premium_annual        FLOAT    annual premium in ₹ (indicative)
 policy_term_min       INTEGER  minimum policy term in years
 policy_term_max       INTEGER  maximum policy term in years
 age_min               INTEGER  minimum entry age
 age_max               INTEGER  maximum entry age
 claim_settlement_ratio FLOAT   e.g. 99.5 (percentage)
 key_features          TEXT     pipe-separated "F1|F2|F3"
 source_url            TEXT     official plan URL
 scraped_at            DATETIME when this record was last updated
```

---

## 🌐 API Reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | — | Health check |
| `GET` | `/api/plans` | — | List all plans (sorted by CSR) |
| `GET` | `/api/plans/{id}` | — | Get one plan |
| `POST` | `/api/plans` | PlanCreate JSON | ➕ Manually add a plan |
| `PUT` | `/api/plans/{id}` | PlanUpdate JSON | ✏️ Edit a plan |
| `DELETE` | `/api/plans/{id}` | — | 🗑️ Delete a plan |
| `POST` | `/api/recommend` | RecommendRequest JSON | 🤖 AI recommendation |
| `POST` | `/api/scrape` | — | Trigger live scrape |
| `GET` | `/api/stats` | — | DB statistics |

**Interactive docs:** http://localhost:8000/docs *(Swagger UI)*

### RecommendRequest body:
```json
{
  "age": 30,
  "sum_assured": 100,
  "premium_budget": 12000,
  "policy_term": 30,
  "min_csr": 97.0
}
```

---

## 🛠️ Tech Stack — Why Each Was Chosen

| Layer | Tool | Why |
|-------|------|-----|
| 🐍 API Server | **FastAPI** | Automatic Swagger docs, async support, Pydantic validation |
| 🗄️ Database | **SQLite + SQLAlchemy** | Zero setup, file-based, perfect for this scale |
| 🕷️ Scraping | **requests + BeautifulSoup** | Fast, no browser needed for server-rendered pages |
| 🤖 Browser Scraping | **Playwright** | Handles JS-heavy sites like PolicyBazaar |
| ⏰ Scheduler | **APScheduler** | In-process background jobs, no Redis/Celery needed |
| 🧠 AI | **Google Gemini 2.5 Flash** | Fast, low-cost, excellent at structured JSON output |
| ⚛️ Frontend | **React + Vite** | Fast HMR dev experience, component reusability |
| 🎨 Styling | **Tailwind CSS** | Utility-first, no custom CSS files needed |

---

## 🚀 Setup & Run (Step by Step)

### Prerequisites

- 🐍 [Python 3.9+](https://python.org/downloads/)
- 🟢 [Node.js 18+](https://nodejs.org/)
- 🔑 [Gemini API Key](https://aistudio.google.com/app/apikey) *(free)*

---

### Step 1 — Clone / open the project

```powershell
cd "C:\path\to\term_insurance_Classifier"
```

---

### Step 2 — Backend setup

```powershell
cd backend

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser (for optional scrapers)
playwright install chromium
```

Add your Gemini key to `backend/.env`:
```
GEMINI_API_KEY=AIza...your_key_here
```

Start the backend:
```powershell
python -m uvicorn main:app --port 8000 --reload
```

✅ You'll see: `Uvicorn running on http://127.0.0.1:8000`

---

### Step 3 — Frontend setup

Open a **second PowerShell window**:

```powershell
cd frontend
npm install
npm run dev
```

✅ You'll see: `Local: http://localhost:5173/`

---

### Step 4 — Open the app

👉 Open **http://localhost:5173** in your browser.

---

## 📱 UI Walkthrough

```
┌─────────────────────────────────────────────────────┐
│  🛡️ Term Insurance Classifier        [↺ Refresh Plans] │
│  ─────────────────────────────────────────────────  │
│  [🔍 Classifier]  [📋 Manage Plans]                   │
└─────────────────────────────────────────────────────┘

🔍 Classifier TAB
───────────────
  ┌──────────────────────────────────────────────────┐
  │  Age: [30]    Sum Assured (L): [100]             │
  │  Premium Budget (₹): [12000]   Term: [30]        │
  │  Min CSR: ━━━━━━●━━━━━━ 97%                      │
  │                                                  │
  │         [ 🔍 Find Best Plans for Me ]            │
  └──────────────────────────────────────────────────┘
                        ↓ (after submit)
  ┌──────────────────────────────────────────────────┐
  │  🏆 Gemini AI Recommendation                    │
  │  10 plans analyzed                               │
  │  Top Pick: Smart Secure Plus by Max Life         │
  │  "Max Life's Smart Secure Plus stands out..."    │
  └──────────────────────────────────────────────────┘

  ┌─────────────────┐  ┌─────────────────┐
  │ 🥇 Smart Secure │  │ 🥈 Click 2      │
  │    Plus         │  │    Protect      │
  │ Score: 96/100   │  │ Score: 91/100   │
  │ ✓ Within Budget │  │ ✓ Within Budget │
  │ CSR: 99.65%     │  │ CSR: 99.5%      │
  │ Pros: ...       │  │ Pros: ...       │
  └─────────────────┘  └─────────────────┘

📋 MANAGE PLANS TAB
────────────────────
  Provider          Plan          Premium  CSR    Actions
  ─────────────────────────────────────────────────────
  HDFC Life       Click 2...    ₹9,200   99.5%  Edit Delete
  Max Life        Smart...      ₹8,100   99.65% Edit Delete
  ...
  [+ Add Plan]  ← opens a modal form for manual entry
```

---

## 🔧 Common Issues & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `Gemini model not found` | Old model name | Auto-fixed — app tries 6 models in order |
| `429 quota exceeded` | Free tier limit | App falls back to next model automatically |
| `NotImplementedError` (Playwright) | Windows asyncio issue | Fixed — uses `ProactorEventLoop` in threads |
| `Port 8000 in use` | Old process running | `netstat -ano \| findstr :8000` then `Stop-Process -Id <PID>` |
| `Cannot reach localhost:5173` | Frontend not started | Run `npm run dev` in `frontend/` folder |
| PolicyBazaar/InsuranceDekho blocked | Anti-bot protection | Expected — BankBazaar is the primary source |

---

## 🧩 How to Extend This Project

### Add a new scraper source
1. Create `backend/scraper/newsite.py`
2. Write a `scrape_newsite() -> List[Dict]` function returning plan dicts
3. Import and call it in `backend/scraper/scheduler.py`

### Add a new field to plans
1. Add the column to `InsurancePlan` in `database.py`
2. Delete `insurance.db` to recreate schema (or use Alembic for migrations)
3. Update `PlanCreate`/`PlanUpdate` schemas in `main.py`
4. Update `PlanFormModal.jsx` to add the new input field

### Change the AI model
Edit `backend/gemini_Classifier.py`:
```python
_model = genai.GenerativeModel("gemini-2.5-flash")  # or any model you prefer
```

### Change scrape frequency
Edit `backend/scraper/scheduler.py`:
```python
scheduler.add_job(run_scrape_job, trigger="interval", hours=12)  # every 12h
```

---

## 📦 Dependencies

### Backend (`requirements.txt`)
```
fastapi          — Web framework & API routing
uvicorn          — ASGI server to run FastAPI
sqlalchemy       — ORM for database operations
playwright       — Headless browser for JS-heavy sites
beautifulsoup4   — HTML parsing for server-rendered pages
requests         — Plain HTTP client for BankBazaar
apscheduler      — Background job scheduler
google-generativeai — Gemini AI SDK
python-dotenv    — Load .env file into environment
pydantic         — Data validation for API request/response
```

### Frontend
```
react            — UI component library
vite             — Build tool & dev server
tailwindcss      — Utility-first CSS framework
```

---

<div align="center">

Made using **FastAPI** + **React** + **Gemini AI**

</div>
