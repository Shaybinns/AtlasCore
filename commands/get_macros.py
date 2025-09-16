import requests
import json
from datetime import datetime
import os
from llm_model import call_gpt
from prompt import get_plugin_system_prompt

def get_required_fields():
    return {}  # No required fields - function is smart enough to work without input

def run(args: dict):
    # Get user query from args if provided, otherwise use empty string for defaults
    user_query = args.get("query", "").strip()
    current_time = datetime.now().strftime("%A, %B %d, %Y at %H:%M %p")
    
    # Default macroeconomic indicators to always search for
    default_indicators = [
        "GDP growth rate",
        "Federal Reserve interest rates", 
        "Inflation rate (CPI)",
        "Unemployment rate",
        "Housing prices and trends",
        "Industrial production index",
        "Consumer confidence index"
    ]
    
    # If no user query provided, generate one using GPT
    if not user_query:
        # Generate a relevant search query based on the current context
        plugin_system_prompt = get_plugin_system_prompt()
        system_prompt = f"{plugin_system_prompt}\n\nYou are Portfolio AI's macroeconomic query generator. Your role is to create relevant search queries for financial analysis and market research."
        
        generation_prompt = f"""You are a web search query generator. The current date and time is {current_time}.

Generate a relevant, useful web search query that would provide valuable information for financial analysis, market research, or investment decisions. 

The query should be:
- Specific and actionable
- Relevant to current market conditions
- Useful for portfolio analysis or investment decisions
- Focused on finding the most up-to-date, reliable information

Generate only the search query itself, nothing else.
"""
        
        try:
            user_query = call_gpt(system_prompt, generation_prompt)
            user_query = user_query.strip()
        except Exception as e:
            # Fallback to a default search if GPT fails
            user_query = f"latest financial market news and analysis {current_time}"

    # Build the search query
    if user_query:
        # User provided specific query - combine with default indicators and current time
        search_query = f"Latest US macroeconomic data as of {current_time}: {user_query}. Also include current data for: {', '.join(default_indicators)}"
    else:
        # No user query - search for default indicators with current time
        search_query = f"Latest US macroeconomic data and current values as of {current_time} for: {', '.join(default_indicators)}. Include most recent data, trends, and Federal Reserve updates."

    prompt = f"""You are a macroeconomic data research specialist. The current date and time is {current_time}.

Search the internet for the most recent, accurate macroeconomic data for the United States. Focus on:

{search_query}

Please provide:
1. Current values for each indicator
2. Recent trends and changes
3. Federal Reserve policy updates
4. Data sources and dates
5. Brief analysis of what the data suggests about the economy

Format your response clearly with the most important data points highlighted.
"""

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "perplexity/sonar-pro",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500
        }
    )

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} — {response.text}")

    data = response.json()
    return data['choices'][0]['message']['content']
