# --- Trading Operations Module ---
"""
Order execution, position management, and trading operations - REAL TRADING ONLY
"""

import datetime
from typing import Optional, Dict, Any, Tuple
from logger_utils import logger, log_order_csv
from validation_utils import validate_tp_sl_levels, validate_trading_conditions
from config import DEFAULT_PARAMS
from telegram_notifications import notify_trade_executed, notify_position_closed

# SMART MT5 Connection - Real on Windows, Mock for Development
try:
    import MetaTrader5 as mt5
    print("✅ Trading Operations using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Trading Operations using mock for development")

# PROFESSIONAL UPGRADES: Import enhanced modules
try:
    from enhanced_position_sizing import get_dynamic_position_size
    DYNAMIC_SIZING_AVAILABLE = True
    logger("✅ Dynamic position sizing loaded")
except ImportError:
    DYNAMIC_SIZING_AVAILABLE = False
    logger("⚠️ Dynamic position sizing not available")

try:
    from trailing_stop_manager import add_trailing_stop_to_position, start_trailing_stop_system
    TRAILING_STOPS_AVAILABLE = True
    logger("✅ Trailing stop system loaded")
except ImportError:
    TRAILING_STOPS_AVAILABLE = False
    logger("⚠️ Trailing stop system not available")

try:
    from economic_calendar import should_pause_for_news, start_economic_calendar
    ECONOMIC_CALENDAR_AVAILABLE = True
    logger("✅ Economic calendar loaded")
except ImportError:
    ECONOMIC_CALENDAR_AVAILABLE = False
    logger("⚠️ Economic calendar not available")

try:
    from drawdown_manager import get_recovery_adjustments, add_trade_to_tracking, initialize_drawdown_tracking
    DRAWDOWN_MANAGER_AVAILABLE = True
    logger("✅ Drawdown manager loaded")
except ImportError:
    DRAWDOWN_MANAGER_AVAILABLE = False
    logger("⚠️ Drawdown manager not available")


def calculate_pip_value(symbol: str, lot_size: float) -> float:
    """Calculate pip value for position sizing"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 1.0

        if "JPY" in symbol:
            pip_value = lot_size * 100000 * 0.01
        else:
            pip_value = lot_size * 100000 * 0.0001

        return pip_value

    except Exception as e:
        logger(f"❌ Error calculating pip value: {str(e)}")
        return 1.0


def calculate_tp_sl_all_modes(input_value: str, unit: str, symbol: str, order_type: str, current_price: float, lot_size: float = 0.01) -> float:
    """Calculate TP/SL for all modes: pips, price, percentage, money - ENHANCED CALCULATIONS"""
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

        # FIXED: Proper TP/SL calculation - NO REVERSAL for HFT or any strategy
        if unit.lower() == "pips":
            # Standard pip calculation
            pip_multiplier = 10 if "JPY" in symbol else 10
            distance = abs(value) * point * pip_multiplier
            
            # CORRECT TP/SL logic - NO reversal needed
            if order_type.upper() == "BUY":
                if value > 0:  # Take Profit
                    return round(current_price + distance, digits)
                else:  # Stop Loss (negative value)
                    return round(current_price - distance, digits)
            else:  # SELL order
                if value > 0:  # Take Profit  
                    return round(current_price - distance, digits)
                else:  # Stop Loss (negative value)
                    return round(current_price + distance, digits)

        elif unit.lower() == "price":
            return round(value, digits)

        elif unit.lower() in ["percent", "percentage", "%"]:
            percentage = abs(value)
            # Percentage-based TP/SL calculation
            if order_type.upper() == "BUY":
                if value > 0:  # Take Profit
                    return round(current_price * (1 + percentage / 100), digits)
                else:  # Stop Loss
                    return round(current_price * (1 - percentage / 100), digits)
            else:  # SELL order
                if value > 0:  # Take Profit
                    return round(current_price * (1 - percentage / 100), digits)
                else:  # Stop Loss
                    return round(current_price * (1 + percentage / 100), digits)

        elif unit.lower() in ["balance%", "balance_percent"]:
            if not account_info:
                logger(f"❌ Cannot get account info for balance% calculation")
                return 0.0

            balance = account_info.balance
            abs_value = abs(value)
            percentage_amount = (balance * abs_value) / 100

            symbol_upper = symbol.upper()

            # Asset class detection for real contracts
            if any(metal in symbol_upper for metal in ['XAU', 'GOLD']):
                contract_size = 100
                point = 0.01
                digits = 2
            elif any(metal in symbol_upper for metal in ['XAG', 'SILVER']):
                contract_size = 5000
                point = 0.001
                digits = 3
            elif any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'LTC']):
                contract_size = 1
                point = 0.01
                digits = 2
            elif any(oil in symbol_upper for oil in ['OIL', 'WTI', 'BRENT']):
                contract_size = 1000
                point = 0.01
                digits = 2
            elif any(index in symbol_upper for index in ['US30', 'US500', 'NAS100']):
                contract_size = 1
                point = 1.0
                digits = 0
            else:
                contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
                point = getattr(symbol_info, 'point', 0.00001)
                digits = getattr(symbol_info, 'digits', 5)

            pip_value = lot_size * contract_size * point
            if pip_value > 0:
                pip_distance = percentage_amount / pip_value
            else:
                pip_distance = abs_value

            # Apply limits
            max_pips = 1000
            min_pips = 1

            if pip_distance > max_pips:
                pip_distance = max_pips
            elif pip_distance < min_pips:
                pip_distance = min_pips

            # Asset-specific minimums
            if 'BTC' in symbol_upper:
                min_pips = 50
            elif 'ETH' in symbol_upper:
                min_pips = 30
            elif 'XAU' in symbol_upper:
                min_pips = 100
            else:
                min_pips = 10

            if pip_distance < min_pips:
                pip_distance = min_pips

            is_stop_loss = value < 0
            if is_stop_loss:
                if order_type.upper() == "BUY":
                    return round(current_price - (pip_distance * point), digits)
                else:  # SELL
                    return round(current_price + (pip_distance * point), digits)
            else:
                if order_type.upper() == "BUY":
                    return round(current_price + (pip_distance * point), digits)
                else:  # SELL
                    return round(current_price - (pip_distance * point), digits)

        elif unit.lower() in ["equity%", "equity_percent"]:
            if not account_info:
                return 0.0

            equity = account_info.equity
            percentage_amount = equity * (abs_value / 100)

            contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
            pip_value = lot_size * contract_size * point
            if pip_value > 0:
                pip_distance = percentage_amount / pip_value
            else:
                pip_distance = abs_value

            is_sl = value < 0
            if is_sl:
                if order_type.upper() == "BUY":
                    return round(current_price - (pip_distance * point), digits)
                else:
                    return round(current_price + (pip_distance * point), digits)
            else:
                if order_type.upper() == "BUY":
                    return round(current_price + (pip_distance * point), digits)
                else:
                    return round(current_price - (pip_distance * point), digits)

        elif unit.lower() == "money":
            money_amount = abs_value
            pip_value = calculate_pip_value(symbol, lot_size) 
            if pip_value <= 0:
                pip_value = 10.0

            pips_distance = money_amount / pip_value
            distance = pips_distance * point * (10 if "JPY" in symbol else 10)

        else:
            return round(value, digits)

        # Apply direction based on order type
        if order_type.upper() == "BUY":
            if is_tp:
                target_price = current_price + distance
            else:
                target_price = current_price - distance
        else:  # SELL
            if is_tp:
                target_price = current_price - distance
            else:
                target_price = current_price + distance

        result = round(target_price, digits)
        logger(f"💰 TP/SL Calc: {unit}={value} → Price={result:.{digits}f}")
        return result

    except Exception as e:
        logger(f"❌ Error calculating TP/SL ({unit}): {str(e)}")
        return 0.0


def open_order(symbol: str, action: str, lot_size: float, tp_price: float = 0.0, 
               sl_price: float = 0.0, comment: str = "Live Trade") -> bool:
    """Execute REAL order on live MT5 account with retry mechanism"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            if not symbol or not action or lot_size <= 0:
                logger(f"❌ Invalid order parameters: {symbol}, {action}, {lot_size}")
                return False

            conditions_ok, message = validate_trading_conditions(symbol)
            if not conditions_ok:
                logger(f"❌ Trading conditions not met: {message}")
                return False
            
            # Check MT5 connection before each attempt
            if not mt5.account_info():
                logger(f"⚠️ MT5 connection lost, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    from mt5_connection import connect_mt5
                    if connect_mt5():
                        continue
                    else:
                        time.sleep(1)
                        continue
                else:
                    return False

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logger(f"❌ Cannot get current tick for {symbol}")
                return False

            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger(f"❌ Cannot get symbol info for {symbol}")
                return False

            if action.upper() == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif action.upper() == "SELL":
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                logger(f"❌ Invalid action: {action}")
                return False

            digits = symbol_info.digits
            point = symbol_info.point

            min_stops_level = getattr(symbol_info, 'trade_stops_level', 0) * point
            if min_stops_level == 0:
                min_stops_level = 10 * point

            # Validate TP/SL distances for real trading
            if action.upper() == "BUY":
                if tp_price > 0:
                    min_tp = price + min_stops_level
                    if tp_price < min_tp:
                        tp_price = round(min_tp, digits)
                if sl_price > 0:
                    max_sl = price - min_stops_level
                    if sl_price > max_sl:
                        sl_price = round(max_sl, digits)
            else:  # SELL
                if tp_price > 0:
                    max_tp = price - min_stops_level
                    if tp_price > max_tp:
                        tp_price = round(max_tp, digits)
                if sl_price > 0:
                    min_sl = price + min_stops_level
                    if sl_price < min_sl:
                        sl_price = round(min_sl, digits)

            filling_mode = getattr(symbol_info, 'filling_mode', 0)
            if filling_mode & 2:
                fill_type = mt5.ORDER_FILLING_IOC
            elif filling_mode & 1:
                fill_type = mt5.ORDER_FILLING_FOK
            else:
                fill_type = mt5.ORDER_FILLING_RETURN

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": round(lot_size, 2),
                "type": order_type,
                "price": round(price, digits),
                "sl": round(sl_price, digits) if sl_price > 0 else 0.0,
                "tp": round(tp_price, digits) if tp_price > 0 else 0.0,
                "deviation": 50,
                "magic": 234000,
                "comment": comment[:31] if comment else "LiveBot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": fill_type,
            }

            logger(f"📤 LIVE ORDER: {action} {lot_size} {symbol} @ {price:.{digits}f}")
            logger(f"   TP: {tp_price:.{digits}f} | SL: {sl_price:.{digits}f}")

            # Send REAL order to live market
            result = mt5.order_send(request)

            if result is None:
                logger("❌ Live order failed: No result returned")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return False

            retcode = result.retcode if hasattr(result, 'retcode') else result.get('retcode', 0)

            if retcode != mt5.TRADE_RETCODE_DONE:
                comment = result.comment if hasattr(result, 'comment') else result.get('comment', 'Unknown error')
                logger(f"❌ Live order failed: Code {retcode} - {comment}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return False
            else:
                order = result.order if hasattr(result, 'order') else result.get('order', 0)
                deal = result.deal if hasattr(result, 'deal') else result.get('deal', 0)
                volume = result.volume if hasattr(result, 'volume') else result.get('volume', 0)
                exec_price = result.price if hasattr(result, 'price') else result.get('price', 0)

                logger(f"✅ LIVE ORDER EXECUTED!")
                logger(f"   Order: #{order} | Deal: #{deal}")
                logger(f"   Volume: {volume} | Price: {exec_price}")

                # Update GUI
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
                    'price': exec_price,
                    'tp': tp_price if tp_price > 0 else 0,
                    'sl': sl_price if sl_price > 0 else 0,
                    'comment': comment,
                    'ticket': order,
                    'profit': 0.0
                }

                log_order_csv("orders.csv", order_data)
                return True

        except Exception as e:
            logger(f"❌ Error executing live order (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False
    
    return False


def close_position_by_ticket(ticket: int) -> bool:
    """Close specific live position"""
    try:
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger(f"❌ Position {ticket} not found")
            return False

        position = positions[0]

        if position.type == 0:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(position.symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).ask

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

        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger(f"✅ Live position {ticket} closed successfully")
            return True
        else:
            logger(f"❌ Failed to close live position {ticket}")
            return False

    except Exception as e:
        logger(f"❌ Error closing position {ticket}: {str(e)}")
        return False


def close_all_orders(symbol: str = None) -> None:
    """Close all live positions"""
    try:
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
            logger(f"🔄 Closing all live positions for {symbol}")
        else:
            positions = mt5.positions_get()
            logger("🔄 Closing ALL live positions")

        if not positions:
            logger("ℹ️ No live positions to close")
            return

        closed_count = 0
        total_profit = 0.0

        for position in positions:
            if close_position_by_ticket(position.ticket):
                closed_count += 1
                total_profit += position.profit

        logger(f"✅ Closed {closed_count}/{len(positions)} live positions")
        logger(f"💰 Total profit: ${total_profit:.2f}")

    except Exception as e:
        logger(f"❌ Error closing positions: {str(e)}")


def execute_trade_signal(symbol: str, action: str) -> bool:
    """Execute REAL trade signal with live money - ENHANCED FOR REAL TRADING"""
    try:
        # SAFETY CHECK 1: Order limits
        from risk_management import check_order_limit
        if not check_order_limit():
            logger("🛑 Order limit reached - skipping live trade")
            return False
        
        # SAFETY CHECK 2: Economic calendar news check
        if ECONOMIC_CALENDAR_AVAILABLE:
            should_pause, pause_reason, event_info = should_pause_for_news(symbol)
            if should_pause:
                logger(f"📅 Trade paused for news: {pause_reason}")
                return False
        
        # SAFETY CHECK 3: Drawdown recovery adjustments
        recovery_adjustments = {}
        if DRAWDOWN_MANAGER_AVAILABLE:
            recovery_adjustments = get_recovery_adjustments()
            if recovery_adjustments.get("pause_low_confidence", False):
                # Additional validation for recovery mode
                logger("⚠️ Recovery mode active - using conservative parameters")

        current_strategy = "Scalping"
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                current_strategy = __main__.gui.current_strategy
        except:
            pass

        params = DEFAULT_PARAMS.get(current_strategy, DEFAULT_PARAMS["Scalping"])
        
        # PROFESSIONAL UPGRADE: Dynamic Position Sizing
        lot_size = float(params["lot_size"])  # Fallback default
        
        # Get initial prices for position sizing calculation
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger(f"❌ Cannot get live price for {symbol}")
            return False
        
        current_price = tick.ask if action.upper() == "BUY" else tick.bid
        
        # Get stop loss for position sizing calculation
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                gui_sl = __main__.gui.sl_entry.get()
                if gui_sl and gui_sl.strip():
                    sl_value_temp = gui_sl.strip()
                else:
                    sl_value_temp = params["sl_pips"]
            else:
                sl_value_temp = params["sl_pips"]
        except:
            sl_value_temp = params["sl_pips"]
        
        # Calculate stop loss price for dynamic sizing
        sl_distance_pips = float(sl_value_temp) if str(sl_value_temp).replace('.', '').isdigit() else 10.0
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            point = getattr(symbol_info, 'point', 0.00001)
            pip_multiplier = 10 if "JPY" in symbol else 10
            sl_distance = sl_distance_pips * point * pip_multiplier
            
            if action.upper() == "BUY":
                estimated_sl_price = current_price - sl_distance
            else:
                estimated_sl_price = current_price + sl_distance
        else:
            estimated_sl_price = current_price * 0.99 if action.upper() == "BUY" else current_price * 1.01
        
        # DYNAMIC POSITION SIZING CALCULATION WITH RECOVERY ADJUSTMENTS
        if DYNAMIC_SIZING_AVAILABLE:
            try:
                dynamic_lot, sizing_details = get_dynamic_position_size(
                    symbol=symbol,
                    entry_price=current_price,
                    stop_loss=estimated_sl_price,
                    strategy=current_strategy
                )
                
                if dynamic_lot > 0:
                    lot_size = dynamic_lot
                    
                    # Apply recovery mode adjustments
                    if recovery_adjustments and "lot_size_multiplier" in recovery_adjustments:
                        lot_adjustment = recovery_adjustments["lot_size_multiplier"]
                        lot_size = lot_size * lot_adjustment
                        logger(f"⚡ Recovery mode: Lot size adjusted by {lot_adjustment:.2f}x")
                    
                    logger(f"💰 Final lot size: {lot_size} (Risk: {sizing_details.get('risk_percent', 0):.2f}%)")
                    logger(f"   Sizing method: {sizing_details.get('method', 'Unknown')}")
                else:
                    logger(f"⚠️ Dynamic sizing returned invalid lot: {dynamic_lot}, using default")
                    
            except Exception as dyn_e:
                logger(f"⚠️ Dynamic sizing error: {str(dyn_e)}, using default lot size")
        
        # GUI override (if user manually sets lot size)
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                gui_lot = __main__.gui.get_current_lot_size()
                if gui_lot > 0:
                    lot_size = gui_lot
                    logger(f"🔧 GUI override: Using manual lot size {lot_size}")
        except:
            pass

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger(f"❌ Cannot get live price for {symbol}")
            return False

        current_price = tick.ask if action.upper() == "BUY" else tick.bid

        tp_value = str(params["tp_pips"])
        sl_value = str(params["sl_pips"])
        tp_unit = "pips"
        sl_unit = "pips"

        # Get GUI settings
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                gui_tp = __main__.gui.tp_entry.get()
                gui_sl = __main__.gui.sl_entry.get()
                gui_tp_unit = __main__.gui.tp_unit_combo.get()
                gui_sl_unit = __main__.gui.sl_unit_combo.get()

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

                if gui_tp and gui_tp.strip():
                    tp_value = gui_tp.strip()
                if gui_sl and gui_sl.strip():
                    sl_value = gui_sl.strip()

                if gui_tp_unit:
                    tp_unit = unit_mapping.get(gui_tp_unit, gui_tp_unit)
                if gui_sl_unit:
                    sl_unit = unit_mapping.get(gui_sl_unit, gui_sl_unit)

                logger(f"✅ Using GUI settings: TP={tp_value} {tp_unit}, SL={sl_value} {sl_unit}")
        except Exception as e:
            logger(f"⚠️ GUI settings error: {e}")

        # Calculate TP/SL for REAL trading
        tp_price = calculate_tp_sl_all_modes(tp_value, tp_unit, symbol, action, current_price, lot_size)
        sl_price = calculate_tp_sl_all_modes(f"-{sl_value}", sl_unit, symbol, action, current_price, lot_size)

        logger(f"🎯 Executing LIVE {action} signal for {symbol}")
        logger(f"📋 Strategy: {current_strategy} | Lot: {lot_size}")
        logger(f"📊 Entry: {current_price:.5f} | TP: {tp_price:.5f} | SL: {sl_price:.5f}")

        # Execute REAL order with REAL money
        success = open_order(
            symbol=symbol,
            action=action,
            lot_size=lot_size,
            tp_price=tp_price,
            sl_price=sl_price,
            comment=f"{current_strategy} LIVE"
        )

        if success:
            logger(f"✅ LIVE {action} order executed successfully for {symbol}")
            
            # PROFESSIONAL ENHANCEMENTS POST-EXECUTION
            
            # 1. Add trailing stop if available
            if TRAILING_STOPS_AVAILABLE:
                try:
                    # Get the position ticket from recent positions
                    positions = mt5.positions_get(symbol=symbol)
                    if positions:
                        latest_position = positions[-1]  # Most recent position
                        trail_config = {
                            "trail_distance_pips": 20,
                            "use_atr_based": True,
                            "min_profit_pips": 10
                        }
                        add_trailing_stop_to_position(latest_position.ticket, symbol, trail_config)
                        logger(f"📈 Trailing stop added to position {latest_position.ticket}")
                except Exception as trail_e:
                    logger(f"⚠️ Failed to add trailing stop: {str(trail_e)}")
            
            # 2. Track trade for drawdown analysis
            if DRAWDOWN_MANAGER_AVAILABLE:
                try:
                    # Initial tracking (profit will be updated when closed)
                    add_trade_to_tracking(symbol, action, 0.0, lot_size)
                except Exception as track_e:
                    logger(f"⚠️ Failed to track trade: {str(track_e)}")
            
            # 3. Log order to CSV
            try:
                log_order_csv(symbol, action, lot_size, current_price, tp_price, sl_price, "LiveSignal")
            except Exception as csv_e:
                logger(f"⚠️ CSV logging failed: {str(csv_e)}")
            
            # 4. Send Telegram notification
            try:
                notify_trade_executed(symbol, action, lot_size, current_price, tp_price, sl_price, current_strategy)
            except Exception as telegram_error:
                logger(f"⚠️ Telegram notification failed: {str(telegram_error)}")
                
        else:
            logger(f"❌ Failed to execute LIVE {action} order for {symbol}")

        return success

    except Exception as e:
        logger(f"❌ Error executing live trade signal: {str(e)}")
        return False