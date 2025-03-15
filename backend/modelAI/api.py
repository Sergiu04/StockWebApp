import os
from flask import Blueprint, request, jsonify
import numpy as np
import tensorflow as tf
import pickle
from pymongo import MongoClient
import pandas as pd

# Create a blueprint
bp = Blueprint("model_api", __name__)

# Build absolute paths to the model files (assumes they are in the same folder as api.py)
model_path = os.path.join(os.path.dirname(__file__), "final_lstm_model.h5")
xgb_model_path = os.path.join(os.path.dirname(__file__), "xgb_model.pkl")

# Load the trained LSTM model with custom_objects mapping for 'mse'
lstm_model = tf.keras.models.load_model(
    model_path,
    custom_objects={'mse': tf.keras.losses.MeanSquaredError()}
)

# Load the trained XGBoost model
with open(xgb_model_path, "rb") as f:
    xgb_model = pickle.load(f)

@bp.route("/", methods=["GET"])
def index():
    return jsonify({"message": "API is working"}), 200

@bp.route("/forecast", methods=["POST"])
def forecast():
    """
    Expects JSON payload:
      {"data": [list of 60 normalized closing prices]}
    Returns the predicted next normalized closing price.
    """
    try:
        json_data = request.get_json()
        data = json_data.get("data")
        if data is None or len(data) != 60:
            return jsonify({"error": "Input data must be a list of 60 numbers."}), 400
        
        input_array = np.array(data).reshape(1, 60, 1)
        prediction = lstm_model.predict(input_array)
        predicted_value = float(prediction[0][0])
        return jsonify({"prediction": predicted_value}), 200
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

# --- New Endpoint for Dynamic Risk Assessment ---
@bp.route("/dynamicRisk", methods=["GET"])
def dynamic_risk():
    """
    Dynamically computes risk assessment for a given ticker using its full historical data
    and a multi-class XGBoost model trained to output risk classes 1-5.
    Expects a query parameter 'ticker'.
    Returns:
      - risk_class: an integer (1-5)
      - detailed_explanation: a detailed text explanation corresponding to the risk class
    """
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "No ticker provided."}), 400

    # Connect to MongoDB and get historical data from "historical_stocks" collection
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client["stock_optimizer"]
    historical_data = list(db["historical_stocks"].find({"Ticker": ticker}))
    if not historical_data:
        return jsonify({"error": "No historical data found for this ticker."}), 404

    df = pd.DataFrame(historical_data)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    
    # Compute features: here, we use Volume, 20-day volatility (Vol20) and Close_norm
    df["Return"] = df["Close_norm"].pct_change()
    df["Vol20"] = df["Return"].rolling(window=20).std().fillna(0)
    # Use the latest record's features for prediction:
    latest = df.iloc[-1]
    features = np.array([[latest["Volume"], latest["Vol20"], latest["Close_norm"]]])
    
    # Load the multi-class XGBoost model (assumed saved as "xgb_model_multiclass.pkl" in the same folder)
    model_path = os.path.join(os.path.dirname(__file__), "xgb_model_multiclass.pkl")
    with open(model_path, "rb") as f:
        xgb_model_mc = pickle.load(f)
    
    # Predict the risk class (an integer from 0 to 4)
    risk_class = int(xgb_model_mc.predict(features)[0]) + 1
    
    # Map each risk class to a detailed explanation.
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
    
    overall_risk, detailed_explanation = explanations.get(risk_class, ("Unknown", "Risk assessment could not be determined."))
    
    return jsonify({
        "risk_class": risk_class,
        "overall_risk": overall_risk,
        "detailed_explanation": detailed_explanation
    }), 200

