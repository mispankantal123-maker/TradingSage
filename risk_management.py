# --- Risk Management Module ---
"""
Risk management, position sizing, and trade limits - REAL ACCOUNT PROTECTION
"""

import datetime
from typing import Dict, Any, Tuple, Optional
from logger_utils import logger
from config import MAX_RISK_PERCENTAGE, MAX_DAILY_TRADES, MAX_OPEN_POSITIONS, DEFAULT_MAX_ORDERS, MIN_MAX_ORDERS, MAX_MAX_ORDERS

# SMART MT5 Connection - Real on Windows, Mock for Development
try:
    import MetaTrader5 as mt5
    print("✅ Risk Management using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Risk Management using mock for development")

# Global risk tracking with thread safety
import threading
import time
_risk_lock = threading.Lock()
daily_trade_count = 0
session_start_time = datetime.datetime.now().date()
max_orders_limit = DEFAULT_MAX_ORDERS
current_order_count = 0
max_daily_orders = 50  # User configurable daily limit
daily_profit = 0.0
last_reset_date = datetime.date.today()

def get_order_limit_status() -> Dict[str, Any]:
    """Get current order limit status"""
    try:
        global current_order_count, max_orders_limit

        percentage_used = (current_order_count / max_orders_limit * 100) if max_orders_limit > 0 else 0

        return {
            'current_count': current_order_count,
            'max_limit': max_orders_limit,
            'percentage_used': percentage_used,
            'orders_remaining': max(0, max_orders_limit - current_order_count)
        }

    except Exception as e:
        logger(f"❌ Error getting order limit status: {str(e)}")
        return {
            'current_count': 0,
            'max_limit': 10,
            'percentage_used': 0,
            'orders_remaining': 10
        }

def get_daily_order_limit_status() -> Dict[str, Any]:
    """Get daily order limit status - FIXED FUNCTION"""
    try:
        global daily_trade_count, max_daily_orders, last_reset_date

        # Reset if new day
        today = datetime.date.today()
        if today != last_reset_date:
            daily_trade_count = 0
            last_reset_date = today

        percentage_used = (daily_trade_count / max_daily_orders * 100) if max_daily_orders > 0 else 0

        return {
            'current_daily_count': daily_trade_count,
            'max_daily_limit': max_daily_orders,
            'daily_percentage_used': percentage_used,
            'orders_remaining': max(0, max_daily_orders - daily_trade_count),
            'reset_date': last_reset_date.strftime('%Y-%m-%d')
        }

    except Exception as e:
        return {
            'current_daily_count': 0,
            'max_daily_limit': 50,
            'daily_percentage_used': 0,
            'orders_remaining': 50,
            'reset_date': datetime.date.today().strftime('%Y-%m-%d')
        }

def update_daily_order_count():
    """Update daily order count"""
    global daily_trade_count
    daily_trade_count += 1
    logger(f"📊 Daily order count updated: {daily_trade_count}")

def set_daily_order_limit(new_limit: int):
    """Set new daily order limit"""
    global max_daily_orders
    max_daily_orders = max(1, min(200, new_limit))  # Between 1-200
    logger(f"⚙️ Daily order limit set to: {max_daily_orders}")

def check_daily_order_limit() -> bool:
    """Check if daily order limit is reached"""
    try:
        status = get_daily_order_limit_status()
        return status['daily_count'] < status['daily_limit']
    except Exception as e:
        logger(f"❌ Error checking daily limit: {str(e)}")
        return True  # Allow trading on error

def reset_order_count():
    """Reset order count to zero"""
    global current_order_count
    current_order_count = 0
    logger("🔄 Order count reset to 0")

def increment_order_count():
    """Increment order count"""
    global current_order_count
    current_order_count += 1
    logger(f"📊 Order count incremented to: {current_order_count}")

def decrement_order_count():
    """Decrement order count"""
    global current_order_count
    if current_order_count > 0:
        current_order_count -= 1
        logger(f"📊 Order count decremented to: {current_order_count}")


def check_order_limit() -> bool:
    """Check if order limit is reached - thread-safe"""
    try:
        with _risk_lock:
            global max_orders_limit

            # Get current order count from GUI
            current_orders = 0
            try:
                import __main__
                if hasattr(__main__, 'gui') and __main__.gui:
                    current_orders = __main__.gui.order_count
            except:
                pass

            # Also check actual MT5 positions with retry
            max_retries = 3
            actual_positions = 0

            for attempt in range(max_retries):
                try:
                    positions = mt5.positions_get()
                    actual_positions = len(positions) if positions else 0
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger(f"⚠️ Failed to get positions after {max_retries} attempts: {e}")
                    else:
                        time.sleep(0.1)

            # Use the higher of the two counts for safety
            total_orders = max(current_orders, actual_positions)

            if total_orders >= max_orders_limit:
                logger(f"🛑 Order limit reached: {total_orders}/{max_orders_limit}")
                return False

            return True

    except Exception as e:
        logger(f"❌ Error checking order limit: {str(e)}")
        return False


def set_max_orders_limit(new_limit: int) -> bool:
    """Set new maximum orders limit"""
    try:
        global max_orders_limit

        if new_limit < 1 or new_limit > 100:
            logger(f"❌ Invalid order limit: {new_limit} (must be 1-100)")
            return False

        max_orders_limit = new_limit
        logger(f"✅ Order limit updated to: {max_orders_limit}")
        return True

    except Exception as e:
        logger(f"❌ Error setting order limit: {str(e)}")
        return False


def reset_order_count() -> None:
    """Reset order count"""
    try:
        # Update GUI order count
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                __main__.gui.order_count = 0
                __main__.gui.update_order_count_display()
        except:
            pass

        logger("✅ Order count reset to 0")

    except Exception as e:
        logger(f"❌ Error resetting order count: {str(e)}")


def check_order_limit() -> bool:
    """Check if order limit is reached - thread-safe"""
    try:
        with _risk_lock:
            global max_orders_limit

            # Get current order count from GUI
            current_orders = 0
            try:
                import __main__
                if hasattr(__main__, 'gui') and __main__.gui:
                    current_orders = __main__.gui.order_count
            except:
                pass

            # Also check actual MT5 positions with retry
            max_retries = 3
            actual_positions = 0

            for attempt in range(max_retries):
                try:
                    positions = mt5.positions_get()
                    actual_positions = len(positions) if positions else 0
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger(f"⚠️ Failed to get positions after {max_retries} attempts: {e}")
                    else:
                        time.sleep(0.1)

            # Use the higher of the two counts for safety
            total_orders = max(current_orders, actual_positions)

            if total_orders >= max_orders_limit:
                logger(f"🛑 Order limit reached: {total_orders}/{max_orders_limit}")
                return False

            return True

    except Exception as e:
        logger(f"❌ Error checking order limit: {str(e)}")
        return False


def set_max_orders_limit(new_limit: int) -> bool:
    """Set new maximum orders limit"""
    try:
        global max_orders_limit

        if new_limit < 1 or new_limit > 100:
            logger(f"❌ Invalid order limit: {new_limit} (must be 1-100)")
            return False

        max_orders_limit = new_limit
        logger(f"✅ Order limit updated to: {max_orders_limit}")
        return True

    except Exception as e:
        logger(f"❌ Error setting order limit: {str(e)}")
        return False


def reset_order_count() -> None:
    """Reset order count"""
    try:
        # Update GUI order count
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                __main__.gui.order_count = 0
                __main__.gui.update_order_count_display()
        except:
            pass

        logger("✅ Order count reset to 0")

    except Exception as e:
        logger(f"❌ Error resetting order count: {str(e)}")


def risk_management_check() -> bool:
    """Comprehensive risk management check for REAL account"""
    try:
        # Check MT5 connection
        account_info = mt5.account_info()
        if not account_info:
            logger("❌ Risk check failed: No account info")
            return False

        # Check if trading is allowed
        if not account_info.trade_allowed:
            logger("❌ Risk check failed: Trading not allowed")
            return False

        # Check account balance
        if account_info.balance <= 0:
            logger("❌ Risk check failed: No account balance")
            return False

        # Check margin level
        if account_info.margin > 0:
            margin_level = (account_info.equity / account_info.margin) * 100
            if margin_level < 200:  # 200% margin level minimum
                logger(f"❌ Risk check failed: Low margin level {margin_level:.1f}%")
                return False

        # Check daily trade limit
        if daily_trade_count >= MAX_DAILY_TRADES:
            logger(f"❌ Daily trade limit reached: {daily_trade_count}/{MAX_DAILY_TRADES}")
            return False

        # Check open positions limit
        positions = mt5.positions_get()
        position_count = len(positions) if positions else 0
        if position_count >= MAX_OPEN_POSITIONS:
            logger(f"❌ Position limit reached: {position_count}/{MAX_OPEN_POSITIONS}")
            return False

        # Check order limit
        if not check_order_limit():
            return False

        # Check drawdown
        if account_info.equity < account_info.balance * 0.8:  # 20% max drawdown
            logger("❌ Risk check failed: Maximum drawdown reached")
            return False

        return True

    except Exception as e:
        logger(f"❌ Risk management check error: {str(e)}")
        return False


def check_daily_limits() -> bool:
    """Check if daily trading limits are exceeded"""
    try:
        global daily_trade_count, max_daily_orders, last_reset_date

        # Reset counters if new day
        if datetime.date.today() != last_reset_date:
            reset_daily_counters()

        # Check daily trade limit (use user-configured limit)
        if daily_trade_count >= max_daily_orders:
            logger(f"⚠️ Daily trade limit reached: {daily_trade_count}/{max_daily_orders}")
            return False

        return True

    except Exception as e:
        logger(f"❌ Error checking daily limits: {str(e)}")
        return True  # Allow trading on error (fail-safe)


def increment_daily_trade_count() -> None:
    """Increment daily trade count safely"""
    try:
        global daily_trade_count, last_reset_date

        # Check if we need to reset for new day
        today = datetime.date.today()
        if today != last_reset_date:
            daily_trade_count = 0
            last_reset_date = today
            logger("🔄 Daily trade count reset for new day")

        daily_trade_count += 1
        logger(f"📈 Daily trade count incremented to: {daily_trade_count}")

    except Exception as e:
        logger(f"❌ Error incrementing daily trade count: {str(e)}")


def safe_update_gui_count():
    """Safely update GUI count on main thread"""
    try:
        import __main__
        if hasattr(__main__, 'gui') and __main__.gui:
            if not hasattr(__main__.gui, 'order_count'):
                __main__.gui.order_count = 0
            __main__.gui.order_count += 1
            __main__.gui.update_order_count_display()
    except Exception as e:
        logger(f"❌ Error updating GUI count: {str(e)}")


def calculate_position_size(symbol: str, risk_amount: float, stop_loss_pips: float) -> float:
    """Calculate appropriate position size for REAL trading"""
    try:
        account_info = mt5.account_info()
        if not account_info:
            return 0.01

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.01

        # Calculate pip value
        if "JPY" in symbol:
            pip_value = 0.01 * symbol_info.trade_contract_size
        else:
            pip_value = 0.0001 * symbol_info.trade_contract_size

        # Calculate lot size based on risk
        lot_size = risk_amount / (stop_loss_pips * pip_value)

        # Apply minimum and maximum limits
        min_lot = symbol_info.volume_min
        max_lot = min(symbol_info.volume_max, account_info.balance / 1000)

        lot_size = max(min_lot, min(lot_size, max_lot))

        # Round to step size
        step = symbol_info.volume_step
        lot_size = round(lot_size / step) * step

        return lot_size

    except Exception as e:
        logger(f"❌ Error calculating position size: {str(e)}")
        return 0.01


def get_current_risk_metrics() -> Dict[str, Any]:
    """Get current risk metrics from REAL account - FIXED VERSION"""
    try:
        account_info = mt5.account_info()
        positions = mt5.positions_get()

        if not account_info:
            return {'error': 'No account info'}

        position_count = len(positions) if positions else 0

        # Calculate total risk with proper type handling
        total_risk = 0.0
        if positions:
            for pos in positions:
                try:
                    if hasattr(pos, 'sl') and pos.sl > 0:  # Has stop loss
                        # FIXED: Ensure all values are numeric
                        price_open = float(pos.price_open)
                        stop_loss = float(pos.sl)
                        volume = float(pos.volume)
                        
                        risk = abs(price_open - stop_loss) * volume
                        total_risk += risk
                except (ValueError, TypeError, AttributeError) as pos_e:
                    logger(f"⚠️ Position risk calculation error: {str(pos_e)}")
                    continue

        # FIXED: Proper type conversion and validation
        balance = float(account_info.balance) if account_info.balance else 0.0
        equity = float(account_info.equity) if account_info.equity else 0.0
        margin = float(account_info.margin) if account_info.margin else 0.0
        
        risk_percentage = (total_risk / balance * 100) if balance > 0 else 0.0
        margin_level = (equity / margin * 100) if margin > 0 else 0.0

        # Calculate daily profit safely
        global daily_profit
        if not isinstance(daily_profit, (int, float)):
            daily_profit = 0.0
            
        daily_profit_pct = (daily_profit / balance * 100) if balance > 0 else 0.0
        equity_ratio = (equity / balance * 100) if balance > 0 else 100.0

        return {
            'balance': balance,
            'equity': equity,
            'margin': margin,
            'free_margin': float(account_info.margin_free) if account_info.margin_free else 0.0,
            'margin_level': margin_level,
            'open_positions': position_count,
            'daily_trades': daily_trade_count,
            'daily_profit': daily_profit,
            'daily_profit_pct': daily_profit_pct,
            'equity_ratio': equity_ratio,
            'total_risk': total_risk,
            'risk_percentage': risk_percentage,
            'max_positions': MAX_OPEN_POSITIONS,
            'max_daily_trades': MAX_DAILY_TRADES,
            'max_orders_limit': max_orders_limit
        }

    except Exception as e:
        logger(f"❌ Error getting risk metrics: {str(e)}")
        import traceback
        logger(f"📝 Risk metrics traceback: {traceback.format_exc()}")
        return {
            'error': str(e),
            'balance': 0.0,
            'equity': 0.0,
            'daily_trades': 0,
            'open_positions': 0
        }


def auto_recovery_check() -> bool:
    """Auto recovery check for REAL account"""
    try:
        account_info = mt5.account_info()
        if not account_info:
            return False

        # Check for margin call situation
        if account_info.margin > 0:
            margin_level = (account_info.equity / account_info.margin) * 100
            if margin_level < 150:  # Critical margin level
                logger(f"🚨 CRITICAL: Low margin level {margin_level:.1f}% - Consider closing positions")
                return False

        # Check for excessive drawdown
        if account_info.equity < account_info.balance * 0.85:  # 15% drawdown
            logger(f"⚠️ WARNING: Account drawdown detected")
            return False

        return True

    except Exception as e:
        logger(f"❌ Auto recovery check error: {str(e)}")
        return False


def emergency_close_all_positions() -> None:
    """Emergency close all positions in REAL account"""
    try:
        logger("🚨 EMERGENCY: Closing all live positions")

        positions = mt5.positions_get()
        if not positions:
            logger("ℹ️ No positions to close")
            return

        closed_count = 0
        for position in positions:
            try:
                # Determine close parameters
                if position.type == 0:  # BUY
                    order_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(position.symbol).bid
                else:  # SELL
                    order_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(position.symbol).ask

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "type": order_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": 50,
                    "magic": 234000,
                    "comment": "Emergency Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed_count += 1

            except Exception as close_error:
                logger(f"❌ Error closing position {position.ticket}: {close_error}")

        logger(f"🚨 Emergency close completed: {closed_count}/{len(positions)} positions closed")

    except Exception as e:
        logger(f"❌ Emergency close error: {str(e)}")


def initialize_risk_management():
    """Initialize risk management system"""
    try:
        global max_orders_limit, max_daily_orders

        # Load from config if available
        try:
            from config_manager import config_manager

            # Load order limit
            saved_limit = config_manager.get("max_orders", DEFAULT_MAX_ORDERS)
            if isinstance(saved_limit, int) and MIN_MAX_ORDERS <= saved_limit <= MAX_MAX_ORDERS:
                max_orders_limit = saved_limit
                logger(f"✅ Order limit loaded from config: {max_orders_limit}")
            else:
                logger(f"⚠️ Invalid saved order limit, using default: {DEFAULT_MAX_ORDERS}")

            # Load daily order limit
            saved_daily_limit = config_manager.get("max_daily_orders", 50)
            if isinstance(saved_daily_limit, int) and 1 <= saved_daily_limit <= 1000:
                max_daily_orders = saved_daily_limit
                logger(f"✅ Daily order limit loaded from config: {max_daily_orders}")
            else:
                logger(f"⚠️ Invalid saved daily limit, using default: 50")

        except Exception as config_e:
            logger(f"⚠️ Config load failed, using defaults: {str(config_e)}")

        # Reset daily counters if needed
        if datetime.date.today() != last_reset_date:
            reset_daily_counters()

        logger("✅ Risk management system initialized")
        logger(f"📊 Limits: Orders={max_orders_limit}, Daily={max_daily_orders}")
        return True

    except Exception as e:
        logger(f"❌ Risk management initialization error: {str(e)}")
        return False


def reset_daily_counters():
    """Reset daily counters"""
    global daily_trade_count, last_reset_date
    daily_trade_count = 0
    last_reset_date = datetime.date.today()
    logger("🔄 Daily trade counters reset.")


def get_daily_trade_status() -> Dict[str, Any]:
    """Get current daily trade status"""
    try:
        global daily_trade_count, max_daily_orders

        percentage_used = (daily_trade_count / max_daily_orders * 100) if max_daily_orders > 0 else 0

        return {
            'current_count': daily_trade_count,
            'max_limit': max_daily_orders,
            'percentage_used': percentage_used,
            'trades_remaining': max(0, max_daily_orders - daily_trade_count)
        }

    except Exception as e:
        logger(f"❌ Error getting daily trade status: {str(e)}")
        return {
            'current_count': 0,
            'max_limit': 50,
            'percentage_used': 0,
            'trades_remaining': 50
        }

def set_max_daily_orders(new_limit: int) -> bool:
    """Set new maximum daily orders limit"""
    try:
        global max_daily_orders

        if not isinstance(new_limit, int) or new_limit < MIN_MAX_ORDERS or new_limit > 1000:
            logger(f"❌ Invalid daily order limit: {new_limit} (must be {MIN_MAX_ORDERS}-1000)")
            return False

        old_limit = max_daily_orders
        max_daily_orders = new_limit

        logger(f"✅ Daily order limit updated: {old_limit} → {max_daily_orders}")

        # Save to config
        try:
            from config_manager import config_manager
            config_manager.set("max_daily_orders", max_daily_orders)
        except Exception as config_e:
            logger(f"⚠️ Failed to save daily limit to config: {str(config_e)}")

        return True

    except Exception as e:
        logger(f"❌ Error setting daily order limit: {str(e)}")
        return False

def get_max_daily_orders() -> int:
    """Get current maximum daily orders limit"""
    try:
        global max_daily_orders
        return max_daily_orders
    except Exception as e:
        logger(f"❌ Error getting daily order limit: {str(e)}")
        return 50