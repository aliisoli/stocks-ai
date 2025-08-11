
import os, json
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse, Response
from dotenv import load_dotenv
import logging

# Load environment variables first, before any other imports
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.agents import analyze_once

app = FastAPI(title="AutoGen Stock Analyzer (Streaming)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sse_pack(event: str, data: dict) -> bytes:
    payload = json.dumps({"event": event, "data": data}, ensure_ascii=False)
    return f"data: {payload}\n\n".encode("utf-8")

@app.get("/api/stream")
def stream(ticker: str, sites: Optional[str] = Query(default=None, description="Comma-separated sites")):
    logger.info(f"Starting stream analysis for ticker: {ticker}")
    
    # Use default sites if none provided (since frontend no longer sends sites)
    if sites:
        site_list = [s.strip() for s in sites.split(",")]
    else:
        # Default to reliable financial sources
        site_list = ["sec.gov", "investor.gov", "finance.yahoo.com", "marketwatch.com"]
    
    def gen():
        try:
            yield sse_pack("status", {"message": f"Starting analysis for {ticker}"})
            
            # Search
            logger.info("Starting search phase")
            yield sse_pack("status", {"message": "Searching recent filings/news..."})
            
            news, data, report = analyze_once(ticker, site_list)
            
            # Stream chunks
            logger.info(f"Found {len(news or [])} news items")
            for i, item in enumerate(news or []):
                yield sse_pack("news", item)
            
            yield sse_pack("status", {"message": "Fetched market data"})
            yield sse_pack("data_summary", data.get("summary", {}))
            
            # Final
            logger.info("Generating final report")
            yield sse_pack("report", {"markdown": report})
            yield sse_pack("done", {"ok": True})
            
            # Properly terminate the SSE stream
            logger.info(f"Analysis completed for {ticker} - terminating stream")
            
        except Exception as e:
            logger.error(f"Error in stream analysis: {str(e)}", exc_info=True)
            yield sse_pack("error", {"message": str(e)})
    
    return StreamingResponse(
        gen(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering if behind proxy
        }
    )

@app.get("/api/health")
def health():
    return JSONResponse({"ok": True})

@app.get("/")
def root():
    return JSONResponse({"message": "AutoGen Stock Analyzer API", "status": "running"})
