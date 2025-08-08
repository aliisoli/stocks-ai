import os, requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def web_search_perplexity(ticker: str, max_results: int = 6) -> List[Dict[str, Any]]:
    """
    Search for financial news about a specific stock ticker using Perplexity API
    """
    key = os.getenv("PERPLEXITY_API_KEY")
    if not key:
        logger.warning("PERPLEXITY_API_KEY not found. Using fallback data.")
        return get_fallback_news(ticker, max_results)
    
    try:
        # Create a focused query for financial news about the ticker
        query = f"Recent financial news and market updates about {ticker} stock"
        logger.info(f"Searching for financial news about: {ticker}")
        
        # Simple request payload
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial news assistant. Provide recent news and updates about the requested stock."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }
        
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        # Make API request
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Handle errors
        if resp.status_code == 400:
            logger.error(f"Bad Request Error. Response: {resp.text}")
            return get_fallback_news(ticker, max_results)
        elif resp.status_code == 401:
            logger.error("Authentication Error. Check your PERPLEXITY_API_KEY")
            return get_fallback_news(ticker, max_results)
        elif resp.status_code == 429:
            logger.error("Rate limit exceeded. Please try again later.")
            return get_fallback_news(ticker, max_results)
        
        resp.raise_for_status()
        
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        
        # Create a simple result with the response content (safely truncated if extremely long)
        snippet = (content or f"Recent financial information about {ticker}").strip()
        if len(snippet) > 2000:
            cutoff = snippet.rfind(" ", 0, 2000)
            if cutoff == -1:
                cutoff = 2000
            snippet = snippet[:cutoff].rstrip() + "…"
        
        results = [{
            "title": f"Financial News for {ticker}",
            "url": "",
            "snippet": snippet
        }]
        
        logger.info(f"Retrieved financial news for {ticker}")
        return results
        
    except requests.exceptions.Timeout:
        logger.error("Request timeout. Using fallback news.")
        return get_fallback_news(ticker, max_results)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return get_fallback_news(ticker, max_results)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return get_fallback_news(ticker, max_results)

def get_fallback_news(ticker: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Generate fallback news data when API is unavailable
    """
    return [
        {
            "title": f"{ticker} - Recent Earnings Report",
            "url": f"https://finance.yahoo.com/quote/{ticker}",
            "snippet": f"Latest quarterly earnings and financial performance for {ticker}"
        },
        {
            "title": f"{ticker} - Market Analysis",
            "url": f"https://www.marketwatch.com/investing/stock/{ticker.lower()}",
            "snippet": f"Current market analysis and price movements for {ticker}"
        },
        {
            "title": f"{ticker} - Analyst Ratings",
            "url": f"https://www.reuters.com/companies/{ticker}",
            "snippet": f"Analyst recommendations and price targets for {ticker}"
        },
        {
            "title": f"{ticker} - SEC Filings",
            "url": f"https://www.sec.gov/edgar/search/#/q={ticker}",
            "snippet": f"Recent SEC filings and regulatory documents for {ticker}"
        }
    ][:max_results]
