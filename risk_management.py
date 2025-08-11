
# --- Risk Management Module ---
"""
Risk management, position sizing, and trade limits - REAL ACCOUNT PROTECTION
"""

import datetime
from typing import Dict, Any, Tuple, Optional
from logger_utils import logger
from config import MAX_RISK_PERCENTAGE, MAX_DAILY_TRADES, MAX_OPEN_POSITIONS, DEFAULT_MAX_ORDERS

# SMART MT5 Connection - Real on Windows, Mock for Development
try:
    import MetaTrader5 as mt5
    print("✅ Risk Management using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Risk Management using mock for development")

# Global risk tracking
daily_trade_count = 0
session_start_time = datetime.datetime.now().date()
max_orders_limit = DEFAULT_MAX_ORDERS


def check_order_limit() -> bool:
    """Check if order limit is reached"""
    try:
        global max_orders_limit
        
        # Get current order count from GUI
        current_orders = 0
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                current_orders = __main__.gui.order_count
        except:
            pass
        
        # Also check actual MT5 positions
        positions = mt5.positions_get()
        actual_positions = len(positions) if positions else 0
        
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
    """Check and reset daily limits"""
    global daily_trade_count, session_start_time
    
    try:
        current_date = datetime.datetime.now().date()
        
        # Reset counters if new day
        if current_date != session_start_time:
            daily_trade_count = 0
            session_start_time = current_date
            logger(f"📅 New trading day: Counters reset")
        
        return daily_trade_count < MAX_DAILY_TRADES
        
    except Exception as e:
        logger(f"❌ Error checking daily limits: {str(e)}")
        return True


def increment_daily_trade_count() -> None:
    """Increment daily trade counter"""
    global daily_trade_count
    
    try:
        daily_trade_count += 1
        logger(f"📊 Daily trades: {daily_trade_count}/{MAX_DAILY_TRADES}")
        
        # Update GUI if available
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                __main__.gui.order_count += 1
                __main__.gui.update_order_count_display()
        except:
            pass
        
    except Exception as e:
        logger(f"❌ Error incrementing trade count: {str(e)}")


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
    """Get current risk metrics from REAL account"""
    try:
        account_info = mt5.account_info()
        positions = mt5.positions_get()
        
        if not account_info:
            return {'error': 'No account info'}
        
        position_count = len(positions) if positions else 0
        
        # Calculate total risk
        total_risk = 0.0
        if positions:
            for pos in positions:
                if pos.sl > 0:  # Has stop loss
                    risk = abs(pos.price_open - pos.sl) * pos.volume
                    total_risk += risk
        
        risk_percentage = (total_risk / account_info.balance) * 100 if account_info.balance > 0 else 0
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': (account_info.equity / account_info.margin * 100) if account_info.margin > 0 else 0,
            'open_positions': position_count,
            'daily_trades': daily_trade_count,
            'total_risk': total_risk,
            'risk_percentage': risk_percentage,
            'max_positions': MAX_OPEN_POSITIONS,
            'max_daily_trades': MAX_DAILY_TRADES,
            'max_orders_limit': max_orders_limit
        }
        
    except Exception as e:
        logger(f"❌ Error getting risk metrics: {str(e)}")
        return {'error': str(e)}


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
