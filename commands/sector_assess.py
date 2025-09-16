import requests
import os
import json
from llm_model import call_gpt
from prompt import get_plugin_system_prompt

def get_required_fields():
    return {
        "sector": {"prompt": "Which sector would you like to assess? (e.g. Technology, Healthcare, Energy, Financial, Consumer Discretionary)"}
    }

def get_sector_news(sector):
    """Fetch current sector-specific headlines and breaking news using Perplexity"""
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }

    prompt = f"""Find the top 5-7 most important {sector} sector headlines and breaking news right now. Focus on:
- Major company earnings or announcements in {sector}
- Regulatory changes affecting {sector}
- Market trends and innovations in {sector}
- Sector-specific economic indicators
- Major mergers, acquisitions, or partnerships in {sector}
- Supply chain or demand changes affecting {sector}

Return only the headlines and brief context, no analysis yet."""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "perplexity/sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
    )

    if response.status_code != 200:
        raise Exception(f"News API Error: {response.status_code} — {response.text}")

    data = response.json()
    return data['choices'][0]['message']['content']

def get_sector_etf_data(sector):
    """Fetch current prices for key sector ETFs, major stocks, and risk proxy assets"""
    # Map sectors to relevant ETFs and major stocks
    sector_mapping = {
        "technology": ["XLK", "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"],
        "healthcare": ["XLV", "JNJ", "PFE", "UNH", "ABBV", "TMO"],
        "energy": ["XLE", "XOM", "CVX", "COP", "EOG", "SLB"],
        "financial": ["XLF", "JPM", "BAC", "WFC", "GS", "MS"],
        "consumer_discretionary": ["XLY", "AMZN", "TSLA", "HD", "MCD", "NKE"],
        "consumer_staples": ["XLP", "PG", "KO", "WMT", "COST", "PEP"],
        "industrials": ["XLI", "BA", "CAT", "MMM", "UPS", "FDX"],
        "materials": ["XLB", "LIN", "APD", "FCX", "NEM", "DD"],
        "utilities": ["XLU", "NEE", "DUK", "SO", "D", "AEP"],
        "real_estate": ["XLRE", "PLD", "AMT", "CCI", "EQIX", "PSA"],
        "communication_services": ["XLC", "META", "NFLX", "DIS", "CMCSA", "T"]
    }
    
    # Risk proxy assets (same as market_assess)
    risk_assets = ["DX-Y.NYB", "^VIX", "^TNX", "^UST2YR", "GC=F", "^GSPC", "CL=F", "HG=F", "BTC-USD"]
    
    # Normalize sector name for mapping
    sector_lower = sector.lower().replace(" ", "_")
    sector_symbols = sector_mapping.get(sector_lower, ["SPY"])  # Default to SPY if sector not found
    
    # Combine sector symbols with risk assets
    all_symbols = sector_symbols + risk_assets
    
    url = "https://yahoo-finance166.p.rapidapi.com/api/market/get-quote-v2"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
    }

    all_data = {}
    for symbol in all_symbols:
        querystring = {"symbols": symbol, "fields": "quoteSummary"}
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            try:
                result = data['quoteResponse']['result'][0]
                all_data[symbol] = {
                    "price": result.get("regularMarketPrice"),
                    "change": result.get("regularMarketChangePercent"),
                    "volume": result.get("regularMarketVolume")
                }
            except (KeyError, IndexError):
                all_data[symbol] = {"error": "Data unavailable"}
        else:
            all_data[symbol] = {"error": f"API Error: {response.status_code}"}

    return all_data

def analyze_sector_sentiment(sector, news_data, sector_data):
    """Analyze sector sentiment using GPT"""
    plugin_system_prompt = get_plugin_system_prompt()
    system_prompt = f"{plugin_system_prompt}\n\nYou are a sector analysis specialist within Portfolio AI. Your role is to analyze sector-specific data and provide actionable investment insights."
    
    # Separate sector data from risk assets
    sector_symbols = ["XLK", "XLV", "XLE", "XLF", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC", "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "JNJ", "PFE", "UNH", "ABBV", "TMO", "XOM", "CVX", "COP", "EOG", "SLB", "JPM", "BAC", "WFC", "GS", "MS", "AMZN", "HD", "MCD", "NKE", "PG", "KO", "WMT", "COST", "PEP", "BA", "CAT", "MMM", "UPS", "FDX", "LIN", "APD", "FCX", "NEM", "DD", "NEE", "DUK", "SO", "D", "AEP", "PLD", "AMT", "CCI", "EQIX", "PSA", "META", "NFLX", "DIS", "CMCSA", "T"]
    risk_assets = ["DX-Y.NYB", "^VIX", "^TNX", "^UST2YR", "GC=F", "^GSPC", "CL=F", "HG=F", "BTC-USD"]
    
    sector_data_formatted = []
    risk_data_formatted = []
    
    for symbol, data in sector_data.items():
        if symbol in sector_symbols:
            sector_data_formatted.append(f"{symbol}: {data}")
        elif symbol in risk_assets:
            risk_data_formatted.append(f"{symbol}: {data}")
    
    sector_data_text = "\n".join(sector_data_formatted) if sector_data_formatted else "No sector data available"
    risk_data_text = "\n".join(risk_data_formatted) if risk_data_formatted else "No risk data available"
    
    user_prompt = f"""
Analyze the current {sector} sector conditions based on:

SECTOR NEWS:
{news_data}

SECTOR PERFORMANCE DATA:
{sector_data_text}

MARKET RISK INDICATORS:
{risk_data_text}

Provide a comprehensive 6-8 sentence analysis covering:
1. What's driving {sector} sector sentiment right now
2. How {sector} stocks are performing relative to the broader market
3. Current market risk environment (VIX, Treasuries, Dollar, etc.)
4. How the risk environment affects {sector} sector specifically
5. Any sector-specific opportunities or risks
6. What this suggests about {sector} sector direction
7. Key catalysts or headwinds to watch in {sector}

Be strategic and actionable. Focus on the most important {sector}-specific insights while considering the broader market risk context. Read between the lines and try to decipher what's really going on in this sector.
"""

    return call_gpt(system_prompt, user_prompt)

def run(args: dict):
    """Main sector assessment function"""
    sector = args["sector"]
    
    # Step 1: Get current sector-specific news
    sector_news = get_sector_news(sector)
    
    # Step 2: Get sector ETF and major stock data
    sector_data = get_sector_etf_data(sector)
    
    # Step 3: Analyze and synthesize
    sector_analysis = analyze_sector_sentiment(sector, sector_news, sector_data)
    
    return sector_analysis
