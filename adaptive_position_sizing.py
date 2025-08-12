# --- Adaptive Position Sizing Module ---
"""
Professional position sizing based on:
- ATR volatility
- Account equity
- Strategy-specific risk parameters
- Correlation risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class AdaptivePositionSizer:
    """Professional position sizing untuk profit optimization"""
    
    def __init__(self):
        # Risk parameters per strategy
        self.strategy_risk_params = {
            'Scalping': {
                'max_risk_per_trade': 0.01,  # 1% of equity
                'atr_multiplier': 2.0,       # 2x ATR for SL
                'max_correlation_exposure': 0.03,  # 3% total correlation risk
                'volatility_adjustment': True
            },
            'Intraday': {
                'max_risk_per_trade': 0.015,  # 1.5% of equity
                'atr_multiplier': 2.5,
                'max_correlation_exposure': 0.04,
                'volatility_adjustment': True
            },
            'HFT': {
                'max_risk_per_trade': 0.005,  # 0.5% of equity
                'atr_multiplier': 1.5,
                'max_correlation_exposure': 0.02,
                'volatility_adjustment': True
            },
            'Arbitrage': {
                'max_risk_per_trade': 0.02,   # 2% of equity
                'atr_multiplier': 3.0,
                'max_correlation_exposure': 0.05,
                'volatility_adjustment': False
            }
        }
        
        # Symbol-specific parameters
        self.symbol_params = {
            'EURUSD': {'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01},
            'GBPUSD': {'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01},
            'USDJPY': {'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01},
            'XAUUSD': {'min_lot': 0.01, 'max_lot': 0.1, 'lot_step': 0.01},
            'USDCAD': {'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01},
            'AUDUSD': {'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01}
        }

    def calculate_optimal_position_size(self, symbol: str, strategy: str, 
                                      entry_price: float, stop_loss: float, 
                                      confidence: float = 1.0) -> Dict[str, Any]:
        """Calculate optimal position size based on multiple factors"""
        try:
            logger(f"🔢 Calculating position size for {symbol} - {strategy}")
            
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                return self._get_fallback_position_size(symbol)
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return self._get_fallback_position_size(symbol)
            
            # Get strategy parameters
            strategy_params = self.strategy_risk_params.get(strategy, self.strategy_risk_params['Scalping'])
            
            # Calculate base position size using different methods
            equity_based_size = self._calculate_equity_based_size(
                account_info, strategy_params, entry_price, stop_loss, symbol_info
            )
            
            atr_based_size = self._calculate_atr_based_size(
                symbol, strategy_params, entry_price, stop_loss, symbol_info
            )
            
            # Get current volatility adjustment
            volatility_multiplier = self._get_volatility_adjustment(symbol, strategy_params)
            
            # Apply confidence adjustment
            confidence_multiplier = min(confidence, 1.0)
            
            # Combine methods (weighted average)
            base_size = (equity_based_size * 0.6 + atr_based_size * 0.4)
            
            # Apply adjustments
            adjusted_size = base_size * volatility_multiplier * confidence_multiplier
            
            # Apply symbol constraints
            final_size = self._apply_symbol_constraints(symbol, adjusted_size)
            
            # Check correlation risk
            correlation_adjusted_size = self._apply_correlation_limits(
                symbol, final_size, strategy_params
            )
            
            position_analysis = {
                'recommended_lot_size': correlation_adjusted_size,
                'base_calculation': {
                    'equity_based': equity_based_size,
                    'atr_based': atr_based_size,
                    'combined_base': base_size
                },
                'adjustments': {
                    'volatility_multiplier': volatility_multiplier,
                    'confidence_multiplier': confidence_multiplier,
                    'correlation_adjustment': correlation_adjusted_size / final_size if final_size > 0 else 1.0
                },
                'risk_metrics': {
                    'risk_per_trade_pct': self._calculate_risk_percentage(
                        correlation_adjusted_size, entry_price, stop_loss, account_info, symbol_info
                    ),
                    'risk_amount': self._calculate_risk_amount(
                        correlation_adjusted_size, entry_price, stop_loss, symbol_info
                    )
                },
                'strategy': strategy,
                'symbol': symbol
            }
            
            logger(f"✅ Position size calculated: {correlation_adjusted_size:.3f} lots")
            logger(f"   📊 Risk: {position_analysis['risk_metrics']['risk_per_trade_pct']:.2f}% of equity")
            
            return position_analysis
            
        except Exception as e:
            logger(f"❌ Position sizing error: {str(e)}")
            return self._get_fallback_position_size(symbol)

    def _calculate_equity_based_size(self, account_info, strategy_params, 
                                   entry_price: float, stop_loss: float, 
                                   symbol_info) -> float:
        """Calculate position size based on equity risk"""
        try:
            max_risk_pct = strategy_params['max_risk_per_trade']
            equity = account_info.equity
            max_risk_amount = equity * max_risk_pct
            
            # Calculate pip value
            point = symbol_info.point
            pip_value = self._calculate_pip_value(symbol_info, account_info.currency)
            
            # Calculate SL distance in pips
            sl_distance_pips = abs(entry_price - stop_loss) / point
            
            if sl_distance_pips > 0 and pip_value > 0:
                # Calculate lot size to risk max_risk_amount
                lot_size = max_risk_amount / (sl_distance_pips * pip_value)
                return max(0.01, lot_size)
            
            return 0.01  # Fallback
            
        except Exception as e:
            logger(f"❌ Equity-based sizing error: {str(e)}")
            return 0.01

    def _calculate_atr_based_size(self, symbol: str, strategy_params, 
                                entry_price: float, stop_loss: float, 
                                symbol_info) -> float:
        """Calculate position size based on ATR volatility"""
        try:
            # Get recent data to calculate ATR
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            if rates is None or len(rates) < 20:
                return 0.01
            
            df = pd.DataFrame(rates)
            
            # Calculate ATR
            from indicators import atr
            df['ATR'] = atr(df, period=14)
            current_atr = df['ATR'].iloc[-1]
            
            if current_atr <= 0:
                return 0.01
            
            # Adjust position size based on volatility
            # Higher volatility = smaller position
            base_lot = 0.01
            atr_multiplier = strategy_params['atr_multiplier']
            
            # Normalize ATR relative to price
            atr_pct = current_atr / entry_price
            
            # Adjust size - more volatile = smaller position
            if atr_pct > 0.01:  # Very volatile
                size_multiplier = 0.5
            elif atr_pct > 0.005:  # Moderately volatile
                size_multiplier = 0.75
            else:  # Low volatility
                size_multiplier = 1.0
            
            return base_lot * size_multiplier
            
        except Exception as e:
            logger(f"❌ ATR-based sizing error: {str(e)}")
            return 0.01

    def _get_volatility_adjustment(self, symbol: str, strategy_params) -> float:
        """Get current volatility adjustment multiplier"""
        try:
            if not strategy_params['volatility_adjustment']:
                return 1.0
            
            # Get recent volatility
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 30)
            if rates is None or len(rates) < 20:
                return 1.0
            
            df = pd.DataFrame(rates)
            
            # Calculate recent volatility vs average
            recent_volatility = df['high'].tail(5).std() / df['close'].tail(5).mean()
            avg_volatility = df['high'].std() / df['close'].mean()
            
            volatility_ratio = recent_volatility / avg_volatility if avg_volatility > 0 else 1.0
            
            # Adjust position size based on volatility
            if volatility_ratio > 1.5:  # High volatility
                return 0.7  # Reduce position size
            elif volatility_ratio < 0.7:  # Low volatility
                return 1.2  # Increase position size slightly
            else:
                return 1.0  # Normal volatility
                
        except Exception as e:
            logger(f"❌ Volatility adjustment error: {str(e)}")
            return 1.0

    def _apply_symbol_constraints(self, symbol: str, lot_size: float) -> float:
        """Apply symbol-specific lot size constraints"""
        try:
            symbol_params = self.symbol_params.get(symbol.upper(), {
                'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01
            })
            
            min_lot = symbol_params['min_lot']
            max_lot = symbol_params['max_lot']
            lot_step = symbol_params['lot_step']
            
            # Apply min/max constraints
            constrained_size = max(min_lot, min(max_lot, lot_size))
            
            # Round to lot step
            rounded_size = round(constrained_size / lot_step) * lot_step
            
            return max(min_lot, rounded_size)
            
        except Exception as e:
            logger(f"❌ Symbol constraint error: {str(e)}")
            return 0.01

    def _apply_correlation_limits(self, symbol: str, lot_size: float, 
                                strategy_params) -> float:
        """Apply correlation-based position limits"""
        try:
            max_correlation_exposure = strategy_params['max_correlation_exposure']
            
            # Get current positions
            positions = mt5.positions_get()
            if not positions:
                return lot_size  # No existing positions
            
            # Calculate current correlation exposure
            correlated_exposure = 0
            symbol_base_currency = symbol[:3]
            
            for pos in positions:
                pos_symbol = pos.symbol
                pos_base_currency = pos_symbol[:3]
                
                # Check for currency correlation
                if (symbol_base_currency == pos_base_currency or 
                    symbol[3:6] == pos_symbol[3:6]):  # Same quote currency
                    
                    # Add correlated exposure
                    correlated_exposure += abs(pos.volume)
            
            # Get account equity
            account_info = mt5.account_info()
            if not account_info:
                return lot_size
            
            # Calculate maximum allowed additional exposure
            max_total_exposure = account_info.equity * max_correlation_exposure / 10000  # Rough conversion
            remaining_exposure = max(0, max_total_exposure - correlated_exposure)
            
            # Limit position size if needed
            if remaining_exposure < lot_size:
                logger(f"⚠️ Correlation limit applied: {lot_size:.3f} -> {remaining_exposure:.3f}")
                return max(0.01, remaining_exposure)
            
            return lot_size
            
        except Exception as e:
            logger(f"❌ Correlation limit error: {str(e)}")
            return lot_size

    def _calculate_pip_value(self, symbol_info, account_currency: str) -> float:
        """Calculate pip value for the symbol"""
        try:
            # This is a simplified calculation
            # In real implementation, you'd want more precise pip value calculation
            
            point = symbol_info.point
            contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
            
            # For major pairs, approximate pip value
            if account_currency == 'USD':
                if symbol_info.name.endswith('USD'):
                    return (point * contract_size) / 1.0  # Direct quote
                else:
                    return point * contract_size  # Indirect quote
            
            return point * contract_size * 0.0001  # Rough approximation
            
        except Exception as e:
            logger(f"❌ Pip value calculation error: {str(e)}")
            return 1.0  # Fallback

    def _calculate_risk_percentage(self, lot_size: float, entry_price: float, 
                                 stop_loss: float, account_info, symbol_info) -> float:
        """Calculate risk percentage of equity"""
        try:
            risk_amount = self._calculate_risk_amount(lot_size, entry_price, stop_loss, symbol_info)
            return (risk_amount / account_info.equity) * 100
        except:
            return 1.0

    def _calculate_risk_amount(self, lot_size: float, entry_price: float, 
                             stop_loss: float, symbol_info) -> float:
        """Calculate risk amount in account currency"""
        try:
            point = symbol_info.point
            pip_value = self._calculate_pip_value(symbol_info, 'USD')  # Assume USD account
            sl_distance_pips = abs(entry_price - stop_loss) / point
            return lot_size * sl_distance_pips * pip_value
        except:
            return 100.0  # Fallback

    def _get_fallback_position_size(self, symbol: str) -> Dict[str, Any]:
        """Get fallback position size when calculation fails"""
        return {
            'recommended_lot_size': 0.01,
            'base_calculation': {'equity_based': 0.01, 'atr_based': 0.01, 'combined_base': 0.01},
            'adjustments': {'volatility_multiplier': 1.0, 'confidence_multiplier': 1.0, 'correlation_adjustment': 1.0},
            'risk_metrics': {'risk_per_trade_pct': 1.0, 'risk_amount': 100.0},
            'strategy': 'Unknown',
            'symbol': symbol,
            'fallback': True
        }


# Global instance
position_sizer = AdaptivePositionSizer()


def get_optimal_position_size(symbol: str, strategy: str, entry_price: float, 
                            stop_loss: float, confidence: float = 1.0) -> Dict[str, Any]:
    """Get optimal position size for trade"""
    return position_sizer.calculate_optimal_position_size(
        symbol, strategy, entry_price, stop_loss, confidence
    )


def get_dynamic_risk_parameters(symbol: str, strategy: str) -> Dict[str, Any]:
    """Get dynamic risk parameters for symbol and strategy"""
    try:
        strategy_params = position_sizer.strategy_risk_params.get(
            strategy, position_sizer.strategy_risk_params['Scalping']
        )
        symbol_params = position_sizer.symbol_params.get(symbol.upper(), {
            'min_lot': 0.01, 'max_lot': 1.0, 'lot_step': 0.01
        })
        
        return {
            'strategy_params': strategy_params,
            'symbol_params': symbol_params,
            'recommended_max_risk': strategy_params['max_risk_per_trade'] * 100  # As percentage
        }
        
    except Exception as e:
        logger(f"❌ Dynamic risk parameters error: {str(e)}")
        return {
            'strategy_params': {'max_risk_per_trade': 0.01},
            'symbol_params': {'min_lot': 0.01, 'max_lot': 1.0},
            'recommended_max_risk': 1.0
        }