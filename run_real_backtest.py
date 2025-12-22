"""
Real 30-Day Backtest Orchestrator
Coordinates Yahoo Finance data, Mistral AI, Finnhub news, and algorithm
"""

from typing import Dict, List
from tqdm import tqdm
import time

from config_real import (
    AI_PROMPTS, ALGORITHM_CONFIG, BACKTEST_CONFIG,
    MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL,
    GEMINI_API_KEY, FINNHUB_API_KEY, MAX_STOCKS_LIMIT
)
from yahoo_data_fetcher import YahooDataFetcher
from finnhub_fetcher import FinnhubNewsFetcher
from mistral_ai_engine import MistralAIEngine
from real_algorithm_engine import RealAlgorithmEngine
from real_excel_reporter import RealExcelReporter


class Real30DayBacktester:
    """
    Main orchestrator for 30-day intraday backtesting with REAL data.
    """
    
    def __init__(self):
        """
        Initialize all components.
        """
        print("=" * 80)
        print("INITIALIZING 30-DAY REAL BACKTESTING SYSTEM")
        print("=" * 80)
        
        # Initialize data fetchers
        self.yahoo_fetcher = YahooDataFetcher(candle_interval='5m')
        self.news_fetcher = FinnhubNewsFetcher(FINNHUB_API_KEY)
        
        # Initialize algorithm
        self.algorithm = RealAlgorithmEngine(ALGORITHM_CONFIG)
        
        # Initialize reporter
        self.reporter = RealExcelReporter(BACKTEST_CONFIG['output_folder'])
        
        # Storage
        self.all_trades = []
        
        print("✅ All components initialized")
        print()
    
    def run_backtest(self):
        """
        Run complete 30-day backtest.
        """
        print("=" * 80)
        print("FETCHING LAST 30 TRADING DAYS")
        print("=" * 80)
        
        # Get last 30 trading days
        trading_days = self.yahoo_fetcher.get_last_n_trading_days(
            BACKTEST_CONFIG['backtest_days']
        )
        
        print(f"Found {len(trading_days)} trading days")
        print(f"From: {trading_days[0]} to {trading_days[-1]}")
        print()
        
        # Run backtest for each prompt type
        for prompt_type, prompt_config in AI_PROMPTS.items():
            print("\n" + "=" * 80)
            print(f"TESTING PROMPT: {prompt_type} - {prompt_config['name']}")
            print("=" * 80)
            
            # Add type to config
            prompt_config['type'] = prompt_type
            
            # Initialize AI engine for this prompt
            ai_engine = MistralAIEngine(
                MISTRAL_API_KEY,
                MISTRAL_API_URL,
                MISTRAL_MODEL,
                prompt_config
            )
            
            # Run backtest for each day
            for date in tqdm(trading_days, desc=f"Backtesting {prompt_type}"):
                self._backtest_single_day(date, prompt_type, ai_engine)
                time.sleep(1)  # Rate limiting
        
        # Generate Excel report
        print("\n" + "=" * 80)
        print("GENERATING EXCEL REPORT")
        print("=" * 80)
        
        self.reporter.generate_report(
            self.all_trades,
            BACKTEST_CONFIG['output_file']
        )
        
        # Print summary
        self._print_summary()
    
    def _backtest_single_day(self, date: str, prompt_type: str, ai_engine):
        """
        Backtest a single day for a specific prompt using position sizing algorithm.
        """
        from stock_allocator import StockAllocator
        
        # Get market context
        market_context = self.news_fetcher.get_market_context(date)
        
        # Get AI suggestions
        suggestions = ai_engine.suggest_stocks(date, market_context, "")
        
        if not suggestions:
            print(f"  No suggestions for {date}")
            return
        
        # Limit to MAX_STOCKS_LIMIT
        suggestions = suggestions[:MAX_STOCKS_LIMIT]
        
        # Prepare stocks for allocation
        stocks_for_allocation = []
        
        for suggestion in suggestions:
            stock_symbol = suggestion['symbol']
            bias = suggestion['bias']
            
            # Fetch intraday data
            stock_data = self.yahoo_fetcher.fetch_intraday_data(stock_symbol, date)
            
            if stock_data is None or stock_data.empty:
                continue
            
            # Calculate entry price (first candle after entry_start_time)
            entry_details = self.algorithm.calculate_entry(
                stock_symbol, stock_data, bias
            )
            
            if entry_details is None:
                continue
            
            # Add to allocation list
            stocks_for_allocation.append({
                'symbol': stock_symbol,
                'entry_price': entry_details['entry_price'],
                'confidence': suggestion['confidence'],
                'bias': bias,
                'stock_data': stock_data,
                'entry_details': entry_details,
                'ai_reason': suggestion.get('reason', 'N/A')
            })
        
        if not stocks_for_allocation:
            return
        
        # ALLOCATE CAPITAL ACROSS ALL STOCKS
        allocator = StockAllocator(ALGORITHM_CONFIG)
        allocated_stocks = allocator.allocate_capital(stocks_for_allocation)
        
        if not allocated_stocks:
            print(f"  No capital allocated for {date}")
            return
        
        # SIMULATE TRADES FOR ALLOCATED STOCKS
        for stock in allocated_stocks:
            # Override quantity in entry_details with allocated quantity
            stock['entry_details']['quantity'] = stock['quantity']
            stock['entry_details']['stop_loss'] = stock['stop_loss']
            stock['entry_details']['target'] = stock['target']
            stock['entry_details']['capital_allocated'] = stock['capital_allocated']
            
            # Simulate trade with allocated position
            trade_result = self.algorithm.simulate_trade(
                stock['entry_details'], stock['stock_data'], date
            )
            
            if trade_result is None:
                continue
            
            # Add allocation info
            trade_result['prompt_type'] = prompt_type
            trade_result['confidence'] = stock['confidence']
            trade_result['ai_reason'] = stock['ai_reason']
            trade_result['allocated_quantity'] = stock['quantity']
            trade_result['allocated_capital'] = stock['capital_allocated']
            trade_result['signal_weight'] = stock['weight']
            
            # Store trade
            self.all_trades.append(trade_result)
    
    def _print_summary(self):
        """
        Print summary of results.
        """
        if not self.all_trades:
            print("\n⚠️  No trades executed")
            return
        
        print("\n" + "=" * 80)
        print("BACKTEST SUMMARY")
        print("=" * 80)
        
        import pandas as pd
        df = pd.DataFrame(self.all_trades)
        
        print(f"\nTotal Trades: {len(df)}")
        print(f"Total Days: {df['date'].nunique()}")
        print(f"Prompts Tested: {df['prompt_type'].nunique()}")
        
        print("\n" + "-" * 80)
        print("PROMPT PERFORMANCE RANKING")
        print("-" * 80)
        
        # Group by prompt
        for prompt_type, group in df.groupby('prompt_type'):
            net_pnl = group['net_pnl'].sum()
            win_rate = (group['net_pnl'] > 0).sum() / len(group) * 100
            
            print(f"\n{prompt_type}:")
            print(f"  Trades: {len(group)}")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Net P&L: ₹{net_pnl:,.2f}")
        
        print("\n" + "=" * 80)
        print(f"Excel Report: {BACKTEST_CONFIG['output_folder']}/{BACKTEST_CONFIG['output_file']}")
        print("=" * 80)


def main():
    """
    Main entry point.
    """
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║               30-DAY REAL INTRADAY BACKTESTING SYSTEM                        ║
    ║                                                                              ║
    ║  Data Source: Yahoo Finance (REAL historical data)                           ║
    ║  News Source: Finnhub (REAL news sentiment)                                  ║
    ║  AI Model: Mistral AI (REAL AI suggestions)                                  ║
    ║  Testing: 5 Different AI Prompt Strategies                                   ║
    ║  Period: Last 30 Trading Days                                                ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        backtester = Real30DayBacktester()
        backtester.run_backtest()
        
        print("\n✅ BACKTEST COMPLETE!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
