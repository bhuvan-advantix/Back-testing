"""
Multi-Timeframe Backtest Runner
Tests ALL candle timeframes (1m, 5m, 15m, 30m, 1h) in one run
"""

from typing import Dict, List
from tqdm import tqdm
import time

from config_real import (
    AI_PROMPTS, ALGORITHM_CONFIG, BACKTEST_CONFIG, DATA_CONFIG,
    MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL,
    GEMINI_API_KEY, FINNHUB_API_KEY, MAX_STOCKS_LIMIT
)
from yahoo_data_fetcher import YahooDataFetcher
from finnhub_fetcher import FinnhubNewsFetcher
from mistral_ai_engine import MistralAIEngine
from real_algorithm_engine import RealAlgorithmEngine
from real_excel_reporter import RealExcelReporter


class MultiTimeframeBacktester:
    """
    Runs backtests across MULTIPLE candle timeframes.
    """
    
    def __init__(self):
        """
        Initialize components.
        """
        print("=" * 80)
        print("MULTI-TIMEFRAME BACKTESTING SYSTEM")
        print("=" * 80)
        
        # Get timeframes to test
        self.timeframes = DATA_CONFIG.get('candle_intervals_to_test', ['5m'])
        
        # Initialize news fetcher (shared across all timeframes)
        self.news_fetcher = FinnhubNewsFetcher(FINNHUB_API_KEY)
        
        # Initialize algorithm (shared)
        self.algorithm = RealAlgorithmEngine(ALGORITHM_CONFIG)
        
        # Initialize reporter
        self.reporter = RealExcelReporter(BACKTEST_CONFIG['output_folder'])
        
        print(f"✅ Will test {len(self.timeframes)} timeframes: {', '.join(self.timeframes)}")
        print()
    
    def run_backtest(self):
        """
        Run backtest for ALL timeframes.
        """
        all_results = []
        
        # Test each timeframe
        for timeframe in self.timeframes:
            print("\n" + "=" * 80)
            print(f"TESTING TIMEFRAME: {timeframe}")
            print("=" * 80)
            
            # Determine appropriate backtest days for this timeframe
            backtest_days = self._get_backtest_days_for_timeframe(timeframe)
            
            print(f"Using {backtest_days} days for {timeframe} candles")
            
            # Initialize Yahoo fetcher for this timeframe
            yahoo_fetcher = YahooDataFetcher(candle_interval=timeframe)
            
            # Get trading days
            trading_days = yahoo_fetcher.get_last_n_trading_days(backtest_days)
            
            print(f"Found {len(trading_days)} trading days")
            print(f"From: {trading_days[0]} to {trading_days[-1]}")
            print()
            
            # Run backtest for each prompt
            timeframe_trades = []
            
            for prompt_type, prompt_config in AI_PROMPTS.items():
                print(f"\nTesting {prompt_type} with {timeframe} candles...")
                
                # Add type to config
                prompt_config['type'] = prompt_type
                
                # Initialize AI engine
                ai_engine = MistralAIEngine(
                    MISTRAL_API_KEY,
                    MISTRAL_API_URL,
                    MISTRAL_MODEL,
                    prompt_config
                )
                
                # Run backtest for each day
                for date in tqdm(trading_days, desc=f"{prompt_type} ({timeframe})"):
                    trades = self._backtest_single_day(
                        date, prompt_type, ai_engine, yahoo_fetcher, timeframe
                    )
                    timeframe_trades.extend(trades)
                    time.sleep(1)  # Rate limiting
            
            # Add timeframe info to all trades
            for trade in timeframe_trades:
                trade['timeframe'] = timeframe
            
            all_results.extend(timeframe_trades)
            
            print(f"\n✅ Completed {timeframe}: {len(timeframe_trades)} trades")
        
        # Generate combined Excel report
        print("\n" + "=" * 80)
        print("GENERATING COMBINED EXCEL REPORT")
        print("=" * 80)
        
        output_file = 'ai_multi_timeframe_backtest.xlsx'
        self.reporter.generate_report(all_results, output_file)
        
        # Print summary
        self._print_summary(all_results)
    
    def _get_backtest_days_for_timeframe(self, timeframe: str) -> int:
        """
        Get appropriate backtest days based on timeframe.
        """
        timeframe_limits = {
            '1m': 7,     # 1-minute: max 7 days
            '5m': 30,    # 5-minute: 30 days
            '15m': 30,   # 15-minute: 30 days
            '30m': 60,   # 30-minute: 60 days
            '1h': 90     # 1-hour: 90 days
        }
        
        return timeframe_limits.get(timeframe, 30)
    
    def _backtest_single_day(self, date: str, prompt_type: str, ai_engine, 
                            yahoo_fetcher, timeframe: str) -> List[Dict]:
        """
        Backtest a single day for a specific prompt and timeframe.
        """
        trades = []
        
        # Get market context
        market_context = self.news_fetcher.get_market_context(date)
        
        # Get AI suggestions
        suggestions = ai_engine.suggest_stocks(date, market_context, "")
        
        if not suggestions:
            return trades
        
        # Limit to MAX_STOCKS_LIMIT
        suggestions = suggestions[:MAX_STOCKS_LIMIT]
        
        # Process each suggestion
        for suggestion in suggestions:
            stock_symbol = suggestion['symbol']
            bias = suggestion['bias']
            
            # Fetch intraday data
            stock_data = yahoo_fetcher.fetch_intraday_data(stock_symbol, date)
            
            if stock_data is None or stock_data.empty:
                continue
            
            # Calculate entry
            entry_details = self.algorithm.calculate_entry(
                stock_symbol, stock_data, bias
            )
            
            if entry_details is None:
                continue
            
            # Simulate trade
            trade_result = self.algorithm.simulate_trade(
                entry_details, stock_data, date
            )
            
            if trade_result is None:
                continue
            
            # Add prompt info and AI reasoning
            trade_result['prompt_type'] = prompt_type
            trade_result['confidence'] = suggestion['confidence']
            trade_result['ai_reason'] = suggestion.get('reason', 'N/A')
            
            trades.append(trade_result)
        
        return trades
    
    def _print_summary(self, all_trades: List[Dict]):
        """
        Print summary of results across all timeframes.
        """
        if not all_trades:
            print("\n⚠️  No trades executed")
            return
        
        import pandas as pd
        df = pd.DataFrame(all_trades)
        
        print("\n" + "=" * 80)
        print("MULTI-TIMEFRAME BACKTEST SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal Trades: {len(df)}")
        print(f"Timeframes Tested: {df['timeframe'].nunique()}")
        print(f"Prompts Tested: {df['prompt_type'].nunique()}")
        
        print("\n" + "-" * 80)
        print("PERFORMANCE BY TIMEFRAME")
        print("-" * 80)
        
        for timeframe, group in df.groupby('timeframe'):
            net_pnl = group['net_pnl'].sum()
            win_rate = (group['net_pnl'] > 0).sum() / len(group) * 100
            
            print(f"\n{timeframe} Candles:")
            print(f"  Trades: {len(group)}")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Net P&L: ₹{net_pnl:,.2f}")
        
        print("\n" + "-" * 80)
        print("BEST TIMEFRAME + PROMPT COMBINATIONS")
        print("-" * 80)
        
        # Group by timeframe and prompt
        for (timeframe, prompt), group in df.groupby(['timeframe', 'prompt_type']):
            net_pnl = group['net_pnl'].sum()
            win_rate = (group['net_pnl'] > 0).sum() / len(group) * 100
            
            print(f"\n{timeframe} + {prompt}:")
            print(f"  Trades: {len(group)}")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Net P&L: ₹{net_pnl:,.2f}")
        
        print("\n" + "=" * 80)
        print(f"Excel Report: {BACKTEST_CONFIG['output_folder']}/ai_multi_timeframe_backtest.xlsx")
        print("=" * 80)


def main():
    """
    Main entry point.
    """
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║            MULTI-TIMEFRAME INTRADAY BACKTESTING SYSTEM                       ║
    ║                                                                              ║
    ║  Tests ALL candle timeframes: 1m, 5m, 15m, 30m, 1h                          ║
    ║  Data Source: Yahoo Finance (REAL historical data)                           ║
    ║  AI Model: Mistral AI (REAL AI suggestions)                                  ║
    ║  Testing: 5 AI Prompts × Multiple Timeframes                                 ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        backtester = MultiTimeframeBacktester()
        backtester.run_backtest()
        
        print("\n✅ MULTI-TIMEFRAME BACKTEST COMPLETE!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
