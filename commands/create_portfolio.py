def get_required_fields():
    return {
        "goal": {
            "type": "string",
            "prompt": "What is your investment goal? (e.g. retirement, income, growth)"
        },
        "duration": {
            "type": "int",
            "prompt": "How long do you plan to invest? (in years)"
        },
        "risk_level": {
            "type": "string",
            "prompt": "What's your risk level? (low, medium, high)"
        }
    }

def run(args):
    return f"Portfolio strategy for a {args['risk_level']} investor over {args['duration']} years, aiming for {args['goal']}."
