# --- Risk Management Module ---
"""
Risk assessment, position sizing, and safety checks
"""

import datetime
from typing import Dict, Any, Optional, Tuple
from logger_utils import logger
from config import MAX_RISK_PERCENTAGE, MAX_DAILY_TRADES, MAX_OPEN_POSITIONS

# REAL MT5 for Windows Trading (FIXED)
try:
    import MetaTrader5 as mt5
    print("✅ Risk Management using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Risk Management using mock - NOT for real trading!")


# Global risk tracking
daily_trades = 0
daily_profit = 0.0
session_start_balance = 0.0
last_reset_date = None

# Manual Order Limit Management
current_order_count = 0
max_orders_limit = 10  # User configurable
order_limit_enabled = True


def risk_management_check() -> bool:
    """Comprehensive risk management check before trading"""
    try:
        # Check account status
        account_info = mt5.account_info()
        if not account_info:
            logger("❌ Cannot get account information")
            return False

        if not account_info.trade_allowed:
            logger("❌ Trading not allowed on this account")
            return False

        # Check equity vs balance
        equity_ratio = account_info.equity / account_info.balance if account_info.balance > 0 else 0
        if equity_ratio < 0.8:  # If equity drops below 80% of balance
            logger(f"⚠️ High drawdown detected: Equity {equity_ratio:.1%} of balance")
            logger("🛡️ Risk management: Reducing position sizes")

        # Check margin level
        if account_info.margin_level < 200 and account_info.margin_level > 0:
            logger(f"⚠️ Low margin level: {account_info.margin_level:.0f}%")
            if account_info.margin_level < 100:
                logger("❌ Margin call risk - trading suspended")
                return False

        # Check daily trade limit
        if daily_trades >= MAX_DAILY_TRADES:
            logger(f"⚠️ Daily trade limit reached: {daily_trades}/{MAX_DAILY_TRADES}")
            return False

        # Check open positions limit
        positions = mt5.positions_get()
        if positions and len(positions) >= MAX_OPEN_POSITIONS:
            logger(f"⚠️ Maximum open positions reached: {len(positions)}/{MAX_OPEN_POSITIONS}")
            return False

        # Check daily loss limit
        global session_start_balance
        if session_start_balance > 0:
            current_profit = account_info.balance - session_start_balance
            max_daily_loss = session_start_balance * (MAX_RISK_PERCENTAGE / 100)

            if current_profit < -max_daily_loss:
                logger(f"❌ Daily loss limit exceeded: ${abs(current_profit):.2f} > ${max_daily_loss:.2f}")
                return False

        return True

    except Exception as e:
        logger(f"❌ Risk management check error: {str(e)}")
        return False


def check_daily_limits() -> bool:
    """Check and reset daily trading limits"""
    global daily_trade_count, daily_profit, last_reset_date

    try:
        current_date = datetime.date.today()

        # Reset counters if new day
        if last_reset_date != current_date:
            logger(f"📅 New trading day: Resetting daily counters")
            daily_trade_count = 0
            daily_profit = 0.0
            last_reset_date = current_date

            # Update session start balance
            account_info = mt5.account_info()
            if account_info:
                global session_start_balance
                session_start_balance = account_info.balance
                logger(f"💰 Session start balance: ${session_start_balance:.2f}")

        return True

    except Exception as e:
        logger(f"❌ Error checking daily limits: {str(e)}")
        return False


def increment_daily_trade_count():
    """Increment daily trade counter"""
    global daily_trades, current_order_count
    daily_trades += 1
    current_order_count += 1
    logger(f"📊 Daily trade count: {daily_trades}")
    logger(f"📊 Current order count: {current_order_count}/{max_orders_limit}")


def reset_daily_counters():
    """Reset daily counters"""
    global daily_trades, daily_profit, session_start_balance
    daily_trades = 0
    daily_profit = 0.0
    session_start_balance = 0.0
    logger("🔄 Daily counters reset")


def set_max_orders_limit(new_limit: int) -> bool:
    """Set new maximum orders limit"""
    global max_orders_limit
    try:
        from config import MIN_MAX_ORDERS, MAX_MAX_ORDERS

        if MIN_MAX_ORDERS <= new_limit <= MAX_MAX_ORDERS:
            old_limit = max_orders_limit
            max_orders_limit = new_limit
            logger(f"⚙️ Max orders limit changed: {old_limit} → {new_limit}")

            # Update GUI if available
            try:
                import __main__
                if hasattr(__main__, 'gui') and __main__.gui:
                    __main__.gui.log(f"⚙️ Max orders limit updated to: {new_limit}")
            except:
                pass

            return True
        else:
            logger(f"❌ Invalid limit: {new_limit}. Must be between {MIN_MAX_ORDERS}-{MAX_MAX_ORDERS}")
            return False
    except Exception as e:
        logger(f"❌ Error setting max orders limit: {str(e)}")
        return False


def reset_order_count():
    """Reset current order count"""
    global current_order_count
    old_count = current_order_count
    current_order_count = 0
    logger(f"🔄 Order count reset: {old_count} → 0")

    # Update GUI if available
    try:
        import __main__
        if hasattr(__main__, 'gui') and __main__.gui:
            __main__.gui.log(f"🔄 Order count reset: {old_count} → 0")
    except:
        pass


def check_order_limit() -> bool:
    """Check if order limit allows new trades"""
    global current_order_count, max_orders_limit, order_limit_enabled

    if not order_limit_enabled:
        return True

    if current_order_count >= max_orders_limit:
        logger(f"🛑 Order limit reached: {current_order_count}/{max_orders_limit}")
        return False

    return True


def get_order_limit_status() -> dict:
    """Get current order limit status"""
    return {
        'current_count': current_order_count,
        'max_limit': max_orders_limit,
        'limit_enabled': order_limit_enabled,
        'remaining': max(0, max_orders_limit - current_order_count),
        'percentage_used': (current_order_count / max_orders_limit * 100) if max_orders_limit > 0 else 0
    }


def calculate_position_size(symbol: str, risk_percentage: float = None) -> float:
    """Calculate optimal position size based on risk management"""
    try:
        if risk_percentage is None:
            risk_percentage = MAX_RISK_PERCENTAGE

        account_info = mt5.account_info()
        if not account_info:
            return 0.01  # Minimal fallback

        # Adjust risk based on current drawdown
        equity_ratio = account_info.equity / account_info.balance if account_info.balance > 0 else 1.0
        if equity_ratio < 0.9:  # If in drawdown
            risk_percentage *= equity_ratio  # Reduce risk proportionally
            logger(f"🛡️ Risk reduced due to drawdown: {risk_percentage:.1f}%")

        # Calculate risk amount
        risk_amount = account_info.balance * (risk_percentage / 100)

        # Get symbol info for calculations
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.01

        # Calculate lot size (simplified)
        # This is a basic calculation - in practice you'd want more sophisticated position sizing
        base_lot_size = risk_amount / 1000  # Simple heuristic

        # Apply limits
        min_lot = 0.01
        max_lot = min(account_info.balance / 5000, 2.0)  # Conservative maximum

        calculated_lot = max(min_lot, min(base_lot_size, max_lot))

        # Round to standard increments
        calculated_lot = round(calculated_lot, 2)

        logger(f"💰 Position size calculated: {calculated_lot} lots (Risk: ${risk_amount:.2f})")

        return calculated_lot

    except Exception as e:
        logger(f"❌ Error calculating position size: {str(e)}")
        return 0.01


def check_profit_targets() -> bool:
    """Check if profit targets have been met"""
    try:
        global session_start_balance

        account_info = mt5.account_info()
        if not account_info or session_start_balance <= 0:
            return False

        current_profit = account_info.balance - session_start_balance
        profit_percentage = (current_profit / session_start_balance) * 100

        # Daily profit target (conservative)
        daily_profit_target = session_start_balance * 0.05  # 5% daily target

        if current_profit >= daily_profit_target:
            logger(f"🎯 Daily profit target reached: ${current_profit:.2f} ({profit_percentage:.1f}%)")
            logger("💡 Consider taking profits and reducing risk")
            return True

        return False

    except Exception as e:
        logger(f"❌ Error checking profit targets: {str(e)}")
        return False


def auto_recovery_check() -> bool:
    """Automatic recovery check for system issues"""
    try:
        # Check MT5 connection
        account_info = mt5.account_info()
        if not account_info:
            logger("🔄 Auto-recovery: MT5 connection lost, attempting reconnect...")
            from mt5_connection import connect_mt5
            return connect_mt5()

        # Check for margin issues
        if account_info.margin_level < 150 and account_info.margin_level > 0:
            logger("🔄 Auto-recovery: Low margin detected, closing losing positions...")

            positions = mt5.positions_get()
            if positions:
                # Close the most losing position
                worst_position = min(positions, key=lambda p: p.profit)
                if worst_position.profit < 0:
                    from trading_operations import close_position_by_ticket
                    if close_position_by_ticket(worst_position.ticket):
                        logger(f"🔄 Auto-recovery: Closed losing position {worst_position.ticket}")

        return True

    except Exception as e:
        logger(f"❌ Auto-recovery error: {str(e)}")
        return False


def get_current_risk_metrics() -> Dict[str, Any]:
    """Get current risk metrics for monitoring"""
    try:
        account_info = mt5.account_info()
        positions = mt5.positions_get()

        if not account_info:
            return {}

        global session_start_balance
        current_profit = account_info.balance - session_start_balance if session_start_balance > 0 else 0

        metrics = {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin_level': account_info.margin_level,
            'free_margin': account_info.margin_free,
            'daily_profit': current_profit,
            'daily_profit_pct': (current_profit / session_start_balance * 100) if session_start_balance > 0 else 0,
            'open_positions': len(positions) if positions else 0,
            'daily_trades': daily_trade_count,
            'equity_ratio': (account_info.equity / account_info.balance * 100) if account_info.balance > 0 else 100
        }

        return metrics

    except Exception as e:
        logger(f"❌ Error getting risk metrics: {str(e)}")
        return {}