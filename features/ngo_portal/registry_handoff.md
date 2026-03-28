# NGO Portal — Integration Guide

**Built by:** Antigravity  
**For:** Teammate integrating this into the main Sevafy repo  
**Time to integrate:** ~10 minutes  
**Zero existing files were modified** — this is a clean drop-in.

---

## What you're adding

| What | Where it goes |
|---|---|
| NGO dashboard page | `src/pages/NGODashboard.jsx` |
| Dashboard styles | `src/pages/NGODashboard.module.css` |
| 12-stage progress tracker component | `src/components/ProgressTracker.jsx` |
| Progress tracker styles | `src/components/ProgressTracker.module.css` |
| Backend API router | `backend/app/ngo_router.py` |

The dashboard shows:
- **Incoming donations** for the NGO (live from DB, with fallback to demo data)
- **Scholarship pipeline** — all applications linked to this NGO's schemes
- **12-stage progress tracker** — click any scholarship to see the full lifecycle
- **AI Impact Rating** — weighted score (1–5) based on utilization, scale, and quality

NGO accounts cannot self-register — they must be seeded via `backend/seed_ngos.py` or `backend/seed_db.py`.

---

## Step 1 — Copy the files

From the repo root, run these 5 copy commands:

```powershell
Copy-Item features\ngo_portal\backend\ngo_router.py backend\app\ngo_router.py
Copy-Item features\ngo_portal\frontend\NGODashboard.jsx src\pages\NGODashboard.jsx
Copy-Item features\ngo_portal\frontend\NGODashboard.module.css src\pages\NGODashboard.module.css
Copy-Item features\ngo_portal\frontend\components\ProgressTracker.jsx src\components\ProgressTracker.jsx
Copy-Item features\ngo_portal\frontend\components\ProgressTracker.module.css src\components\ProgressTracker.module.css
```

---

## Step 2 — Update `backend/app/ngo_router.py`

After copying, open `backend/app/ngo_router.py` and **replace lines 1–10** (the docstring/comment block at the top) with the real imports:

**Delete this block at the top of the file:**
```python
"""
╔══════════════════════════════════════════════════════════════════╗
║  SEVAFY — NGO Portal API Router                                  ║
...
╚══════════════════════════════════════════════════════════════════╝
"""
```

**Add these imports right after the existing imports** (after `import uuid as uuid_module`):
```python
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db
```

Then **find these 3 endpoint stubs** and replace each one's signature and body:

### `/ngo/stats`
Find:
```python
@router.get("/stats", response_model=NGOStatsResponse)
def get_ngo_stats(
    # These are imported at integration time — see registry_handoff.md
    # current_user: models.User = Depends(auth.get_current_user),
    # db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=501,
        detail="Integration pending..."
    )
```
Replace with:
```python
@router.get("/stats", response_model=NGOStatsResponse)
def get_ngo_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return get_ngo_stats_live(current_user, db)
```

### `/ngo/donations`
Find:
```python
@router.get("/donations", response_model=List[DonationRecord])
def get_incoming_donations(current_user=None, db=None):
```
Replace with:
```python
@router.get("/donations", response_model=List[DonationRecord])
def get_incoming_donations(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
```

### `/ngo/scholarships`
Find:
```python
@router.get("/scholarships", response_model=List[ScholarshipSummary])
def get_ongoing_scholarships(current_user=None, db=None):
```
Replace with:
```python
@router.get("/scholarships", response_model=List[ScholarshipSummary])
def get_ongoing_scholarships(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
```

### `/ngo/scholarships/{application_id}`
Find:
```python
@router.get("/scholarships/{application_id}", response_model=ScholarshipDetailResponse)
def get_scholarship_detail(application_id: str, current_user=None, db=None):
```
Replace with:
```python
@router.get("/scholarships/{application_id}", response_model=ScholarshipDetailResponse)
def get_scholarship_detail(
    application_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
```

---

## Step 3 — Mount the router in `backend/app/main.py`

Open `backend/app/main.py`.

**After line 22** (after `from .event_listener import start_event_listener`), add:
```python
from .ngo_router import router as ngo_router
```

**After line 37** (after `app.add_middleware(CORSMiddleware, ...)`), add:
```python
app.include_router(ngo_router, prefix="/api")
```

---

## Step 4 — Add the route and nav link in `src/App.jsx`

Open `src/App.jsx`.

**After line 17** (after `import TransparentLedger from './pages/TransparentLedger';`), add:
```jsx
import NGODashboard from './pages/NGODashboard';
```

**After line 46** (inside the `{user ? ...}` navbar block, after the Dashboard link), add:
```jsx
{user?.role === 'NGO_PERSONNEL' && (
  <Link to="/ngo-portal" className="btn btn-ghost">NGO Portal</Link>
)}
```

**After line 106** (after `<Route path="/ledger" .../>`), add:
```jsx
<Route path="/ngo-portal" element={<NGODashboard />} />
```

---

## Step 5 — Restart both servers

```powershell
# Backend (in /backend with venv active)
uvicorn app.main:app --reload

# Frontend (in repo root)
npm run dev
```

Then open `http://localhost:5173/ngo-portal` — log in as an `NGO_PERSONNEL` user and you're done.

> **Note:** If the `/api/ngo/*` endpoints return errors (e.g. no data seeded yet), the dashboard automatically falls back to rich demo data so the UI always renders. No blank screens.

---

## Verify it worked

1. Open `http://127.0.0.1:8000/docs` in your browser
2. You should see 4 new endpoints under the **NGO Portal** tag:
   - `GET /api/ngo/stats`
   - `GET /api/ngo/donations`
   - `GET /api/ngo/scholarships`
   - `GET /api/ngo/scholarships/{application_id}`
3. Navigate to `/ngo-portal` in the frontend — you should see the dashboard

---

## Blocking NGO self-registration

Open `src/pages/Register.jsx` and find **line 71**:
```jsx
<option value="NGO_PERSONNEL">NGO Representative</option>
```
Delete or comment out that line. NGO accounts are provisioned by admins only via `backend/seed_ngos.py`.

---

## How the AI Impact Rating works

Score is 1.0–5.0, computed in `ngo_router.py → calculate_impact_rating()`:

| Component | Weight | How it's measured |
|---|---|---|
| Fund Utilization | 40% | `total_disbursed ÷ net_funding` |
| Scale | 30% | Log-normalized count of APPROVED applications |
| Per-student quality | 20% | `avg_amount_per_student ÷ ₹50,000` |
| Fund mobilization | 10% | `net_funding ÷ ₹1 crore` |

**Rating tiers:** 💎 Platinum (≥4.5) · 🏆 Gold (≥3.5) · 🥈 Silver (≥2.5) · 🥉 Bronze (≥1.5) · 🌱 Emerging (<1.5)
