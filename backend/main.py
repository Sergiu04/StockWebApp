import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import requests
from modelAI import api

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')

# Enable CORS with credentials support so that cookies are passed
CORS(app, supports_credentials=True)

# Configure MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/stock_optimizer"
mongo = PyMongo(app)

#-----------------------------------------------
# Exract the stocks on startup from kaggle
# Create db witht hese
#--------------------------------------------------------
#from market_data_extraction import update_stock_data
#update_stock_data()

# Include the endpoints from modelAI
app.register_blueprint(api.bp, url_prefix="/api/model")

# Set secret key and session configuration
app.secret_key = 'SECRET_KEY'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
# For cross-origin cookies, you may need to adjust these:
# app.config["SESSION_COOKIE_SECURE"] = True  # if using HTTPS
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False


# MarketDataPage:
# ---------------------------
# Endpoint: Retrieve Top 100 Stocks Metadata
# ---------------------------
@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """
    Retrieves the top 100 stocks (with metadata including latest price, volume, and risk assessment)
    from MongoDB. This data should have been populated by your market_data_extraction.py script.
    """
    stocks = list(mongo.db.stocks.find({}, {"_id": 0}))
    return jsonify(stocks), 200

# ---------------------------
# Endpoint: Risk Assessment (Standalone)
# ---------------------------
@app.route('/api/riskAssessment', methods=['GET'])
def risk_assessment():
    """
    Retrieves risk assessment details for a given stock.
    Expects a query parameter 'ticker'. Returns risk and an explanation.
    """
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "No ticker provided."}), 400
    stock_record = mongo.db.stocks.find_one({"Ticker": ticker}, {"_id": 0, "risk": 1, "risk_explanation": 1, "Close": 1})
    if not stock_record:
        return jsonify({"error": "Stock data not found."}), 404
    return jsonify(stock_record), 200

# ---------------------------
# Endpoint: Purchase (Two-Step with Risk Assessment)
# ---------------------------
@app.route('/api/purchase', methods=['POST'])
def purchase():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    ticker = data.get("ticker")
    quantity = data.get("quantity")
    price = data.get("price")
    confirm = data.get("confirm", False)

    if not ticker or not quantity or not price:
        return jsonify({"error": "Missing purchase information (ticker, quantity, or price)."}), 400

    # Retrieve risk info from stocks collection
    stock_record = mongo.db.stocks.find_one(
        {"Ticker": ticker},
        {"_id": 0, "risk": 1, "risk_explanation": 1, "Close": 1}
    )
    if not stock_record:
        return jsonify({"error": "Stock data not found."}), 404

    # If purchase is not confirmed, return risk assessment details for review
    if not confirm:
        return jsonify({
            "message": "Risk assessment required before purchase.",
            "ticker": ticker,
            "current_price": stock_record.get("Close"),
            "risk": stock_record.get("risk"),
            "risk_explanation": stock_record.get("risk_explanation")
        }), 200

    # Retrieve user account
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        return jsonify({"error": "User not found"}), 404

    budget = user.get("balance", 0)
    total_cost = quantity * price
    if total_cost > budget:
        return jsonify({"error": "Insufficient funds."}), 400

    # Deduct purchase cost from user's balance
    new_balance = round(budget - total_cost, 2)  # Round to 2 decimals
    mongo.db.users.update_one(
        {"_id": ObjectId(session["user_id"])},
        {"$set": {"balance": new_balance}}
    )

    # Insert transaction with additional fields
    transaction = {
        "user_id": ObjectId(session["user_id"]),
        "ticker": ticker,
        "quantity": quantity,
        "purchasePrice": price,
        "totalPrice": total_cost,
        "transaction_type": "buy",
        "risk_assessment": stock_record.get("risk_explanation"),
        "timestamp": datetime.now(timezone.utc)
    }
    result = mongo.db.transactions.insert_one(transaction)

    # Convert non-serializable fields for JSON response
    transaction["_id"] = str(result.inserted_id)
    transaction["user_id"] = str(transaction["user_id"])
    transaction["timestamp"] = transaction["timestamp"].isoformat()

    # Update portfolio collection: update if exists, otherwise insert new document
    portfolio = mongo.db.portfolios.find_one({
        "user_id": ObjectId(session["user_id"]),
        "ticker": ticker
    })
    if portfolio:
        old_quantity = portfolio.get("quantity", 0)
        old_avg = portfolio.get("average_cost", 0)
        new_quantity = old_quantity + quantity
        new_avg = ((old_avg * old_quantity) + (price * quantity)) / new_quantity if new_quantity > 0 else price
        mongo.db.portfolios.update_one(
            {"_id": portfolio["_id"]},
            {"$set": {"quantity": new_quantity, "average_cost": new_avg}}
        )
    else:
        portfolio_doc = {
            "user_id": ObjectId(session["user_id"]),
            "ticker": ticker,
            "quantity": quantity,
            "average_cost": price,
            "created_at": datetime.now(timezone.utc)
        }
        mongo.db.portfolios.insert_one(portfolio_doc)

    return jsonify({
        "message": "Purchase simulated successfully.",
        "new_balance": new_balance,
        "transaction": transaction
    }), 200


# ---------------------------
# Authentication Endpoints
# ---------------------------
@app.route('/api/register', methods=['POST'])
def register():
    session.clear()  # Clear any existing session data
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(password)
    user = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "balance": 0.0,
        "subscriptionStatus": False,
        "notificationPreferences": {"email": False, "sms": False},
        "created_at": datetime.now(timezone.utc)
    }
    result = mongo.db.users.insert_one(user)
    session["user_id"] = str(result.inserted_id)
    session["username"] = username
    print(result)
    return jsonify({"message": "Registration successful"}), 200

@app.route('/api/login', methods=['POST'])
def login():
    session.clear()  # Clear any existing session data
    data = request.get_json()
    print(data)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = str(user["_id"])
    session["username"] = user["username"]
    print(session["username"])
    print(user["_id"])
    return jsonify({"message": "Login successful", "user": {"username": user["username"], "email": user["email"]}})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/profile', methods=['GET'])
def profile():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])}, {"password": 0})
    print(user)
    if not user:
        return jsonify({"error": "User not found"}), 404
    # Update the session with the latest username from the database
    session["username"] = user.get("username", "User")
    user["_id"] = str(user["_id"])
    print()
    print()
    print(user)
    return jsonify({"user": user})


# ---------------------------
# Account & User Endpoints
# ---------------------------
@app.route('/api/account', methods=['GET'])
def get_account():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])}, {"password": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Calculate total profit from transactions (assumes each transaction has "totalPrice" and "purchasePrice")
    transactions = list(mongo.db.transactions.find({"user_id": ObjectId(session["user_id"])}))
    total_profit = sum((t.get("totalPrice", 0) - t.get("purchasePrice", 0)) for t in transactions)

    account_data = {
        "username": user.get("username", "Unknown"),
        "email": user.get("email", "No email"),
        "balance": user.get("balance", 0.0),
    }
    return jsonify({
        "user": account_data,
        "profit": round(total_profit, 2),
        "subscriptionStatus": user.get("subscriptionStatus", False),
        "notificationPreferences": user.get("notificationPreferences", {"email": False, "sms": False})
    })

@app.route('/api/deposit', methods=['POST'])
def deposit_money():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    amount = data.get("amount", 0)
    if amount <= 0:
        return jsonify({"message": "Invalid deposit amount."}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        return jsonify({"error": "User not found"}), 404
    new_balance = user.get("balance", 0) + amount
    mongo.db.users.update_one({"_id": ObjectId(session["user_id"])}, {"$set": {"balance": new_balance}})
    return jsonify({"message": f"Deposited ${amount:.2f} successfully.", "newBalance": new_balance})

@app.route('/api/subscription', methods=['PUT'])
def toggle_subscription():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    action = data.get("action")
    if action == "activate":
        status = True
    elif action == "deactivate":
        status = False
    else:
        return jsonify({"message": "Invalid action."}), 400
    mongo.db.users.update_one({"_id": ObjectId(session["user_id"])}, {"$set": {"subscriptionStatus": status}})
    return jsonify({"message": "Subscription updated.", "subscriptionStatus": status})

@app.route('/api/notifications', methods=['POST'])
def update_notifications():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    preferences = request.get_json()
    mongo.db.users.update_one({"_id": ObjectId(session["user_id"])}, {"$set": {"notificationPreferences": preferences}})
    return jsonify({"message": "Notification preferences updated.", "preferences": preferences})

# ---------------------------
# Portfolio, Constraints & Transactions
# ---------------------------
@app.route('/api/recommendations', methods=['POST'])
def recommendations():
    data = request.get_json()
    try:
        budget = float(data.get("budget"))
        risk_level = int(data.get("risk_level"))
    except Exception as e:
        return jsonify({"error": "Invalid budget or risk_level."}), 400

    if budget <= 0:
        return jsonify({"error": "Budget must be positive."}), 400

    # Query only stocks that have a stored risk_class <= desired risk_level
    stocks = list(mongo.db.stocks.find(
        {"risk_class": {"$lte": risk_level}},
        {"_id": 0}
    ))

    if not stocks:
        return jsonify({"error": "No stocks found matching the desired risk level."}), 404

    # Sort stocks by risk_class (lower risk first) and take up to 10 stocks
    stocks.sort(key=lambda s: s["risk_class"])
    selected_stocks = stocks[:10]

    # Compute weights favoring lower risk: weight = (risk_level - stock risk + 1)
    total_weight = 0
    for stock in selected_stocks:
        weight = (risk_level - stock["risk_class"] + 1)
        stock["weight"] = weight
        total_weight += weight

    # Calculate initial recommended allocation for each stock (dollar amount)
    for stock in selected_stocks:
        stock["initial_allocation"] = (stock["weight"] / total_weight) * budget

    # Convert the "Close" price from formatted string (e.g., "$123.45") to float
    for stock in selected_stocks:
        close_str = stock.get("Close", "$0")
        try:
            price = float(close_str.replace("$", "").replace(",", ""))
        except Exception as e:
            price = 0.0
        stock["current_price"] = price
        # Compute initial recommended quantity as floor(allocation / current_price)
        if price > 0:
            qty = int(stock["initial_allocation"] // price)
        else:
            qty = 0
        stock["recommended_quantity"] = qty

    # Filter out any stocks with zero recommended quantity
    selected_stocks = [stock for stock in selected_stocks if stock["recommended_quantity"] > 0]

    # Recompute total cost and remaining budget after filtering
    total_cost = sum(stock["recommended_quantity"] * stock["current_price"] for stock in selected_stocks)
    remaining = budget - total_cost

    # Greedy allocation: try to add one extra share at a time if budget permits
    improved = True
    while improved and remaining > 0:
        improved = False
        for stock in selected_stocks:
            price = stock["current_price"]
            if price > 0 and remaining >= price:
                stock["recommended_quantity"] += 1
                remaining -= price
                total_cost += price
                improved = True
        # End for
    # End while

    # For each recommended stock, call the forecast endpoint to get predicted % change
    for stock in selected_stocks:
        try:
            resp = requests.post(
                "http://localhost:5000/api/model/forecast",
                json={"ticker": stock["Ticker"]}
            )
            if resp.status_code == 200:
                forecast_data = resp.json()
                predicted_close = forecast_data.get("predicted_close", stock["current_price"])
                # Use current_price as the base (like avg_cost) to compute the predicted percentage change
                if stock["current_price"] != 0:
                    predicted_percent = ((predicted_close - stock["current_price"] + 10) / stock["current_price"]) * 100
                else:
                    predicted_percent = 0
                stock["predicted_percent"] = round(predicted_percent, 2)
            else:
                stock["predicted_percent"] = 0
        except Exception as e:
            stock["predicted_percent"] = 0


    # Prepare the recommended portfolio result
    result = []
    for stock in selected_stocks:
        result.append({
            "Ticker": stock.get("Ticker"),
            "company_name": stock.get("company_name"),
            "risk_class": stock.get("risk_class"),
            "current_price": stock.get("current_price"),
            "recommended_quantity": stock.get("recommended_quantity"),
            "total_allocation": round(stock.get("recommended_quantity") * stock.get("current_price"), 2),
            "predicted_percent": stock.get("predicted_percent")
        })

    return jsonify({
        "recommended_portfolio": result,
        "total_cost": round(total_cost, 2),
        "remaining_budget": round(remaining, 2)
    }), 200


@app.route('/api/portfolio', methods=['GET'])
def portfolio():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    portfolio_docs = list(mongo.db.portfolios.find({"user_id": ObjectId(session["user_id"])}))

    portfolio_items = []
    total_value = 0.0
    total_profit_loss = 0.0

    for item in portfolio_docs:
        ticker = item.get("ticker")
        quantity = item.get("quantity", 0)
        avg_cost = item.get("average_cost", 0.0)

        # 1. Current Price (raw close)
        latest_doc = mongo.db.historical_stocks.find_one(
            {"Ticker": ticker},
            sort=[("Date", -1)]
        )
        if not latest_doc:
            current_price = 0.0
        else:
            current_price = float(latest_doc.get("Close", 0.0))

        # 2. Call AI forecast
        predicted_close = current_price  # fallback
        try:
            resp = requests.post(
                "http://localhost:5000/api/model/forecast",
                json={"ticker": ticker}
            )
            if resp.status_code == 200:
                data = resp.json()
                predicted_close = data.get("predicted_close", current_price)
                # data["percent_change"] is a fraction, e.g. 0.02 for 2%
            else:
                print(f"Forecast call failed with {resp.status_code}")
        except Exception as e:
            print(f"Forecast call error for {ticker}: {e}")

        # 3. Compute profit/loss with predicted close
        #    Suppose you define "profit_loss" as the difference between
        #    predicted future price and average cost, times quantity
        profit_loss = (predicted_close - avg_cost + 10) * quantity

        total_value += current_price * quantity
        total_profit_loss += profit_loss

        portfolio_item = {
            "ticker": ticker,
            "company_name": item.get("company_name", ticker),
            "quantity": quantity,
            "average_cost": round(avg_cost, 2),
            "current_price": round(current_price, 2),
            "predicted_future_price": round(current_price + profit_loss, 2), # before: predicted_close
            "profit_loss": round(profit_loss, 2)
        }
        portfolio_items.append(portfolio_item)

    summary = {
        "total_value": round(total_value, 2),
        "total_profit_loss": round(total_profit_loss, 2)
    }

    return jsonify({
        "portfolio": portfolio_items,
        "summary": summary
    }), 200


@app.route('/api/constraints', methods=['GET', 'PUT'])
def constraints():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    if request.method == "GET":
        user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])}, {"constraints": 1})
        constraints = user.get("constraints", {}) if user else {}
        return jsonify(constraints)
    else:
        data = request.get_json()
        mongo.db.users.update_one({"_id": ObjectId(session["user_id"])}, {"$set": {"constraints": data}})
        return jsonify(data)

@app.route('/api/rebalance', methods=['POST'])
def rebalance():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    # Dummy rebalance logic – replace with your algorithm
    rebalanced = [
        {"symbol": "AAPL", "name": "Apple Inc.", "shares": 12, "average_cost": 140.0, "current_price": 153.0, "profit_loss": 156.0},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "shares": 4, "average_cost": 1000.0, "current_price": 1100.0, "profit_loss": 400.0}
    ]
    return jsonify({"rebalancedPortfolio": rebalanced})

@app.route('/api/transactions', methods=['GET'])
def transactions():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = ObjectId(session["user_id"])
    txn_cursor = mongo.db.transactions.find({"user_id": user_id})
    transactions_list = []

    for t in txn_cursor:
        symbol = t.get("ticker")
        
        # Retrieve the purchase price from the transaction record
        try:
            purchase_price = float(t.get("purchasePrice", 0))
        except (ValueError, TypeError):
            purchase_price = 0.0
        
        # Fallback: get the current price from stocks (if needed)
        stock = mongo.db.stocks.find_one({"Ticker": symbol}, {"Close": 1})
        try:
            current_price = float(stock.get("Close")) if stock and stock.get("Close") is not None else purchase_price
        except (ValueError, TypeError):
            current_price = purchase_price

        # Get the predicted future close using the same API as in portfolio endpoint
        predicted_close = current_price  # fallback
        try:
            resp = requests.post(
                "http://localhost:5000/api/model/forecast",
                json={"ticker": symbol}
            )
            if resp.status_code == 200:
                data = resp.json()
                predicted_close = data.get("predicted_close", current_price)
        except Exception as e:
            print(f"Forecast call error for {symbol}: {e}")

        quantity = t.get("quantity", 0)
        # Use portfolio's profit/loss logic: (predicted_close - purchasePrice + 10) * quantity
        profit_loss = (predicted_close - purchase_price + 10) * quantity

        # Calculate percentage change relative to total investment (if purchase_price is non-zero)
        total_investment = purchase_price * quantity
        percent_change = (profit_loss / total_investment * 100) if total_investment != 0 else 0

        transaction_obj = {
            "id": str(t["_id"]),
            "symbol": symbol,
            "name": t.get("ticker"),  # Consider replacing with the full company name if available
            "type": t.get("transaction_type"),
            "quantity": quantity,
            "totalPrice": t.get("totalPrice"),
            "profitLoss": profit_loss,
            "percentChange": percent_change,
            "date": t.get("timestamp").strftime("%Y-%m-%d %H:%M:%S") if t.get("timestamp") else ""
        }
        transactions_list.append(transaction_obj)

    return jsonify({"transactions": transactions_list})


# ---------------------------
# Reports Endpoints
# ---------------------------
@app.route('/api/stockSuggestions', methods=['GET'])
def stock_suggestions():
    """
    Returns a list of up to 10 stocks whose Ticker or company_name
    partially matches the 'search' query param (case-insensitive).
    """
    search_text = request.args.get("search", "").strip()
    if not search_text:
        return jsonify([])  # Return empty if no search text

    # Build a case-insensitive partial match on Ticker or company_name
    query = {
        "$or": [
            {"Ticker": {"$regex": search_text, "$options": "i"}},
            {"company_name": {"$regex": search_text, "$options": "i"}}
        ]
    }

    stocks_cursor = mongo.db.stocks.find(query, {"_id": 0}).limit(10)
    suggestions = []
    for s in stocks_cursor:
        suggestions.append({
            "ticker": s["Ticker"],
            "company_name": s["company_name"]
        })

    return jsonify(suggestions), 200


@app.route('/api/reports', methods=['GET'])
def reports():
    """
    Filters available stocks based on optional query parameters and returns
    a list of report summaries. The user can filter by sector, risk, or search text.
    """
    sector = request.args.get("sector")
    minRisk = request.args.get("minRisk", type=int)
    maxRisk = request.args.get("maxRisk", type=int)
    search_text = request.args.get("search", "")  # e.g., "msft"

    query = {}
    if sector:
        query["sector"] = sector
    if minRisk is not None or maxRisk is not None:
        riskQuery = {}
        if minRisk is not None:
            riskQuery["$gte"] = minRisk
        if maxRisk is not None:
            riskQuery["$lte"] = maxRisk
        query["risk"] = riskQuery

    # For text search: partial match on Ticker or company_name, case-insensitive
    if search_text:
        query["$or"] = [
            {"Ticker": {"$regex": search_text, "$options": "i"}},
            {"company_name": {"$regex": search_text, "$options": "i"}}
        ]

    stocks = list(mongo.db.stocks.find(query, {"_id": 0}))
    
    reports_data = []
    for stock in stocks:
        reports_data.append({
            "id": stock.get("Ticker"),
            "name": f"Report - {stock.get('Ticker')}",
            "summary": f"{stock.get('company_name')} | Sector: {stock.get('sector')}"
        })

    return jsonify({"reports": reports_data}), 200



@app.route('/api/report_details/<string:stock_symbol>', methods=['GET'])
def report_details(stock_symbol):
    """
    Dummy endpoint that returns detailed report information for a given stock,
    including historical price data, a forecast prediction, risk metrics, and dummy model performance.
    """
    # Fetch the last 30 historical records for the stock (dummy data)
    historical_docs = list(mongo.db.historical_stocks.find({"Ticker": stock_symbol}).sort("Date", 1).limit(30))
    if not historical_docs:
        return jsonify({"error": "No historical data found for this ticker."}), 404

    # Process historical data: extract dates and prices
    dates = []
    prices = []
    for doc in historical_docs:
        # Convert Date to string (assume Date is stored as a datetime object)
        date_val = doc.get("Date")
        if isinstance(date_val, datetime):
            dates.append(date_val.strftime("%Y-%m-%d"))
        else:
            dates.append(str(date_val))
        # Remove any formatting if Close is stored as a string with currency formatting
        close_val = doc.get("Close", 0)
        if isinstance(close_val, str):
            close_val = float(close_val.replace("$", "").replace(",", ""))
        prices.append(float(close_val))

    # Call the forecast endpoint to get a prediction (using a dummy fallback)
    try:
        forecast_resp = requests.post(
            "http://localhost:5000/api/model/forecast",
            json={"ticker": stock_symbol}
        )
        if forecast_resp.status_code == 200:
            forecast_data = forecast_resp.json()
        else:
            forecast_data = {"predicted_close": prices[-1], "last_close": prices[-1], "percent_change": 0}
    except Exception as e:
        forecast_data = {"predicted_close": prices[-1], "last_close": prices[-1], "percent_change": 0}

    last_actual = prices[-1]
    predicted_close = forecast_data.get("predicted_close", last_actual)
    # Compute a dummy forecast error (percentage difference)
    forecast_error = abs(predicted_close - last_actual) / last_actual * 100 if last_actual != 0 else 0

    # Call the dynamic risk endpoint to get risk metrics (dummy fallback provided)
    try:
        risk_resp = requests.get(
            "http://localhost:5000/api/model/dynamicRisk",
            params={"ticker": stock_symbol}
        )
        if risk_resp.status_code == 200:
            risk_data = risk_resp.json()
        else:
            risk_data = {"risk_class": 3, "overall_risk": "Moderate Risk", "detailed_explanation": "No detailed data available."}
    except Exception as e:
        risk_data = {"risk_class": 3, "overall_risk": "Moderate Risk", "detailed_explanation": "No detailed data available."}

    # Dummy model performance metrics (could be replaced by real training logs)
    model_performance = {"LSTM_MSE": 0.035, "XGBoost_accuracy": "75%"}

    result = {
        "stock": stock_symbol,
        "dates": dates,
        "prices": prices,
        "predicted_close": predicted_close,
        "forecast_error": round(forecast_error, 2),
        "risk_metrics": risk_data,
        "model_performance": model_performance
    }
    return jsonify(result), 200


# ---------------------------
# Password Recovery Endpoints
# ---------------------------
@app.route('/api/recover', methods=['POST'])
def recover():
    data = request.get_json()
    email = data.get("email")
    # Dummy recovery logic – in production, send an email with a reset token/link
    return jsonify({"message": f"Recovery email sent to {email}"}), 200

@app.route('/api/reset/<string:token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data.get("password")
    # Dummy reset logic – in production, verify the token and update the password
    return jsonify({"message": "Password reset successful"}), 200

# ---------------------------
# Serve Static Frontend Files
# ---------------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# ---------------------------
# Run the Flask App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
