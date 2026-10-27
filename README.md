# FoodBridge

FoodBridge is an open-source hackathon project that connects restaurants and hotels that have **surplus edible food** with **NGOs and community organizations** that can collect it.

> **Status: hackathon prototype.** Donations and claims are real (stored in a database), but there are no user accounts, no NGO verification and no notifications yet. See [Known limitations](#known-limitations). The landing page still shows clearly-labelled demo/target content (for example the "Project Goals" section); no real impact figures or partnerships are claimed.

## How it works

1. A donor fills in the **Donate Food** form (food, description, servings, pickup location, pickup window, contact).
2. The listing is stored by the backend and appears under **Find Food**.
3. An NGO enters its organization name and **claims** a listing. A donation can only be claimed once.
4. The claiming NGO is shown the donor's contact details to arrange pickup. Contact details are never included in the public listing.
5. Listings whose pickup deadline has passed show as `expired` and cannot be claimed.

## Project structure

```
FoodBridge/
├── frontend/   React + Vite single-page app
└── backend/    Python + FastAPI API, SQLite storage, pytest tests
```

## Quick start

You need Python 3 and Node.js with npm. This was developed and tested with Python 3.12 and Node 22; other versions are untested.

### 1. Backend (http://localhost:8000)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:create_app --factory --reload
```

Interactive API docs: http://localhost:8000/docs

The SQLite database file (`backend/foodbridge.db`) is created automatically on first start and is git-ignored.

### 2. Frontend (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

### Configuration

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `FOODBRIDGE_DB_PATH` | backend (environment) | `backend/foodbridge.db` | SQLite file location |
| `FOODBRIDGE_CORS_ORIGINS` | backend (environment) | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated browser origins allowed to call the API |
| `VITE_API_BASE_URL` | frontend (`frontend/.env.local`) | `http://localhost:8000` | Where the frontend finds the API |

The backend reads real environment variables (it does not load `.env` files). See `backend/.env.example` and `frontend/.env.example`; they contain placeholders only. **Never commit real `.env` files.** Anything in a `VITE_*` variable is public in the browser bundle, so never put secrets there.

## API

All bodies are JSON. Timestamps are ISO 8601 in UTC.

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | Liveness check | 200 `{"status":"ok"}` | |
| POST | `/donations` | Create a donation | 201 | 422 validation |
| GET | `/donations` | List donations, newest first. Query: `status` (`available`\|`claimed`\|`expired`), `limit` (1-100, default 50), `offset` | 200 | 422 |
| GET | `/donations/{id}` | Get one donation | 200 | 404, 422 |
| POST | `/donations/{id}/claim` | Claim a donation. Body: `{"claimed_by": "Org name"}` | 200 (includes `donor_contact`) | 404, 409 already claimed or expired, 422 |

**Create a donation**

```bash
curl -X POST http://localhost:8000/donations \
  -H "Content-Type: application/json" \
  -d '{
    "food_name": "Vegetable biryani",
    "description": "Cooked this evening, packed in sealed trays.",
    "servings": 40,
    "location": "12 Example Street, Sample Town",
    "pickup_deadline": "2030-01-01T18:00:00Z",
    "donor_name": "Example Kitchen",
    "donor_contact": "donor@example.com",
    "category": "Prepared Meals"
  }'
```

**Claim it**

```bash
curl -X POST http://localhost:8000/donations/1/claim \
  -H "Content-Type: application/json" \
  -d '{"claimed_by": "Example Community Kitchen"}'
```

**Validation rules**

- `food_name` 1-120 chars, `description` 1-500, `location` 1-200, `donor_name` 1-120 (whitespace is trimmed; blanks rejected)
- `servings`: a whole number from 1 to 100,000
- `pickup_deadline`: must include a timezone, be in the future and within the next 7 days
- `donor_contact`: a valid email address or phone number (it is stored, but never returned by list/get endpoints)
- Unknown fields are rejected

A donation's `status` is `available`, `claimed`, or `expired` (unclaimed and past its deadline; derived, not stored).

## Database

SQLite via Python's standard-library `sqlite3` with parameterised queries. One table, `donations` (schema in `backend/app/db.py`). Claiming is a single atomic `UPDATE ... WHERE status = 'available'`, so two simultaneous claims cannot both succeed.

## Tests

```bash
cd backend && pytest          # API tests (temporary database per test)
cd frontend && npm run build  # production build check
```

The backend suite covers creation, listing, filtering/pagination, validation, retrieval, claiming (including double-claim, expiry and a concurrent-claim race), persistence across restarts and CORS. There are currently no automated frontend tests.

## Known limitations

- **No authentication or accounts.** Anyone can create or claim a donation, and the NGO name is just typed text. "Verified NGO" is a goal, not a feature; nothing is verified yet.
- Donor contact details are revealed to whoever claims, so without authentication they can be obtained by anyone who claims.
- No rate limiting, abuse protection or moderation.
- No notifications (email/SMS) to NGOs or donors, no geo-search or distance matching, and no editing/cancelling of donations.
- The pickup-window options on the donate form are converted to an absolute deadline in the donor's browser time.
- SQLite is suited to a single-server prototype, not a scaled deployment.
- No automated frontend tests.
- Some landing-page copy (for example the Good Samaritan Act notice, which is a US law, and "100% Verified NGOs") predates the backend and has not been reviewed for accuracy.

---

## Original project notes (preserved from the previous README)

The text below is the README content that existed before this change, kept unmodified.

We are building **FoodBridge**, an open-source hackathon project that connects restaurants and hotels with surplus edible food to NGOs and community organizations that can collect and distribute it.

The project is already partially implemented. Your task is to elevate the EXISTING repository to a professional, polished, hackathon-ready standard without breaking working features.

## PHASE 1 — Inspect Before Changing Anything
1. Inspect the complete repository structure, Git branch, working tree, recent commits, and existing README.
2. Identify the frontend framework, backend framework, database, current features, and missing functionality.
3. Run the available tests and identify existing errors.
4. Do not assume a feature exists unless you verify it in the code.
5. Do not overwrite, delete, or rewrite working code unnecessarily.

## PHASE 2 — Professional Repository Quality
Improve the repository where appropriate:
- A polished root README.md with project overview, problem statement, solution, features, architecture, technology stack, setup instructions, testing instructions, screenshots section, and team contributions.
- A clean and accurate project folder structure.
- A useful .gitignore that excludes secrets, environment files, dependencies, caches, and build output.
- A .env.example containing placeholder values only, if environment variables are required.
- Appropriate LICENSE, CONTRIBUTING.md, and CODE_OF_CONDUCT.md files if missing. Never invent contributor details or falsely claim a license has been selected.
- Separate frontend and backend setup instructions.
- Clear API documentation and example requests based on the actual implementation.
- Consistent naming, readable code, useful error messages, and accessible UI.
- Sensible security checks, input validation, and safe handling of configuration.
- Tests for important existing functionality.
- A clear list of known limitations and future improvements.

## PHASE 3 — Product Quality
Review the existing FoodBridge user journey:
1. A restaurant lists surplus edible food.
2. An NGO discovers suitable donations.
3. The NGO requests or accepts a donation.
4. The donation status can be tracked.
5. The application displays verified impact metrics when real data is available.

Improve only what is necessary and feasible. Do not fabricate real NGO partnerships, completed donations, users, impact statistics, or deployment URLs. Do not claim AI functionality exists unless it is implemented and tested.

## PHASE 4 — Safe Engineering Workflow
- Preserve the existing architecture unless there is a clear technical reason to change it.
- Do not replace the application with a newly generated project.
- Do not remove existing features.
- Do not install unnecessary packages.
- Do not expose API keys, credentials, or personal data.
- Do not automatically commit, push, reset, or delete files.
- Inspect Git status before and after making changes.
- Run relevant tests and build checks where possible.
- Fix only issues that can be safely verified.
- Work in small, reviewable milestones.

## PHASE 5 — Report and Wait
First provide:
1. A concise repository audit.
2. The most important problems, ranked by priority.
3. A proposed improvement plan divided into small milestones.

Then implement only the first approved milestone. Show the changed files, explain the changes in beginner-friendly language, report test results honestly, and suggest a meaningful Git commit message.

Wait for my approval before proceeding to the next milestone.
