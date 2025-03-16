export const setupWebSocket = () => {
    const socket = new WebSocket('ws://127.0.0.1:8000/ws');

    socket.onopen = () => {
        console.log('WebSocket connection established.');
    };

    socket.onmessage = (event) => {
        console.log('Message received:', event.data);
    };

    socket.onclose = () => {
        console.log('WebSocket connection closed.');
    };

    return socket;
};
