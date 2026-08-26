"""
Loading .env here, at the top of the app package's __init__, guarantees it
runs before any submodule that reads an environment variable at import time
(e.g. app.auth.security reads JWT_SECRET_KEY at module load) - regardless of
which script or entry point (uvicorn, a scripts/*.py CLI tool, a test) is
the first to import something from app.*.
"""
from dotenv import load_dotenv

load_dotenv()
