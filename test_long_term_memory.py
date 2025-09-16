#!/usr/bin/env python3
"""
Test script for the new long-term memory system
"""

from memory.long_term_db import (
    create_user_profile, update_portfolio_holdings, update_portfolio_performance,
    add_user_transaction, update_user_goals, update_user_pathway,
    get_user_facts, get_user_data_summary, clear_user_data
)

def test_long_term_memory():
    """Test the long-term memory system"""
    test_user_id = "a220247d-b621-4b8d-9653-f1f1d6b8f105"
    
    print("🧠 Testing Long-Term Memory System")
    print("=" * 50)
    
    # Clear any existing data
    print("1. Clearing existing data...")
    clear_user_data(test_user_id)
    
    # Test 1: Create user profile
    print("\n2. Creating user profile...")
    profile_data = {
        "risk_tolerance": "moderate",
        "investment_goal": "retirement_savings",
        "asset_preferences": {
            "stocks": 60,
            "bonds": 30,
            "cash": 10
        },
        "industry_preferences": {
            "technology": "high",
            "healthcare": "medium",
            "energy": "low"
        },
        "investment_style": "growth_and_income"
    }
    
    success = create_user_profile(test_user_id, profile_data)
    print(f"   Profile creation: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 2: Update portfolio holdings
    print("\n3. Updating portfolio holdings...")
    holdings = {
        "AAPL": {"shares": 100, "value": 15000},
        "MSFT": {"shares": 50, "value": 12000},
        "GOOGL": {"shares": 25, "value": 8000}
    }
    success = update_portfolio_holdings(test_user_id, holdings)
    print(f"   Holdings update: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 3: Update portfolio performance
    print("\n4. Updating portfolio performance...")
    performance = {
        "total_return": 12.5,
        "annual_return": 8.3,
        "volatility": 15.2,
        "sharpe_ratio": 1.2
    }
    success = update_portfolio_performance(test_user_id, performance)
    print(f"   Performance update: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 4: Add transactions
    print("\n5. Adding transactions...")
    transactions = [
        {"action": "buy", "symbol": "AAPL", "shares": 100, "price": 150.00},
        {"action": "buy", "symbol": "MSFT", "shares": 50, "price": 240.00},
        {"action": "sell", "symbol": "TSLA", "shares": 10, "price": 800.00}
    ]
    
    for transaction in transactions:
        success = add_user_transaction(test_user_id, transaction)
        print(f"   Transaction {transaction['action']} {transaction['symbol']}: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 5: Update goals
    print("\n6. Updating user goals...")
    goals = {
        "short_term": "Build emergency fund of $10,000",
        "medium_term": "Save $50,000 for house down payment",
        "long_term": "Retire with $1M portfolio by age 65"
    }
    success = update_user_goals(test_user_id, goals)
    print(f"   Goals update: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 6: Update pathway
    print("\n7. Updating investment pathway...")
    pathway = {
        "strategy": "dollar_cost_averaging",
        "rebalancing": "quarterly",
        "risk_management": "stop_loss_at_10_percent",
        "diversification": "across_sectors_and_geographies"
    }
    success = update_user_pathway(test_user_id, pathway)
    print(f"   Pathway update: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 7: Get user facts (for brain.py integration)
    print("\n8. Retrieving user facts for AI context...")
    user_facts = get_user_facts(test_user_id)
    print("   User Facts:")
    print("   " + "\n   ".join(user_facts.split("\n")))
    
    # Test 8: Get data summary
    print("\n9. Getting data summary...")
    summary = get_user_data_summary(test_user_id)
    print(f"   Status: {summary.get('status', 'unknown')}")
    print(f"   Profile Completeness: {summary.get('profile_completeness', '0%')}")
    print(f"   Has Portfolio: {summary.get('has_portfolio', False)}")
    print(f"   Transaction Count: {summary.get('transaction_count', 0)}")
    print(f"   Has Goals: {summary.get('has_goals', False)}")
    print(f"   Has Pathway: {summary.get('has_pathway', False)}")
    
    print("\n✅ Long-term memory system test completed!")
    print("\nThe system is now ready to be used by brain.py for AI context.")

if __name__ == "__main__":
    test_long_term_memory()
