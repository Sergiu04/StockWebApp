import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/LoginPage.css';
import { login } from '../api'; // Import the login function


const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

    const handleSubmit = async (e) => {
      e.preventDefault();
      setMessage('');
      setError('');

      try {
          const result = await login(email, password);
          setMessage(result.message || 'Login successful!');
          navigate('/profile'); // Redirect to profile page
      } catch (error) {
          setError(error); // Display error message
      }
    };

  return (
    <div className="login-container">
      {/* Home Button */}
      <nav className="home-button">
        <Link to="/">
          <button className="button home">Home</button>
        </Link>
      </nav>

      {/* Login Form */}
      <div className="login-form">
        <h2 className="form-title">Login</h2>
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
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
          <div className="form-group">
            <label htmlFor="password" className="form-label">Password:</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-link">
            <Link to="/recover" className="recover-link">
              Forgot your password? Recover here
            </Link>
          </div>
          <button type="submit" className="button login">
            Login
          </button>
        </form>
        <div className="form-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="register-link">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
