import json
from memory.long_term_db import get_portfolio_data, get_user_transactions
from memory.short_term_cache import get_current_cache

def get_required_fields():
    """No required fields - uses current user context"""
    return {}

def run_command(args):
    """
    Get user's portfolio information including holdings, performance, and recent transactions
    """
    try:
        # Get user_id from current cache or args
        user_id = args.get('user_id')
        if not user_id:
            # Try to get from current cache context
            cache = get_current_cache('default_user')  # You might want to pass user_id differently
            user_id = cache.get('current_user_id', 'default_user')
        
        # Get portfolio data
        portfolio_data = get_portfolio_data(user_id)
        holdings = portfolio_data.get('holdings', {})
        performance = portfolio_data.get('performance', {})
        
        # Get recent transactions (last 10)
        transactions = get_user_transactions(user_id, limit=10)
        
        # Format the response
        result = {
            "user_id": user_id,
            "portfolio_holdings": holdings,
            "portfolio_performance": performance,
            "user_transactions": transactions,
            "summary": {
                "total_holdings": len(holdings),
                "total_transactions": len(transactions),
                "has_performance_data": bool(performance)
            }
        }
        
        # Create a readable summary
        summary_text = f"Portfolio Summary for User {user_id}:\n"
        summary_text += f"Holdings: {len(holdings)} positions\n"
        summary_text += f"Recent Transactions: {len(transactions)} transactions\n"
        summary_text += f"Performance Data: {'Available' if performance else 'Not available'}\n"
        
        if holdings:
            summary_text += "\nCurrent Holdings:\n"
            for symbol, data in holdings.items():
                if isinstance(data, dict):
                    shares = data.get('shares', 'N/A')
                    value = data.get('value', 'N/A')
                    summary_text += f"  {symbol}: {shares} shares (${value})\n"
                else:
                    summary_text += f"  {symbol}: {data}\n"
        
        if performance:
            summary_text += "\nPerformance Metrics:\n"
            for metric, value in performance.items():
                if metric != 'last_updated':  # Skip timestamp
                    summary_text += f"  {metric.replace('_', ' ').title()}: {value}\n"
        
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
            "error": f"Failed to retrieve portfolio data: {str(e)}",
            "user_id": args.get('user_id', 'unknown')
        }
