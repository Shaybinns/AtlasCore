import requests
import os
import json
from llm_model import call_gpt
from memory.long_term_db import get_latest_result
from memory.short_term_cache import get_recent_conversation
from prompt import get_plugin_system_prompt

def get_required_fields():
    return {
        "symbol": {"prompt": "Which asset (ticker) would you like to assess?"}
    }

### Use this until i update long_term_db to store historical runs of commands
def extract_from_recent_chat(recent_chat: str, data_type: str, symbol: str = None):
    """Extract specific data from recent conversation"""
    lines = recent_chat.split('\n')
    
    if data_type == "asset_info":
        # Look for asset info in recent chat
        for i, line in enumerate(lines):
            if symbol and symbol.upper() in line and any(keyword in line.lower() for keyword in ['trading at', 'price', 'current']):
                # Get the next few lines for context
                context = '\n'.join(lines[i:i+3])
                return f"Recent asset info for {symbol}: {context}"
    
    elif data_type == "market_data":
        # Look for market assessment data
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['market', 'conditions', 'sentiment', 'volatility']):
                # Get surrounding context
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = '\n'.join(lines[start:end])
                return f"Recent market data: {context}"
    
    return None

def run(args: dict):
    symbol = args["symbol"]
    user_id = args.get("user_id")  # Fallback to default if not provided
    
    # Get data from current command stack execution results
    from memory.short_term_cache import get_current_cache
    current_cache = get_current_cache(user_id)
    execution_results = current_cache.get("execution_results", [])
    
    # Find asset_info and market_assess results from the current stack execution
    asset_info = None
    market_data = None
    
    for result in execution_results:
        if result["command"] == "get_asset_info" and result["is_required"]:
            asset_info = result["result"]
        elif result["command"] == "market_assess" and result["is_required"]:
            market_data = result["result"]
    
    # Fallback to long-term database if not found in current execution
    if not asset_info:
        asset_info = get_latest_result("get_asset_info", symbol)
        if not asset_info:
            asset_info = f"Asset info for {symbol} not available from previous commands. Please run get_asset_info first."
    
    if not market_data:
        market_data = get_latest_result("market_assess")
        if not market_data:
            market_data = "Market assessment data not available from previous commands. Please run market_assess first."

    # Analyze the asset using GPT
    plugin_system_prompt = get_plugin_system_prompt()
    system_prompt = f"{plugin_system_prompt}\n\nYou are an asset assessment specialist within Portfolio AI. Your role is to evaluate assets and provide buy/sell/hold recommendations based on comprehensive analysis."
    
    prompt = f"""
You have the ananlytical skills of a world class investment analyst, you do not hesitate to let the user know what you think, you give financial suggests aren't afraid to give tell them when is a good time to buy or sell an asset.
You will now evaluate whether a specific asset is a good buy or sell based on the following information and relay your opnion to the user.
Based on the following data, provide a comprehensive assessment of {symbol}:

ASSET INFORMATION:
{asset_info}

MARKET CONDITIONS:
{market_data}

Please provide:
1. A clear buy/sell/hold recommendation with confidence level
2. Price targets or entry/exit points
3. Time horizon for your recommendation
4. Key factors supporting your recommendation, understanding the type of macroeconomic environment the market is in (e.g., risk-on/risk-off, inflationary, recessionary, etc).
5. Determine what kind of moves this asset would benefit from in such a climate.
6. Evaluate the asset's valuation, financial health, and growth potential.
7. Decide whether it's currently undervalued or overvalued.

Be specific, actionable, and data-driven in your analysis.
"""

    return call_gpt(system_prompt, prompt)
