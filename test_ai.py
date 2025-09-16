#!/usr/bin/env python3
"""
Simple test script for InvestCore AI
"""

from brain import handle_user_message

def main():
    print("🤖 InvestCore AI - Financial Assistant")
    print("=" * 50)
    print("Type 'quit' to exit")
    print()
    
    user_id = "a220247d-b621-4b8d-9653-f1f1d6b8f105"
    
    while True:
        try:
            # Get user input
            user_message = input("You: ").strip()
            
            if user_message.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if user_message.lower() == 'debug':
                from memory.short_term_cache import get_user_data_summary
                from memory.long_term_db import get_user_data_summary as get_lt_summary
                print(f"\n🔍 DEBUG INFO:")
                short_term_summary = get_user_data_summary(user_id)
                long_term_summary = get_lt_summary(user_id)
                print(f"Short-term memory status: {short_term_summary.get('execution_status', 'unknown')}")
                print(f"Long-term memory status: {long_term_summary.get('status', 'unknown')}")
                print(f"Profile completeness: {long_term_summary.get('profile_completeness', '0%')}")
                print(f"Has portfolio: {long_term_summary.get('has_portfolio', False)}")
                print(f"Transaction count: {long_term_summary.get('transaction_count', 0)}")
                continue
            
            if not user_message:
                continue
            
            # Process the message
            print("\n🤖 Processing...")
            response = handle_user_message(user_id, user_message)
            
            print(f"\nAI: {response}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("-" * 50)

if __name__ == "__main__":
    main() 