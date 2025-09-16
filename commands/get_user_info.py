import json
from memory.long_term_db import get_user_goals_and_pathway, get_user_transactions
from memory.short_term_cache import get_current_cache

def get_required_fields():
    """No required fields - uses current user context"""
    return {}

def run_command(args):
    """
    Get user's investment information including goals, pathway, and recent transactions
    """
    try:
        # Get user_id from current cache or args
        user_id = args.get('user_id')
        if not user_id:
            # Try to get from current cache context
            cache = get_current_cache('default_user')  # You might want to pass user_id differently
            user_id = cache.get('current_user_id', 'default_user')
        
        # Get goals and pathway data
        goals_pathway = get_user_goals_and_pathway(user_id)
        goals = goals_pathway.get('goals', {})
        pathway = goals_pathway.get('pathway', {})
        
        # Get recent transactions (last 10)
        transactions = get_user_transactions(user_id, limit=10)
        
        # Format the response
        result = {
            "user_id": user_id,
            "user_goals": goals,
            "user_pathway": pathway,
            "user_transactions": transactions,
            "summary": {
                "has_goals": bool(goals),
                "has_pathway": bool(pathway),
                "total_transactions": len(transactions)
            }
        }
        
        # Create a readable summary
        summary_text = f"User Investment Info for User {user_id}:\n"
        summary_text += f"Goals: {'Set' if goals else 'Not set'}\n"
        summary_text += f"Investment Pathway: {'Defined' if pathway else 'Not defined'}\n"
        summary_text += f"Recent Transactions: {len(transactions)} transactions\n"
        
        if goals:
            summary_text += "\nInvestment Goals:\n"
            for goal_type, goal_description in goals.items():
                summary_text += f"  {goal_type.replace('_', ' ').title()}: {goal_description}\n"
        
        if pathway:
            summary_text += "\nInvestment Pathway:\n"
            for strategy_type, strategy_value in pathway.items():
                summary_text += f"  {strategy_type.replace('_', ' ').title()}: {strategy_value}\n"
        
        if transactions:
            summary_text += "\nRecent Transactions:\n"
            for i, transaction in enumerate(transactions[-5:], 1):  # Show last 5
                action = transaction.get('action', 'unknown')
                symbol = transaction.get('symbol', 'N/A')
                shares = transaction.get('shares', 'N/A')
                price = transaction.get('price', 'N/A')
                timestamp = transaction.get('timestamp', 'N/A')
                summary_text += f"  {i}. {action.upper()} {shares} {symbol} @ ${price} ({timestamp})\n"
        
        result["formatted_summary"] = summary_text
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to retrieve user info: {str(e)}",
            "user_id": args.get('user_id', 'unknown')
        }
