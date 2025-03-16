import os
from flask import Blueprint, request, jsonify
import numpy as np
import tensorflow as tf
import pickle
from pymongo import MongoClient
import pandas as pd
import logging
bp = Blueprint("model_api", __name__)

logging.basicConfig(level=logging.INFO)
# Paths to your models
model_path = os.path.join(os.path.dirname(__file__), "final_lstm_model.h5")
xgb_model_path = os.path.join(os.path.dirname(__file__), "xgb_model.pkl")

# Load the LSTM model
lstm_model = tf.keras.models.load_model(
    model_path,
    custom_objects={'mse': tf.keras.losses.MeanSquaredError()}
)
logging.info("LSTM model loaded.")
# Load the XGBoost model
with open(xgb_model_path, "rb") as f:
    xgb_model = pickle.load(f)

@bp.route("/", methods=["GET"])
def index():
    logging.info("Index endpoint called.")
    return jsonify({"message": "API is working"}), 200
logging.info("Risk model (LightGBM) loaded.")

@bp.route("/forecast", methods=["POST"])
def forecast():
    """
    Expects JSON payload: {"ticker": "MSFT"}
    Uses normalized data from the DB, compares predicted_norm vs. last_norm_close.
    """
    try:
        json_data = request.get_json()
        ticker = json_data.get("ticker")
        if not ticker:
            logging.error("Ticker not provided in payload.")
            return jsonify({"error": "Please provide a 'ticker' in the payload."}), 400

        client = MongoClient("mongodb://localhost:27017")
        db = client["stock_optimizer"]
        historical_data = list(db["historical_stocks"].find({"Ticker": ticker}))
        if not historical_data:
            logging.error(f"No historical data found for ticker {ticker}.")
            return jsonify({"error": f"No historical data found for {ticker}"}), 404

        df = pd.DataFrame(historical_data).sort_values("Date")
        if len(df) < 1000:
            logging.error("Not enough historical records for forecasting.")
            return jsonify({"error": "Not enough data (need >= 1000 records)."}), 400

        if "Close_norm" not in df.columns:
            logging.error("Normalized close column missing.")
            return jsonify({"error": "No 'Close_norm' in data."}), 400

        last_1000_norm = df["Close_norm"].iloc[-1000:].values
        # Quick check for zero variance:
        if np.allclose(last_1000_norm, last_1000_norm[0]):
            # e.g., if all 1000 are the same, no real forecast can be made
            logging.error("No variation in last 10000 days of normalized close.")
            return jsonify({"error": "Last 1000 days have no variation in normalized close."}), 400

        # Build input for LSTM
        input_array = last_1000_norm.reshape(1, 1000, 1)
        prediction = lstm_model.predict(input_array)
        predicted_norm = float(prediction[0][0])

        last_norm_close = last_1000_norm[-1]
        if np.isclose(last_norm_close, 0.0):
            # avoid dividing by zero
            return jsonify({
                "predicted_norm": predicted_norm,
                "last_norm_close": last_norm_close,
                "percent_change": None,
                "warning": "Last close_norm is near 0.0; percentage change is meaningless."
            })

        #difference = abs(predicted_norm - last_norm_close)
        percent_change = (predicted_norm - last_norm_close)/ (last_norm_close * 10)

        return jsonify({
            "predicted_norm": predicted_norm,
            "last_norm_close": last_norm_close,
            "percent_change": percent_change
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/risk", methods=["POST"])
def risk():
    """
    Expects JSON payload:
      {"MA20": <value>, "Vol20": <value>}
    Returns the predicted risk label (0 = Low risk, 1 = High risk) and a short description.
    """
    try:
        json_data = request.get_json()
        ma20 = json_data.get("MA20")
        vol20 = json_data.get("Vol20")
        if ma20 is None or vol20 is None:
            return jsonify({"error": "Input must include both 'MA20' and 'Vol20'."}), 400

        features = np.array([[float(ma20), float(vol20)]])
        risk_pred = xgb_model.predict(features)
        risk_label = int(risk_pred[0])
        risk_desc = "High risk" if risk_label == 1 else "Low risk"
        return jsonify({"risk": risk_label, "description": risk_desc}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/dynamicRisk", methods=["GET"])
def dynamic_risk():
    """
    Dynamically computes risk assessment for a given ticker using its full historical data
    and a multi-class XGBoost model trained to output risk classes 1-5.
    Expects a query parameter 'ticker'.
    """
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "No ticker provided."}), 400

    client = MongoClient("mongodb://localhost:27017")
    db = client["stock_optimizer"]
    historical_data = list(db["historical_stocks"].find({"Ticker": ticker}))
    if not historical_data:
        return jsonify({"error": "No historical data found for this ticker."}), 404

    df = pd.DataFrame(historical_data)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # Compute Return and Vol20
    df["Return"] = df["Close_norm"].pct_change()
    df["Vol20"] = df["Return"].rolling(window=20).std().fillna(0)
    latest = df.iloc[-1]
    features = np.array([[latest["Volume"], latest["Vol20"], latest["Close_norm"]]])

    # This is functional:
    model_path_mc = os.path.join(os.path.dirname(__file__), "xgb_model_multiclass_good.pkl")
    #model_path_mc = os.path.join(os.path.dirname(__file__), "lgb_model.pkl") idk why isn t working -> trained on 1000 stocks
    
    with open(model_path_mc, "rb") as f:
        xgb_model_mc = pickle.load(f)

    risk_class = int(xgb_model_mc.predict(features)[0]) + 1

    explanations = {
        1: ("Very Low Risk",
            "The model indicates that this stock has very low volatility, stable volume, and strong market capitalization. "
            "Such stocks are generally considered very safe with minimal price fluctuations."),
        2: ("Low Risk",
            "This stock appears to have low volatility and stable trading activity with a solid market cap, suggesting relatively low risk. "
            "It may offer modest returns with little downside."),
        3: ("Moderate Risk",
            "The risk assessment shows moderate volatility and trading volume. "
            "This stock exhibits average risk characteristics; it might offer balanced potential for both gains and losses."),
        4: ("High Risk",
            "The stock is characterized by high volatility and increased trading volume, indicating potential for significant price swings. "
            "Investors should exercise caution, as the risk of loss is higher."),
        5: ("Very High Risk",
            "The model classifies this stock as very high risk due to extremely high volatility and abnormal trading volume. "
            "Such stocks can experience dramatic price fluctuations, making them very unpredictable and risky for investment.")
    }

    overall_risk, detailed_explanation = explanations.get(
        risk_class,
        ("Unknown", "Risk assessment could not be determined.")
    )

    return jsonify({
        "risk_class": risk_class,
        "overall_risk": overall_risk,
        "detailed_explanation": detailed_explanation
    }), 200
