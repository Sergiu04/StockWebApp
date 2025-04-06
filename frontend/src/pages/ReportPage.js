import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Line, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip,
  ArcElement
} from "chart.js";
import "../styles/ReportPage.css";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip, ArcElement);

// GaugeChart component using a Doughnut chart wrapped in a fixed-size container
const GaugeChart = ({ value, threshold }) => {
  const data = {
    labels: ["Risk", "Remaining"],
    datasets: [
      {
        data: [value, 100 - value],
        backgroundColor: [value > threshold ? "red" : "green", "#e0e0e0"],
        borderWidth: 0,
      },
    ],
  };

  const options = {
    rotation: -Math.PI,
    circumference: Math.PI,
    cutout: "70%",
    plugins: {
      tooltip: { enabled: false },
      legend: { display: false },
    },
  };

  return (
    <div style={{ width: "150px", height: "150px", margin: "0 auto" }}>
      <Doughnut data={data} options={options} />
    </div>
  );
};

const ReportPage = () => {
  const [searchText, setSearchText] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const [selectedTicker, setSelectedTicker] = useState("");
  const [chartData, setChartData] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [customRiskThreshold, setCustomRiskThreshold] = useState(60);

  // For closing suggestions when clicking outside
  const suggestionsRef = useRef(null);

  // Fetch suggestions as user types
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!searchText) {
        setSuggestions([]);
        return;
      }
      try {
        const resp = await axios.get("http://localhost:5000/api/stockSuggestions", {
          params: { search: searchText },
        });
        setSuggestions(resp.data);
      } catch (error) {
        console.error("Error fetching stock suggestions:", error);
      }
    };

    fetchSuggestions();
  }, [searchText]);

  // Close suggestions if clicked outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // When user selects a suggestion, fetch the report details
  const handleSelectTicker = async (ticker) => {
    setSelectedTicker(ticker);
    setSearchText(ticker);
    setShowSuggestions(false);
    setSuggestions([]);

    try {
      const resp = await axios.get(`http://localhost:5000/api/report_details/${ticker}`);
      const reportData = resp.data;

      // Build chart data using denormalized price values; hide dates on the x-axis
      const labels = reportData.dates;
      const datasets = [
        {
          label: `${ticker} Price`,
          data: reportData.prices,
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 1)",
          fill: false,
          tension: 0.4,
          pointBackgroundColor: "rgba(54, 162, 235, 1)",
          pointBorderWidth: 2,
        },
      ];
      setChartData({ labels, datasets });
      setRiskMetrics(reportData.risk_metrics);
    } catch (error) {
      console.error("Error fetching report details:", error);
    }
  };

  // Compute risk value from risk_class (assuming risk_class 1-5 maps to 20%-100%)
  const riskValue = riskMetrics ? (riskMetrics.risk_class / 5) * 100 : 0;

  return (
    <div className="report-page">
      <h1>Performance Reports</h1>

      {/* Search bar container */}
      <div className="search-bar" ref={suggestionsRef}>
        <input
          type="text"
          placeholder="Type a ticker (e.g., MSFT, AAPL)..."
          value={searchText}
          onChange={(e) => {
            setSearchText(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
        />
        {showSuggestions && suggestions.length > 0 && (
          <ul className="suggestions-list">
            {suggestions.map((item) => (
              <li key={item.ticker} onClick={() => handleSelectTicker(item.ticker)}>
                <strong>{item.ticker.toUpperCase()}</strong> - {item.company_name}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Show selected stock chart if data is available */}
      {chartData && (
        <div className="graph-container">
          <h2>{selectedTicker.toUpperCase()} - Performance Graph</h2>
          <div className="chart-wrapper">
            <Line
              data={chartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: "top" },
                },
                scales: {
                  x: { 
                    display: false, // Hide x-axis labels (dates)
                    grid: { display: false } 
                  },
                  y: { 
                    grid: { color: "rgba(255, 255, 255, 0.2)" } 
                  },
                },
              }}
            />
          </div>

          <div className="additional-panels">
            <div className="risk-panel">
              <h3>Visual Risk Metrics</h3>
              {riskMetrics ? (
                <>
                  <p>
                    <strong>Risk Level:</strong> {riskMetrics.overall_risk} (Class {riskMetrics.risk_class})
                  </p>
                  <GaugeChart value={riskValue} threshold={customRiskThreshold} />
                  <div className="threshold-control">
                    <label>
                      Set Custom Risk Threshold: {customRiskThreshold}
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={customRiskThreshold}
                        onChange={(e) => setCustomRiskThreshold(parseInt(e.target.value))}
                      />
                    </label>
                  </div>
                  <p>{riskMetrics.detailed_explanation}</p>
                </>
              ) : (
                <p>Loading risk metrics...</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportPage;
