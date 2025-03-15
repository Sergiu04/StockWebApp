# market_data_extraction.py
def update_stock_data():
    import os, glob
    import pandas as pd
    import kagglehub
    from pymongo import MongoClient
    from sklearn.preprocessing import MinMaxScaler
    import numpy as np

    # Download dataset from Kaggle
    path = kagglehub.dataset_download("borismarjanovic/price-volume-data-for-all-us-stocks-etfs")
    stocks_path = os.path.join(path, "Stocks")
    etfs_path = os.path.join(path, "ETFs")
    
    stocks_txt = glob.glob(os.path.join(stocks_path, "*.us.txt"))
    etfs_txt = glob.glob(os.path.join(etfs_path, "*.us.txt")) if os.path.exists(etfs_path) else []
    all_txt = stocks_txt + etfs_txt
    df_list = []
    for file in all_txt:
        if os.path.getsize(file) == 0:
            continue
        base_name = os.path.basename(file)
        ticker = base_name.replace(".us.txt", "")
        try:
            temp_df = pd.read_csv(file, sep=",")
        except pd.errors.EmptyDataError:
            continue
        if temp_df.empty:
            continue
        temp_df["Ticker"] = ticker
        temp_df["Date"] = pd.to_datetime(temp_df["Date"], errors="coerce")
        temp_df.dropna(subset=["Date"], inplace=True)
        if "OpenInt" in temp_df.columns:
            temp_df.drop(columns=["OpenInt"], inplace=True)
        # Simulate additional metadata: company_name, sector, market_cap
        temp_df["company_name"] = ticker.upper()  # dummy company name
        temp_df["sector"] = "Technology"           # dummy sector (adjust as needed)
        temp_df["market_cap"] = np.random.uniform(100e6, 100e9)  # random between 100M and 100B
        df_list.append(temp_df)

    data = pd.concat(df_list, ignore_index=True)
    
    # Create a column for training (normalized close) but keep the real Close for display.
    scaler = MinMaxScaler(feature_range=(0, 1))
    data["Close_norm"] = scaler.fit_transform(data["Close"].values.reshape(-1, 1))
    
    # Filter top 100 tickers by average Volume (using real volume)
    avg_vol = data.groupby("Ticker")["Volume"].mean().reset_index().sort_values(by="Volume", ascending=False)
    top_100_tickers = avg_vol.head(100)["Ticker"].tolist()
    data_top = data[data["Ticker"].isin(top_100_tickers)].copy()
    data_top.sort_values(by=["Ticker", "Date"], inplace=True)
    
    # Get the most recent record per ticker for quick lookup and format the real Close price
    latest_data = data_top.groupby("Ticker").tail(1).reset_index(drop=True)
    latest_data["Close"] = latest_data["Close"].apply(lambda x: f"${x:,.2f}")
    
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client["stock_optimizer"]
    # Update the "stocks" collection with the latest record per ticker
    stocks_collection = db["stocks"]
    stocks_collection.delete_many({})
    stocks_collection.insert_many(latest_data[["Ticker", "company_name", "sector", "market_cap", "Close", "Volume", "Date"]].to_dict("records"))
    
    # Also, update a "historical_stocks" collection with all historical data for these tickers
    historical_collection = db["historical_stocks"]
    historical_collection.delete_many({})
    historical_collection.insert_many(data_top.to_dict("records"))
    
    print("Updated stock data in MongoDB (latest and historical).")
