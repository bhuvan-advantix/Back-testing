"""
Real Algorithm Engine - Fixed trading rules applied to AI suggestions
Uses REAL market data from Yahoo Finance
"""

from typing import Dict, List, Optional
from datetime import datetime, time
import pandas as pd


class RealAlgorithmEngine:
    """
    Fixed algorithm that applies consistent trading rules to ALL AI suggestions.
    Works with REAL market data only.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize algorithm with fixed parameters.
        """
        self.config = config
        self.daily_capital = config['daily_capital']
        self.capital_per_trade = config['capital_per_trade']
        self.max_positions = config['max_positions_per_day']
        self.stop_loss_percent = config['stop_loss_percent']
        self.target_percent = config['target_percent']
        self.slippage_percent = config['slippage_percent']
        self.transaction_cost_percent = config['transaction_cost_percent']
        
        # Parse time strings
        self.market_open = datetime.strptime(config['market_open_time'], '%H:%M').time()
        self.entry_start = datetime.strptime(config['entry_start_time'], '%H:%M').time()
        self.market_close = datetime.strptime(config['market_close_time'], '%H:%M').time()
        self.force_exit_time = datetime.strptime(config['force_exit_time'], '%H:%M').time()
    
    def calculate_entry(self, stock_symbol: str, candle_data: pd.DataFrame, 
                       bias: str) -> Optional[Dict]:
        """
        Calculate entry price and position details using REAL candle data.
        """
        # Find the first valid candle after entry_start_time
        entry_candle = None
        
        for idx, candle in candle_data.iterrows():
            try:
                candle_time = datetime.strptime(str(candle['Time']), '%H:%M:%S').time()
            except:
                continue
            
            if candle_time >= self.entry_start:
                entry_candle = candle
                break
        
        if entry_candle is None:
            return None
        
        # Entry price = Open of entry candle + slippage
        base_price = float(entry_candle['Open'])
        
        if bias == 'BULLISH':
            entry_price = base_price * (1 + self.slippage_percent / 100)
        else:
            entry_price = base_price * (1 - self.slippage_percent / 100)
        
        # Calculate quantity
        quantity = int(self.capital_per_trade / entry_price)
        
        if quantity == 0:
            return None
        
        # Calculate stop loss and target
        if bias == 'BULLISH':
            stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
            target = entry_price * (1 + self.target_percent / 100)
        else:
            stop_loss = entry_price * (1 + self.stop_loss_percent / 100)
            target = entry_price * (1 - self.target_percent / 100)
        
        invested_amount = entry_price * quantity
        
        return {
            'symbol': stock_symbol,
            'entry_time': str(entry_candle['Time']),
            'entry_price': round(entry_price, 2),
            'quantity': quantity,
            'bias': bias,
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'invested_amount': round(invested_amount, 2)
        }
    
    def simulate_trade(self, entry_details: Dict, candle_data: pd.DataFrame, 
                      trade_date: str) -> Dict:
        """
        Simulate complete trade using REAL candle-by-candle data.
        """
        entry_time = entry_details['entry_time']
        entry_price = entry_details['entry_price']
        quantity = entry_details['quantity']
        bias = entry_details['bias']
        stop_loss = entry_details['stop_loss']
        target = entry_details['target']
        invested_amount = entry_details['invested_amount']
        
        # Find entry candle index
        entry_idx = None
        for idx, candle in candle_data.iterrows():
            if str(candle['Time']) == entry_time:
                entry_idx = idx
                break
        
        if entry_idx is None:
            return None
        
        # Simulate candle by candle
        exit_price = None
        exit_time = None
        exit_reason = None
        
        for idx in range(entry_idx + 1, len(candle_data)):
            candle = candle_data.iloc[idx]
            
            try:
                candle_time = datetime.strptime(str(candle['Time']), '%H:%M:%S').time()
            except:
                continue
            
            # Force exit check
            if candle_time >= self.force_exit_time:
                exit_price = float(candle['Close'])
                exit_time = str(candle['Time'])
                exit_reason = 'FORCE_EXIT_EOD'
                break
            
            # Check stop loss and target
            candle_high = float(candle['High'])
            candle_low = float(candle['Low'])
            
            if bias == 'BULLISH':
                # Check stop loss first (conservative)
                if candle_low <= stop_loss:
                    exit_price = stop_loss
                    exit_time = str(candle['Time'])
                    exit_reason = 'STOP_LOSS'
                    break
                # Then check target
                elif candle_high >= target:
                    exit_price = target
                    exit_time = str(candle['Time'])
                    exit_reason = 'TARGET'
                    break
            else:
                # For short positions
                if candle_high >= stop_loss:
                    exit_price = stop_loss
                    exit_time = str(candle['Time'])
                    exit_reason = 'STOP_LOSS'
                    break
                elif candle_low <= target:
                    exit_price = target
                    exit_time = str(candle['Time'])
                    exit_reason = 'TARGET'
                    break
        
        # If no exit found, force exit at last candle
        if exit_price is None:
            last_candle = candle_data.iloc[-1]
            exit_price = float(last_candle['Close'])
            exit_time = str(last_candle['Time'])
            exit_reason = 'FORCE_EXIT_EOD'
        
        # Apply slippage on exit
        if bias == 'BULLISH':
            exit_price = exit_price * (1 - self.slippage_percent / 100)
        else:
            exit_price = exit_price * (1 + self.slippage_percent / 100)
        
        # Calculate P&L
        if bias == 'BULLISH':
            gross_pnl = (exit_price - entry_price) * quantity
        else:
            gross_pnl = (entry_price - exit_price) * quantity
        
        # Transaction costs
        transaction_cost = invested_amount * 2 * (self.transaction_cost_percent / 100)
        net_pnl = gross_pnl - transaction_cost
        
        return {
            'date': trade_date,
            'symbol': entry_details['symbol'],
            'bias': bias,
            'entry_time': entry_time,
            'entry_price': round(entry_price, 2),
            'exit_time': exit_time,
            'exit_price': round(exit_price, 2),
            'quantity': quantity,
            'invested_amount': round(invested_amount, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'exit_reason': exit_reason,
            'gross_pnl': round(gross_pnl, 2),
            'transaction_cost': round(transaction_cost, 2),
            'net_pnl': round(net_pnl, 2),
            'profit_or_loss': 'PROFIT' if net_pnl > 0 else ('LOSS' if net_pnl < 0 else 'BREAKEVEN')
        }
