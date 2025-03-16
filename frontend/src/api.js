import axios from 'axios';

// Login function
export const login = async (email, password) => {
    try {
        const res = await axios.post('http://localhost:5000/api/login', {
            email,
            password,
        }, {
            withCredentials: true, // Send cookies
        });

        return res.data; // Return login success message or data
    } catch (error) {
        throw error.response?.data?.error || 'An unexpected error occurred.';
    }
};

// Fetch user profile data
export const fetchUserData = async () => {
    try {
        const res = await axios.get('http://localhost:5000/api/profile', {
            withCredentials: true, // Send session cookies
        });

        return res.data.user; // Return user object
    } catch (error) {
        throw error.response?.data?.error || 'An unexpected error occurred.';
    }
};
