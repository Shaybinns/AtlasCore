import requests
import os
import json
from datetime import datetime, timezone
from llm_model import call_gpt
from prompt import get_plugin_system_prompt

def get_required_fields():
    return {}  # No required fields - runs automatically

def get_market_news():
    """Fetch current market headlines and breaking news using Perplexity"""
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }

    # Get current datetime for context
    current_time = datetime.now(timezone.utc)
    current_date = current_time.strftime("%Y-%m-%d")
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")

    prompt = f"""Find the top 5-7 most important market-moving headlines and breaking news as of {current_time_str} (today is {current_date}). Focus on:
- Major economic data releases from today
- Central bank announcements from today
- Geopolitical events affecting markets from today
- Corporate earnings or major company news from today
- Market sentiment indicators from today
- Any breaking news that happened in the last few hours

IMPORTANT: Only include news from today ({current_date}) or very recent breaking news. Ignore older news.

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

def get_risk_proxy_data():
    """Fetch current prices for key risk proxy assets"""
    symbols = ["DX-Y.NYB", "^VIX", "^TNX", "^UST2YR", "GC=F", "^GSPC", "CL=F", "HG=F", "BTC-USD"]
    
    url = "https://yahoo-finance166.p.rapidapi.com/api/market/get-quote-v2"
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
    }

    all_data = {}
    for symbol in symbols:
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

def analyze_market_sentiment(news_data, risk_data):
    """Analyze market sentiment using GPT"""
    plugin_system_prompt = get_plugin_system_prompt()
    system_prompt = f"{plugin_system_prompt}\n\nYou are a market sentiment analyst within Portfolio AI. Your role is to analyze market conditions and provide strategic investment insights."
    
    # Get current datetime for context
    current_time = datetime.now(timezone.utc)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    current_date = current_time.strftime("%Y-%m-%d")
    
    user_prompt = f"""
Analyze the current market conditions as of {current_time_str} (today is {current_date}) based on:

MARKET NEWS (from today):
{news_data}

RISK PROXY ASSETS (current prices as of {current_time_str}):
DXY (Dollar Index): {risk_data.get('DX-Y.NYB', 'N/A')}
VIX (Volatility): {risk_data.get('^VIX', 'N/A')}
10Y Treasury: {risk_data.get('^TNX', 'N/A')}
2Y Treasury: {risk_data.get('^UST2YR', 'N/A')}
Gold: {risk_data.get('GC=F', 'N/A')}
S&P 500: {risk_data.get('^GSPC', 'N/A')}
Oil: {risk_data.get('CL=F', 'N/A')}
Copper: {risk_data.get('HG=F', 'N/A')}
Bitcoin: {risk_data.get('BTC-USD', 'N/A')}

Provide a concise 5-7 sentence analysis covering:
1. What's driving market sentiment right now (as of {current_time_str})
2. How investors are reacting (risk-on vs risk-off) based on today's data
3. Any arbitrage opportunities or misalignments visible in current prices
4. What this suggests about near-term market direction
5. Key risks or opportunities to watch for the rest of today and tomorrow

Be strategic and actionable. Focus on the most important insights from today's data. But read between the lines and try and decipher what's really going on.
"""

    return call_gpt(system_prompt, user_prompt)

def run(args: dict):
    """Main market assessment function"""
    # Get current datetime for logging
    current_time = datetime.now(timezone.utc)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Step 1: Get current market news
    market_news = get_market_news()
    
    # Step 2: Get risk proxy asset data
    risk_data = get_risk_proxy_data()
    
    # Step 3: Analyze and synthesize
    market_analysis = analyze_market_sentiment(market_news, risk_data)
    
    # Add timestamp to the analysis
    timestamped_analysis = f"[Market Assessment as of {current_time_str}]\n\n{market_analysis}"
    
    return timestamped_analysis
