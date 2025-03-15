import React, { useEffect, useState } from 'react';
import axios from 'axios';
import '../styles/PortofolioPage.css';

const PortfolioPage = () => {
  const [portfolio, setPortfolio] = useState([]);
  const [constraints, setConstraints] = useState({ budgetLimit: '', sectorLimits: {} });
  const [rebalancedPortfolio, setRebalancedPortfolio] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPortfolioData();
    fetchConstraints();
  }, []);

  const fetchPortfolioData = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/portfolio', { withCredentials: true });
      setPortfolio(res.data.portfolio);
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
      setRebalancedPortfolio(res.data.rebalancedPortfolio);
    } catch (err) {
      console.error('Error rebalancing portfolio:', err);
      setError('Failed to rebalance portfolio.');
    }
  };

  return (
    <div className="portfolio-page">
      <h2>Portfolio Management</h2>
      {error && <p className="error">{error}</p>}

      <div className="constraints">
        <h3>Define Constraints</h3>
        <div className="constraint-field">
          <label>Budget Limit ($):</label>
          <input
            type="number"
            value={constraints.budgetLimit}
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

      <div className="portfolio-table">
        <h3>Current Portfolio</h3>
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Name</th>
              <th>Shares</th>
              <th>Average Cost</th>
              <th>Current Price</th>
              <th>Profit/Loss</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.map((stock, index) => (
              <tr key={index}>
                <td>{stock.symbol}</td>
                <td>{stock.name}</td>
                <td>{stock.shares}</td>
                <td>${stock.average_cost.toFixed(2)}</td>
                <td>${stock.current_price.toFixed(2)}</td>
                <td style={{ color: stock.profit_loss >= 0 ? 'green' : 'red' }}>
                  ${stock.profit_loss.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rebalancedPortfolio && rebalancedPortfolio.length > 0 && (
        <div className="portfolio-table rebalanced">
          <h3>Rebalanced Portfolio</h3>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Shares</th>
                <th>Average Cost</th>
                <th>Current Price</th>
                <th>Profit/Loss</th>
              </tr>
            </thead>
            <tbody>
              {rebalancedPortfolio.map((stock, index) => (
                <tr key={index}>
                  <td>{stock.symbol}</td>
                  <td>{stock.name}</td>
                  <td>{stock.shares}</td>
                  <td>${stock.average_cost.toFixed(2)}</td>
                  <td>${stock.current_price.toFixed(2)}</td>
                  <td style={{ color: stock.profit_loss >= 0 ? 'green' : 'red' }}>
                    ${stock.profit_loss.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PortfolioPage;
