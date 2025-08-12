# --- Enhanced Position Sizing Module ---
"""
Dynamic position sizing berdasarkan volatility dan risk management
Professional-grade position sizing untuk maximize profit dengan controlled risk
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class DynamicPositionSizer:
    """Professional position sizing dengan multiple methods"""
    
    def __init__(self):
        self.min_lot_size = 0.01
        self.max_lot_size = 10.0
        self.base_risk_percent = 2.0  # 2% base risk per trade
        self.volatility_multiplier = 1.5
        self.correlation_adjustment = 0.8
        
    def calculate_optimal_position_size(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_loss: float, 
        strategy: str = "Scalping",
        account_info: dict = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate optimal position size using multiple factors:
        1. ATR-based volatility sizing
        2. Account equity percentage risk
        3. Strategy-specific adjustments
        4. Symbol-specific risk factors
        5. Correlation risk adjustment
        """
        
        try:
            # Get account information
            if not account_info:
                account_info = self._get_account_info()
            
            if not account_info:
                logger("❌ Cannot get account info for position sizing")
                return self.min_lot_size, {"error": "No account info"}
            
            balance = account_info.get('balance', 10000)
            equity = account_info.get('equity', balance)
            currency = account_info.get('currency', 'USD')
            
            # Get symbol information
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger(f"❌ Cannot get symbol info for {symbol}")
                return self.min_lot_size, {"error": "No symbol info"}
            
            # Calculate risk parameters
            price_diff = abs(entry_price - stop_loss)
            if price_diff <= 0:
                logger(f"❌ Invalid price difference: {price_diff}")
                return self.min_lot_size, {"error": "Invalid price diff"}
            
            # Method 1: ATR-based volatility sizing
            atr_size = self._calculate_atr_based_size(symbol, balance, price_diff)
            
            # Method 2: Equity percentage risk sizing
            equity_size = self._calculate_equity_risk_size(equity, entry_price, stop_loss, symbol_info)
            
            # Method 3: Strategy-specific adjustments
            strategy_size = self._apply_strategy_adjustments(
                atr_size, equity_size, strategy, symbol
            )
            
            # Method 4: Correlation risk adjustment
            final_size = self._apply_correlation_adjustment(strategy_size, symbol)
            
            # Apply symbol-specific limits
            final_size = self._apply_symbol_limits(final_size, symbol_info)
            
            # Comprehensive sizing details
            sizing_details = {
                "method": "Dynamic Multi-Factor Sizing",
                "atr_based_size": round(atr_size, 2),
                "equity_risk_size": round(equity_size, 2), 
                "strategy_adjusted": round(strategy_size, 2),
                "correlation_adjusted": round(final_size, 2),
                "risk_percent": self._calculate_actual_risk_percent(
                    final_size, entry_price, stop_loss, balance
                ),
                "strategy": strategy,
                "symbol": symbol,
                "account_currency": currency,
                "balance": balance,
                "equity": equity
            }
            
            logger(f"💰 Dynamic Position Size for {symbol}: {final_size} lots")
            logger(f"   Risk: {sizing_details['risk_percent']:.2f}% | Strategy: {strategy}")
            
            return max(self.min_lot_size, min(final_size, self.max_lot_size)), sizing_details
            
        except Exception as e:
            logger(f"❌ Error calculating position size: {str(e)}")
            return self.min_lot_size, {"error": str(e)}
    
    def _calculate_atr_based_size(self, symbol: str, balance: float, price_diff: float) -> float:
        """Calculate position size based on ATR volatility"""
        try:
            # Get recent price data for ATR calculation
            from data_manager import get_symbol_data
            df = get_symbol_data(symbol, count=50)
            
            if df is None or len(df) < 14:
                logger(f"⚠️ Insufficient data for ATR calculation: {symbol}")
                return balance * 0.0001  # Conservative fallback
            
            # Calculate ATR
            from indicators import atr
            df['ATR'] = atr(df, period=14)
            current_atr = df['ATR'].iloc[-1]
            
            if pd.isna(current_atr) or current_atr <= 0:
                logger(f"⚠️ Invalid ATR for {symbol}: {current_atr}")
                return balance * 0.0001
            
            # ATR-based risk calculation
            # Higher ATR = lower position size for same risk
            atr_risk_factor = price_diff / current_atr
            base_size = (balance * self.base_risk_percent / 100) / price_diff
            
            # Adjust based on volatility
            if atr_risk_factor > 2.0:  # High volatility
                volatility_adjustment = 0.7
            elif atr_risk_factor > 1.0:  # Medium volatility  
                volatility_adjustment = 0.85
            else:  # Low volatility
                volatility_adjustment = 1.2
            
            atr_size = base_size * volatility_adjustment
            
            logger(f"📊 ATR Analysis for {symbol}: ATR={current_atr:.5f}, Risk Factor={atr_risk_factor:.2f}")
            
            return atr_size
            
        except Exception as e:
            logger(f"❌ ATR calculation error for {symbol}: {str(e)}")
            return balance * 0.0001
    
    def _calculate_equity_risk_size(self, equity: float, entry_price: float, 
                                  stop_loss: float, symbol_info) -> float:
        """Calculate position size based on equity percentage risk"""
        try:
            # Determine risk percentage based on account size
            if equity > 100000:  # Large account
                risk_percent = 1.5
            elif equity > 50000:  # Medium account
                risk_percent = 2.0
            elif equity > 10000:  # Small account
                risk_percent = 2.5
            else:  # Very small account
                risk_percent = 3.0
                
            # Calculate position size
            risk_amount = equity * (risk_percent / 100)
            price_difference = abs(entry_price - stop_loss)
            
            # Get pip value for the symbol
            pip_value = self._get_pip_value(symbol_info, equity)
            
            if pip_value > 0 and price_difference > 0:
                pips_at_risk = price_difference / symbol_info.point
                lot_size = risk_amount / (pips_at_risk * pip_value)
            else:
                # Fallback calculation
                lot_size = risk_amount / price_difference
                
            return lot_size
            
        except Exception as e:
            logger(f"❌ Equity risk calculation error: {str(e)}")
            return 0.01
    
    def _apply_strategy_adjustments(self, atr_size: float, equity_size: float, 
                                  strategy: str, symbol: str) -> float:
        """Apply strategy-specific position size adjustments"""
        try:
            # Use the more conservative of the two sizes as base
            base_size = min(atr_size, equity_size)
            
            # Strategy multipliers based on typical risk/reward profiles
            strategy_multipliers = {
                "Scalping": 1.2,      # Smaller stops, more frequent trades
                "Intraday": 1.0,      # Balanced approach
                "Arbitrage": 0.8,     # Lower risk, smaller positions
                "HFT": 1.5            # Very short duration, tighter risk control
            }
            
            # Symbol type adjustments
            symbol_upper = symbol.upper()
            if 'JPY' in symbol_upper:
                symbol_adjustment = 0.85  # JPY pairs typically more volatile
            elif 'GBP' in symbol_upper:
                symbol_adjustment = 0.8   # GBP very volatile
            elif 'XAU' in symbol_upper or 'GOLD' in symbol_upper:
                symbol_adjustment = 0.6   # Gold very volatile
            elif 'EUR' in symbol_upper or 'USD' in symbol_upper:
                symbol_adjustment = 1.0   # Major pairs, normal sizing
            else:
                symbol_adjustment = 0.75  # Exotic pairs, more conservative
            
            strategy_multiplier = strategy_multipliers.get(strategy, 1.0)
            adjusted_size = base_size * strategy_multiplier * symbol_adjustment
            
            logger(f"🎯 Strategy adjustment for {strategy}: {strategy_multiplier}x, Symbol: {symbol_adjustment}x")
            
            return adjusted_size
            
        except Exception as e:
            logger(f"❌ Strategy adjustment error: {str(e)}")
            return min(atr_size, equity_size)
    
    def _apply_correlation_adjustment(self, base_size: float, symbol: str) -> float:
        """Adjust position size based on existing correlated positions"""
        try:
            # Get current positions
            positions = mt5.positions_get()
            if not positions:
                return base_size  # No positions, no correlation risk
            
            # Define correlation groups
            correlation_groups = {
                'EUR': ['EURUSD', 'EURJPY', 'EURGBP', 'EURAUD', 'EURCHF'],
                'GBP': ['GBPUSD', 'GBPJPY', 'EURGBP', 'GBPAUD', 'GBPCHF'], 
                'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CHFJPY'],
                'GOLD': ['XAUUSD', 'XAUEUR', 'GOLD'],
                'OIL': ['CRUDE', 'OIL', 'WTI', 'BRENT']
            }
            
            # Check for correlation exposure
            current_exposure = 0
            symbol_group = None
            
            for group, symbols in correlation_groups.items():
                if any(curr in symbol.upper() for curr in symbols if curr in symbol.upper()):
                    symbol_group = group
                    break
            
            if symbol_group:
                # Count positions in the same correlation group
                correlated_positions = 0
                for pos in positions:
                    pos_symbol = pos.symbol.upper()
                    if any(curr in pos_symbol for curr in correlation_groups[symbol_group]):
                        correlated_positions += 1
                        current_exposure += pos.volume
                
                # Apply correlation adjustment
                if correlated_positions > 0:
                    correlation_factor = max(0.5, 1 - (correlated_positions * 0.2))
                    adjusted_size = base_size * correlation_factor
                    
                    logger(f"⚖️ Correlation adjustment: {correlated_positions} positions in {symbol_group} group")
                    logger(f"   Reduction factor: {correlation_factor:.2f}")
                    
                    return adjusted_size
            
            return base_size
            
        except Exception as e:
            logger(f"❌ Correlation adjustment error: {str(e)}")
            return base_size
    
    def _apply_symbol_limits(self, size: float, symbol_info) -> float:
        """Apply symbol-specific limits and constraints"""
        try:
            # Get symbol constraints
            min_volume = getattr(symbol_info, 'volume_min', 0.01)
            max_volume = getattr(symbol_info, 'volume_max', 100.0)
            volume_step = getattr(symbol_info, 'volume_step', 0.01)
            
            # Round to valid step size
            if volume_step > 0:
                size = round(size / volume_step) * volume_step
            
            # Apply min/max constraints
            size = max(min_volume, min(size, max_volume))
            
            # Additional safety limits
            size = max(self.min_lot_size, min(size, self.max_lot_size))
            
            return size
            
        except Exception as e:
            logger(f"❌ Symbol limits error: {str(e)}")
            return max(self.min_lot_size, min(size, self.max_lot_size))
    
    def _get_account_info(self) -> Dict[str, Any]:
        """Get current account information"""
        try:
            account = mt5.account_info()
            if account:
                return {
                    'balance': account.balance,
                    'equity': account.equity,
                    'currency': account.currency,
                    'leverage': account.leverage,
                    'margin_free': account.margin_free
                }
            return None
        except Exception as e:
            logger(f"❌ Account info error: {str(e)}")
            return None
    
    def _get_pip_value(self, symbol_info, account_balance: float) -> float:
        """Calculate pip value for position sizing"""
        try:
            # Standard pip values for major pairs (approximate)
            pip_values = {
                'EURUSD': 10.0, 'GBPUSD': 10.0, 'AUDUSD': 10.0, 'NZDUSD': 10.0,
                'USDJPY': 9.0, 'USDCHF': 10.0, 'USDCAD': 8.0,
                'EURJPY': 9.0, 'GBPJPY': 9.0, 'AUDJPY': 9.0,
                'XAUUSD': 100.0  # Gold
            }
            
            symbol_name = symbol_info.name.upper()
            return pip_values.get(symbol_name, 10.0)  # Default pip value
            
        except Exception as e:
            logger(f"❌ Pip value calculation error: {str(e)}")
            return 10.0
    
    def _calculate_actual_risk_percent(self, lot_size: float, entry_price: float, 
                                     stop_loss: float, balance: float) -> float:
        """Calculate actual risk percentage for logging"""
        try:
            price_diff = abs(entry_price - stop_loss)
            risk_amount = lot_size * price_diff
            risk_percent = (risk_amount / balance) * 100
            return risk_percent
        except:
            return 0.0


# Global instance for use across the application
position_sizer = DynamicPositionSizer()


def get_dynamic_position_size(symbol: str, entry_price: float, stop_loss: float, 
                            strategy: str = "Scalping") -> Tuple[float, Dict[str, Any]]:
    """
    Main function to get optimized position size
    This replaces any fixed lot size calculations
    """
    return position_sizer.calculate_optimal_position_size(
        symbol, entry_price, stop_loss, strategy
    )


def update_position_sizer_settings(base_risk_percent: float = None, 
                                 volatility_multiplier: float = None,
                                 max_lot_size: float = None):
    """Update position sizer settings"""
    global position_sizer
    
    if base_risk_percent is not None:
        position_sizer.base_risk_percent = base_risk_percent
        logger(f"📊 Updated base risk percent: {base_risk_percent}%")
    
    if volatility_multiplier is not None:
        position_sizer.volatility_multiplier = volatility_multiplier
        logger(f"📊 Updated volatility multiplier: {volatility_multiplier}")
    
    if max_lot_size is not None:
        position_sizer.max_lot_size = max_lot_size
        logger(f"📊 Updated max lot size: {max_lot_size}")