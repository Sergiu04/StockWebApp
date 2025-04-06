from pymongo import MongoClient
import requests

client = MongoClient("mongodb://localhost:27017")
db = client["stock_optimizer"]

stocks_collection = db["stocks"]

stocks = list(stocks_collection.find({}, {"Ticker": 1}))

for s in stocks:
    ticker = s["Ticker"]
    try:
        resp = requests.get("http://localhost:5000/api/model/dynamicRisk", params={"ticker": ticker})
        if resp.status_code == 200:
            print(f"Extrac dynamicRisk for {ticker}")
            data = resp.json()
            risk_class = data.get("risk_class", 3)
            stocks_collection.update_one({"Ticker": ticker}, {"$set": {"risk_class": risk_class}})
    except Exception as e:
        print(f"Error computing risk for {ticker}: {e}")

print("Risk classes updated in 'stocks' collection.")
