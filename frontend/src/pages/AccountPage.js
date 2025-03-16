import React, { useState, useEffect } from 'react';
import '../styles/AccountPage.css';

const AccountPage = () => {
  const [userData, setUserData] = useState(null); // Initialize as null
  const [depositAmount, setDepositAmount] = useState('');
  const [subscriptionStatus, setSubscriptionStatus] = useState('');
  const [profit, setProfit] = useState(0);
  const [notificationPreferences, setNotificationPreferences] = useState({
    email: false,
    sms: false,
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('http://localhost:5000/api/account', {
      method: 'GET',
      credentials: 'include',  // Important
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
          return;
        }
        setUserData(data.user || {});
        setProfit(data.profit || 0);
        setSubscriptionStatus(data.subscriptionStatus ? 'Active' : 'Inactive');
        setNotificationPreferences(data.notificationPreferences || {});
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to load account data.');
      });
  }, []);

  // Define your action handlers (same as before)
  const handleDeposit = () => {
    fetch('http://localhost:5000/api/deposit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: parseFloat(depositAmount) }),
      credentials: 'include',
    })
      .then((res) => res.json())
      .then((data) => {
        alert(data.message);
        setUserData((prev) => ({ ...prev, balance: data.newBalance }));
        setDepositAmount('');
      });
  };

  const handleSubscriptionToggle = () => {
    fetch('http://localhost:5000/api/subscription', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: subscriptionStatus === 'Active' ? 'deactivate' : 'activate',
      }),
      credentials: 'include',
    })
      .then((res) => res.json())
      .then((data) => {
        alert(data.message);
        setSubscriptionStatus(data.subscriptionStatus ? 'Active' : 'Inactive');
      });
  };

  const handleNotificationChange = (type) => {
    const updatedPreferences = {
      ...notificationPreferences,
      [type]: !notificationPreferences[type],
    };
    setNotificationPreferences(updatedPreferences);

    fetch('http://localhost:5000/api/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedPreferences),
      credentials: 'include',
    }).then((res) => res.json());
  };

  // Render error or loading states before accessing userData properties
  if (error) {
    return <div className="account-page"><p>Error: {error}</p></div>;
  }

  if (!userData) {
    return <div className="account-page"><p>Loading...</p></div>;
  }

  return (
    <div className="account-page">
      <h1>Account Management</h1>
      <div className="account-info">
        <p>
          <strong>Username:</strong> {userData.username}
        </p>
        <p>
          <strong>Email:</strong> {userData.email}
        </p>
        <p>
          <strong>Balance:</strong> ${userData.balance?.toFixed(2)}
        </p>
        <p>
          <strong>Profit:</strong> ${profit.toFixed(2)}
        </p>
        <p>
          <strong>Subscription Status:</strong> {subscriptionStatus}
        </p>
      </div>

      <div className="account-actions">
        <h3>Deposit Money</h3>
        <input
          type="number"
          value={depositAmount}
          onChange={(e) => setDepositAmount(e.target.value)}
          placeholder="Enter amount"
        />
        <button onClick={handleDeposit}>Deposit</button>

        <h3>Notification Preferences</h3>
        <label>
          <input
            type="checkbox"
            checked={notificationPreferences.email}
            onChange={() => handleNotificationChange('email')}
          />
          Email Notifications
        </label>
        <label>
          <input
            type="checkbox"
            checked={notificationPreferences.sms}
            onChange={() => handleNotificationChange('sms')}
          />
          SMS Notifications
        </label>

        <h3>Subscription Management</h3>
        <button onClick={handleSubscriptionToggle}>
          {subscriptionStatus === 'Active' ? 'Deactivate' : 'Activate'} Subscription
        </button>
      </div>
    </div>
  );
};

export default AccountPage;
