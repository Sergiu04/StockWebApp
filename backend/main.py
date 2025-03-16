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
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # for cross-domain
app.config["SESSION_COOKIE_SECURE"] = False     # or True if using HTTPS


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
@app.route('/api/portfolio', methods=['GET'])
def portfolio():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    portfolio_docs = list(mongo.db.portfolios.find({"user_id": ObjectId(session["user_id"])}, {"_id": 0}))
    
    portfolio_items = []
    total_value = 0.0
    total_profit_loss = 0.0

    for item in portfolio_docs:
        ticker = item.get("ticker")
        quantity = item.get("quantity", 0)
        average_cost = item.get("average_cost", 0.0)
        company_name = item.get("company_name", ticker)
        
        # Fetch current price from stocks collection
        stock_record = mongo.db.stocks.find_one({"Ticker": ticker}, {"Close": 1})
        try:
            current_price = float(stock_record.get("Close")) if stock_record and stock_record.get("Close") is not None else 0.0
        except (ValueError, TypeError):
            current_price = 0.0

        # Call the forecast endpoint
        try:
            forecast_response = requests.post(
                "http://localhost:5000/api/model/forecast",
                json={"ticker": ticker}
            )
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                forecast_pct = float(forecast_data.get("percent_change", 0))
            else:
                print(f"Forecast endpoint returned {forecast_response.status_code} for {ticker}. Defaulting forecast_pct to 0.")
                forecast_pct = 0
        except Exception as e:
            print("Forecast error for", ticker, ":", str(e))
            forecast_pct = 0

        # Optionally, if you want new investments not to show an immediate loss, you could clamp forecast_pct:
        forecast_pct = max(forecast_pct, 0)

        predicted_future_price = current_price * (1 + forecast_pct / 100)
        profit_loss = (predicted_future_price - average_cost) * quantity

        total_value += current_price * quantity
        total_profit_loss += profit_loss

        portfolio_item = {
            "ticker": ticker,
            "company_name": company_name,
            "quantity": quantity,
            "average_cost": round(average_cost, 2),
            "current_price": round(current_price, 2),
            "predicted_future_price": round(predicted_future_price, 2),
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
    })



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
        # Get current price from stocks collection to compute percent change
        symbol = t.get("ticker")
        stock = mongo.db.stocks.find_one({"Ticker": symbol}, {"Close": 1})
        try:
            purchase_price = float(t.get("purchasePrice", 0))
        except (ValueError, TypeError):
            purchase_price = 0.0
        try:
            current_price = float(stock.get("Close")) if stock and stock.get("Close") is not None else purchase_price
        except (ValueError, TypeError):
            current_price = purchase_price

        percent_change = ((current_price - purchase_price) / purchase_price * 100) if purchase_price != 0 else 0

        # Format the transaction to match frontend expectations
        transaction_obj = {
            "id": str(t["_id"]),
            "symbol": t.get("ticker"),
            "name": t.get("ticker"),  # Placeholder: you can enhance this later
            "type": t.get("transaction_type"),
            "quantity": t.get("quantity"),
            "totalPrice": t.get("totalPrice"),
            "percentChange": percent_change,
            "date": t.get("timestamp").strftime("%Y-%m-%d %H:%M:%S") if t.get("timestamp") else ""
        }
        transactions_list.append(transaction_obj)

    return jsonify({"transactions": transactions_list})


# ---------------------------
# Reports Endpoints
# ---------------------------
@app.route('/api/reports', methods=['GET'])
def reports():
    # Dummy reports data – replace with your report generation logic
    reports_data = [
        {"id": 1, "name": "Report - AAPL", "summary": "Performance report for Apple Inc."},
        {"id": 2, "name": "Report - GOOGL", "summary": "Performance report for Alphabet Inc."}
    ]
    return jsonify({"reports": reports_data})

@app.route('/api/report/<string:stock_symbol>', methods=['GET'])
def report(stock_symbol):
    data = {
        "data": [
            {
                "stock": stock_symbol,
                "dates": ["2025-03-10", "2025-03-11", "2025-03-12", "2025-03-13", "2025-03-14"],
                "prices": [150, 152, 153, 154, 153]
            }
        ]
    }
    return jsonify(data)

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
