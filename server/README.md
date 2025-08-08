# Server (FastAPI) — Streaming SSE
Run:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add OPENAI_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Endpoints:
- `GET /api/stream?ticker=NVDA&sites=site:sec.gov,site:investor.apple.com` (SSE)
- `GET /api/health`
