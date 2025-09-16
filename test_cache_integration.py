#!/usr/bin/env python3
"""
Test script for the new comprehensive cache integration
Shows how command_stack, running_state, and current_cache work together
"""

import uuid
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.short_term_cache import (
    get_comprehensive_cache, 
    get_user_data_summary,
    update_current_cache
)
from memory.command_stack import (
    push_stack, 
    start_command_execution, 
    mark_current_complete,
    get_stack_summary
)
from memory.running_state import (
    set_running, 
    update_running_context, 
    get_execution_summary,
    log_session_event
)

def test_comprehensive_integration():
    """Test the full integration of all cache systems"""
    
    # Generate a test UUID
    test_user_id = str(uuid.uuid4())
    print(f"🧪 Testing with user ID: {test_user_id}")
    print("=" * 60)
    
    # Test 1: Initial state
    print("\n📊 1. Initial State:")
    initial_summary = get_user_data_summary(test_user_id)
    print(f"   Status: {initial_summary.get('execution_status', 'unknown')}")
    print(f"   Cache keys: {initial_summary.get('cache_keys', [])}")
    
    # Test 2: Start a command execution
    print("\n🚀 2. Starting Command Execution:")
    command_info = push_stack(
        user_id=test_user_id,
        command_name="market_assess",
        args={"timeframe": "1d"},
        goal="Analyze current market conditions"
    )
    print(f"   Command added: {command_info['command']}")
    print(f"   Goal: {command_info['goal']}")
    print(f"   Status: {command_info['status']}")
    
    # Test 3: Set running state
    print("\n⚡ 3. Setting Running State:")
    running_state = set_running(
        user_id=test_user_id,
        status=True,
        context="Market analysis in progress",
        command="market_assess"
    )
    print(f"   Running: {running_state['is_running']}")
    print(f"   Context: {running_state['context']}")
    
    # Test 4: Start execution
    print("\n▶️  4. Starting Execution:")
    execution_started = start_command_execution(test_user_id)
    print(f"   Execution started: {execution_started['status']}")
    print(f"   Started at: {execution_started['execution_start']}")
    
    # Test 5: Update running context
    print("\n📝 5. Updating Running Context:")
    updated_context = update_running_context(
        user_id=test_user_id,
        progress="Fetching market data... 50% complete"
    )
    print(f"   Progress: {updated_context['progress']}")
    
    # Test 6: Log some events
    print("\n📋 6. Logging Session Events:")
    log_session_event(test_user_id, "data_fetched", "Market data retrieved successfully")
    log_session_event(test_user_id, "analysis_started", "Beginning sentiment analysis")
    
    # Test 7: Complete the command
    print("\n✅ 7. Completing Command:")
    completion = mark_current_complete(
        user_id=test_user_id,
        result="Market analysis completed successfully",
        completion_notes="Sentiment: Bullish, Volatility: Medium"
    )
    print(f"   Completion status: {completion['status']}")
    print(f"   Result: {completion['result']}")
    
    # Test 8: Stop running state
    print("\n🛑 8. Stopping Running State:")
    final_state = set_running(test_user_id, status=False)
    print(f"   Status: {final_state['status']}")
    print(f"   Session ended: {final_state['session_end']}")
    
    # Test 9: Get comprehensive summary
    print("\n📈 9. Comprehensive Summary:")
    comprehensive = get_comprehensive_cache(test_user_id)
    print(f"   Cache size: {comprehensive['cache_size']}")
    print(f"   Command stack: {comprehensive['command_stack']['overview']}")
    print(f"   Running state: {comprehensive['running_state']}")
    print(f"   Session history: {len(comprehensive['session_history'])} events")
    
    # Test 10: Get user data summary
    print("\n🎯 10. User Data Summary:")
    final_summary = get_user_data_summary(test_user_id)
    print(f"   Execution status: {final_summary['execution_status']}")
    print(f"   Cache summary: {final_summary['cache_summary']}")
    
    print("\n" + "=" * 60)
    print("🎉 Integration test completed successfully!")
    print(f"📊 Check your database for user: {test_user_id}")
    
    return test_user_id

if __name__ == "__main__":
    test_user_id = test_comprehensive_integration()
    
    # Show how to query the data
    print(f"\n🔍 To query this data in your database:")
    print(f"   SELECT current_cache FROM short_term_memory WHERE user_id = '{test_user_id}';")
