import React, { useEffect, useState } from 'react';
import axios from 'axios';
import '../styles/PortofolioPage.css';

const RecommendationModal = ({ onClose, onRecommendations }) => {
  const [budget, setBudget] = useState("");
  const [riskLevel, setRiskLevel] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!budget) {
      setError("Please enter a budget.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await axios.post("http://localhost:5000/api/recommendations", {
        budget: parseFloat(budget),
        risk_level: parseInt(riskLevel)
      });
      onRecommendations(response.data.recommended_portfolio);
      onClose();
    } catch (err) {
      console.error(err);
      setError("Failed to get recommendations.");
    }
    setLoading(false);
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Portfolio Recommendations</h2>
        {error && <p className="error">{error}</p>}
        <div className="form-group">
          <label>Investment Budget ($):</label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label>Desired Risk Level (1-5):</label>
          <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)}>
            <option value="1">1 (Very Low Risk)</option>
            <option value="2">2 (Low Risk)</option>
            <option value="3">3 (Moderate Risk)</option>
            <option value="4">4 (High Risk)</option>
            <option value="5">5 (Very High Risk)</option>
          </select>
        </div>
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Loading..." : "Get Recommendations"}
        </button>
        <button onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
};

const PortfolioPage = () => {
  const [portfolioData, setPortfolioData] = useState({ portfolio: [], summary: {} });
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const fetchPortfolioData = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/portfolio', { withCredentials: true });
      setPortfolioData(res.data);
    } catch (err) {
      console.error('Error fetching portfolio:', err);
      setError('Failed to fetch portfolio data.');
    }
  };

  // Purchase function for recommended stocks
  const handlePurchase = (stock) => {
    const quantity = stock.recommended_quantity;
    if (!quantity || Number(quantity) <= 0) {
      alert("Invalid quantity.");
      return;
    }
    const priceNumber = stock.current_price;
    const purchaseData = {
      ticker: stock.Ticker,
      quantity: Number(quantity),
      price: priceNumber,
      confirm: true
    };
    console.log("Purchase data:", purchaseData);
    fetch("http://localhost:5000/api/purchase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(purchaseData)
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
        } else {
          alert(`Purchase successful! New balance: $${data.new_balance}`);
          fetchPortfolioData();
        }
      })
      .catch(err => {
        alert("Purchase failed.");
        console.error(err);
      });
  };

  // Function to clear recommendations from state
  const clearRecommendations = () => {
    setRecommendations([]);
  };

  // Filter out any recommended stock with recommended_quantity 0
  const filteredRecommendations = recommendations.filter(stock => stock.recommended_quantity > 0);

  return (
    <div className="portfolio-page">
      <h2>Portfolio Management</h2>
      {error && <p className="error">{error}</p>}

      {/* Portfolio Summary */}
      <div className="portfolio-summary">
        <h3>Portfolio Summary</h3>
        <p>Total Portfolio Value: ${portfolioData.summary.total_value?.toFixed(2)}</p>
        <p>
          Overall Profit/Loss:{" "}
          <span style={{ color: portfolioData.summary.total_profit_loss >= 0 ? 'green' : 'red' }}>
            ${portfolioData.summary.total_profit_loss?.toFixed(2)}
          </span>
        </p>
      </div>

      {/* New Recommendation Button */}
      <div className="recommendation-section">
        <button onClick={() => setShowModal(true)}>Get Portfolio Recommendations</button>
      </div>

      {showModal && (
        <RecommendationModal
          onClose={() => setShowModal(false)}
          onRecommendations={(recs) => setRecommendations(recs)}
        />
      )}

      {/* Display Recommendations if available */}
      {filteredRecommendations.length > 0 && (
        <div className="portfolio-table">
          <h3>Recommended Portfolio</h3>
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Company Name</th>
                <th>Risk Class</th>
                <th>Current Price ($)</th>
                <th>Recommended Qty</th>
                <th>Total Allocation ($)</th>
                <th>Predicted % Change</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecommendations.map((stock, index) => (
                <tr key={index}>
                  <td>{stock.Ticker}</td>
                  <td>{stock.company_name}</td>
                  <td>{stock.risk_class}</td>
                  <td>${stock.current_price}</td>
                  <td>{stock.recommended_quantity}</td>
                  <td>${(stock.recommended_quantity * stock.current_price).toFixed(2)}</td>
                  <td>{stock.predicted_percent}%</td>
                  <td>
                    <button onClick={() => handlePurchase(stock)}>Buy</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ textAlign: "center", marginTop: "10px" }}>
            <button
              onClick={clearRecommendations}
              style={{ backgroundColor: "#d32f2f", color: "#fff", padding: "8px 16px", border: "none", borderRadius: "4px", cursor: "pointer" }}
            >
              Clear Recommendations
            </button>
          </div>
        </div>
      )}

      {/* Existing Portfolio Table */}
      <div className="portfolio-table">
        <h3>Current Portfolio</h3>
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Company Name</th>
              <th>Shares</th>
              <th>Average Cost</th>
              <th>Current Price</th>
              <th>Predicted Price</th>
              <th>Profit/Loss</th>
            </tr>
          </thead>
          <tbody>
            {portfolioData.portfolio.map((stock, index) => (
              <tr key={index}>
                <td>{stock.ticker}</td>
                <td>{stock.company_name || stock.ticker}</td>
                <td>{stock.quantity}</td>
                <td>${stock.average_cost.toFixed(2)}</td>
                <td>${stock.current_price.toFixed(2)}</td>
                <td>${stock.predicted_future_price.toFixed(2)}</td>
                <td style={{ color: stock.profit_loss >= 0 ? 'green' : 'red' }}>
                  ${stock.profit_loss.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PortfolioPage;
