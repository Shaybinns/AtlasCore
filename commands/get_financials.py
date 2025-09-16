# commands/get_financials.py

import requests
import os

def get_required_fields():
    return {
        "symbol": {"prompt": "Which stock symbol would you like financial data for? (e.g. AAPL, TSLA)"}
    }

def run(args: dict):
    symbol = args["symbol"].upper()
    
    url = "https://yahoo-finance166.p.rapidapi.com/api/stock/get-financial-data"
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
        # Return the full quoteSummary data for AI processing
        if 'quoteSummary' not in data or 'result' not in data['quoteSummary']:
            raise Exception("No quoteSummary data available for this symbol.")
        
        return {
            "symbol": symbol,
            "quoteSummary": data['quoteSummary']['result'][0]
        }

    except (KeyError, IndexError) as e:
        raise Exception(f"Could not parse financial data from response: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing financial data: {str(e)}")
