# Fire Safety Regulations — Next.js Dashboard

A third frontend for the version-comparison engine, alongside the embedded
HTML dashboard (`app/api/dashboard.py`, served at `/ui`) and the standalone
React + Vite app (`web/`). This one is built for eventual deployment on
Vercel and expands on the other two:

- **Multi-page navigation**: a documents overview page, a dedicated
  comparison page per version pair (`/compare/[oldId]/[newId]`), and a
  linkable/bookmarkable clause detail page.
- **Dashboard/overview page** (`/`): lists every ingested document and
  version with clause counts, and comparison shortcuts.
- **Charts**: a change-type breakdown (pie) and a similarity-score
  distribution (histogram) alongside the stat tiles.
- **Export**: CSV download, and PDF via the browser's print dialog (a
  print stylesheet hides the nav/controls so only the results print).

All three frontends talk to the same FastAPI backend (`app/api/main.py`) as
a plain JSON API - nothing in the backend is specific to this frontend.

## Setup

```bash
npm install
npm run dev
```

Opens on http://localhost:3000. Requires the FastAPI backend running
separately on http://localhost:8000 (`uvicorn app.api.main:app --reload`
from the project root). To point at a different backend (e.g. once it's
deployed somewhere Vercel can reach), set `NEXT_PUBLIC_API_BASE_URL` in
`.env.local`.

## Deploying to Vercel

Vercel can host this frontend directly (`vercel --prod` or connect the repo
in the Vercel dashboard, with this folder as the project root). It **cannot**
host the FastAPI backend - Vercel's serverless functions aren't suited to a
stateful Python process with a SQLite database and sentence-transformers
models that take 30-45 seconds per request. Deploy the backend separately
(Render, Railway, Fly.io, or a VPS all work), then set
`NEXT_PUBLIC_API_BASE_URL` in the Vercel project's environment variables to
that backend's public URL.

## Structure

```
lib/
  api.ts       Typed fetch wrappers for /documents, /versions, /compare
  diff.ts       Token-level LCS diff (kept in sync with web/src/lib/diff.js)
  export.ts     CSV export helper
  types.ts      Shared TypeScript types matching the FastAPI response shapes
components/     Header, Controls, StatsGrid, charts, FilterBar, ClauseCard, ExportButtons
app/
  page.tsx                                    Dashboard/overview
  compare/[oldId]/[newId]/page.tsx             Comparison view
  compare/[oldId]/[newId]/clause/[number]/     Clause detail page
```
