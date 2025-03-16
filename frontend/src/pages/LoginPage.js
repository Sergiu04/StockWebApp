import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/LoginPage.css';
import { login } from '../api'; // Ensure your login function includes withCredentials: true

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);
      setLoading(false);
      if (result.error) {
        // If the API returns an error message, show it to the user.
        setError(result.error);
      } else {
        setMessage(result.message || 'Login successful!');
        // Navigate to profile after a brief delay so the user sees the success message.
        setTimeout(() => {
          navigate('/profile');
        }, 500);
      }
    } catch (err) {
      setLoading(false);
      console.error('Login error:', err);
      setError('Login failed. Please check your credentials and try again.');
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
        {message && (
          <div className="success-message" role="alert">
            {message}
          </div>
        )}
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} aria-label="Login Form">
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email:
            </label>
            <input
              id="email"
              type="email"
              placeholder="Enter your email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              aria-required="true"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Password:
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              aria-required="true"
            />
          </div>
          <div className="form-link">
            <Link to="/recover" className="recover-link">
              Forgot your password? Recover here
            </Link>
          </div>
          <button type="submit" className="button login" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
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
