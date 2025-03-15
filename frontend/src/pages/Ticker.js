import React from 'react';
import Ticker from 'react-ticker';

const StockTicker = () => {
  return (
    <div className="ticker-container">
      <Ticker>
        {() => (
          <p className="ticker-text">
            AAPL: $145.60 ↑ | TSLA: $1,004.30 ↓ | AMZN: $3,200.10 ↑ | MSFT: $305.20 ↑
          </p>
        )}
      </Ticker>
    </div>
  );
};

export default StockTicker;
