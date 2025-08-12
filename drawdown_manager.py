# --- Drawdown Manager Module ---
"""
Professional drawdown management untuk capital preservation
Implements emergency stops, correlation monitoring, dan recovery protocols
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class DrawdownManager:
    """Professional drawdown management untuk 2 miliar profit protection"""

    def __init__(self):
        # Drawdown thresholds per strategy
        self.strategy_thresholds = {
            'Scalping': {
                'daily_dd_limit': 0.05,      # 5% daily drawdown limit
                'weekly_dd_limit': 0.10,     # 10% weekly drawdown limit
                'consecutive_losses': 5,      # Stop after 5 consecutive losses
                'recovery_multiplier': 1.5    # Position size reduction during recovery
            },
            'Intraday': {
                'daily_dd_limit': 0.08,
                'weekly_dd_limit': 0.15,
                'consecutive_losses': 4,
                'recovery_multiplier': 1.3
            },
            'HFT': {
                'daily_dd_limit': 0.03,      # Tighter control for HFT
                'weekly_dd_limit': 0.06,
                'consecutive_losses': 8,      # More trades = more losses allowed
                'recovery_multiplier': 2.0
            },
            'Arbitrage': {
                'daily_dd_limit': 0.10,
                'weekly_dd_limit': 0.20,
                'consecutive_losses': 3,
                'recovery_multiplier': 1.2
            }
        }

        # Global emergency thresholds
        self.emergency_thresholds = {
            'total_dd_limit': 0.20,         # 20% total portfolio drawdown
            'correlation_spike_limit': 0.85, # Stop if correlation > 85%
            'volatility_spike_multiplier': 3.0, # Stop if volatility > 3x normal
            'news_event_pause_hours': 2     # Hours to pause after major news
        }

        # Track performance metrics
        self.performance_history = []
        self.loss_streak = 0
        self.last_trade_result = None
        self.daily_pnl = 0
        self.weekly_pnl = 0

    def check_trading_allowed(self, strategy: str, symbol: str = None) -> Dict[str, Any]:
        """Check if trading is allowed based on drawdown analysis"""
        try:
            logger(f"🛡️ Drawdown check for {strategy} - {symbol or 'ALL'}")

            # Get current account status
            account_info = mt5.account_info()
            if not account_info:
                return self._create_block_response("No account info available", "TECHNICAL")

            # Check emergency stops first
            emergency_check = self._check_emergency_stops(account_info)
            if not emergency_check['allowed']:
                return emergency_check

            # Check strategy-specific limits
            strategy_check = self._check_strategy_limits(strategy, account_info)
            if not strategy_check['allowed']:
                return strategy_check

            # Check correlation risk
            correlation_check = self._check_correlation_risk(symbol)
            if not correlation_check['allowed']:
                return correlation_check

            # Check volatility spikes
            volatility_check = self._check_volatility_spikes(symbol)
            if not volatility_check['allowed']:
                return volatility_check

            # All checks passed
            return {
                'allowed': True,
                'reason': 'All drawdown checks passed',
                'risk_level': 'NORMAL',
                'position_size_multiplier': 1.0,
                'additional_checks': {
                    'emergency': emergency_check,
                    'strategy': strategy_check,
                    'correlation': correlation_check,
                    'volatility': volatility_check
                }
            }

        except Exception as e:
            logger(f"❌ Drawdown check error: {str(e)}")
            return self._create_block_response(f"Drawdown check error: {str(e)}", "ERROR")

    def _check_emergency_stops(self, account_info) -> Dict[str, Any]:
        """Check emergency stop conditions"""
        try:
            # Calculate total drawdown from peak equity
            equity = account_info.equity
            balance = account_info.balance

            # Calculate floating P&L percentage
            if balance > 0:
                floating_pnl_pct = (equity - balance) / balance
                total_dd_pct = min(0, floating_pnl_pct)  # Only negative values

                if abs(total_dd_pct) >= self.emergency_thresholds['total_dd_limit']:
                    return self._create_block_response(
                        f"Emergency stop: Total drawdown {abs(total_dd_pct):.1%} >= {self.emergency_thresholds['total_dd_limit']:.1%}",
                        "EMERGENCY"
                    )

            # Check for margin level
            if hasattr(account_info, 'margin_level') and account_info.margin_level < 200:
                return self._create_block_response(
                    f"Emergency stop: Low margin level {account_info.margin_level:.1f}%",
                    "MARGIN"
                )

            return {'allowed': True, 'emergency_level': 'NONE'}

        except Exception as e:
            logger(f"❌ Emergency stop check error: {str(e)}")
            return self._create_block_response("Emergency check failed", "ERROR")

    def _check_strategy_limits(self, strategy: str, account_info) -> Dict[str, Any]:
        """Check strategy-specific drawdown limits"""
        try:
            strategy_limits = self.strategy_thresholds.get(strategy, self.strategy_thresholds['Scalping'])

            # Check daily drawdown
            daily_dd = self._calculate_daily_drawdown(account_info)
            if abs(daily_dd) >= strategy_limits['daily_dd_limit']:
                return self._create_block_response(
                    f"Daily drawdown limit reached: {abs(daily_dd):.1%} >= {strategy_limits['daily_dd_limit']:.1%}",
                    "DAILY_LIMIT"
                )

            # Check weekly drawdown
            weekly_dd = self._calculate_weekly_drawdown(account_info)
            if abs(weekly_dd) >= strategy_limits['weekly_dd_limit']:
                return self._create_block_response(
                    f"Weekly drawdown limit reached: {abs(weekly_dd):.1%} >= {strategy_limits['weekly_dd_limit']:.1%}",
                    "WEEKLY_LIMIT"
                )

            # Check consecutive losses
            if self.loss_streak >= strategy_limits['consecutive_losses']:
                return self._create_block_response(
                    f"Consecutive loss limit reached: {self.loss_streak} >= {strategy_limits['consecutive_losses']}",
                    "LOSS_STREAK"
                )

            # Calculate position size adjustment for recovery
            position_multiplier = 1.0
            if self.loss_streak > 0:
                position_multiplier = 1.0 / strategy_limits['recovery_multiplier']

            return {
                'allowed': True,
                'position_size_multiplier': position_multiplier,
                'daily_dd': daily_dd,
                'weekly_dd': weekly_dd,
                'loss_streak': self.loss_streak
            }

        except Exception as e:
            logger(f"❌ Strategy limit check error: {str(e)}")
            return self._create_block_response("Strategy check failed", "ERROR")

    def _check_correlation_risk(self, symbol: str) -> Dict[str, Any]:
        """Check correlation risk across open positions"""
        try:
            if not symbol:
                return {'allowed': True, 'correlation_risk': 'LOW'}

            # Get current positions
            positions = mt5.positions_get()
            if not positions or len(positions) == 0:
                return {'allowed': True, 'correlation_risk': 'NONE'}

            # Calculate currency exposure
            currency_exposure = {}
            base_currency = symbol[:3]
            quote_currency = symbol[3:6]

            for pos in positions:
                pos_base = pos.symbol[:3]
                pos_quote = pos.symbol[3:6]

                # Count exposure by currency
                currency_exposure[pos_base] = currency_exposure.get(pos_base, 0) + pos.volume
                currency_exposure[pos_quote] = currency_exposure.get(pos_quote, 0) - pos.volume

            # Check if adding this trade would create excessive exposure
            total_base_exposure = currency_exposure.get(base_currency, 0)
            total_quote_exposure = currency_exposure.get(quote_currency, 0)

            max_single_currency_exposure = 5.0  # Max 5 lots exposure to single currency

            if (abs(total_base_exposure) >= max_single_currency_exposure or 
                abs(total_quote_exposure) >= max_single_currency_exposure):
                return self._create_block_response(
                    f"High correlation risk: Currency exposure limit reached",
                    "CORRELATION"
                )

            return {'allowed': True, 'correlation_risk': 'NORMAL'}

        except Exception as e:
            logger(f"❌ Correlation check error: {str(e)}")
            return {'allowed': True, 'correlation_risk': 'UNKNOWN'}

    def _check_volatility_spikes(self, symbol: str) -> Dict[str, Any]:
        """Check for extreme volatility conditions"""
        try:
            if not symbol:
                return {'allowed': True, 'volatility_risk': 'UNKNOWN'}

            # Get recent data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
            if rates is None or len(rates) < 20:
                return {'allowed': True, 'volatility_risk': 'NO_DATA'}

            df = pd.DataFrame(rates)

            # Calculate current vs historical volatility
            current_range = (df['high'].tail(5).max() - df['low'].tail(5).min()) / df['close'].tail(5).mean()
            historical_range = (df['high'].max() - df['low'].min()) / df['close'].mean()

            volatility_ratio = current_range / historical_range if historical_range > 0 else 1.0

            if volatility_ratio >= self.emergency_thresholds['volatility_spike_multiplier']:
                return self._create_block_response(
                    f"Volatility spike detected: {volatility_ratio:.1f}x normal levels",
                    "VOLATILITY"
                )

            return {
                'allowed': True, 
                'volatility_risk': 'NORMAL',
                'volatility_ratio': volatility_ratio
            }

        except Exception as e:
            logger(f"❌ Volatility check error: {str(e)}")
            return {'allowed': True, 'volatility_risk': 'ERROR'}

    def _calculate_daily_drawdown(self, account_info) -> float:
        """Calculate current daily drawdown"""
        try:
            # This is simplified - in real implementation, you'd track daily starting equity
            # For now, use a rough estimate based on current equity vs balance
            equity = account_info.equity
            balance = account_info.balance

            # Estimate daily drawdown (this should be improved with proper tracking)
            if balance > 0:
                return (equity - balance) / balance
            return 0.0

        except Exception as e:
            logger(f"❌ Daily drawdown calculation error: {str(e)}")
            return 0.0

    def _calculate_weekly_drawdown(self, account_info) -> float:
        """Calculate current weekly drawdown"""
        try:
            # Simplified calculation - should be improved with historical tracking
            return self._calculate_daily_drawdown(account_info) * 1.5  # Rough estimate
        except Exception as e:
            logger(f"❌ Weekly drawdown calculation error: {str(e)}")
            return 0.0

    def record_trade_result(self, symbol: str, strategy: str, pnl: float, 
                          lot_size: float, trade_type: str) -> None:
        """Record trade result for drawdown tracking"""
        try:
            trade_record = {
                'timestamp': datetime.datetime.now(),
                'symbol': symbol,
                'strategy': strategy,
                'pnl': pnl,
                'lot_size': lot_size,
                'trade_type': trade_type
            }

            self.performance_history.append(trade_record)

            # Update loss streak
            if pnl < 0:
                self.loss_streak += 1
                logger(f"📉 Loss recorded: {pnl:.2f} | Loss streak: {self.loss_streak}")
            else:
                if self.loss_streak > 0:
                    logger(f"🔄 Loss streak broken after {self.loss_streak} losses")
                self.loss_streak = 0
                logger(f"📈 Profit recorded: {pnl:.2f}")

            self.last_trade_result = pnl
            self.daily_pnl += pnl
            self.weekly_pnl += pnl

            # Keep only last 1000 trades in memory
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]

        except Exception as e:
            logger(f"❌ Trade result recording error: {str(e)}")

    def get_recovery_recommendations(self, strategy: str) -> Dict[str, Any]:
        """Get recommendations for recovery after drawdown"""
        try:
            if self.loss_streak == 0:
                return {'in_recovery': False, 'recommendations': []}

            recommendations = []

            # Position size reduction
            strategy_params = self.strategy_thresholds.get(strategy, self.strategy_thresholds['Scalping'])
            size_reduction = 1.0 / strategy_params['recovery_multiplier']
            recommendations.append(f"Reduce position size by {(1-size_reduction)*100:.0f}%")

            # Strategy adjustments
            if self.loss_streak >= 3:
                recommendations.append("Consider switching to lower-frequency strategy")
                recommendations.append("Increase confirmation requirements")

            if self.loss_streak >= 5:
                recommendations.append("Take trading break for market reassessment")
                recommendations.append("Review and optimize strategy parameters")

            return {
                'in_recovery': True,
                'loss_streak': self.loss_streak,
                'position_size_multiplier': size_reduction,
                'recommendations': recommendations
            }

        except Exception as e:
            logger(f"❌ Recovery recommendations error: {str(e)}")
            return {'in_recovery': False, 'error': str(e)}

    def _create_block_response(self, reason: str, block_type: str) -> Dict[str, Any]:
        """Create a standardized block response"""
        return {
            'allowed': False,
            'reason': reason,
            'block_type': block_type,
            'timestamp': datetime.datetime.now().isoformat(),
            'position_size_multiplier': 0.0
        }

    def get_current_risk_status(self) -> Dict[str, Any]:
        """Get current risk status summary"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return {'status': 'ERROR', 'reason': 'No account info'}

            return {
                'status': 'ACTIVE' if self.loss_streak < 3 else 'CAUTION' if self.loss_streak < 5 else 'RECOVERY',
                'loss_streak': self.loss_streak,
                'daily_pnl': self.daily_pnl,
                'weekly_pnl': self.weekly_pnl,
                'equity': account_info.equity,
                'balance': account_info.balance,
                'free_margin': getattr(account_info, 'margin_free', 0),
                'margin_level': getattr(account_info, 'margin_level', 0),
                'total_trades_today': len([t for t in self.performance_history 
                                         if t['timestamp'].date() == datetime.date.today()])
            }

        except Exception as e:
            logger(f"❌ Risk status error: {str(e)}")
            return {'status': 'ERROR', 'reason': str(e)}


# Global instance
drawdown_manager = DrawdownManager()


def check_drawdown_limits(strategy: str, symbol: str = None) -> Dict[str, Any]:
    """Check if trading is allowed based on drawdown limits"""
    return drawdown_manager.check_trading_allowed(strategy, symbol)


def record_trade_outcome(symbol: str, strategy: str, pnl: float, 
                        lot_size: float, trade_type: str) -> None:
    """Record trade outcome for drawdown tracking"""
    drawdown_manager.record_trade_result(symbol, strategy, pnl, lot_size, trade_type)


def get_risk_adjusted_position_size(base_size: float, strategy: str) -> float:
    """Get risk-adjusted position size based on current drawdown"""
    try:
        recovery_info = drawdown_manager.get_recovery_recommendations(strategy)
        if recovery_info['in_recovery']:
            return base_size * recovery_info['position_size_multiplier']
        return base_size
    except:
        return base_size

# --- Helper functions for position sizing ---

def calculate_current_drawdown() -> float:
    """Placeholder for calculating current drawdown. Replace with actual implementation."""
    # In a real scenario, this would fetch account equity and balance, 
    # and compare it to the peak equity to determine drawdown.
    # For now, returning a dummy value for demonstration.
    # Accessing drawdown_manager directly for demo purposes.
    try:
        account_info = mt5.account_info()
        if not account_info:
            return 0.0
        balance = account_info.balance
        equity = account_info.equity
        if balance == 0:
            return 0.0
        drawdown = (balance - equity) / balance if balance > 0 else 0.0
        return max(0.0, drawdown) # Ensure drawdown is not negative
    except:
        return 0.0


def should_reduce_position_size() -> Tuple[bool, float]:
    """Check if position size should be reduced due to drawdown"""
    try:
        current_drawdown = calculate_current_drawdown()

        if current_drawdown > 0.15:  # 15% drawdown
            return True, 0.5  # Reduce to 50%
        elif current_drawdown > 0.10:  # 10% drawdown
            return True, 0.7  # Reduce to 70%
        elif current_drawdown > 0.05:  # 5% drawdown
            return True, 0.85  # Reduce to 85%

        return False, 1.0  # No reduction

    except Exception as e:
        logger(f"❌ Position size check error: {str(e)}")
        return False, 1.0


def get_recovery_adjustments(base_lot_size: float) -> Tuple[bool, float]:
    """Get recovery mode adjustments for lot size - FIXED MISSING FUNCTION"""
    try:
        current_drawdown = calculate_current_drawdown()

        # Recovery mode activation
        if current_drawdown > 0.10:  # 10% drawdown threshold
            recovery_mode = True

            # Progressive lot size reduction based on drawdown severity
            if current_drawdown > 0.20:  # Severe drawdown
                adjusted_lot = base_lot_size * 0.3  # Reduce to 30%
                logger(f"🔄 SEVERE RECOVERY: Lot reduced to 30% ({adjusted_lot})")
            elif current_drawdown > 0.15:  # High drawdown
                adjusted_lot = base_lot_size * 0.5  # Reduce to 50%
                logger(f"🔄 HIGH RECOVERY: Lot reduced to 50% ({adjusted_lot})")
            else:  # Moderate drawdown
                adjusted_lot = base_lot_size * 0.7  # Reduce to 70%
                logger(f"🔄 MODERATE RECOVERY: Lot reduced to 70% ({adjusted_lot})")

            return recovery_mode, adjusted_lot
        else:
            # Normal mode - no recovery needed
            return False, base_lot_size

    except Exception as e:
        logger(f"❌ Recovery adjustments error: {str(e)}")
        return False, base_lot_size