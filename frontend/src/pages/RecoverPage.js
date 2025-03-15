import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/RecoverPage.css';

const RecoverPage = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleRecover = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/recover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();

      if (response.ok) {
        setMessage(result.message);
      } else {
        setError(result.message);
      }
    } catch (error) {
      setError('Failed to connect to the server. Please try again.');
    }
  };

  return (
    <div className="recover-container">
      <nav className="home-button">
        <Link to="/">
          <button className="button home">Home</button>
        </Link>
      </nav>
      <div className="recover-form">
        <h2 className="form-title">Recover Password</h2>
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleRecover}>
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email:</label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="button recover">
            Send Recovery Email
          </button>
        </form>
        <div className="form-footer">
          <p>
            Remember your password?{' '}
            <Link to="/login" className="login-link">
              Login here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RecoverPage;
