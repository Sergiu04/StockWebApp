import React, { useState, useEffect } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip,
} from "chart.js";
import "../styles/ReportPage.css";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

const ReportPage = () => {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await axios.get("http://localhost:5000/api/reports");
        setReports(response.data.reports);
      } catch (error) {
        console.error("Error fetching reports:", error);
      }
    };
    fetchReports();
  }, []);

  const handleViewGraph = async (report) => {
    setSelectedReport(report);

    try {
      const response = await axios.get(`http://localhost:5000/api/report/${report.name.split(" - ")[1]}`);
      const stockData = response.data.data;

      const labels = stockData[0].dates; // X-axis (dates)
      const predefinedColors = [
        "rgba(255, 99, 132, 1)", // Red
        "rgba(54, 162, 235, 1)", // Blue
        "rgba(255, 206, 86, 1)", // Yellow
        "rgba(75, 192, 192, 1)", // Green
        "rgba(153, 102, 255, 1)", // Purple
      ];

      const datasets = stockData.map((stock, index) => ({
        label: stock.stock,
        data: stock.prices,
        borderColor: predefinedColors[index % predefinedColors.length],
        backgroundColor: predefinedColors[index % predefinedColors.length],
        fill: false,
        tension: 0.4,
        pointBackgroundColor: predefinedColors[index % predefinedColors.length],
        pointBorderWidth: 2,
      }));

      setChartData({
        labels,
        datasets,
      });
    } catch (error) {
      console.error("Error fetching report data:", error);
    }
  };

  return (
    <div className="report-page">
      <h1>Performance Reports</h1>
      <div className="reports-container">
        {reports.map((report) => (
          <div key={report.id} className="report-card">
            <h2>{report.name}</h2>
            <p>{report.summary}</p>
            <button onClick={() => handleViewGraph(report)}>View Graph</button>
          </div>
        ))}
      </div>

      {selectedReport && chartData && (
        <div className="graph-container">
          <h2>{selectedReport.name} - Performance Graph</h2>
          <Line
            data={chartData}
            options={{
              responsive: true,
              plugins: {
                legend: { position: "top" },
              },
              scales: {
                x: { grid: { color: "rgba(255, 255, 255, 0.2)" } },
                y: { grid: { color: "rgba(255, 255, 255, 0.2)" } },
              },
            }}
          />
        </div>
      )}
    </div>
  );
};

export default ReportPage;
