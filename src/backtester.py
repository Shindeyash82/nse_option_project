"""
Option-level backtester: simulate buys, premiums, theta decay.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OptionPosition:
    """Represents an option position."""
    strike: float
    option_type: str  # 'CE' or 'PE'
    premium: float
    quantity: int
    entry_time: datetime
    expiry: datetime
    iv: Optional[float] = None
    
    def __post_init__(self):
        if self.option_type not in ['CE', 'PE']:
            raise ValueError("option_type must be 'CE' or 'PE'")


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    trades: List[Dict] = None


class OptionBacktester:
    """Backtester for option trading strategies."""
    
    def __init__(self, initial_capital: float = 100000):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: List[OptionPosition] = []
        self.closed_trades: List[Dict] = []
        self.equity_curve: List[float] = []
    
    def calculate_theta(self, days_to_expiry: float, premium: float, iv: float = 0.2) -> float:
        """
        Simple theta approximation (time decay).
        
        Args:
            days_to_expiry: Days until expiry
            premium: Current premium
            iv: Implied volatility
            
        Returns:
            Theta value (premium decay per day)
        """
        if days_to_expiry <= 0:
            return premium  # Full decay if expired
        
        # Simple approximation: theta increases as expiry approaches
        theta_factor = iv * premium / (days_to_expiry + 1)
        return theta_factor
    
    def calculate_intrinsic_value(self, spot: float, strike: float, option_type: str) -> float:
        """
        Calculate intrinsic value of option.
        
        Args:
            spot: Current spot price
            strike: Strike price
            option_type: 'CE' or 'PE'
            
        Returns:
            Intrinsic value
        """
        if option_type == 'CE':
            return max(0, spot - strike)
        else:  # PE
            return max(0, strike - spot)
    
    def buy_option(
        self,
        strike: float,
        option_type: str,
        premium: float,
        quantity: int,
        entry_time: datetime,
        expiry: datetime,
        iv: Optional[float] = None
    ) -> bool:
        """
        Buy an option position.
        
        Returns:
            True if successful, False if insufficient capital
        """
        cost = premium * quantity
        
        if cost > self.capital:
            return False
        
        position = OptionPosition(
            strike=strike,
            option_type=option_type,
            premium=premium,
            quantity=quantity,
            entry_time=entry_time,
            expiry=expiry,
            iv=iv
        )
        
        self.positions.append(position)
        self.capital -= cost
        return True
    
    def close_position(
        self,
        position_idx: int,
        exit_premium: float,
        exit_time: datetime,
        spot: float
    ) -> Optional[Dict]:
        """
        Close a position and record trade.
        
        Returns:
            Trade record dictionary or None if invalid index
        """
        if position_idx < 0 or position_idx >= len(self.positions):
            return None
        
        position = self.positions.pop(position_idx)
        
        # Calculate P&L
        entry_cost = position.premium * position.quantity
        exit_value = exit_premium * position.quantity
        pnl = exit_value - entry_cost
        
        # Update capital
        self.capital += exit_value
        
        # Calculate metrics
        holding_days = (exit_time - position.entry_time).days
        intrinsic = self.calculate_intrinsic_value(spot, position.strike, position.option_type)
        
        trade_record = {
            'entry_time': position.entry_time.isoformat(),
            'exit_time': exit_time.isoformat(),
            'strike': position.strike,
            'option_type': position.option_type,
            'entry_premium': position.premium,
            'exit_premium': exit_premium,
            'quantity': position.quantity,
            'pnl': pnl,
            'return_pct': (pnl / entry_cost * 100) if entry_cost > 0 else 0,
            'holding_days': holding_days,
            'intrinsic_value': intrinsic,
            'spot_at_exit': spot
        }
        
        self.closed_trades.append(trade_record)
        return trade_record
    
    def update_positions(self, current_time: datetime, spot: float, days_passed: float = 1.0):
        """
        Update positions with theta decay and check for expiry.
        
        Args:
            current_time: Current timestamp
            spot: Current spot price
            days_passed: Number of days passed since last update
        """
        expired_positions = []
        
        for i, position in enumerate(self.positions):
            days_to_expiry = (position.expiry - current_time).days
            
            # Check expiry
            if days_to_expiry <= 0:
                expired_positions.append((i, position))
                continue
            
            # Apply theta decay (simplified)
            if position.iv:
                theta = self.calculate_theta(days_to_expiry, position.premium, position.iv)
                # Update premium (simplified - in reality, need full option pricing model)
                position.premium = max(0, position.premium - theta * days_passed)
        
        # Close expired positions
        for i, position in reversed(expired_positions):
            intrinsic = self.calculate_intrinsic_value(spot, position.strike, position.option_type)
            self.close_position(i, intrinsic, current_time, spot)
    
    def get_portfolio_value(self, current_time: datetime, spot: float) -> float:
        """
        Calculate current portfolio value (capital + position values).
        
        Args:
            current_time: Current timestamp
            spot: Current spot price
            
        Returns:
            Total portfolio value
        """
        position_value = 0
        
        for position in self.positions:
            days_to_expiry = (position.expiry - current_time).days
            
            if days_to_expiry <= 0:
                # Expired - use intrinsic value
                intrinsic = self.calculate_intrinsic_value(spot, position.strike, position.option_type)
                position_value += intrinsic * position.quantity
            else:
                # Use current premium (simplified - would need market data)
                # For now, use intrinsic + some time value approximation
                intrinsic = self.calculate_intrinsic_value(spot, position.strike, position.option_type)
                time_value = max(0, position.premium * 0.1 * (days_to_expiry / 30))  # Rough approximation
                position_value += (intrinsic + time_value) * position.quantity
        
        return self.capital + position_value
    
    def run_backtest(
        self,
        historical_data: pd.DataFrame,
        strategy_func,
        **strategy_kwargs
    ) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            historical_data: DataFrame with columns: timestamp, spot, and option chain data
            strategy_func: Function that generates buy signals
            **strategy_kwargs: Additional arguments for strategy function
            
        Returns:
            BacktestResult object
        """
        self.capital = self.initial_capital
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
        
        # Sort by timestamp
        data = historical_data.sort_values('timestamp').reset_index(drop=True)
        
        for idx, row in data.iterrows():
            current_time = pd.to_datetime(row['timestamp'])
            spot = row['spot']
            
            # Update existing positions
            days_passed = 1.0 if idx == 0 else (current_time - pd.to_datetime(data.loc[idx-1, 'timestamp'])).days
            self.update_positions(current_time, spot, days_passed)
            
            # Get strategy signals
            signals = strategy_func(row, **strategy_kwargs)
            
            # Execute trades based on signals
            if signals:
                for signal in signals:
                    if signal.get('action') == 'buy':
                        self.buy_option(
                            strike=signal['strike'],
                            option_type=signal['option_type'],
                            premium=signal['premium'],
                            quantity=signal.get('quantity', 1),
                            entry_time=current_time,
                            expiry=signal.get('expiry', current_time + timedelta(days=30)),
                            iv=signal.get('iv')
                        )
            
            # Record equity
            portfolio_value = self.get_portfolio_value(current_time, spot)
            self.equity_curve.append(portfolio_value)
        
        # Close all remaining positions at end
        final_time = pd.to_datetime(data.iloc[-1]['timestamp'])
        final_spot = data.iloc[-1]['spot']
        
        while self.positions:
            position = self.positions[0]
            intrinsic = self.calculate_intrinsic_value(final_spot, position.strike, position.option_type)
            self.close_position(0, intrinsic, final_time, final_spot)
        
        # Calculate results
        return self.calculate_results()
    
    def calculate_results(self) -> BacktestResult:
        """Calculate backtest statistics."""
        if not self.closed_trades:
            return BacktestResult(
                total_pnl=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_profit=0,
                avg_loss=0,
                max_drawdown=0,
                trades=[]
            )
        
        trades_df = pd.DataFrame(self.closed_trades)
        
        total_pnl = trades_df['pnl'].sum()
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_profit = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # Calculate max drawdown
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
        
        # Calculate Sharpe ratio
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe_ratio = None
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
        
        return BacktestResult(
            total_pnl=total_pnl,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=self.closed_trades
        )


if __name__ == "__main__":
    # Example usage
    print("Option Backtester - Example usage")
    print("Import this module and use OptionBacktester class with your strategy function")



