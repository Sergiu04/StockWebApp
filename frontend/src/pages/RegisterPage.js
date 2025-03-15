import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/RegisterPage.css';

const RegisterPage = () => {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [responseMessage, setResponseMessage] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
        const response = await fetch('http://127.0.0.1:5000/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });

        const data = await response.json();

        // Handle response status
        if (response.ok) {
            setResponseMessage({ type: 'success', text: data.message || 'Registration successful!' });
        } else {
            setResponseMessage({ type: 'error', text: data.error || 'Registration failed. Please try again.' });
        }
    } catch (error) {
        console.error('Error:', error);
        setResponseMessage({ type: 'error', text: 'An error occurred. Please try again.' });
    }
};


  return (
    <div className="register-container">
      {/* Home Button */}
      <nav className="home-button">
        <Link to="/">
          <button className="button home">Home</button>
        </Link>
      </nav>

      {/* Register Form */}
      <div className="register-form">
        <h2 className="form-title">Register</h2>
        {responseMessage && (
          <p className={`response-message ${responseMessage.type}`}>
            {responseMessage.text}
          </p>
        )}
        <form onSubmit={handleSubmit}>
          {/* Username Field */}
          <div className="form-group">
            <label htmlFor="username" className="form-label">Username:</label>
            <input
              id="username"
              name="username"
              type="text"
              placeholder="Enter your username"
              className="form-input"
              value={formData.username}
              onChange={handleInputChange}
              required
            />
          </div>

          {/* Email Field */}
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email:</label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="Enter your email"
              className="form-input"
              value={formData.email}
              onChange={handleInputChange}
              required
            />
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">Password:</label>
            <input
              id="password"
              name="password"
              type="password"
              placeholder="Enter your password"
              className="form-input"
              value={formData.password}
              onChange={handleInputChange}
              required
            />
          </div>

         

          {/* Submit Button */}
          <button type="submit" className="button register">Register</button>
        </form>

        {/* Footer: Login Link */}
        <div className="form-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="login-link">
              Login here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
