# Backend image for the FastAPI service - built for Hugging Face Spaces
# (Docker SDK), which expects the app to listen on port 7860. The Next.js
# frontend (nextjs/) is deployed separately on Vercel and talks to this
# container over HTTP (NEXT_PUBLIC_API_BASE_URL) - it is not part of this
# image.
FROM python:3.11-slim

# tesseract-ocr-spa adds Spanish language data for the OCR fallback in
# app/ingestion/generic_extractor.py, matching this project's multilingual
# comparison feature. Installed via apt at the default system paths, so
# none of TESSERACT_CMD / TESSDATA_PREFIX need to be set here - only local
# Windows dev needs those (see .env.example).
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY Data/*.pdf ./Data/

# Bake the fixed UK Approved Document B regulation content into the image at
# build time. Free container hosts don't guarantee a persistent disk, so
# anything written at runtime (user accounts, custom document uploads) can
# be lost on restart - but this seed data survives every restart because
# it's part of the image itself, not the writable runtime layer.
RUN python scripts/ingest.py \
      --document "Approved Document B, Volume 1: Dwellings" \
      --label "2019 edition" \
      --pdf "Data/Approved_Document_B__fire_safety__volume_1_-_Dwellings__2019_edition.pdf" && \
    python scripts/ingest.py \
      --document "Approved Document B, Volume 1: Dwellings" \
      --label "2019 + 2020 amendments" \
      --pdf "Data/Approved_Document_B__fire_safety__volume_1_Dwellings__2019_edition_incorporating_2020_amendments.pdf" && \
    python scripts/ingest.py \
      --document "Approved Document B, Volume 1: Dwellings" \
      --label "2019 + 2020 and 2022 amendments" \
      --pdf "Data/Approved_Document_B__fire_safety__volume_1_-_Dwellings__2019_edition_incorporating_2020_and_2022_amendments.pdf" && \
    python scripts/ingest.py \
      --document "Approved Document B, Volume 2: Buildings other than dwellings" \
      --label "2019 edition" \
      --pdf "Data/Approved_Document_B__fire_safety__volume_2_-_Buildings_other_than_dwellings__2019_edition.pdf" && \
    python scripts/ingest.py \
      --document "Approved Document B, Volume 2: Buildings other than dwellings" \
      --label "2019 + 2020 and 2022 amendments" \
      --pdf "Data/Approved_Document_B__fire_safety__volume_2_-_Buildings_other_than_dwellings__2019_edition_incorporating_2020_and_2022_amendments.pdf"

# Hugging Face Spaces runs containers as a non-root user by convention;
# give that user write access to /app since the SQLite file at
# /app/fire_regs.db gets written to at runtime (registrations, uploads).
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
