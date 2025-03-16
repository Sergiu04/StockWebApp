import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const fetchData = async () => {
    const response = await axios.get(`${API_BASE_URL}/fetch-data`);
    return response.data;
};

export const optimizePortfolio = async (inputData) => {
    const response = await axios.post(`${API_BASE_URL}/optimize`, inputData);
    return response.data;
};
