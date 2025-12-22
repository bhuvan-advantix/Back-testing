"""
Real Data Fetcher - Yahoo Finance Integration
Fetches actual historical intraday data (NO MOCK DATA)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time


class YahooDataFetcher:
    """
    Fetches real historical intraday data from Yahoo Finance.
    """
    
    def __init__(self, candle_interval='5m'):
        """
        Initialize Yahoo Finance data fetcher.
        
        Args:
            candle_interval: Candle interval ('1m', '5m', '15m', '30m', '60m')
        """
        self.candle_interval = candle_interval
        self.cache = {}
    
    def fetch_intraday_data(self, symbol: str, date: str) -> Optional[pd.DataFrame]:
        """
        Fetch real intraday data for a specific stock on a specific date.
        
        Args:
            symbol: Stock symbol (NSE format, e.g., 'RELIANCE')
            date: Date in YYYY-MM-DD format
        
        Returns:
            DataFrame with intraday candles or None if not available
        """
        cache_key = f"{symbol}_{date}_{self.candle_interval}"
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Convert NSE symbol to Yahoo Finance format
            yahoo_symbol = f"{symbol}.NS"
            
            # Parse date
            target_date = datetime.strptime(date, '%Y-%m-%d')
            
            # Yahoo Finance requires a date range
            # Fetch data for the specific day
            start_date = target_date
            end_date = target_date + timedelta(days=1)
            
            print(f"Fetching {symbol} data for {date}...")
            
            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=self.candle_interval,
                actions=False
            )
            
            if df.empty:
                print(f"No data available for {symbol} on {date}")
                return None
            
            # Reset index to get datetime as column
            df = df.reset_index()
            
            # Rename columns to standard format
            df = df.rename(columns={
                'Datetime': 'Time',
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            })
            
            # Extract date and time
            df['Date'] = df['Time'].dt.date.astype(str)
            df['Time'] = df['Time'].dt.time.astype(str)
            
            # Filter for the specific date
            df = df[df['Date'] == date]
            
            if df.empty:
                print(f"No data for {symbol} on {date} after filtering")
                return None
            
            # Select required columns
            df = df[['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Validate data
            if not self._validate_data(df):
                print(f"Invalid data for {symbol} on {date}")
                return None
            
            # Cache the data
            self.cache[cache_key] = df
            
            print(f"✅ Fetched {len(df)} candles for {symbol} on {date}")
            
            # Rate limiting
            time.sleep(0.5)
            
            return df
        
        except Exception as e:
            print(f"Error fetching {symbol} on {date}: {str(e)}")
            return None
    
    def get_last_n_trading_days(self, n_days: int = 30) -> List[str]:
        """
        Get list of last N trading days (excluding weekends and holidays).
        
        Args:
            n_days: Number of trading days to fetch
        
        Returns:
            List of dates in YYYY-MM-DD format
        """
        # Use a liquid stock to determine trading days
        try:
            ticker = yf.Ticker("RELIANCE.NS")
            
            # Fetch daily data for last 60 calendar days to ensure we get 30 trading days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            df = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if df.empty:
                print("Could not fetch trading days, using calendar days")
                return self._get_calendar_days(n_days)
            
            # Get dates
            trading_days = df.index.date
            trading_days = [d.strftime('%Y-%m-%d') for d in trading_days]
            
            # Return last n_days
            return trading_days[-n_days:]
        
        except Exception as e:
            print(f"Error getting trading days: {str(e)}")
            return self._get_calendar_days(n_days)
    
    def _get_calendar_days(self, n_days: int) -> List[str]:
        """
        Fallback: Get last N calendar days excluding weekends.
        """
        dates = []
        current_date = datetime.now()
        
        while len(dates) < n_days:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                dates.append(current_date.strftime('%Y-%m-%d'))
            current_date -= timedelta(days=1)
        
        return list(reversed(dates))
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate OHLC data quality.
        """
        if df.empty:
            return False
        
        # Check for null values
        if df[['Open', 'High', 'Low', 'Close']].isnull().any().any():
            return False
        
        # Validate OHLC logic
        if not (df['High'] >= df['Low']).all():
            return False
        
        if not (df['High'] >= df['Open']).all():
            return False
        
        if not (df['High'] >= df['Close']).all():
            return False
        
        if not (df['Low'] <= df['Open']).all():
            return False
        
        if not (df['Low'] <= df['Close']).all():
            return False
        
        return True
    
    def fetch_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current price for a stock.
        """
        try:
            yahoo_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            return None
        
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {str(e)}")
            return None
