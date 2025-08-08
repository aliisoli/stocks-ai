
import json, os
from datetime import datetime, timedelta
from typing import Any, Dict, List
import autogen
import yfinance as yf
from .tools.perplexity_search import web_search_perplexity
import logging

logger = logging.getLogger(__name__)

def price_fetch(ticker: str, lookback_days: int = 400) -> Dict[str, Any]:
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=lookback_days)
        df = yf.download(ticker, start=start, end=end, progress=False)
        info = yf.Ticker(ticker).info or {}
        df = df.tail(400).reset_index()
        
        # Convert DataFrame to JSON-serializable format
        ohlc_data = []
        for _, row in df.iterrows():
            row_dict = {}
            for col, val in row.items():
                # Convert any problematic types to strings or basic types
                if hasattr(val, 'isoformat'):  # datetime objects
                    row_dict[str(col)] = val.isoformat()
                elif isinstance(val, (tuple, list)):
                    row_dict[str(col)] = str(val)
                else:
                    row_dict[str(col)] = val
            ohlc_data.append(row_dict)
        
        return {
            "ohlc": ohlc_data,
            "summary": {
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "marketCap": info.get("marketCap"),
                "sector": info.get("sector"),
                "beta": info.get("beta"),
                "longName": info.get("longName") or ticker,
                "currentPrice": info.get("currentPrice"),
                "targetHighPrice": info.get("targetHighPrice"),
                "targetLowPrice": info.get("targetLowPrice"),
                "recommendationKey": info.get("recommendationKey")
            }
        }
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker}: {str(e)}")
        return {
            "ohlc": [],
            "summary": {
                "error": f"Failed to fetch data for {ticker}: {str(e)}"
            }
        }

LLM_CFG = {"config_list":[{"model": "gpt-4o-mini"}]}

SearchAgent = autogen.AssistantAgent(
    name="SearchAgent",
    system_message=("You are a meticulous equity researcher. Use web_search_perplexity(ticker, max_results). Return compact JSON only."),
    llm_config=LLM_CFG,
    function_map={"web_search_perplexity": web_search_perplexity}
)


DataAgent = autogen.AssistantAgent(
    name="DataAgent",
    system_message=(
        "You fetch clean market data and compute simple indicators via price_fetch. "
        "Return JSON only."
    ),
    llm_config=LLM_CFG,
    function_map={"price_fetch": price_fetch}
)

AnalystAgent = autogen.AssistantAgent(
    name="AnalystAgent",
    system_message=(
        "Senior equity analyst. Combine SearchAgent + DataAgent outputs. "
        "Produce a punchy memo with:\n"
        "- Ticker summary (sector, cap, beta)\n"
        "- Signals: 30/120d trend (use OHLC), max drawdown ~12m, quick valuation note (PE)\n"
        "- Top 3 risks (specific), 3 catalysts/monitors, and a one-line stance.\n"
        "Output Markdown only. Be concise and concrete."
    ),
    llm_config=LLM_CFG
)

def generate_analysis_report_with_openai(ticker: str, news_data: list, data: dict) -> str:
    """
    Generate analysis report using OpenAI directly (more reliable than autogen for this case)
    """
    try:
        import openai
        
        # Set API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Using template report.")
            return generate_template_report(ticker, data, news_data)
        
        logger.info(f"Generating AI analysis for {ticker}")
        
        # Prepare data summaries
        data_summary = json.dumps(data, indent=2, default=str)[:4000]
        news_summary = json.dumps(news_data, indent=2, default=str)[:4000]
        
        prompt = f"""
Synthesize a professional equity analysis memo for {ticker} using the provided data.

Structure your analysis as follows:
- **Company Overview**: Sector, market cap, beta from the data
- **Technical Signals**: 30-day and 120-day trends, max drawdown over ~12 months, valuation note (PE ratios)
- **Key Risks**: Top 3 specific risks based on the data and news
- **Catalysts & Monitors**: 3 things to watch based on recent developments
- **Investment Stance**: One clear line recommendation

Be concise, concrete, and focus on actionable insights. Output in Markdown format.

Stock Data:
{data_summary}

Recent News:
{news_summary}
"""
        
        # Handle both old and new OpenAI API versions
        try:
            # Try new client (v1.0+)
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except AttributeError:
            # Fall back to old API (v0.x)
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating AI report: {str(e)}")
        return generate_template_report(ticker, data, news_data)

def generate_template_report(ticker: str, data: dict, news_data: list) -> str:
    """
    Generate a template report when AI is not available
    """
    summary = data.get('summary', {})
    
    # Format market cap
    market_cap = summary.get('marketCap')
    if market_cap:
        market_cap_str = f"${market_cap:,}"
    else:
        market_cap_str = "N/A"
    
    # Get current price
    current_price = summary.get('currentPrice', 'N/A')
    if isinstance(current_price, (int, float)):
        price_str = f"${current_price:.2f}"
    else:
        price_str = str(current_price)
    
    report = f"""
# {ticker} - Equity Analysis Report

## Company Overview
- **Company**: {summary.get('longName', ticker)}
- **Sector**: {summary.get('sector', 'N/A')}
- **Market Cap**: {market_cap_str}
- **Beta**: {summary.get('beta', 'N/A')}
- **Current Price**: {price_str}

## Technical Signals
- **Trailing P/E**: {summary.get('trailingPE', 'N/A')}
- **Forward P/E**: {summary.get('forwardPE', 'N/A')}
- **Target High**: ${summary.get('targetHighPrice', 'N/A')}
- **Target Low**: ${summary.get('targetLowPrice', 'N/A')}

## Key Risks
1. **Market Volatility**: Current beta of {summary.get('beta', 'N/A')} indicates sensitivity to market movements
2. **Valuation Concerns**: P/E ratios suggest potential overvaluation risks
3. **Sector-Specific Risks**: {summary.get('sector', 'Industry')}-related regulatory and competitive pressures

## Catalysts & Monitors
1. **Earnings Reports**: Monitor quarterly results and guidance updates
2. **Technical Levels**: Watch for breaks of recent support/resistance
3. **Sector News**: Keep track of {summary.get('sector', 'industry')}-wide developments

## Investment Stance
**{summary.get('recommendationKey', 'HOLD').upper()}** - Monitor technical trends and upcoming catalysts for entry/exit opportunities.

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report

def analyze_once(ticker: str, sites: List[str] | None):
    try:
        logger.info(f"Starting analysis for {ticker}")
        
        # Use the simplified Perplexity search function that takes ticker directly
        news = web_search_perplexity(ticker=ticker, max_results=6)
        
        # Call the function directly instead of using the agent
        data = price_fetch(ticker=ticker, lookback_days=400)
        
        # Ensure we have serializable data
        if not isinstance(news, (list, dict)):
            news = []
        if not isinstance(data, dict):
            data = {"summary": {"error": "Failed to parse data response"}}
        
        # Use OpenAI directly for more reliable report generation
        report = generate_analysis_report_with_openai(ticker, news, data)
        
        logger.info(f"Analysis completed for {ticker}")
        return news, data, report
        
    except Exception as e:
        logger.error(f"Error in analyze_once for {ticker}: {str(e)}", exc_info=True)
        # Return fallback data instead of crashing
        return [], {"summary": {"error": f"Analysis failed: {str(e)}"}}, f"# Analysis Error\n\nFailed to analyze {ticker}: {str(e)}"
