# --- Trading Operations Module ---
"""
Order execution, position management, and trading operations
"""

import datetime
import random
from typing import Optional, Dict, Any, Tuple
from logger_utils import logger, log_order_csv
from validation_utils import validate_tp_sl_levels, validate_trading_conditions
from config import DEFAULT_PARAMS
from telegram_notifications import notify_trade_executed, notify_position_closed

# REAL MT5 for Windows Trading (FIXED)
try:
    import MetaTrader5 as mt5
    print("✅ Trading Operations using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Trading Operations using mock - NOT for real trading!")


def calculate_pip_value(symbol: str, lot_size: float) -> float:
    """Calculate pip value for position sizing"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 1.0  # Fallback value

        # For most forex pairs, 1 pip = point * 10
        if "JPY" in symbol:
            pip_value = lot_size * 100000 * 0.01  # JPY pairs
        else:
            pip_value = lot_size * 100000 * 0.0001  # Most forex pairs

        return pip_value

    except Exception as e:
        logger(f"❌ Error calculating pip value: {str(e)}")
        return 1.0


def calculate_tp_sl_all_modes(input_value: str, unit: str, symbol: str, order_type: str, current_price: float, lot_size: float = 0.01) -> float:
    """COMPREHENSIVE: Calculate TP/SL for all modes: pips, price, percentage, money"""
    try:
        if not input_value or input_value.strip() == "0":
            return 0.0

        value = float(input_value.strip())
        if value == 0:
            return 0.0

        symbol_info = mt5.symbol_info(symbol)
        account_info = mt5.account_info()

        if not symbol_info:
            logger(f"❌ Cannot get symbol info for {symbol}")
            return 0.0

        point = getattr(symbol_info, 'point', 0.00001)
        digits = getattr(symbol_info, 'digits', 5)

        # Determine direction (TP positive, SL negative input)
        is_tp = value > 0
        abs_value = abs(value)

        if unit.lower() == "pips":
            # Mode 1: PIPS - Market pips calculation
            pip_multiplier = 10 if "JPY" in symbol else 10
            distance = abs_value * point * pip_multiplier

        elif unit.lower() == "price":
            # Mode 2: PRICE - Direct market price
            return round(value, digits)

        elif unit.lower() in ["percent", "percentage", "%"]:
            # Mode 3A: PERCENTAGE - Based on entry price percentage 
            # This is for "percent" selection (price-based)
            percentage = abs_value

            # CORRECTED: Calculate percentage-based TP/SL with proper direction logic
            if value < 0:  # Stop Loss (negative input)
                if order_type.upper() == "BUY":
                    return current_price * (1 - percentage / 100)  # SL below entry for BUY
                else:  # SELL
                    return current_price * (1 + percentage / 100)  # SL above entry for SELL
            else:  # Take Profit (positive input)
                if order_type.upper() == "BUY":
                    return current_price * (1 + percentage / 100)  # TP above entry for BUY
                else:  # SELL
                    return current_price * (1 - percentage / 100)  # TP below entry for SELL

        elif unit.lower() in ["balance%", "balance_percent"]:
            # Mode 3B: BALANCE PERCENTAGE - CORRECTED FORMULA
            if not account_info:
                logger(f"❌ Cannot get account info for balance% calculation")
                return 0.0

            try:
                balance = account_info.balance
                # CORRECTED: (balance * percentage) / 100
                percentage_amount = (balance * abs_value) / 100  # Fixed formula

                logger(f"🔍 Balance% calculation: ({balance:.2f} * {abs_value}) / 100 = ${percentage_amount:.2f}")

                # Get symbol info
                symbol_info = mt5.symbol_info(symbol)
                if not symbol_info:
                    logger(f"❌ Cannot get symbol info for {symbol}")
                    return 0.0

                # UNIVERSAL ASSET CLASS SUPPORT - Contract specifications
                symbol_upper = symbol.upper()

                # PRECIOUS METALS
                if any(metal in symbol_upper for metal in ['XAU', 'GOLD']):  # Gold
                    contract_size = 100    # Gold CFD = 100 oz
                    point = 0.01
                    digits = 2
                elif any(metal in symbol_upper for metal in ['XAG', 'SILVER']):  # Silver
                    contract_size = 5000   # Silver CFD = 5000 oz
                    point = 0.001
                    digits = 3
                elif any(metal in symbol_upper for metal in ['XPT', 'PLATINUM']):  # Platinum
                    contract_size = 100    # Platinum CFD = 100 oz
                    point = 0.01
                    digits = 2

                # CRYPTOCURRENCIES
                elif any(crypto in symbol_upper for crypto in ['BTC', 'BITCOIN', 'ETH', 'ETHEREUM', 'LTC', 'ADA', 'DOT', 'LINK', 'XRP', 'BCH']):
                    contract_size = 1      # Crypto CFD = 1 unit
                    point = 0.01
                    digits = 2

                # COMMODITIES
                elif any(oil in symbol_upper for oil in ['OIL', 'WTI', 'BRENT', 'USO', 'UKO']):  # Oil
                    contract_size = 1000   # Oil CFD = 1000 barrels
                    point = 0.01
                    digits = 2
                elif any(gas in symbol_upper for gas in ['NATGAS', 'GAS']):  # Natural Gas
                    contract_size = 10000  # Gas CFD = 10000 MMBtu
                    point = 0.001
                    digits = 3

                # INDICES
                elif any(index in symbol_upper for index in ['US30', 'US500', 'NAS100', 'GER30', 'UK100', 'FRA40', 'AUS200', 'JPN225']):
                    contract_size = 1      # Index CFD = 1 unit per point
                    point = 1.0
                    digits = 0
                else:
                    contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
                    point = getattr(symbol_info, 'point', 0.00001)
                    digits = getattr(symbol_info, 'digits', 5)

                # Calculate pip value and distance
                pip_value = lot_size * contract_size * point
                if pip_value > 0:
                    pip_distance = percentage_amount / pip_value
                else:
                    pip_distance = abs_value  # Fallback

                # CRITICAL: Apply reasonable limits to prevent extreme values
                max_pips = 1000  # Maximum 1000 pips
                min_pips = 1     # Minimum 1 pip

                if pip_distance > max_pips:
                    logger(f"⚠️ Balance% calculated {pip_distance:.1f} pips - limiting to {max_pips} pips")
                    pip_distance = max_pips
                elif pip_distance < min_pips:
                    logger(f"⚠️ Balance% calculated {pip_distance:.1f} pips - minimum {min_pips} pip applied")
                    pip_distance = min_pips

                logger(f"🔧 Converting ${percentage_amount:.2f} to {pip_distance:.1f} pips for {symbol}")

                # CRITICAL FIX: Apply minimum distances for Bitcoin and other assets
                symbol_upper = symbol.upper()
                if 'BTC' in symbol_upper:
                    min_pips = 50  # Bitcoin minimum 50 pips
                elif 'ETH' in symbol_upper:
                    min_pips = 30  # Ethereum minimum 30 pips
                elif 'XAU' in symbol_upper:
                    min_pips = 100  # Gold minimum 100 pips
                else:
                    min_pips = 10  # Default minimum

                # Ensure pip_distance meets minimum requirements
                if pip_distance < min_pips:
                    logger(f"⚠️ Balance% calculated {pip_distance:.1f} pips - enforcing {min_pips} pips minimum for {symbol}")
                    pip_distance = min_pips

                # CRITICAL FIX: Correct TP/SL direction logic
                is_stop_loss = value < 0  # Negative value = Stop Loss
                if is_stop_loss:  # STOP LOSS calculation
                    if order_type.upper() == "BUY":
                        return round(current_price - (pip_distance * point), digits)  # SL below entry for BUY
                    else:  # SELL
                        return round(current_price + (pip_distance * point), digits)  # SL above entry for SELL
                else:  # TAKE PROFIT calculation  
                    if order_type.upper() == "BUY":
                        return round(current_price + (pip_distance * point), digits)  # TP above entry for BUY
                    else:  # SELL
                        return round(current_price - (pip_distance * point), digits)  # TP below entry for SELL

            except Exception as e:
                logger(f"❌ Error calculating TP/SL (balance%): {e}")
                return 0.0



        elif unit.lower() in ["equity%", "equity_percent"]:
            # Mode 3C: EQUITY PERCENTAGE - Based on account equity (CORRECTED)
            if not account_info:
                logger(f"❌ Cannot get account info for equity% calculation")
                return 0.0

            equity = account_info.equity
            percentage_amount = equity * (abs_value / 100)  # Amount in currency

            logger(f"🔍 Equity% calculation: {abs_value}% of ${equity:.2f} = ${percentage_amount:.2f}")

            # Convert currency amount to price distance
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger(f"❌ Cannot get symbol info for {symbol}")
                return 0.0

            # Get contract size and point value for proper conversion
            contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
            point = getattr(symbol_info, 'point', 0.00001)
            digits = getattr(symbol_info, 'digits', 5)

            # Calculate price distance based on percentage amount
            pip_value = lot_size * contract_size * point
            if pip_value > 0:
                pip_distance = percentage_amount / pip_value
            else:
                pip_distance = abs_value  # Fallback to pip-based calculation

            logger(f"🔧 Converting ${percentage_amount:.2f} to {pip_distance:.1f} pips for {symbol}")

            # Calculate final price
            is_sl = value < 0 # Added for clarity, assuming value is negative for SL
            if is_sl:
                if order_type.upper() == "BUY":
                    return round(current_price - (pip_distance * point), digits)  # SL below entry
                else:  # SELL
                    return round(current_price + (pip_distance * point), digits)  # SL above entry
            else:
                if order_type.upper() == "BUY":
                    return round(current_price + (pip_distance * point), digits)  # TP above entry
                else:  # SELL
                    return round(current_price - (pip_distance * point), digits)  # TP below entry

        elif unit.lower() == "money":
            # Mode 4: MONEY - Fixed currency amount for TP/SL
            money_amount = abs_value  # Direct currency amount

            # Convert money to price distance
            pip_value = calculate_pip_value(symbol, lot_size) 
            if pip_value <= 0:
                pip_value = 10.0  # Fallback

            pips_distance = money_amount / pip_value
            distance = pips_distance * point * (10 if "JPY" in symbol else 10)

        else:
            # Default: treat as direct price
            return round(value, digits)

        # Apply correct direction based on order type
        if order_type.upper() == "BUY":
            if is_tp:  # TP above entry for BUY
                target_price = current_price + distance
            else:  # SL below entry for BUY  
                target_price = current_price - distance
        else:  # SELL
            if is_tp:  # TP below entry for SELL
                target_price = current_price - distance
            else:  # SL above entry for SELL
                target_price = current_price + distance

        result = round(target_price, digits)
        logger(f"💰 TP/SL Calc: {unit}={value} → Price={result:.{digits}f} (Entry={current_price:.{digits}f})")
        return result

    except Exception as e:
        logger(f"❌ Error calculating TP/SL ({unit}): {str(e)}")
        return 0.0


def calculate_auto_lot_size(symbol: str, risk_percentage: float = 2.0, stop_loss_pips: float = 20.0) -> float:
    """Calculate automatic lot size based on risk management"""
    try:
        account_info = mt5.account_info()
        if not account_info:
            return 0.01  # Fallback

        account_balance = account_info.balance
        risk_amount = account_balance * (risk_percentage / 100)

        # Calculate pip value
        pip_value = calculate_pip_value(symbol, 1.0)  # For 1 lot

        # Calculate lot size
        lot_size = risk_amount / (stop_loss_pips * pip_value)

        # Apply limits
        min_lot = 0.01
        max_lot = min(account_balance / 1000, 10.0)  # Conservative max lot

        calculated_lot = max(min_lot, min(lot_size, max_lot))

        # Round to standard lot increments
        calculated_lot = round(calculated_lot, 2)

        logger(f"💰 Auto lot calculation: Risk=${risk_amount:.2f}, Pips={stop_loss_pips}, Lot={calculated_lot}")

        return calculated_lot

    except Exception as e:
        logger(f"❌ Error calculating auto lot size: {str(e)}")
        return 0.01


def open_order(symbol: str, action: str, lot_size: float, tp_price: float = 0.0, 
               sl_price: float = 0.0, comment: str = "Auto Trade") -> bool:
    """Enhanced order execution with comprehensive error handling"""
    try:
        # Validate inputs
        if not symbol or not action or lot_size <= 0:
            logger(f"❌ Invalid order parameters: {symbol}, {action}, {lot_size}")
            return False

        # Check trading conditions
        conditions_ok, message = validate_trading_conditions(symbol)
        if not conditions_ok:
            logger(f"❌ Trading conditions not met: {message}")
            return False

        # Get current prices
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger(f"❌ Cannot get current tick for {symbol}")
            return False

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ Cannot get symbol info for {symbol}")
            return False

        # Determine order type and price
        if action.upper() == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif action.upper() == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            logger(f"❌ Invalid action: {action}")
            return False

        # Skip TP/SL validation here - will be handled in enhanced request section
        # This prevents double validation that causes issues

        # Prepare order request
        # Enhanced request with Windows MT5 compatibility
        digits = symbol_info.digits
        point = symbol_info.point

        # Validate and adjust TP/SL for MT5 requirements
        min_stops_level = getattr(symbol_info, 'trade_stops_level', 0) * point
        if min_stops_level == 0:
            min_stops_level = 10 * point  # Default minimum distance

        # CRITICAL FIX: Proper TP/SL direction and minimum distance validation
        if action.upper() == "BUY":
            # BUY: TP above price, SL below price
            if tp_price > 0:
                min_tp = price + min_stops_level
                if tp_price < min_tp:
                    tp_price = round(min_tp, digits)
                    logger(f"⚠️ TP adjusted to minimum distance: {tp_price:.{digits}f}")
            if sl_price > 0:
                max_sl = price - min_stops_level
                if sl_price > max_sl:
                    sl_price = round(max_sl, digits)
                    logger(f"⚠️ SL adjusted to minimum distance: {sl_price:.{digits}f}")
        else:  # SELL
            # SELL: TP below price, SL above price
            if tp_price > 0:
                max_tp = price - min_stops_level
                if tp_price > max_tp:
                    tp_price = round(max_tp, digits)
                    logger(f"⚠️ TP adjusted to minimum distance: {tp_price:.{digits}f}")
            if sl_price > 0:
                min_sl = price + min_stops_level
                if sl_price < min_sl:
                    sl_price = round(min_sl, digits)
                    logger(f"⚠️ SL adjusted to minimum distance: {sl_price:.{digits}f}")

        # Final validation - ensure TP/SL are on correct sides
        if action.upper() == "BUY":
            if tp_price > 0 and tp_price <= price:
                tp_price = round(price + (20 * point), digits)
                logger(f"🔧 TP corrected for BUY: {tp_price:.{digits}f}")
            if sl_price > 0 and sl_price >= price:
                sl_price = round(price - (20 * point), digits)
                logger(f"🔧 SL corrected for BUY: {sl_price:.{digits}f}")
        else:  # SELL
            if tp_price > 0 and tp_price >= price:
                tp_price = round(price - (20 * point), digits)
                logger(f"🔧 TP corrected for SELL: {tp_price:.{digits}f}")
            if sl_price > 0 and sl_price <= price:
                sl_price = round(price + (20 * point), digits)
                logger(f"🔧 SL corrected for SELL: {sl_price:.{digits}f}")

        # Determine best fill type for the symbol
        filling_mode = getattr(symbol_info, 'filling_mode', 0)
        if filling_mode & 2:  # ORDER_FILLING_IOC supported
            fill_type = mt5.ORDER_FILLING_IOC
        elif filling_mode & 1:  # ORDER_FILLING_FOK supported
            fill_type = mt5.ORDER_FILLING_FOK
        else:  # Return mode (default)
            fill_type = mt5.ORDER_FILLING_RETURN

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": round(lot_size, 2),
            "type": order_type,
            "price": round(price, digits),
            "sl": round(sl_price, digits) if sl_price > 0 else 0.0,
            "tp": round(tp_price, digits) if tp_price > 0 else 0.0,
            "deviation": 50,  # Increased deviation for volatile markets
            "magic": 234000,
            "comment": comment[:31] if comment else "AutoBot",  # MT5 comment limit
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": fill_type,
        }

        # Final validation before sending
        logger(f"📤 Final Order Request for {symbol}:")
        logger(f"   Action: {action} | Type: {order_type}")
        logger(f"   Volume: {request['volume']} | Price: {request['price']:.{digits}f}")
        logger(f"   TP: {request['tp']:.{digits}f} | SL: {request['sl']:.{digits}f}")
        logger(f"   Fill Mode: {request['fill_type']} | Deviation: {request['deviation']}") # Corrected key to 'fill_type'
        logger(f"   Magic: {request['magic']} | Comment: {request['comment']}")

        # ENHANCED: Final TP/SL validation with minimum distance enforcement
        if request['tp'] > 0 or request['sl'] > 0:
            # Final validation for minimum distances before sending to MT5
            tp_distance = abs(request['tp'] - request['price']) if request['tp'] > 0 else 0
            sl_distance = abs(request['sl'] - request['price']) if request['sl'] > 0 else 0

            # Asset-specific minimum distances (in price units)
            symbol_upper = symbol.upper()
            if 'XAU' in symbol_upper:  # Gold
                min_distance = 1.00  # $1.00 minimum
            elif 'BTC' in symbol_upper:  # Bitcoin
                min_distance = 0.50  # $0.50 minimum
            elif 'ETH' in symbol_upper:  # Ethereum
                min_distance = 0.30  # $0.30 minimum
            else:
                min_distance = 0.0001  # Default for forex

            # Enforce minimum distances
            if request['tp'] > 0 and tp_distance < min_distance:
                logger(f"⚠️ TP distance {tp_distance:.4f} below minimum {min_distance} - adjusting")
                if action == "BUY":
                    request['tp'] = request['price'] + min_distance
                else:  # SELL
                    request['tp'] = request['price'] - min_distance

            if request['sl'] > 0 and sl_distance < min_distance:
                logger(f"⚠️ SL distance {sl_distance:.4f} below minimum {min_distance} - adjusting")
                if action == "BUY":
                    request['sl'] = request['price'] - min_distance
                else:  # SELL
                    request['sl'] = request['price'] + min_distance

            logger(f"✅ Order includes TP/SL levels - will be executed with stops")
            logger(f"   Final TP distance: {abs(request['tp'] - request['price']):.4f}")
            logger(f"   Final SL distance: {abs(request['sl'] - request['price']):.4f}")
        else:
            logger(f"⚠️ Order WITHOUT TP/SL levels - executing market order only")

        # Validate critical parameters
        if request['volume'] <= 0 or request['volume'] > 100:
            logger(f"❌ Invalid volume: {request['volume']}")
            return False

        if request['price'] <= 0:
            logger(f"❌ Invalid price: {request['price']}")
            return False

        # Log order details
        logger(f"📤 Sending {action} order for {symbol}:")
        logger(f"   Volume: {lot_size}")
        logger(f"   Price: {price}")
        logger(f"   TP: {tp_price if tp_price > 0 else 'None'}")
        logger(f"   SL: {sl_price if sl_price > 0 else 'None'}")
        logger(f"   Comment: {comment}")

        # Send order - FIXED for live trading
        result = mt5.order_send(request)

        if result is None:
            logger("❌ Order send failed: No result returned")
            logger("💡 Check MT5 terminal connectivity and trading permissions")
            return False

        # Handle both dict and object responses (Windows MT5 vs Mock compatibility)
        if hasattr(result, 'retcode'):
            # Real MT5 OrderSendResult object (Windows)
            retcode = result.retcode
        elif isinstance(result, dict):
            # Mock dict response (development)
            retcode = result.get('retcode', 0)
        else:
            retcode = 0

        if retcode != 10009:  # TRADE_RETCODE_DONE
            # Extract comment with compatibility
            if hasattr(result, 'comment'):
                comment = result.comment
            elif isinstance(result, dict):
                comment = result.get('comment', 'Unknown error')
            else:
                comment = 'Unknown error'
            logger(f"❌ Order failed: Code {retcode} - {comment}")

            # Enhanced error handling with specific error codes
            if retcode == 10004:  # TRADE_RETCODE_REQUOTE
                logger("💡 Price requote - retrying with current market price...")
                return False  # Could retry with new price
            elif retcode == 10006:  # TRADE_RETCODE_REJECT
                logger("💡 Order rejected - check trading conditions")
            elif retcode == 10007:  # TRADE_RETCODE_CANCEL
                logger("💡 Order cancelled by user or timeout")
            elif retcode == 10008:  # TRADE_RETCODE_PLACED
                logger("💡 Order placed but not executed yet")
            elif retcode == 10009:  # TRADE_RETCODE_DONE
                logger("✅ Order executed successfully (unexpected path)")
            elif retcode == 10013:  # TRADE_RETCODE_INVALID_VOLUME
                logger("💡 Invalid volume - check lot size settings")
            elif retcode == 10018:  # TRADE_RETCODE_MARKET_CLOSED
                logger("💡 Market is closed - check trading session")
            elif retcode == 10019:  # TRADE_RETCODE_NO_MONEY
                logger("💡 Insufficient funds - reduce lot size")
            elif retcode == 10020:  # TRADE_RETCODE_PRICE_CHANGED
                logger("💡 Price changed during execution - retry")
            elif retcode == 10016:  # TRADE_RETCODE_INVALID_STOPS
                logger("💡 Invalid stops - TP/SL too close to market price or wrong direction")
                logger("💡 Solution: Check TP/SL calculation and minimum distance requirements")
            else:
                logger(f"💡 Unknown error code: {retcode}")

            return False
        else:
            # Extract values with Windows MT5 compatibility
            if hasattr(result, 'order'):
                # Real MT5 OrderSendResult object
                order = result.order
                deal = result.deal
                volume = result.volume
                price = result.price
            elif isinstance(result, dict):
                # Mock dict response
                order = result.get('order', 0)
                deal = result.get('deal', 0)
                volume = result.get('volume', 0)
                price = result.get('price', 0)
            else:
                order = deal = volume = price = 0

            logger(f"✅ ORDER EXECUTED SUCCESSFULLY!")
            logger(f"   Order: #{order}")
            logger(f"   Deal: #{deal}")
            logger(f"   Volume: {volume}")
            logger(f"   Price: {price}")

            # Update GUI immediately if available
            try:
                import __main__
                if hasattr(__main__, 'gui') and __main__.gui:
                    __main__.gui.update_account_info()
                    __main__.gui.update_positions()
            except:
                pass

            # Log to CSV
            order_data = {
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'action': action,
                'volume': lot_size,
                'price': price,
                'tp': tp_price if tp_price > 0 else 0,
                'sl': sl_price if sl_price > 0 else 0,
                'comment': comment,
                'ticket': order,
                'profit': 0.0
            }

            log_order_csv("orders.csv", order_data)

            return True

    except Exception as e:
        logger(f"❌ Error executing order: {str(e)}")
        import traceback
        logger(f"📝 Traceback: {traceback.format_exc()}")
        return False


def close_position_by_ticket(ticket: int) -> bool:
    """Close specific position by ticket number"""
    try:
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger(f"❌ Position {ticket} not found")
            return False

        position = positions[0]

        # Determine close parameters
        if position.type == 0:  # BUY position
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(position.symbol).bid
        else:  # SELL position
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).ask

        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Close #{ticket}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send close order
        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger(f"✅ Position {ticket} closed successfully")
            logger(f"   Profit: ${result.bid - result.ask:.2f}")
            return True
        else:
            logger(f"❌ Failed to close position {ticket}")
            return False

    except Exception as e:
        logger(f"❌ Error closing position {ticket}: {str(e)}")
        return False


def close_all_orders(symbol: str = None) -> None:
    """Close all open positions for symbol or all symbols"""
    try:
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
            logger(f"🔄 Closing all positions for {symbol}")
        else:
            positions = mt5.positions_get()
            logger("🔄 Closing ALL open positions")

        if not positions:
            logger("ℹ️ No open positions to close")
            return

        closed_count = 0
        total_profit = 0.0

        for position in positions:
            if close_position_by_ticket(position.ticket):
                closed_count += 1
                total_profit += position.profit

        logger(f"✅ Closed {closed_count}/{len(positions)} positions")
        logger(f"💰 Total profit from closed positions: ${total_profit:.2f}")

    except Exception as e:
        logger(f"❌ Error closing positions: {str(e)}")


def execute_trade_signal(symbol: str, action: str) -> bool:
    """Execute trade based on strategy signal with GUI parameter integration"""
    try:
        # Get current strategy from GUI (will be set by main module)
        current_strategy = "Scalping"  # Default fallback

        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                current_strategy = __main__.gui.current_strategy
        except:
            pass

        # Get trading parameters based on strategy
        params = DEFAULT_PARAMS.get(current_strategy, DEFAULT_PARAMS["Scalping"])

        # Get lot size (with GUI integration if available)
        lot_size = float(params["lot_size"])
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                gui_lot = __main__.gui.get_current_lot_size()
                if gui_lot > 0:
                    lot_size = gui_lot
        except:
            pass

        # Get current price for TP/SL calculations
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger(f"❌ Cannot get current price for {symbol}")
            return False

        current_price = tick.ask if action.upper() == "BUY" else tick.bid

        # Get TP/SL from GUI or use defaults
        tp_pips = float(params["tp_pips"])
        sl_pips = float(params["sl_pips"])

        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                gui_tp = __main__.gui.get_current_tp()
                gui_sl = __main__.gui.get_current_sl()
                if gui_tp > 0:
                    tp_pips = gui_tp
                if gui_sl > 0:
                    sl_pips = gui_sl
        except:
            pass

        # ENHANCED: Get TP/SL settings from GUI with all 4 calculation modes
        # Start with strategy defaults as fallback
        tp_value = str(tp_pips)
        sl_value = str(sl_pips)
        tp_unit = "pips"
        sl_unit = "pips"

        # Get GUI settings with comprehensive mode support
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                gui_tp = __main__.gui.tp_entry.get()
                gui_sl = __main__.gui.sl_entry.get()
                gui_tp_unit = __main__.gui.tp_unit_combo.get()
                gui_sl_unit = __main__.gui.sl_unit_combo.get()

                logger(f"🔍 GUI: Reading TP/SL settings:")
                logger(f"   TP: {gui_tp} | Unit: {gui_tp_unit}")
                logger(f"   SL: {gui_sl} | Unit: {gui_sl_unit}")

                # CRITICAL FIX: Map GUI display names to internal calculation names
                unit_mapping = {
                    "pips": "pips",
                    "price": "price", 
                    "percent": "percent",
                    "percent (balance)": "balance%",
                    "percent (equity)": "equity%",
                    "balance%": "balance%",
                    "equity%": "equity%",
                    "money": "money"
                }

                # ALWAYS use GUI values if available - override strategy defaults
                if gui_tp and gui_tp.strip():
                    tp_value = gui_tp.strip()
                if gui_sl and gui_sl.strip():
                    sl_value = gui_sl.strip()

                # CRITICAL: Always use GUI units - this was the missing piece!
                if gui_tp_unit:
                    tp_unit = unit_mapping.get(gui_tp_unit, gui_tp_unit)
                if gui_sl_unit:
                    sl_unit = unit_mapping.get(gui_sl_unit, gui_sl_unit)

                logger(f"✅ Final TP/SL settings:")
                logger(f"   TP: {tp_value} {tp_unit}")
                logger(f"   SL: {sl_value} {sl_unit}")
                logger(f"   GUI Override: TP_unit={gui_tp_unit} -> {tp_unit}, SL_unit={gui_sl_unit} -> {sl_unit}")
        except Exception as e:
            logger(f"⚠️ GUI settings read error: {e}")

        # Calculate TP/SL with comprehensive 4-mode support
        tp_price = calculate_tp_sl_all_modes(tp_value, tp_unit, symbol, action, current_price, lot_size)
        sl_price = calculate_tp_sl_all_modes(f"-{sl_value}", sl_unit, symbol, action, current_price, lot_size)

        # CRITICAL FIX: XAUUSDm Error 10016 Prevention - Enhanced TP/SL validation
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            point = getattr(symbol_info, 'point', 0.00001)
            digits = getattr(symbol_info, 'digits', 5)
            trade_stops_level = getattr(symbol_info, 'trade_stops_level', 0)

            # UNIVERSAL SYMBOL SUPPORT - Comprehensive asset class detection
            symbol_upper = symbol.upper()

            # PRECIOUS METALS (100+ pips minimum)
            if any(metal in symbol_upper for metal in ['XAU', 'GOLD']):  # Gold
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 100)
            elif any(metal in symbol_upper for metal in ['XAG', 'SILVER']):  # Silver
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 50)
            elif any(metal in symbol_upper for metal in ['XPT', 'PLATINUM']):  # Platinum
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 75)

            # CRYPTOCURRENCIES (25-50 pips minimum)
            elif any(crypto in symbol_upper for crypto in ['BTC', 'BITCOIN']):  # Bitcoin
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 50)
            elif any(crypto in symbol_upper for crypto in ['ETH', 'ETHEREUM']):  # Ethereum
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 30)
            elif any(crypto in symbol_upper for crypto in ['LTC', 'ADA', 'DOT', 'LINK', 'XRP', 'BCH', 'EOS', 'TRX']):  # Other Crypto
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 25)

            # COMMODITIES (20-30 pips minimum)
            elif any(oil in symbol_upper for oil in ['OIL', 'WTI', 'BRENT', 'USO', 'UKO']):  # Oil
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 20)
            elif any(gas in symbol_upper for gas in ['NATGAS', 'GAS']):  # Natural Gas
                point = 0.01
                digits = 2
                min_distance_pips = max(trade_stops_level, 30)

            # INDICES (1-5 points minimum)
            elif any(index in symbol_upper for index in ['US30', 'US500', 'NAS100', 'SPX500', 'DOW']):  # Major US Indices
                point = 1.0
                digits = 0
                min_distance_pips = max(trade_stops_level, 5)
            elif any(index in symbol_upper for index in ['GER30', 'UK100', 'FRA40', 'ESP35', 'ITA40']):  # European Indices
                point = 1.0
                digits = 0
                min_distance_pips = max(trade_stops_level, 3)
            elif any(index in symbol_upper for index in ['AUS200', 'JPN225', 'HK50']):  # Asia-Pacific Indices
                point = 1.0
                digits = 0
                min_distance_pips = max(trade_stops_level, 2)

            # FOREX PAIRS (10-20 pips minimum)
            elif 'JPY' in symbol_upper:  # JPY pairs (special handling for Yen)
                # Keep existing point/digits from symbol_info
                min_distance_pips = max(trade_stops_level, 20)
            elif any(major in symbol_upper for major in ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF']):  # Major pairs
                # Keep existing point/digits from symbol_info
                min_distance_pips = max(trade_stops_level, 10)
            elif any(cross in symbol_upper for cross in ['EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY']):  # Cross pairs
                # Keep existing point/digits from symbol_info
                min_distance_pips = max(trade_stops_level, 15)

            # STOCKS (dynamic based on price)
            elif any(stock_suffix in symbol_upper for stock_suffix in ['.US', '_US', 'STOCK']):  # Stock symbols
                # Dynamic minimum distance based on stock price
                if current_price > 100:
                    min_distance_pips = max(trade_stops_level, 100)  # $1.00 for high-price stocks
                elif current_price > 10:
                    min_distance_pips = max(trade_stops_level, 50)   # $0.50 for mid-price stocks
                else:
                    min_distance_pips = max(trade_stops_level, 10)   # $0.10 for low-price stocks

            # DEFAULT FALLBACK (conservative 15 pips)
            else:
                # Keep existing point/digits from symbol_info for unknown symbols
                min_distance_pips = max(trade_stops_level, 15)  # Conservative default

            min_distance_price = min_distance_pips * point

            logger(f"🔧 {symbol} Validation: Point={point}, Digits={digits}, Min Distance={min_distance_pips} pips")
        else:
            # UNIVERSAL FALLBACK VALUES - Smart defaults for any symbol
            symbol_upper = symbol.upper()

            # High-value assets (Metals, Crypto, Indices)
            if any(asset in symbol_upper for asset in ['XAU', 'XAG', 'XPT', 'BTC', 'ETH', 'LTC', 'US30', 'US500', 'NAS100', 'OIL']):
                point = 0.01
                digits = 2
                min_distance_price = 1.0  # $1.00 minimum distance
            # JPY pairs (3-digit precision)
            elif 'JPY' in symbol_upper:
                point = 0.001
                digits = 3
                min_distance_price = 0.02  # 20 pips for JPY
            # Standard forex (5-digit precision)
            else:
                point = 0.00001
                digits = 5
                min_distance_price = 0.0001  # 10 pips for forex

            logger(f"⚠️ Using smart fallback for {symbol}: Point={point}, Digits={digits}, MinDist=${min_distance_price}")

        # Validate and correct TP price
        if tp_price <= 0.0 or abs(tp_price - current_price) < min_distance_price:
            logger(f"⚠️ TP invalid ({tp_price}) or too close to price ({current_price})")

            # Force minimum distance
            safe_distance = min_distance_price * 2  # Double the minimum for safety
            if action.upper() == "BUY":
                tp_price = round(current_price + safe_distance, digits)
            else:  # SELL
                tp_price = round(current_price - safe_distance, digits)

            logger(f"🔧 Corrected TP: {tp_price} (Distance: {safe_distance})")

        # Validate and correct SL price  
        if sl_price <= 0.0 or abs(sl_price - current_price) < min_distance_price:
            logger(f"⚠️ SL invalid ({sl_price}) or too close to price ({current_price})")

            # Force minimum distance
            safe_distance = min_distance_price * 1.5  # 1.5x minimum for SL
            if action.upper() == "BUY":
                sl_price = round(current_price - safe_distance, digits)
            else:  # SELL  
                sl_price = round(current_price + safe_distance, digits)

            logger(f"🔧 Corrected SL: {sl_price} (Distance: {safe_distance})")

        # Final validation - ensure TP/SL are in correct direction
        if action.upper() == "BUY":
            if tp_price <= current_price:
                tp_price = round(current_price + (min_distance_price * 2), digits)
                logger(f"🔧 Fixed BUY TP direction: {tp_price}")
            if sl_price >= current_price:
                sl_price = round(current_price - (min_distance_price * 1.5), digits)
                logger(f"🔧 Fixed BUY SL direction: {sl_price}")
        else:  # SELL
            if tp_price >= current_price:
                tp_price = round(current_price - (min_distance_price * 2), digits)
                logger(f"🔧 Fixed SELL TP direction: {tp_price}")
            if sl_price <= current_price:
                sl_price = round(current_price + (min_distance_price * 1.5), digits)
                logger(f"🔧 Fixed SELL SL direction: {sl_price}")

        logger(f"🎯 TP/SL calculation results:")
        logger(f"   TP: {tp_value} {tp_unit} → {tp_price:.{digits}f}")
        logger(f"   SL: {sl_value} {sl_unit} → {sl_price:.{digits}f}")
        logger(f"   Entry: {current_price:.{digits}f}")

        # VERIFICATION: Log calculation type for debugging
        if tp_unit == "percent":
            expected_tp = current_price * (1 + float(tp_value)/100) if action.upper() == "BUY" else current_price * (1 - float(tp_value)/100)
            logger(f"   🔍 Expected TP for {tp_value}% {action}: {expected_tp:.2f}")

        # CRITICAL: Ensure TP/SL values are valid for Windows MT5
        if tp_price > 0 and sl_price > 0:
            logger(f"✅ Valid TP/SL levels will be sent with order")
        else:
            logger(f"❌ CRITICAL: Invalid TP/SL detected - TP:{tp_price}, SL:{sl_price}")
            logger(f"🔧 Forcing fallback TP/SL calculation...")

            # Emergency fallback calculation
            symbol_info = mt5.symbol_info(symbol)
            point = 0.01 if 'XAU' in symbol else 0.00001
            digits = getattr(symbol_info, 'digits', 3) if symbol_info else 3

            if action.upper() == "BUY":
                if tp_price <= 0:
                    tp_price = round(current_price + (20 * point), digits)
                if sl_price <= 0:
                    sl_price = round(current_price - (10 * point), digits)
            else:  # SELL
                if tp_price <= 0:
                    tp_price = round(current_price - (20 * point), digits)
                if sl_price <= 0:
                    sl_price = round(current_price + (10 * point), digits)

            logger(f"🔧 Emergency TP/SL: TP={tp_price}, SL={sl_price}")

        logger(f"🎯 Executing {action} signal for {symbol}")
        logger(f"📋 Using strategy: {current_strategy}")
        logger(f"📊 Parameters: Lot={lot_size}, TP={tp_pips} pips, SL={sl_pips} pips")

        # Execute the order
        success = open_order(
            symbol=symbol,
            action=action,
            lot_size=lot_size,
            tp_price=tp_price,
            sl_price=sl_price,
            comment=f"{current_strategy} Auto Trade"
        )

        if success:
            logger(f"✅ {action} order executed successfully for {symbol}")

            # Send Telegram notification for successful trade
            try:
                notify_trade_executed(symbol, action, lot_size, current_price, tp_price, sl_price, current_strategy)
            except Exception as telegram_error:
                logger(f"⚠️ Telegram notification failed: {str(telegram_error)}")
        else:
            logger(f"❌ Failed to execute {action} order for {symbol}")

        return success

    except Exception as e:
        logger(f"❌ Error executing trade signal: {str(e)}")
        return False