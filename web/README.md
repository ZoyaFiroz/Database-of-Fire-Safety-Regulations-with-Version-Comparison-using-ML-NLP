# Fire Safety Regulations — React Dashboard

A separate React + Vite frontend for the version-comparison engine. This
talks to the FastAPI backend (`app/api/main.py`) purely as a JSON API — it
does not replace the existing HTML dashboard served at `/ui` on the backend,
which still works standalone for local hosting.

## Setup

```bash
npm install
npm run dev
```

Opens on http://localhost:5173. Requires the FastAPI backend running
separately on http://localhost:8000 (`uvicorn app.api.main:app --reload`
from the project root) — CORS is already enabled on the backend for this.

To point at a different backend URL, set `VITE_API_BASE_URL` (e.g. in a
`.env.local` file in this folder).

## Structure

```
src/
  lib/api.js        Fetch wrappers for /documents, /versions, /compare
  lib/diff.js        Token-level LCS diff (ported from app/api/dashboard.py)
  components/         Controls, StatsGrid, FilterBar, ClauseCard
  App.jsx             Wires it all together with data-fetching effects
```
