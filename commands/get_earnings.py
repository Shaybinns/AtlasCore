import requests
import json
from llm_model import call_gpt

def get_required_fields():
    return {
        "symbol": {"prompt": "Which stock (ticker) would you like to get earnings data for?"}
    }

def run(args: dict):
    symbol = args["symbol"].upper()
    
    # Yahoo Finance API endpoint for earnings
    url = "https://yahoo-finance166.p.rapidapi.com/api/stock/get-earnings"
    
    # Query parameters
    querystring = {
        "symbol": symbol,
        "region": "US"
    }
    
    # Headers (same as get_asset_info)
    headers = {
        "x-rapidapi-key": "5440e1fc4cmshf3f532851e0252cp1e9e06jsnebae0559f24b",
        "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
    }
    
    try:
        # Make the API call
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Navigate to the correct path in the JSON structure
            try:
                quote_summary = data.get("quoteSummary", {})
                result = quote_summary.get("result", [])
                
                if result and len(result) > 0:
                    earnings = result[0].get("earnings", {})
                    earnings_chart = earnings.get("earningsChart", {})
                    quarterly_data = earnings_chart.get("quarterly", [])
                    
                    if quarterly_data:
                        # Format the earnings data for display
                        formatted_earnings = format_earnings_data(quarterly_data, symbol)
                        return formatted_earnings
                    else:
                        return f"No quarterly earnings data found for {symbol}. This might be because the company doesn't have recent earnings reports or the data is not available."
                else:
                    return f"No earnings data found for {symbol}. This might be because the company doesn't have recent earnings reports or the data is not available."
                    
            except (KeyError, IndexError) as e:
                return f"Error parsing earnings data structure for {symbol}: {str(e)}"
        
        else:
            return f"Error fetching earnings data for {symbol}. API returned status code: {response.status_code}"
    
    except requests.exceptions.Timeout:
        return f"Timeout error while fetching earnings data for {symbol}. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Network error while fetching earnings data for {symbol}: {str(e)}"
    except json.JSONDecodeError:
        return f"Error parsing earnings data for {symbol}. The API response was not valid JSON."
    except Exception as e:
        return f"Unexpected error while fetching earnings data for {symbol}: {str(e)}"

def format_earnings_data(quarterly_data, symbol):
    """Format earnings data into a readable string"""
    
    # Create a summary of the earnings data
    summary = f"📊 Earnings Data for {symbol}\n\n"
    
    # Process each earnings report (quarterly_data is already the array we need)
    for i, quarter in enumerate(quarterly_data[:4]):  # Show last 4 earnings
        try:
            # Extract key data points from the correct structure
            date = quarter.get("date", "N/A")
            actual = quarter.get("actual", {})
            estimate = quarter.get("estimate", {})
            
            # Get actual and estimate values
            actual_eps = actual.get("fmt", "N/A") if actual else "N/A"
            estimate_eps = estimate.get("fmt", "N/A") if estimate else "N/A"
            
            # Calculate surprise percentage if we have both values
            surprise_info = ""
            if actual_eps != "N/A" and estimate_eps != "N/A":
                try:
                    actual_raw = float(actual.get("raw", 0))
                    estimate_raw = float(estimate.get("raw", 0))
                    if estimate_raw > 0:
                        surprise_pct = ((actual_raw - estimate_raw) / estimate_raw) * 100
                        surprise_info = f" | Surprise: {surprise_pct:+.1f}%"
                except (ValueError, TypeError):
                    pass
            
            # Format the period
            period = date if date != "N/A" else f"Quarter {i+1}"
            
            # Format EPS data
            eps_info = f"EPS: ${actual_eps}" if actual_eps != "N/A" else "EPS: N/A"
            if estimate_eps != "N/A":
                eps_info += f" (Est: ${estimate_eps})"
            
            # Add to summary
            summary += f"**{period}**\n"
            summary += f"{eps_info}{surprise_info}\n\n"
            
        except Exception as e:
            summary += f"Error processing earnings data: {str(e)}\n\n"
    
    # Add a note about data availability
    summary += "💡 *Data provided by Yahoo Finance*"
    
    return summary
