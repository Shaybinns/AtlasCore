import requests
import json
from datetime import datetime
import os

def get_required_fields():
    return {
        "query": {"prompt": "What would you like to search the internet for?"}
    }

def run(args: dict):
    query = args["query"]
    current_time = datetime.now().strftime("%A, %B %d, %Y at %H:%M %p")

    prompt = f"""You are a comprehensive web search functionality of Portfolio AI. The current date and time is {current_time}.

SEARCH QUERY (from user or written by yourself to find information):
{query}

YOUR TASK:
Cast a WIDE NET and find ALL relevant and up-to-date information on this query from the internet so you can provide yourself with all the relevant information to be able to answer the user's query.

Search comprehensively and gather:
- All relevant facts, figures, dates, statistics
- Current news, events, and developments
- Multiple perspectives and sources
- Recent updates and breaking information
- Any related context that would be useful

Relay everything you find in a very easy-to-read format. If the question is simple (like "When is the next Fed meeting?"), then ALL the relevant and up-to-date info will naturally give just that simple answer. If it's complex, provide comprehensive coverage.

Be thorough, be current, be clear. Present the information in an organized, readable way."""

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
            "max_tokens": 1000
        }
    )

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} — {response.text}")

    data = response.json()
    return data['choices'][0]['message']['content']
