import requests
import os
from llm_model import call_gpt
import json
from prompt import get_plugin_system_prompt

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

YF_HEADERS = {
    "X-RapidAPI-Host": "yahoo-finance166.p.rapidapi.com",
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "Content-Type": "application/json"
}

def parse_user_input_to_filters(user_input): # replace the 'some fields you can use' with a db of the fields
    plugin_system_prompt = get_plugin_system_prompt()
    system_prompt = f"{plugin_system_prompt}\n\nYou are Portfolio AI's filter parser. Your role is to convert natural language into structured screening filters."
    
    prompt = f"""You are an expert investment assistant. The user will give you a natural language description of the kind of stocks they want to screen for.

Your job is to return a list of JSON filters in the following format:
[
  {{"field": "intradayprice", "operator": "GT", "value": 50}},
  {{"field": "dayvolume", "operator": "GT", "value": 10000}},
  ...
]

Where field is the field you want to filter on like intradayprice, sector, etc, operator is the operator you want to use like GT, LT, BTWN, EQ, and value is the value you want to use for the filter like 50, Financial Services.

Only use fields from Yahoo Finance screener. Keep the result concise. DO NOT explain or comment—only return the JSON.

User input: "{user_input}"

Here are the some of the field values you can use for sectors or industries:
The sectors you can use are: Basic Materials, Consumer Cyclical, Financial Services, Real Estate, Consumer Defensive, Healthcare, Utilities, Communication Services, Energy, Industrials, andTechnology.
The industries you can use are: Agricultural Inputs, Building Materials, Chemicals, Specialty Chemicals, Lumber & Wood Production, Paper & Paper Products, Aluminum, Copper, Other Industrial Metals & Mining, Gold, Silver, Other Precious Metals & Mining, Coking Coal, Steel, Auto & Truck Dealerships, Auto Manufacturers, Auto Parts, Recreational Vehicles, Furnishings, Fixtures & Appliances, Residential Construction, Textile Manufacturing, Apparel Manufacturing, Footwear & Accessories, Packaging & Containers, Personal Services, Restaurants, Apparel Retail, Department Stores, Home Improvement Retail, Luxury Goods, Internet Retail, Specialty Retail, Gambling, Leisure, Lodging, Resorts & Casinos, Travel Services, Asset Management, Banks—Diversified, Banks—Regional, Mortgage Finance, Capital Markets, Financial Data & Stock Exchanges, Insurance—Life, Insurance—Property & Casualty, Insurance—Reinsurance, Insurance—Specialty, Insurance Brokers, Insurance—Diversified, Shell Companies, Financial Conglomerates, Credit Services, Real Estate—Development, Real Estate Services, Real Estate—Diversified, REIT—Healthcare Facilities, REIT—Hotel & Motel, REIT—Industrial, REIT—Office, REIT—Residential, REIT—Retail, REIT—Mortgage, REIT—Specialty, REIT—Diversified, Beverages—Brewers, Beverages—Wineries & Distilleries, Beverages—Non-Alcoholic, Confectioners, Farm Products, Household & Personal Products, Packaged Foods, Education & Training Services, Discount Stores, Food Distribution, Grocery Stores, Tobacco, Biotechnology, Drug Manufacturers—General, Drug Manufacturers—Specialty & Generic, Healthcare Plans, Medical Care Facilities, Pharmaceutical Retailers, Health Information Services, Medical Devices, Medical Instruments & Supplies, Diagnostics & Research, Medical Distribution, Utilities—Independent Power Producers, Utilities—Renewable, Utilities—Regulated Water, Utilities—Regulated Electric, Utilities—Regulated Gas, Utilities—Diversified, Telecom Services, Advertising Agencies, Publishing, Broadcasting, Entertainment, Internet Content & Information, Electronic Gaming & Multimedia, Oil & Gas Drilling, Oil & Gas E&P, Oil & Gas Integrated, Oil & Gas Midstream, Oil & Gas Refining & Marketing, Oil & Gas Equipment & Services, Thermal Coal, Uranium, Aerospace & Defense, Specialty Business Services, Consulting Services, Rental & Leasing Services, Security & Protection Services, Staffing & Employment Services, Conglomerates, Engineering & Construction, Infrastructure Operations, Building Products & Equipment, Farm & Heavy Construction Machinery, Industrial Distribution, Business Equipment & Supplies, Specialty Industrial Machinery, Metal Fabrication, Pollution & Treatment Controls, Tools & Accessories, Electrical Equipment & Parts, Airports & Air Services, Airlines, Railroads, Marine Shipping, Trucking, Integrated Freight & Logistics, Waste Management, Information Technology Services, Software—Application, Software—Infrastructure, Communication Equipment, Computer Hardware, Consumer Electronics, Electronic Components, Electronics & Computer Distribution, Scientific & Technical Instruments, Semiconductor Equipment & Materials, Semiconductors, Solar

Example:
User input: "I want to screen for stocks over $50 with volume above 10k"
Result: [{{"field": "intradayprice", "operator": "GT", "value": 50}}, {{"field": "dayvolume", "operator": "GT", "value": 10000}}]
"""
    result = call_gpt(system_prompt, prompt)
    return result

def build_filter_clause(filters):
    """Converts user-friendly filters to Yahoo Finance screener operands."""
    operand_blocks = []
    for f in filters:
        op_block = {
            "operator": "or",
            "operands": [   
                {
                    "operator": f["operator"].upper(),
                    "operands": [
                        f["field"],
                        *([f["value"]] if f["operator"].upper() != "BTWN" else f["value"])
                    ]
                }
            ]
        }
        operand_blocks.append(op_block)
    return operand_blocks

def screen_assets(filters):
    url = "https://yahoo-finance166.p.rapidapi.com/api/screener/list"

    querystring = {
        "sortType": "DESC",
        "sortField": "percentchange",
        "size": "20",
        "offset": "0"
    }

    region_filter = {
        "operator": "or",
        "operands": [
            {
                "operator": "EQ",
                "operands": ["region", "us"]
            }
        ]
    }

    payload = {
        "operator": "and",
        "operands": [
            region_filter,
            *build_filter_clause(filters)
        ]
    }

    response = requests.post(url, headers=YF_HEADERS, params=querystring, json=payload)
    data = response.json()

    try:
        results = data["data"]["items"][:5]  # Top 5 results
        summaries = []
        for item in results:
            summaries.append(f"{item['shortName']} ({item['symbol']}): ${item['regularMarketPrice']} — {item['regularMarketChangePercent']:.2f}%")
        screening_results = "Top Matches:\n" + "\n".join(summaries)
    except Exception as e:
        screening_results = f"Error parsing screener results: {str(e)}"
        return screening_results

    # Use GPT to analyze the screening results
    plugin_system_prompt = get_plugin_system_prompt()
    system_prompt = f"{plugin_system_prompt}\n\nYou are Portfolio AI's asset screening specialist. Your role is to analyze screening results and provide actionable investment insights."
    
    prompt = f"""Analyze the following asset screening results based on the criteria: {filters}

Screening Results:
{screening_results}

Please provide:
1. Summary of what the screening revealed
2. Key patterns or trends in the results
3. Notable opportunities or risks
4. Recommendations for further analysis
5. Any adjustments to consider for the screening criteria

Be specific and actionable in your analysis."""
    
    analysis = call_gpt(system_prompt, prompt)
    
    # Return both the raw results and the analysis
    return f"{screening_results}\n\nANALYSIS:\n{analysis}"

def get_required_fields():
    return {
        "filters": {
            "prompt": "What kind of stocks are you looking for? (e.g., stocks over $50 with volume above 10k)"
        }
    }

def run(args: dict):
    user_query = args["filters"]
    parsed_filters = parse_user_input_to_filters(user_query)
    return screen_assets(json.loads(parsed_filters))
