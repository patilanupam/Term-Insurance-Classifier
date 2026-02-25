"""
FastAPI backend for Term Insurance Analyzer.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import init_db, get_db, InsurancePlan
from gemini_analyzer import analyze_plans
from scraper.scheduler import run_scrape_job, start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    init_db()
    run_scrape_job()          # seed + scrape on startup
    scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Term Insurance Analyzer API",
    description="Scrapes term insurance plans and uses Gemini AI to recommend the best plan for you.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PlanOut(BaseModel):
    id: int
    plan_name: str
    provider: str
    source: str
    sum_assured_min: float
    sum_assured_max: float
    premium_annual: float
    policy_term_min: int
    policy_term_max: int
    age_min: int
    age_max: int
    claim_settlement_ratio: float
    key_features: str
    source_url: str

    class Config:
        from_attributes = True


class PlanCreate(BaseModel):
    plan_name: str = Field(..., min_length=2)
    provider: str = Field(..., min_length=2)
    sum_assured_min: float = Field(..., gt=0, description="Min sum assured in Lakhs")
    sum_assured_max: float = Field(..., gt=0, description="Max sum assured in Lakhs")
    premium_annual: float = Field(..., gt=0, description="Annual premium in INR")
    policy_term_min: int = Field(..., ge=1, le=50)
    policy_term_max: int = Field(..., ge=1, le=60)
    age_min: int = Field(18, ge=1, le=99)
    age_max: int = Field(65, ge=1, le=99)
    claim_settlement_ratio: float = Field(..., ge=0, le=100)
    key_features: str = Field("", description="Pipe-separated features e.g. 'Feature 1|Feature 2'")
    source_url: str = Field("", description="Official plan URL")


class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    provider: Optional[str] = None
    sum_assured_min: Optional[float] = None
    sum_assured_max: Optional[float] = None
    premium_annual: Optional[float] = None
    policy_term_min: Optional[int] = None
    policy_term_max: Optional[int] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    claim_settlement_ratio: Optional[float] = None
    key_features: Optional[str] = None
    source_url: Optional[str] = None



class RecommendRequest(BaseModel):
    age: int = Field(..., ge=18, le=70, description="User's current age")
    sum_assured: float = Field(..., gt=0, description="Desired sum assured in Lakhs")
    premium_budget: float = Field(..., gt=0, description="Max annual premium in INR")
    policy_term: int = Field(..., ge=5, le=50, description="Desired policy term in years")
    min_csr: float = Field(95.0, ge=0, le=100, description="Minimum claim settlement ratio %")


class RecommendResponse(BaseModel):
    overall_summary: str
    top_pick: str
    ranked_plans: list
    total_plans_analyzed: int


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Term Insurance Analyzer API is running"}


@app.get("/api/plans", response_model=List[PlanOut])
def get_plans(
    source: Optional[str] = None,
    min_csr: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """List all stored insurance plans with optional filters."""
    query = db.query(InsurancePlan)
    if source:
        query = query.filter(InsurancePlan.source == source)
    if min_csr is not None:
        query = query.filter(InsurancePlan.claim_settlement_ratio >= min_csr)
    plans = query.order_by(InsurancePlan.claim_settlement_ratio.desc()).all()
    return plans


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    """Analyze plans for the given user profile using Gemini AI."""
    plans = db.query(InsurancePlan).all()
    if not plans:
        raise HTTPException(
            status_code=404,
            detail="No plans in database. Trigger /api/scrape first.",
        )

    # Serialize plans to dicts for the analyzer
    plans_data = [
        {
            "plan_name": p.plan_name,
            "provider": p.provider,
            "source": p.source,
            "sum_assured_min": p.sum_assured_min,
            "sum_assured_max": p.sum_assured_max,
            "premium_annual": p.premium_annual,
            "policy_term_min": p.policy_term_min,
            "policy_term_max": p.policy_term_max,
            "age_min": p.age_min,
            "age_max": p.age_max,
            "claim_settlement_ratio": p.claim_settlement_ratio,
            "key_features": p.key_features,
        }
        for p in plans
    ]

    result = analyze_plans(req.model_dump(), plans_data)

    return RecommendResponse(
        overall_summary=result.get("overall_summary", ""),
        top_pick=result.get("top_pick", ""),
        ranked_plans=result.get("ranked_plans", []),
        total_plans_analyzed=len(plans_data),
    )


@app.post("/api/scrape")
def trigger_scrape(background_tasks: BackgroundTasks):
    """Manually trigger a fresh scrape in the background."""
    background_tasks.add_task(run_scrape_job)
    return {"message": "Scrape job started in background. Check /api/plans in ~30s."}


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    """Return DB statistics."""
    total = db.query(InsurancePlan).count()
    sources = (
        db.query(InsurancePlan.source, db.query(InsurancePlan).filter(
            InsurancePlan.source == InsurancePlan.source).count())
        .distinct()
        .all()
    )
    return {
        "total_plans": total,
        "sources": [s[0] for s in sources],
    }


# ── Manual CRUD endpoints ─────────────────────────────────────────────────────

@app.post("/api/plans", response_model=PlanOut, status_code=201)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    """Manually add a new insurance plan."""
    new_plan = InsurancePlan(**plan.model_dump(), source="manual")
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


@app.put("/api/plans/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, updates: PlanUpdate, db: Session = Depends(get_db)):
    """Update an existing insurance plan."""
    plan = db.query(InsurancePlan).filter(InsurancePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


@app.delete("/api/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete an insurance plan."""
    plan = db.query(InsurancePlan).filter(InsurancePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"message": f"Plan '{plan.plan_name}' deleted successfully"}


@app.get("/api/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a single plan by ID."""
    plan = db.query(InsurancePlan).filter(InsurancePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


# ── Serve built React frontend (production) ───────────────────────────────────

_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="static")
