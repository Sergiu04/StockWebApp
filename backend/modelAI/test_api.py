import requests

base_url = "http://127.0.0.1:5000"

# Test health endpoint
print("Health:", requests.get(f"{base_url}/").json())

# Test forecast endpoint with a dummy list of 60 values
forecast_payload = {"data": [0.5] * 60}
print("Forecast:", requests.post(f"{base_url}/forecast", json=forecast_payload).json())

# Test risk endpoint with dummy feature values
risk_payload = {"MA20": 0.5, "Vol20": 0.05}
print("Risk:", requests.post(f"{base_url}/risk", json=risk_payload).json())
