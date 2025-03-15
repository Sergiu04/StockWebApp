import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/ResetPasswordPage.css';

const ResetPasswordPage = () => {
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleReset = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    try {
      const response = await fetch(`http://localhost:5000/api/reset/${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
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
    <div className="reset-container">
      <div className="reset-form">
        <h2 className="form-title">Reset Password</h2>
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleReset}>
          <div className="form-group">
            <label htmlFor="password" className="form-label">New Password:</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your new password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="button reset">
            Reset Password
          </button>
        </form>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
