from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # Enable CORS for app integration

# Simple configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# ============================================================================
# ESSENTIAL API ENDPOINTS FOR APP INTEGRATION
# ============================================================================

@app.route("/api/health")
def health_check():
    """
    Health check endpoint — also initialises DB tables on first boot.
    Railway hits this after deploy; if DATABASE_URL is set the tables
    are created automatically (CREATE TABLE IF NOT EXISTS — safe to repeat).
    """
    db_status = "not_configured"
    if os.getenv("DATABASE_URL"):
        try:
            from database import init_database
            init_database()
            db_status = "ok"
        except Exception as e:
            db_status = f"error: {e}"

    try:
        from brain import handle_user_message
        brain_status = "available"
    except ImportError as e:
        brain_status = f"unavailable: {e}"

    return jsonify({
        "status": "healthy",
        "service": "AtlasCore API",
        "version": "1.0.0",
        "database": db_status,
        "brain_module": brain_status
    }), 200

@app.route("/")
def root():
    """Root endpoint for basic connectivity test"""
    return jsonify({
        "message": "InvestCore API is running",
        "health_check": "/api/health",
        "chat_endpoint": "/api/chat",
        "railway": "ready",
        "available_endpoints": [
            "/api/health",
            "/api/chat",
            "/api/chat/stream",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/me",
            "/api/auth/history",
            "/api/asset/<symbol>",
            "/api/screen",
            "/api/market/assess",
            "/api/sector/assess",
            "/api/asset/assess",
            "/api/financials/<symbol>",
            "/api/earnings/<symbol>",
            "/api/macros",
            "/api/search/web"
        ],
        "total_endpoints": 16
    })

@app.route("/api/railway/status")
def railway_status():
    """Railway-specific status endpoint"""
    try:
        from brain import handle_user_message
        brain_status = "available"
    except ImportError:
        brain_status = "unavailable"
    
    return jsonify({
        "railway": "deployed",
        "status": "healthy",
        "brain_module": brain_status,
        "timestamp": "2024-08-24",
        "deployment": "successful"
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint - handles natural language requests"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        user_id = data.get("user_id")
        message = data.get("message")

        if not user_id or not message:
            return jsonify({"error": "Missing user_id or message"}), 400

        # Import brain here to avoid circular imports
        try:
            from brain import handle_user_message
            response_data = handle_user_message(user_id, message)
        except ImportError as e:
            return jsonify({
                "error": f"Brain module not available: {str(e)}",
                "success": False,
                "railway_status": "brain_module_unavailable"
            }), 503  # Service Unavailable

        # If registered user, persist to users.recent_messages for /api/auth/history
        try:
            from user_tracking import is_user_active, add_message
            if is_user_active(user_id):
                add_message(user_id, "user", message)
                reply = response_data.get("initial_response") or ""
                if response_data.get("command_result"):
                    reply += "\n\n" + (response_data.get("command_result") or "")
                add_message(user_id, "assistant", reply)
        except Exception:
            pass

        # Return structured response for backward compatibility
        return jsonify({
            "success": True,
            "user_id": user_id,
            "initial_response": response_data.get("initial_response"),
            "command_result": response_data.get("command_result"),
            "command_executed": response_data.get("command_executed", False),
            "status": response_data.get("status"),
            "command_name": response_data.get("command_name"),
            "goal": response_data.get("goal"),
            "missing_fields": response_data.get("missing_fields"),
            "has_more_steps": response_data.get("has_more_steps"),
            "error": response_data.get("error")
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "success": False,
            "railway_status": "internal_error"
        }), 500

@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """True streaming chat endpoint that sends data as it's generated"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        user_id = data.get("user_id")
        message = data.get("message")

        if not user_id or not message:
            return jsonify({"error": "Missing user_id or message"}), 400

        def generate_stream():
            """Generate true streaming response"""
            import time
            
            # Send start signal
            yield json.dumps({
                "type": "stream_start",
                "user_id": user_id,
                "timestamp": time.time()
            }) + "\n"
            
            # Import brain here to avoid circular imports
            try:
                from brain import generate_ai_response_only, execute_command_streaming
                
                # STEP 1: Get AI response immediately (without executing commands)
                ai_response_data = generate_ai_response_only(user_id, message)
                
                # Handle the response data
                if isinstance(ai_response_data, tuple):
                    # Command detected
                    ai_response, command_name, args, goal = ai_response_data
                    command_result = None  # set after execute
                else:
                    # No command, just conversation
                    ai_response = ai_response_data
                    command_name, args, goal, command_result = None, None, None, None
                
                # STEP 2: Stream the AI response immediately
                if ai_response:
                    sentences = ai_response.split('. ')
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            yield json.dumps({
                                "type": "initial_response",
                                "chunk": sentence.strip() + ('.' if i < len(sentences) - 1 else ''),
                                "chunk_number": i + 1,
                                "total_chunks": len(sentences),
                                "timestamp": time.time()
                            }) + "\n"
                            time.sleep(0.1)  # Small delay for streaming effect
                
                # STEP 3: If there's a command, execute it and stream progress
                if command_name:
                    # Send command start
                    yield json.dumps({
                        "type": "command_start",
                        "message": f"Executing {command_name}...",
                        "command_name": command_name,
                        "timestamp": time.time()
                    }) + "\n"
                    
                    # Execute the command (this is where the real work happens)
                    command_result = execute_command_streaming(command_name, args, user_id, message)
                    
                    # Send command result
                    yield json.dumps({
                        "type": "command_result",
                        "user_id": user_id,
                        "command_result": command_result.get("command_result"),
                        "command_executed": command_result.get("command_executed", False),
                        "status": command_result.get("status"),
                        "command_name": command_result.get("command_name"),
                        "goal": goal,
                        "missing_fields": command_result.get("missing_fields"),
                        "has_more_steps": command_result.get("has_more_steps"),
                        "error": command_result.get("error"),
                        "timestamp": time.time()
                    }) + "\n"
                else:
                    # No command to execute, send empty command result
                    yield json.dumps({
                        "type": "command_result",
                        "user_id": user_id,
                        "command_result": None,
                        "command_executed": False,
                        "status": "conversation_only",
                        "command_name": None,
                        "goal": None,
                        "missing_fields": None,
                        "has_more_steps": False,
                        "error": None,
                        "timestamp": time.time()
                    }) + "\n"

                # If registered user, persist to users.recent_messages for /api/auth/history
                full_reply = ai_response or ""
                if command_name:
                    cmd_res = command_result.get("command_result") if command_name else None
                    if cmd_res:
                        full_reply += "\n\n" + (cmd_res if isinstance(cmd_res, str) else json.dumps(cmd_res))
                try:
                    from user_tracking import is_user_active, add_message
                    if is_user_active(user_id):
                        add_message(user_id, "user", message)
                        add_message(user_id, "assistant", full_reply)
                except Exception:
                    pass
                
                # Send completion
                yield json.dumps({
                    "type": "completion",
                    "success": True,
                    "timestamp": time.time()
                }) + "\n"
                
            except ImportError as e:
                yield json.dumps({
                    "type": "error",
                    "error": f"Brain module not available: {str(e)}",
                    "timestamp": time.time()
                }) + "\n"
            except Exception as e:
                yield json.dumps({
                    "type": "error",
                    "error": f"Processing failed: {str(e)}",
                    "timestamp": time.time()
                }) + "\n"

        return app.response_class(
            generate_stream(),
            mimetype='application/x-ndjson',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "success": False
        }), 500

@app.route("/api/asset/<symbol>", methods=["GET"])
def get_asset_info(symbol: str):
    """Get detailed information about a specific asset"""
    try:
        from commands.get_asset_info import run
        
        result = run({"symbol": symbol.upper()})
        
        return jsonify({
            "success": True,
            "symbol": symbol.upper(),
            "data": result
        })
        
    except ImportError as e:
        return jsonify({
            "error": f"Asset info module not available: {str(e)}",
            "success": False
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to get asset info for {symbol}: {str(e)}",
            "success": False
        }), 500

@app.route("/api/screen", methods=["POST"])
def screen_assets():
    """Screen assets based on provided filters"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        filters = data.get("filters", [])
        user_description = data.get("description", "")
        
        if not filters and not user_description:
            return jsonify({"error": "Either filters or description must be provided"}), 400
        
        try:
            from commands.screen_assets import run
            
            if user_description:
                # Parse natural language to filters
                from commands.screen_assets import parse_user_input_to_filters
                filters = parse_user_input_to_filters(user_description)
            
            result = run({"filters": filters})
        except ImportError as e:
            return jsonify({
                "error": f"Screen assets module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "filters": filters,
            "results": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to screen assets: {str(e)}",
            "success": False
        }), 500

@app.route("/api/market/assess", methods=["POST"])
def assess_market():
    """Assess current market conditions"""
    try:
        data = request.get_json() or {}
        
        try:
            from commands.market_assess import run
            result = run(data)
        except ImportError as e:
            return jsonify({
                "error": f"Market assess module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "assessment": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to assess market: {str(e)}",
            "success": False
        }), 500

@app.route("/api/sector/assess", methods=["POST"])
def assess_sector():
    """Assess specific sector performance"""
    try:
        data = request.get_json() or {}
        sector = data.get("sector")
        
        if not sector:
            return jsonify({"error": "Sector parameter is required"}), 400
            
        try:
            from commands.sector_assess import run
            result = run({"sector": sector})
        except ImportError as e:
            return jsonify({
                "error": f"Sector assess module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "sector": sector,
            "assessment": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to assess sector: {str(e)}",
            "success": False
        }), 500

@app.route("/api/asset/assess", methods=["POST"])
def assess_asset():
    """Assess specific asset performance and metrics"""
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol")
        
        if not symbol:
            return jsonify({"error": "Symbol parameter is required"}), 400
            
        try:
            from commands.asset_assess import run
            result = run({"symbol": symbol})
        except ImportError as e:
            return jsonify({
                "error": f"Asset assess module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "symbol": symbol,
            "assessment": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to assess asset: {str(e)}",
            "success": False
        }), 500

@app.route("/api/financials/<symbol>", methods=["GET"])
def get_financials(symbol: str):
    """Get financial data for a specific asset"""
    try:
        try:
            from commands.get_financials import run
            result = run({"symbol": symbol.upper()})
        except ImportError as e:
            return jsonify({
                "error": f"Financials module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "symbol": symbol.upper(),
            "financials": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get financials for {symbol}: {str(e)}",
            "success": False
        }), 500

@app.route("/api/earnings/<symbol>", methods=["GET"])
def get_earnings(symbol: str):
    """Get earnings data for a specific asset"""
    try:
        try:
            from commands.get_earnings import run
            result = run({"symbol": symbol.upper()})
        except ImportError as e:
            return jsonify({
                "error": f"Earnings module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "symbol": symbol.upper(),
            "earnings": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get earnings for {symbol}: {str(e)}",
            "success": False
        }), 500

@app.route("/api/macros", methods=["GET"])
def get_macros():
    """Get macroeconomic data and indicators"""
    try:
        try:
            from commands.get_macros import run
            result = run({})
        except ImportError as e:
            return jsonify({
                "error": f"Macros module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "macro_data": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to get macro data: {str(e)}",
            "success": False
        }), 500

@app.route("/api/search/web", methods=["POST"])
def search_web():
    """Search the web for financial information"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        query = data.get("query")
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
            
        try:
            from commands.search_web import run
            result = run({"query": query})
        except ImportError as e:
            return jsonify({
                "error": f"Web search module not available: {str(e)}",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "query": query,
            "results": result
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to search web: {str(e)}",
            "success": False
        }), 500

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    """
    Register a new user.
    Body: { "email": "...", "password": "...", "full_name": "..." }
    Returns: { "success": true, "user_id": "...", "email": "...", "full_name": "...", "created_at": "..." }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        full_name = (data.get("full_name") or "").strip()
        if not email:
            return jsonify({"error": "Missing email"}), 400
        if not password:
            return jsonify({"error": "Missing password"}), 400
        if not full_name:
            return jsonify({"error": "Missing full_name"}), 400

        from user_tracking import create_user
        try:
            user = create_user(email=email, password=password, full_name=full_name)
        except ValueError as ve:
            return jsonify({"error": str(ve), "success": False}), 409

        if not user:
            return jsonify({"error": "Failed to create user", "success": False}), 500
        return jsonify({"success": True, **user}), 201
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """
    Authenticate user.
    Body: { "email": "...", "password": "..." }
    Returns: { "success": true, "user_id": "...", "email": "...", "full_name": "...", "created_at": "..." }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        if not email:
            return jsonify({"error": "Missing email"}), 400
        if not password:
            return jsonify({"error": "Missing password"}), 400

        from user_tracking import get_user_by_email, verify_password
        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "Email not found", "success": False}), 404
        if not verify_password(password, user.get("password", "")):
            return jsonify({"error": "Invalid password", "success": False}), 401
        out = {"success": True, "user_id": user["user_id"], "email": user["email"], "full_name": user["full_name"], "created_at": user["created_at"]}
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    """Get profile for user. Query: ?user_id=<uuid>"""
    try:
        user_id = (request.args.get("user_id") or "").strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        from user_tracking import get_user_by_id
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found", "success": False}), 404
        return jsonify({"success": True, **user})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/auth/history", methods=["GET", "DELETE"])
def auth_history():
    """
    GET:  Return recent message history. Query: ?user_id=<uuid>
    DELETE: Clear message history. Body: { "user_id": "<uuid>" }
    """
    try:
        if request.method == "GET":
            user_id = (request.args.get("user_id") or "").strip()
        else:
            data = request.get_json() or {}
            user_id = (data.get("user_id") or "").strip()
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        from user_tracking import get_messages, clear_messages, is_user_active
        if not is_user_active(user_id):
            return jsonify({"error": "User not found", "success": False}), 404
        if request.method == "GET":
            messages = get_messages(user_id)
            return jsonify({"success": True, "user_id": user_id, "messages": messages})
        clear_messages(user_id)
        return jsonify({"success": True, "user_id": user_id, "message": "History cleared"})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "success": False,
        "available_endpoints": [
            "/api/health",
            "/api/chat",
            "/api/chat/stream",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/me",
            "/api/auth/history",
            "/api/asset/<symbol>",
            "/api/screen",
            "/api/market/assess",
            "/api/sector/assess",
            "/api/asset/assess",
            "/api/financials/<symbol>",
            "/api/earnings/<symbol>",
            "/api/macros",
            "/api/search/web"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "success": False
    }), 500

# ============================================================================
# MAIN APPLICATION
# ============================================================================

if __name__ == "__main__":
    try:
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')
        
        print(f"🚀 Starting InvestCore API on {host}:{port}")
        print(f"📱 App endpoints available at http://{host}:{port}/api/")
        print(f"🔍 Health check at http://{host}:{port}/api/health")
        print(f"🌍 Railway deployment ready!")
        
        # Railway-friendly startup - don't fail on brain import
        print("🔍 Testing imports...")
        
        # Debug environment variables
        print("🔍 Environment check:")
        print(f"   RAPIDAPI_KEY: {'✅ Found' if os.getenv('RAPIDAPI_KEY') else '❌ Missing'}")
        print(f"   OPENAI_API_KEY: {'✅ Found' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
        print(f"   SECRET_KEY: {'✅ Found' if os.getenv('SECRET_KEY') else '❌ Missing'}")
        print(f"   PORT: {os.getenv('PORT', '5000 (default)')}")
        
        try:
            from brain import handle_user_message
            print("✅ Brain module imported successfully")
            brain_available = True
        except Exception as e:
            print(f"⚠️ Brain import failed: {e}")
            print("💡 Continuing startup for Railway deployment...")
            brain_available = False
            
        print("🚀 Starting Flask server...")
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("Full traceback:")
        import traceback
        traceback.print_exc()
        print("Exiting with error code 1")
        exit(1)
