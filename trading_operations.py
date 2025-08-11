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

try:
    import MetaTrader5 as mt5
except ImportError:
    # Use mock MT5 for testing on non-Windows platforms
    import mt5_mock as mt5


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


def parse_tp_sl_input(input_value: str, unit: str, symbol: str, order_type: str, current_price: float) -> float:
    """Parse and convert TP/SL input to absolute price"""
    try:
        if not input_value or input_value.strip() == "0":
            return 0.0
            
        value = float(input_value.strip())
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ Cannot get symbol info for {symbol}")
            return 0.0
            
        point = getattr(symbol_info, 'point', 0.00001)
        digits = getattr(symbol_info, 'digits', 5)
        
        if unit.lower() == "pips":
            # Convert pips to price
            if "JPY" in symbol:
                pip_value = point * 10  # For JPY pairs
            else:
                pip_value = point * 10  # For most forex pairs
                
            if order_type.upper() == "BUY":
                if value > 0:  # TP
                    target_price = current_price + (value * pip_value)
                else:  # SL (negative value)
                    target_price = current_price + (value * pip_value)
            else:  # SELL
                if value > 0:  # TP
                    target_price = current_price - (value * pip_value)
                else:  # SL (negative value)
                    target_price = current_price - (value * pip_value)
                    
        elif unit.lower() == "points":
            # Convert points to price
            if order_type.upper() == "BUY":
                target_price = current_price + (value * point)
            else:
                target_price = current_price - (value * point)
                
        else:  # Absolute price
            target_price = value
            
        return round(target_price, digits)
        
    except Exception as e:
        logger(f"❌ Error parsing TP/SL input: {str(e)}")
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
            
        # Adjust TP/SL if too close
        if sl_price > 0:
            if action.upper() == "BUY":
                min_sl = price - min_stops_level
                if sl_price > min_sl:
                    sl_price = round(min_sl, digits)
                    logger(f"⚠️ SL adjusted to minimum distance: {sl_price:.{digits}f}")
            else:  # SELL
                min_sl = price + min_stops_level
                if sl_price < min_sl:
                    sl_price = round(min_sl, digits)
                    logger(f"⚠️ SL adjusted to minimum distance: {sl_price:.{digits}f}")
                    
        if tp_price > 0:
            if action.upper() == "BUY":
                min_tp = price + min_stops_level
                if tp_price < min_tp:
                    tp_price = round(min_tp, digits)
                    logger(f"⚠️ TP adjusted to minimum distance: {tp_price:.{digits}f}")
            else:  # SELL
                min_tp = price - min_stops_level
                if tp_price > min_tp:
                    tp_price = round(min_tp, digits)
                    logger(f"⚠️ TP adjusted to minimum distance: {tp_price:.{digits}f}")
        
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
        logger(f"   Fill Mode: {fill_type} | Deviation: {request['deviation']}")
        logger(f"   Magic: {request['magic']} | Comment: {request['comment']}")
        
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
        
        # Calculate TP/SL prices
        tp_price = parse_tp_sl_input(str(tp_pips), "pips", symbol, action, current_price)
        sl_price = parse_tp_sl_input(str(-sl_pips), "pips", symbol, action, current_price)  # Negative for SL
        
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
        else:
            logger(f"❌ Failed to execute {action} order for {symbol}")
            
        return success
        
    except Exception as e:
        logger(f"❌ Error executing trade signal: {str(e)}")
        return False