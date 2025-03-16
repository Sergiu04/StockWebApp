import React, { useEffect, useState } from 'react';
import axios from 'axios';
import '../styles/PortofolioPage.css';

const PortfolioPage = () => {
  const [portfolioData, setPortfolioData] = useState({ portfolio: [], summary: {} });
  const [constraints, setConstraints] = useState({ budgetLimit: '', sectorLimits: {} });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPortfolioData();
    fetchConstraints();
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

  const fetchConstraints = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/constraints', { withCredentials: true });
      setConstraints(res.data);
    } catch (err) {
      console.error('Error fetching constraints:', err);
      setError('Failed to fetch constraints.');
    }
  };

  const updateConstraints = async (updatedConstraints) => {
    try {
      await axios.put('http://localhost:5000/api/constraints', updatedConstraints, { withCredentials: true });
      setConstraints(updatedConstraints);
    } catch (err) {
      console.error('Error updating constraints:', err);
      setError('Failed to update constraints.');
    }
  };

  const handleConstraintChange = (field, value) => {
    const newConstraints = { ...constraints, [field]: value };
    setConstraints(newConstraints);
  };

  const handleSectorLimitsChange = (value) => {
    try {
      const parsed = JSON.parse(value);
      setConstraints({ ...constraints, sectorLimits: parsed });
    } catch (err) {
      setError('Sector limits must be valid JSON.');
    }
  };

  const rebalancePortfolio = async () => {
    try {
      const res = await axios.post(
        'http://localhost:5000/api/rebalance',
        { constraints },
        { withCredentials: true }
      );
      // For now, just log the dummy rebalanced portfolio.
      console.log('Rebalanced portfolio:', res.data.rebalancedPortfolio);
      alert("Rebalance algorithm triggered (dummy implementation).");
    } catch (err) {
      console.error('Error rebalancing portfolio:', err);
      setError('Failed to rebalance portfolio.');
    }
  };

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

      {/* Constraints and Rebalance */}
      <div className="constraints">
        <h3>Define Constraints</h3>
        <div className="constraint-field">
          <label>Budget Limit ($):</label>
          <input
            type="number"
            value={constraints.budgetLimit || ''}
            onChange={(e) => handleConstraintChange('budgetLimit', e.target.value)}
          />
        </div>
        <div className="constraint-field">
          <label>Sector Limits (%):</label>
          <input
            type="text"
            value={JSON.stringify(constraints.sectorLimits)}
            onChange={(e) => handleSectorLimitsChange(e.target.value)}
          />
        </div>
        <button onClick={() => updateConstraints(constraints)}>Save Constraints</button>
        <button onClick={rebalancePortfolio}>Rebalance Portfolio</button>
      </div>

      {/* Portfolio Table */}
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
