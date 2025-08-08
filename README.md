# AutoGen Stock Analyzer — UI + Streaming

This bundle adds a **FastAPI server** with **SSE streaming** and a **Vite React UI**.

## Run backend
```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Run frontend
```bash
cd web
npm install
npm run dev
# open http://localhost:5173
```

In the UI, enter a ticker and optional sites (comma-separated), click **Analyze**.
You’ll see **streaming**: status → news items → data snapshot → final analyst memo.
