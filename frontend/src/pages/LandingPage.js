import React from 'react';
import { Link } from 'react-router-dom';
import Ticker from './Ticker'; // Import the separated Ticker component
import '../styles/LandingPage.css'; // Import CSS for the landing page

const LandingPage = () => {
  return (
    <div className="landing-container">
      {/* Background Overlay */}
      <div className="background-overlay"></div>

      {/* Main Content */}
      <div className="main-content">
        {/* Navigation */}
        <nav className="nav-links">
          <Link to="/login" className="nav-button">Login</Link>
          <Link to="/register" className="nav-button">Register</Link>
        </nav>

        {/* Hero Section */}
        <div className="hero-section">
          <h1 className="hero-title">Optimize Your Portfolio</h1>
          <p className="hero-description">
            Harness the power of AI and real-time data to make smarter investment decisions.
          </p>
          <button className="hero-button" onClick={() => window.location.href = "/register"}>
            Get Started
          </button>
        </div>

        {/* Stock Ticker */}
        <Ticker />

        {/* Footer */}
        <footer className="footer">© 2024 Stock Optimization App. All rights reserved.</footer>
      </div>
    </div>
  );
};

export default LandingPage;
