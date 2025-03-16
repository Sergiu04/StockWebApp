import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/TransactionPage.css";

const TransactionPage = () => {
  const [transactions, setTransactions] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [filters, setFilters] = useState({
    dateRange: "all",
    percentChange: "",
    minPrice: "",
    maxPrice: "",
    setOrder: "",
  });

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await axios.get("http://localhost:5000/api/transactions", {
          params: filters, // Sending filters if needed
          withCredentials: true,  // Ensure session cookies are sent
        });
        setTransactions(response.data.transactions);
        setFilteredTransactions(response.data.transactions);
      } catch (error) {
        console.error("Error fetching transactions:", error);
      }
    };
    fetchTransactions();
  }, [filters]);
  
  const applyFilters = () => {
    let filtered = [...transactions];

    if (filters.dateRange !== "all") {
      const now = new Date();
      filtered = filtered.filter((transaction) => {
        const transactionDate = new Date(transaction.date);
        if (filters.dateRange === "week") {
          return transactionDate >= new Date(now.setDate(now.getDate() - 7));
        } else if (filters.dateRange === "month") {
          return transactionDate >= new Date(now.setMonth(now.getMonth() - 1));
        } else if (filters.dateRange === "year") {
          return transactionDate >= new Date(now.setFullYear(now.getFullYear() - 1));
        }
        return true;
      });
    }

    if (filters.minPrice) {
      filtered = filtered.filter(
        (transaction) => transaction.totalPrice >= parseFloat(filters.minPrice)
      );
    }

    if (filters.maxPrice) {
      filtered = filtered.filter(
        (transaction) => transaction.totalPrice <= parseFloat(filters.maxPrice)
      );
    }

    if (filters.percentChange) {
      filtered = filtered.filter((transaction) => {
        if (filters.percentChange === "increase") return transaction.percentChange > 0;
        if (filters.percentChange === "decrease") return transaction.percentChange < 0;
        return true;
      });
    }

    setFilteredTransactions(filtered);
  };

  return (
    <div className="transaction-page">
      <h1>Transaction Dashboard</h1>
      <div className="filters">
        <label>
          Date Range:
          <select
            value={filters.dateRange}
            onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
          >
            <option value="all">All</option>
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="year">Last Year</option>
          </select>
        </label>
        <label>
          Min Price:
          <input
            type="number"
            value={filters.minPrice}
            onChange={(e) => setFilters({ ...filters, minPrice: e.target.value })}
          />
        </label>
        <label>
          Max Price:
          <input
            type="number"
            value={filters.maxPrice}
            onChange={(e) => setFilters({ ...filters, maxPrice: e.target.value })}
          />
        </label>
        <label>
          % Change:
          <select
            value={filters.percentChange}
            onChange={(e) => setFilters({ ...filters, percentChange: e.target.value })}
          >
            <option value="">All</option>
            <option value="increase">Increase</option>
            <option value="decrease">Decrease</option>
          </select>
        </label>
        <button onClick={applyFilters}>Apply Filters</button>
      </div>
      <table className="transaction-table">
        <thead>
          <tr>
            <th>Stock Symbol</th>
            <th>Stock Name</th>
            <th>Transaction Type</th>
            <th>Quantity</th>
            <th>Total Price</th>
            <th>Profit/Loss (%)</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {filteredTransactions.map((transaction) => (
            <tr key={transaction.id}>
              <td>{transaction.symbol}</td>
              <td>{transaction.name}</td>
              <td>{transaction.type}</td>
              <td>{transaction.quantity}</td>
              <td>${transaction.totalPrice.toFixed(2)}</td>
              <td
                style={{
                  color: transaction.percentChange >= 0 ? "green" : "red",
                }}
              >
                {transaction.percentChange.toFixed(2)}%
              </td>
              <td>{transaction.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TransactionPage;
