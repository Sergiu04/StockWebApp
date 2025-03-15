// MarketDataPage.js
import React, { useState, useEffect } from 'react';
import '../styles/MarketDataPage.css';

const MarketDataPage = () => {
  const [stocks, setStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStock, setSelectedStock] = useState(null);
  const [riskInfo, setRiskInfo] = useState('');
  const [purchaseMessage, setPurchaseMessage] = useState('');
  const [quantity, setQuantity] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Fetch stocks metadata from backend
  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/stocks")
      .then(res => res.json())
      .then(data => {
        setStocks(data);
        setFilteredStocks(data);
      })
      .catch(err => {
        setError("Failed to fetch stock data.");
        console.error(err);
      });
  }, []);

  // Filter stocks based on search query
  useEffect(() => {
    const filtered = stocks.filter(stock =>
      stock.Ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (stock.company_name && stock.company_name.toLowerCase().includes(searchQuery.toLowerCase()))
    );
    setFilteredStocks(filtered);
  }, [searchQuery, stocks]);

  // NEW: Fetch dynamic risk assessment from the backend
  const handleDynamicRiskAssessment = (stock) => {
    fetch(`http://127.0.0.1:5000/api/model/dynamicRisk?ticker=${stock.Ticker}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setRiskInfo(data.error);
        } else {
          // Display both the risk class and detailed explanation.
          setRiskInfo(`Risk Class: ${data.risk_class} (${data.overall_risk})\n${data.detailed_explanation}`);
        }
      })
      .catch(err => {
        setRiskInfo("Failed to retrieve risk assessment.");
        console.error(err);
      });
  };
  

  const handlePurchase = (stock) => {
    if (!quantity || Number(quantity) <= 0) {
      setPurchaseMessage("Please enter a valid quantity.");
      return;
    }
    // Before confirming purchase, ensure the risk information is shown
    if (!riskInfo) {
      setPurchaseMessage("Please view the detailed risk assessment before confirming purchase.");
      return;
    }
    // Prepare purchase data; assume current price is the stored Close value (with the $ already included)
    // Remove "$" sign for calculations if necessary.
    const priceNumber = Number(stock.Close.replace(/\$/g, "").replace(/,/g, ""));
    const purchaseData = {
      ticker: stock.Ticker,
      quantity: Number(quantity),
      price: priceNumber,
      confirm: true
    };

    fetch("http://127.0.0.1:5000/api/purchase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include", // if using session/cookies
      body: JSON.stringify(purchaseData)
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setPurchaseMessage(data.error);
        } else {
          setPurchaseMessage(`Purchase successful! New balance: $${data.new_balance}`);
        }
      })
      .catch(err => {
        setPurchaseMessage("Purchase failed.");
        console.error(err);
      });
  };

  return (
    <div className="market-data-page">
      <h1>Market Data</h1>
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search by ticker or company name"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      <div className="stock-list">
        {filteredStocks.map((stock) => (
          <div
            key={stock.Ticker}
            className={`stock-item ${selectedStock?.Ticker === stock.Ticker ? "selected" : ""}`}
            onClick={() => { 
              setSelectedStock(stock); 
              setRiskInfo(''); 
              setPurchaseMessage(''); 
              setQuantity('');
            }}
          >
            <h2>{stock.Ticker}</h2>
            <p>Company: {stock.company_name}</p>
            <p>Price: {stock.Close}</p>
            <p>Volume: {stock.Volume.toLocaleString()}</p>
            <p>Sector: {stock.sector}</p>
            <p>Market Cap: ${Number(stock.market_cap).toLocaleString()}</p>
          </div>
        ))}
      </div>
      {selectedStock && (
        <div className="stock-details">
          <h2>Details for {selectedStock.Ticker}</h2>
          <p>Company: {selectedStock.company_name}</p>
          <p>Latest Price: {selectedStock.Close}</p>
          <p>Volume: {selectedStock.Volume.toLocaleString()}</p>
          <p>Sector: {selectedStock.sector}</p>
          <p>Market Cap: ${Number(selectedStock.market_cap).toLocaleString()}</p>
          <button onClick={() => handleDynamicRiskAssessment(selectedStock)}>
            Show Detailed Risk Assessment
          </button>
          {riskInfo && (
            <div className="risk-info">
              <h3>Risk Assessment</h3>
              <pre>{riskInfo}</pre>
            </div>
          )}
          <div className="purchase-section">
            <h3>Purchase {selectedStock.Ticker}</h3>
            <input
              type="number"
              placeholder="Quantity"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
            <button onClick={() => handlePurchase(selectedStock)}>Purchase</button>
            {purchaseMessage && <p className="purchase-message">{purchaseMessage}</p>}
          </div>
        </div>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default MarketDataPage;
