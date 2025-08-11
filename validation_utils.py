# --- Validation Utilities Module ---
"""
Input validation and data validation functions
"""

from typing import List, Optional
from logger_utils import logger


def validate_numeric_input(value: str, min_val: float = 0.0, max_val: float = None) -> float:
    """Validate and convert numeric input with proper error handling"""
    try:
        numeric_value = float(value.strip())
        if numeric_value < min_val:
            raise ValueError(f"Value {numeric_value} is below minimum {min_val}")
        if max_val is not None and numeric_value > max_val:
            raise ValueError(f"Value {numeric_value} exceeds maximum {max_val}")
        return numeric_value
    except (ValueError, AttributeError) as e:
        logger(f"Invalid numeric input '{value}': {str(e)}")
        raise


def validate_string_input(value: str, allowed_values: Optional[List[str]] = None) -> str:
    """Validate string input with specific allowed values"""
    try:
        clean_value = value.strip().upper()
        if not clean_value:
            raise ValueError("Empty string not allowed")
        if allowed_values and clean_value not in allowed_values:
            raise ValueError(f"Value '{clean_value}' not in allowed values: {allowed_values}")
        return clean_value
    except AttributeError as e:
        logger(f"Invalid string input: {str(e)}")
        raise


def validate_tp_sl_levels(symbol: str, tp_price: Optional[float], sl_price: Optional[float], order_type: str) -> bool:
    """Validate TP/SL levels according to broker requirements"""
    try:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            # Use mock MT5 for testing
            import mt5_mock as mt5
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ Cannot get symbol info for {symbol}")
            return False
            
        current_tick = mt5.symbol_info_tick(symbol)
        if not current_tick:
            logger(f"❌ Cannot get current tick for {symbol}")
            return False
            
        # Get minimum distance requirements
        stops_level = getattr(symbol_info, 'trade_stops_level', 0)
        point = getattr(symbol_info, 'point', 0.00001)
        min_distance = stops_level * point
        
        if order_type.upper() == "BUY":
            current_price = current_tick.ask
            if tp_price > 0 and tp_price - current_price < min_distance:
                logger(f"❌ TP too close to current price. Min distance: {min_distance}")
                return False
            if sl_price > 0 and current_price - sl_price < min_distance:
                logger(f"❌ SL too close to current price. Min distance: {min_distance}")
                return False
        else:  # SELL
            current_price = current_tick.bid
            if tp_price > 0 and current_price - tp_price < min_distance:
                logger(f"❌ TP too close to current price. Min distance: {min_distance}")
                return False
            if sl_price > 0 and sl_price - current_price < min_distance:
                logger(f"❌ SL too close to current price. Min distance: {min_distance}")
                return False
                
        return True
        
    except Exception as e:
        logger(f"❌ Error validating TP/SL levels: {str(e)}")
        return False


def validate_trading_conditions(symbol: str) -> tuple[bool, str]:
    """Validate if trading conditions are met for the symbol"""
    try:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            # Use mock MT5 for testing
            import mt5_mock as mt5
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return False, f"Symbol {symbol} not found"
            
        if not getattr(symbol_info, 'visible', True):
            return False, f"Symbol {symbol} not visible in Market Watch"
            
        # Check if trading is allowed
        trade_mode = getattr(symbol_info, 'trade_mode', 0)
        if trade_mode == 0:  # SYMBOL_TRADE_MODE_DISABLED
            return False, f"Trading disabled for {symbol}"
            
        # Check market session
        current_tick = mt5.symbol_info_tick(symbol)
        if not current_tick or current_tick.bid == 0 or current_tick.ask == 0:
            return False, f"No valid quotes for {symbol}"
            
        return True, "Trading conditions OK"
        
    except Exception as e:
        logger(f"❌ Error validating trading conditions: {str(e)}")
        return False, f"Validation error: {str(e)}"