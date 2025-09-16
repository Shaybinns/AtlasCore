# commands/get_asset_info.py

import requests
import os

def get_required_fields():
    return {
        "symbol": {"prompt": "Which asset symbol would you like info for? (e.g. AAPL, TSLA)"}
    }

def run(args: dict):
    symbol = args["symbol"].upper()
    
    url = "https://yahoo-finance166.p.rapidapi.com/api/market/get-quote-v2"
    querystring = {"symbols": symbol, "fields": "quoteSummary"}

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} — {response.text}")

    data = response.json()
    try:
        # Return the full quoteResponse data for AI processing
        if 'quoteResponse' not in data or 'result' not in data['quoteResponse']:
            raise Exception("No quoteResponse data available for this symbol.")
        
        return {
            "symbol": symbol,
            "quoteResponse": data['quoteResponse']['result'][0]
        }

    except (KeyError, IndexError):
        raise Exception("Could not parse asset info from response.")
