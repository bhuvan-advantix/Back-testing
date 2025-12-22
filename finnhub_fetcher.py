"""
Finnhub News Fetcher - Real news sentiment data
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time


class FinnhubNewsFetcher:
    """
    Fetches real news and sentiment data from Finnhub API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Finnhub news fetcher.
        
        Args:
            api_key: Finnhub API key
        """
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.cache = {}
    
    def fetch_company_news(self, symbol: str, date: str) -> List[Dict]:
        """
        Fetch company-specific news for a stock.
        
        Args:
            symbol: Stock symbol (will be converted to appropriate format)
            date: Date in YYYY-MM-DD format
        
        Returns:
            List of news articles
        """
        cache_key = f"{symbol}_{date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Convert NSE symbol to ticker format (may need adjustment)
            # For Indian stocks, Finnhub might use different symbols
            # This is a best-effort conversion
            
            # Calculate date range (news from previous day to current day)
            target_date = datetime.strptime(date, '%Y-%m-%d')
            from_date = (target_date - timedelta(days=1)).strftime('%Y-%m-%d')
            to_date = date
            
            url = f"{self.base_url}/company-news"
            params = {
                'symbol': symbol,
                'from': from_date,
                'to': to_date,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                news = response.json()
                self.cache[cache_key] = news
                time.sleep(0.5)  # Rate limiting
                return news
            else:
                print(f"Finnhub API error for {symbol}: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"Error fetching news for {symbol}: {str(e)}")
            return []
    
    def fetch_market_news(self, date: str, category: str = 'general') -> List[Dict]:
        """
        Fetch general market news.
        
        Args:
            date: Date in YYYY-MM-DD format
            category: News category
        
        Returns:
            List of news articles
        """
        cache_key = f"market_{category}_{date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/news"
            params = {
                'category': category,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                news = response.json()
                self.cache[cache_key] = news
                time.sleep(0.5)  # Rate limiting
                return news
            else:
                print(f"Finnhub API error for market news: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"Error fetching market news: {str(e)}")
            return []
    
    def get_news_summary(self, symbol: str, date: str) -> str:
        """
        Get a formatted summary of news for a stock.
        
        Args:
            symbol: Stock symbol
            date: Date in YYYY-MM-DD format
        
        Returns:
            Formatted news summary string
        """
        news = self.fetch_company_news(symbol, date)
        
        if not news:
            return "No recent news available."
        
        # Format top 3 news items
        summary_lines = []
        for i, article in enumerate(news[:3], 1):
            headline = article.get('headline', 'No headline')
            summary = article.get('summary', '')
            summary_lines.append(f"{i}. {headline}")
            if summary:
                summary_lines.append(f"   {summary[:100]}...")
        
        return "\n".join(summary_lines)
    
    def get_market_context(self, date: str) -> str:
        """
        Get general market context for the day.
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            Market context string
        """
        news = self.fetch_market_news(date)
        
        if not news:
            return "No significant market news."
        
        # Format top 5 market news
        summary_lines = ["Market News:"]
        for i, article in enumerate(news[:5], 1):
            headline = article.get('headline', 'No headline')
            summary_lines.append(f"{i}. {headline}")
        
        return "\n".join(summary_lines)
