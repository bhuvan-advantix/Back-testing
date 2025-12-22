"""
Stock Allocation Algorithm for Intraday Trading

Implements the 7-step algorithm for distributing capital across multiple stocks
based on AI signal strength weights and risk management principles.

Based on the mathematical framework:
- Signal strength from expectancy calculation
- Risk-based position sizing
- Capital allocation with constraints
"""

from typing import List, Dict
import math


class StockAllocator:
    """
    Allocates trading capital across multiple stocks using risk-based position sizing.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize allocator with configuration.
        
        Args:
            config: Dictionary with:
                - daily_capital: Total capital available
                - basket_loss_percent: Max basket loss % (L%)
                - basket_profit_percent: Target basket profit % (G%)
                - risk_reward_ratio: Risk-reward ratio (R)
                - stop_loss_percent: Stop loss % per stock (s%)
                - capital_cap_percent: Max capital per stock % (c%)
        """
        self.total_capital = config['daily_capital']
        self.basket_loss_percent = config.get('basket_loss_percent', 2.0)
        self.basket_profit_percent = config.get('basket_profit_percent', 4.0)
        self.risk_reward_ratio = config.get('risk_reward_ratio', 2.0)
        self.stop_loss_percent = config['stop_loss_percent']
        self.capital_cap_percent = config.get('capital_cap_percent', 30.0)
    
    def allocate_capital(self, stocks: List[Dict]) -> List[Dict]:
        """
        Allocate capital across stocks using the 7-step algorithm.
        
        Args:
            stocks: List of stock dictionaries with:
                - symbol: Stock symbol
                - entry_price: Entry price
                - confidence: AI confidence score (0-100)
                - bias: BULLISH or BEARISH
        
        Returns:
            List of stocks with allocation details added:
                - weight: Normalized weight
                - quantity: Shares to buy
                - capital_allocated: Capital used
                - stop_loss: Stop loss price
                - target: Target price
                - max_loss: Maximum loss for this position
                - target_profit: Target profit for this position
        """
        if not stocks or len(stocks) == 0:
            return []
        
        # STEP 1: Normalize Weights from AI Confidence
        total_confidence = sum(stock['confidence'] for stock in stocks)
        
        for stock in stocks:
            stock['weight'] = stock['confidence'] / total_confidence if total_confidence > 0 else 1.0 / len(stocks)
        
        # STEP 2: Per-Stock Loss Cap
        max_basket_loss = self.total_capital * (self.basket_loss_percent / 100)
        
        for stock in stocks:
            stock['loss_cap'] = max_basket_loss * stock['weight']
        
        # STEP 3: Entry, Stop, Target Calculation
        for stock in stocks:
            entry = stock['entry_price']
            
            if stock['bias'] == 'BULLISH':
                # Long position
                stock['stop_loss'] = entry * (1 - self.stop_loss_percent / 100)
                risk_per_share = entry - stock['stop_loss']
                stock['target'] = entry + (risk_per_share * self.risk_reward_ratio)
            else:
                # Short position (for future implementation)
                stock['stop_loss'] = entry * (1 + self.stop_loss_percent / 100)
                risk_per_share = stock['stop_loss'] - entry
                stock['target'] = entry - (risk_per_share * self.risk_reward_ratio)
        
        # STEP 4: Raw Quantity from Risk
        for stock in stocks:
            entry = stock['entry_price']
            risk_per_share = abs(entry - stock['stop_loss'])
            
            if risk_per_share > 0:
                stock['raw_quantity'] = stock['loss_cap'] / risk_per_share
            else:
                stock['raw_quantity'] = 0
        
        # STEP 5: Capital Cap Per Stock
        max_capital_per_stock = self.total_capital * (self.capital_cap_percent / 100)
        
        for stock in stocks:
            entry = stock['entry_price']
            
            # Apply capital cap
            capped_quantity = min(
                stock['raw_quantity'],
                max_capital_per_stock / entry if entry > 0 else 0
            )
            
            # Floor to integer shares (at least 1 if we can afford it)
            floored_qty = math.floor(capped_quantity)
            stock['quantity'] = floored_qty if floored_qty > 0 else (1 if entry <= max_capital_per_stock else 0)
        
        # STEP 6: Total Capital Check & Scaling
        capital_used = sum(stock['quantity'] * stock['entry_price'] for stock in stocks)
        
        if capital_used > self.total_capital:
            # Scale down all positions proportionally
            scale_factor = self.total_capital / capital_used
            
            for stock in stocks:
                stock['quantity'] = math.floor(stock['quantity'] * scale_factor)
            
            # Recalculate capital used
            capital_used = sum(stock['quantity'] * stock['entry_price'] for stock in stocks)
        
        # STEP 7: Calculate Final Allocation Details
        for stock in stocks:
            stock['capital_allocated'] = stock['quantity'] * stock['entry_price']
            stock['max_loss'] = stock['quantity'] * abs(stock['entry_price'] - stock['stop_loss'])
            stock['target_profit'] = stock['quantity'] * abs(stock['target'] - stock['entry_price'])
        
        # Filter out stocks with zero quantity
        allocated_stocks = [s for s in stocks if s['quantity'] > 0]
        
        return allocated_stocks
    
    def validate_allocation(self, allocated_stocks: List[Dict]) -> Dict:
        """
        Validate allocation against constraints.
        
        Returns:
            Dictionary with validation results and summary statistics
        """
        if not allocated_stocks:
            return {
                'valid': False,
                'capital_used': 0,
                'total_risk': 0,
                'total_target': 0,
                'errors': ['No stocks allocated']
            }
        
        capital_used = sum(s['capital_allocated'] for s in allocated_stocks)
        total_risk = sum(s['max_loss'] for s in allocated_stocks)
        total_target = sum(s['target_profit'] for s in allocated_stocks)
        
        expected_max_loss = self.total_capital * (self.basket_loss_percent / 100)
        expected_min_profit = self.total_capital * (self.basket_profit_percent / 100)
        
        errors = []
        
        if capital_used > self.total_capital:
            errors.append(f'Capital used (₹{capital_used:.2f}) exceeds total capital (₹{self.total_capital:.2f})')
        
        if total_risk > expected_max_loss * 1.1:  # 10% tolerance
            errors.append(f'Total risk (₹{total_risk:.2f}) exceeds expected max loss (₹{expected_max_loss:.2f})')
        
        return {
            'valid': len(errors) == 0,
            'capital_used': capital_used,
            'capital_remaining': self.total_capital - capital_used,
            'total_risk': total_risk,
            'total_target': total_target,
            'actual_risk_reward': total_target / total_risk if total_risk > 0 else 0,
            'utilization_percent': (capital_used / self.total_capital * 100) if self.total_capital > 0 else 0,
            'errors': errors
        }


def calculate_expectancy(trades: List[Dict]) -> Dict:
    """
    Calculate trading expectancy from historical trades.
    
    Args:
        trades: List of trade dictionaries with 'net_pnl' field
    
    Returns:
        Dictionary with:
            - win_rate: Win rate percentage
            - avg_win: Average profit per winning trade
            - avg_loss: Average loss per losing trade
            - expectancy: Expected profit per trade
            - signal_strength: Clipped expectancy (>= 0)
    """
    if not trades or len(trades) == 0:
        return {
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'expectancy': 0,
            'signal_strength': 0,
            'total_trades': 0
        }
    
    wins = [t['net_pnl'] for t in trades if t['net_pnl'] > 0]
    losses = [t['net_pnl'] for t in trades if t['net_pnl'] < 0]
    
    win_rate = len(wins) / len(trades)
    loss_rate = len(losses) / len(trades)
    
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0
    
    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
    signal_strength = max(0, expectancy)
    
    return {
        'win_rate': win_rate * 100,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'expectancy': expectancy,
        'signal_strength': signal_strength,
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses)
    }
