import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MarketDataPage from './MarketDataPage';
import PortfolioPage from './PortofolioPage';
import ReportPage from './ReportPage';
import TransactionPage from './TransactionPage';
import '../styles/ProfilePage.css';
import AccountPage from './AccountPage';

const ProfilePage = () => {
    const [user, setUser] = useState({});
    const [activeTab, setActiveTab] = useState('portfolio');

    useEffect(() => {
        fetchUserData();
    }, []);

    const fetchUserData = async () => {
        try {
            const res = await axios.get('http://localhost:5000/api/profile', { withCredentials: true });
            setUser(res.data.user);
        } catch (err) {
            console.error('Error fetching user data:', err);
        }
    };

    const handleLogout = async () => {
        try {
            await axios.post('http://localhost:5000/api/logout', {}, { withCredentials: true });
            window.location.href = '/login';
        } catch (err) {
            console.error('Error during logout:', err);
        }
    };
    

    return (
        <div className="profile-page">
            <div className="header">
                <h1>Welcome, {user.username || 'User'}</h1>
                <button className="logout-btn" onClick={handleLogout}>
                    Logout
                </button>
            </div>
            <div className="content">
                <div className="sidebar">
                    <button onClick={() => setActiveTab('portfolio')}>Portfolio</button>
                    <button onClick={() => setActiveTab('reports')}>Reports</button>
                    <button onClick={() => setActiveTab('transactions')}>Transactions</button>
                    <button onClick={() => setActiveTab('marketData')}>Market Data</button>
                    <button onClick={() => setActiveTab('account')}>Account</button>
                </div>
                <div className="main-content">
                    {activeTab === 'marketData' && <MarketDataPage />}
                    {activeTab === 'portfolio' && <PortfolioPage />}
                    {activeTab === 'reports' && <ReportPage />}
                    {activeTab === 'transactions' && <TransactionPage />}
                    {activeTab === 'account' && <AccountPage />}
                    {/* Add more tabs and components as needed */}
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
