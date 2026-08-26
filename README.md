# Veritext — Frontend

The Next.js UI for the fire-safety regulation comparison engine. This
branch contains only the frontend; the FastAPI backend lives on the
`backend` branch (and in `app/`/`scripts/`/`Data/` on `main`) and is deployed
separately.

Two comparison workflows:
- **UK Safety Regulation Comparison** (`/regulations`, `/compare/[oldId]/[newId]`) -
  fixed clause-numbering schema, structured clause-level diffing across
  ingested versions of Approved Document B.
- **Custom Document Comparison** (`/general-compare`) - upload any two
  documents (PDF or .txt), no fixed schema, aligned by content similarity
  and summarized in plain language with an AI-synthesized report and a
  "connecting threads" similarity view.

Login/signup (`/login`, `/register`) gate a dashboard hub (`/`) that links
into both workflows; a logged-in user can save comparisons, add clause
notes, and export CSV/PDF.

## Setup

```bash
npm install
npm run dev
```

Opens on http://localhost:3000. Requires the FastAPI backend running
separately on http://localhost:8000 (see the `backend` branch). To point at
a different backend (e.g. once it's deployed), set `NEXT_PUBLIC_API_BASE_URL`
in `.env.local`.

## Deploying to Vercel

Import this branch directly - `vercel --prod`, or connect the repo in the
Vercel dashboard and set **Production Branch** to `frontend`. Set
`NEXT_PUBLIC_API_BASE_URL` in the Vercel project's environment variables to
the deployed backend's public URL (e.g. a Hugging Face Space).

## Structure

```
lib/
  api.ts       Typed fetch wrappers for the backend's JSON API
  auth.ts      Token storage/retrieval for the logged-in user
  export.ts    CSV export helper
  types.ts     Shared TypeScript types matching the FastAPI response shapes
components/    Header, AuthProvider, Controls, charts, FilterBar, ClauseCard,
               GeneralChangeCard, ConceptualMatchDiagram, SimilarityHeatmap, ...
app/
  page.tsx                                    Dashboard hub (post-login)
  login/, register/, account/                  Auth pages
  regulations/                                 UK regulation document/version picker
  compare/[oldId]/[newId]/                     Clause-level comparison view
  compare/[oldId]/[newId]/clause/[number]/     Clause detail page
  general-compare/                             Custom document comparison + results
```
