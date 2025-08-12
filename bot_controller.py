# --- Bot Controller Module ---
"""
Main bot logic and trading automation controller
"""

import time
import datetime
import threading
from typing import Optional, Dict, Any

# Import all our modular components
from logger_utils import logger
from config import DEFAULT_SYMBOLS
from mt5_connection import check_mt5_status
from data_manager import get_symbol_data, get_multiple_symbols_data
from indicators import calculate_indicators
from strategies import run_strategy
from trading_operations import execute_trade_signal
from session_management import check_trading_time, get_current_trading_session, adjust_strategy_for_session
from risk_management import risk_management_check, check_daily_limits, increment_daily_trade_count, auto_recovery_check, check_order_limit
from ai_analysis import ai_market_analysis
from performance_tracking import send_hourly_report
from validation_utils import validate_trading_conditions

# Global bot state
# NOTE: The original code used 'bot_running' but the provided changes use 'is_running'.
# To maintain consistency with the provided changes, 'is_running' will be used.
# If the original code intended a different meaning for 'bot_running', this might need adjustment.
is_running = False  # Renamed from bot_running to align with changes
bot_thread: Optional[threading.Thread] = None # Explicitly typing bot_thread
recovery_thread: Optional[threading.Thread] = None # Added for recovery monitor
current_strategy = "Scalping"


def main_trading_loop() -> None:
    """Main bot thread - identical logic to original but modular"""
    global is_running, current_strategy # Changed bot_running to is_running

    try:
        logger("🚀 Trading bot thread started")
        logger("🔍 Initializing automated trading system...")

        # Reset daily counters
        check_daily_limits()

        # Main trading loop - FIXED stop mechanism
        while True:
            try:
                # Single bot running check per iteration
                if not is_running: # Changed bot_running to is_running
                    logger("🛑 Bot stopped")
                    break

                # Risk management checks (non-blocking)
                if not risk_management_check():
                    logger("⚠️ Risk management warning - continuing with caution")

                # Check daily limits (now includes user-configurable daily order limit)
                if not check_daily_limits():
                    from risk_management import get_daily_trade_status
                    status = get_daily_trade_status()
                    logger(f"📊 Daily order limit reached ({status['current_count']}/{status['max_limit']}) - pausing for today")
                    time.sleep(300)  # Wait 5 minutes then check again
                    continue

                # Check trading session
                if not check_trading_time():
                    logger("⏰ Outside trading hours - waiting...")
                    time.sleep(60)
                    continue

                # Get current strategy from GUI
                try:
                    # Attempt to import __main__ cautiously
                    main_module = __import__('__main__')
                    if hasattr(main_module, 'gui') and main_module.gui:
                        gui_strategy = main_module.gui.current_strategy
                        if gui_strategy != current_strategy:
                            current_strategy = gui_strategy
                            logger(f"🔄 Strategy updated from GUI to: {current_strategy}")
                except ImportError:
                    logger("⚠️ __main__ module not found, cannot get strategy from GUI.")
                except Exception as gui_e:
                    logger(f"⚠️ GUI connection issue: {str(gui_e)}")
                    current_strategy = "Scalping" # Fallback strategy

                # Check MT5 connection status
                if not check_mt5_status():
                    logger("❌ MT5 connection lost, attempting recovery...")
                    from mt5_connection import connect_mt5
                    if not connect_mt5():
                        logger("🔄 Waiting 30 seconds before retry...")
                        # Check stop signal during retry wait
                        for wait_second in range(30):
                            if not is_running: # Changed bot_running to is_running
                                logger("🛑 Bot stopped during MT5 reconnection wait")
                                return
                            time.sleep(1)
                        continue

                # Get trading symbols
                try:
                    main_module = __import__('__main__')
                    if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'symbol_combo') and main_module.gui.symbol_combo.get():
                        trading_symbols = [main_module.gui.symbol_combo.get()]
                    else:
                        trading_symbols = DEFAULT_SYMBOLS[:3]  # Use first 3 default symbols
                except Exception as gui_sym_e:
                    logger(f"⚠️ GUI symbol retrieval issue: {str(gui_sym_e)}")
                    trading_symbols = DEFAULT_SYMBOLS[:3] # Fallback symbols

                logger(f"📊 Analyzing {len(trading_symbols)} symbols with {current_strategy} strategy")

                # Get data for all symbols - FIXED parameter
                symbol_data = get_multiple_symbols_data(trading_symbols, count=500)

                if not symbol_data:
                    logger("❌ No symbol data available, waiting...")
                    time.sleep(60)
                    continue

                # Process each symbol
                signals_found = 0

                for symbol, df in symbol_data.items():
                    try:
                        # Calculate indicators
                        df_with_indicators = calculate_indicators(df)

                        if df_with_indicators is None:
                            logger(f"⚠️ Indicator calculation failed for {symbol}")
                            continue

                        # Run strategy with current strategy from GUI
                        action, signals = run_strategy(current_strategy, df_with_indicators, symbol)

                        if action and len(signals) > 0:
                            signals_found += 1
                            logger(f"🎯 Signal detected for {symbol}: {action}")

                            # Validate trading conditions
                            conditions_ok, condition_msg = validate_trading_conditions(symbol)
                            if not conditions_ok:
                                logger(f"⚠️ Trading conditions not met for {symbol}: {condition_msg}")
                                continue

                            # Get current trading session and adjustments
                            current_session = get_current_trading_session()
                            session_adjustments = adjust_strategy_for_session(current_strategy, current_session)

                            # LIVE TRADING: More aggressive signal acceptance
                            signal_threshold = max(1, 1 + session_adjustments.get("signal_threshold_modifier", 0))
                            if len(signals) < signal_threshold:
                                logger(f"⚪ {symbol}: Signal strength {len(signals)} below threshold {signal_threshold}")
                                continue

                            try:
                                # CRITICAL: Final stop check before trade execution
                                if not is_running: # Changed bot_running to is_running
                                    logger(f"🛑 Bot stopped before executing trade for {symbol}")
                                    return

                                # Check order limit before execution - BYPASS FOR AGGRESSIVENESS
                                order_limit_ok = check_order_limit()
                                if not order_limit_ok:
                                    logger(f"⚠️ Order limit reached but FORCING execution for maximum opportunities")

                                # Get GUI instance for parameter retrieval
                                gui = None
                                try:
                                    main_module = __import__('__main__')
                                    if hasattr(main_module, 'gui'):
                                        gui = main_module.gui
                                except Exception as gui_e:
                                    logger(f"⚠️ GUI instance retrieval failed: {str(gui_e)}")

                                # Get trading parameters from GUI with proper defaults
                                lot_size = 0.01
                                tp_value = "20"
                                sl_value = "10"
                                tp_unit = "pips"
                                sl_unit = "pips"

                                if gui:
                                    try:
                                        lot_size = float(gui.get_current_lot() or 0.01)
                                        tp_value = gui.get_current_tp() or "20"
                                        sl_value = gui.get_current_sl() or "10"
                                        tp_unit = gui.get_current_tp_unit() or "pips"
                                        sl_unit = gui.get_current_sl_unit() or "pips"
                                    except:
                                        pass  # Use defaults

                                # Set strategy-specific defaults if empty
                                if not tp_value or tp_value == "0":
                                    tp_value = {
                                        "Scalping": "15",
                                        "HFT": "8",
                                        "Intraday": "50",
                                        "Arbitrage": "25"
                                    }.get(current_strategy, "20")

                                if not sl_value or sl_value == "0":
                                    sl_value = {
                                        "Scalping": "8",
                                        "HFT": "4",
                                        "Intraday": "25",
                                        "Arbitrage": "10"
                                    }.get(current_strategy, "10")

                                # Execute the trade with proper validation
                                success = execute_trade_signal(symbol, action, lot_size, tp_value, sl_value, tp_unit, sl_unit, current_strategy)

                                if success:
                                    logger(f"✅ Trade executed successfully for {symbol}")

                                    # Update GUI order count safely
                                    if gui and hasattr(gui, 'order_count'):
                                        gui.order_count += 1
                                        if hasattr(gui, 'update_order_count_display'):
                                            gui.root.after(0, gui.update_order_count_display)
                                else:
                                    logger(f"❌ Trade execution failed for {symbol}")

                            except Exception as trade_e:
                                logger(f"❌ Trade execution error for {symbol}: {str(trade_e)}")

                        # Small delay between symbol processing
                        time.sleep(2)

                    except Exception as symbol_e:
                        logger(f"❌ Error processing {symbol}: {str(symbol_e)}")
                        continue

                # Log summary
                if signals_found > 0:
                    logger(f"📊 Scan complete: {signals_found} signals found from {len(symbol_data)} symbols")
                else:
                    logger(f"📊 Scan complete: No signals found from {len(symbol_data)} symbols")

                # Auto-recovery check
                auto_recovery_check()

                # Send hourly report
                current_time = datetime.datetime.now()
                if current_time.minute == 0:  # Top of the hour
                    send_hourly_report()

                # Get scan interval from GUI
                scan_interval = 15  # More aggressive scanning
                try:
                    main_module = __import__('__main__')
                    if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'interval_entry'):
                        interval_text = main_module.gui.interval_entry.get().strip()
                        if interval_text and interval_text.isdigit():
                            scan_interval = max(5, min(int(interval_text), 300))  # 5-300 seconds range
                except Exception as gui_interval_e:
                    logger(f"⚠️ GUI interval retrieval issue: {str(gui_interval_e)}")
                    pass

                # CRITICAL: Interruptible wait - check stop signal during wait
                logger(f"⏳ Waiting {scan_interval} seconds before next scan...")
                for wait_second in range(scan_interval):
                    if not is_running: # Changed bot_running to is_running
                        logger("🛑 Bot stopped during scan interval wait")
                        return
                    time.sleep(1)

            except KeyboardInterrupt:
                logger("⚠️ Bot interrupted by user")
                break

            except Exception as cycle_e:
                logger(f"❌ Error in trading cycle: {str(cycle_e)}")
                import traceback
                logger(f"📝 Traceback: {traceback.format_exc()}")
                time.sleep(60)  # Wait 1 minute before retry

    except Exception as e:
        logger(f"❌ Critical error in bot thread: {str(e)}")
        import traceback
        logger(f"📝 Critical traceback: {traceback.format_exc()}")

    finally:
        is_running = False # Changed bot_running to is_running
        logger("🛑 Bot thread stopped")

        # Update GUI status if available
        try:
            main_module = __import__('__main__')
            if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'bot_status_lbl'):
                main_module.gui.bot_status_lbl.config(text="Bot: Stopped 🔴", foreground="red")
        except Exception as gui_status_e:
            logger(f"⚠️ GUI status update error: {str(gui_status_e)}")


# --- Modified Functions for Robustness ---

def start_bot_thread() -> bool:
    """Start bot thread with safety checks"""
    global is_running, bot_thread

    try:
        if is_running:
            logger("⚠️ Bot already running")
            return True

        # Check MT5 connection
        if not check_mt5_status():
            logger("❌ MT5 not connected. Please connect first.")
            return False

        logger("🚀 Starting trading bot thread...")
        is_running = True

        # Create and start thread
        bot_thread = threading.Thread(target=main_trading_loop, daemon=True)
        bot_thread.start()

        # Verify thread started
        time.sleep(2)
        if bot_thread.is_alive():
            logger("✅ Trading bot started successfully - ACTIVE TRADING MODE")
            logger("🎯 Bot akan mulai menganalisis dan mengambil order")
            return True
        else:
            logger("❌ Bot thread failed to start")
            is_running = False
            return False

    except Exception as e:
        logger(f"❌ Error starting bot: {str(e)}")
        is_running = False
        return False


def safe_trading_loop():
    """Trading loop with comprehensive error handling"""
    global is_running

    try:
        # Call the original bot_thread logic
        main_trading_loop()
    except KeyboardInterrupt:
        logger("⚠️ Trading loop interrupted by user")
    except Exception as e:
        logger(f"❌ Critical error in trading loop: {str(e)}")
        import traceback
        logger(f"📝 Traceback: {traceback.format_exc()}")

        # Attempt recovery
        try:
            logger("🔄 Attempting automatic recovery...")
            emergency_cleanup()

            # Wait before potential restart
            time.sleep(5)

            # Check if we should restart
            if is_running and check_mt5_status():
                logger("🔄 Restarting trading loop...")
                # Recursively call safe_trading_loop to restart the process
                safe_trading_loop()
            else:
                logger("❌ Recovery conditions not met, stopping bot.")
                is_running = False # Ensure bot stops if recovery fails

        except Exception as recovery_error:
            logger(f"❌ Recovery failed: {str(recovery_error)}")
            is_running = False # Ensure bot stops if recovery itself fails
    finally:
        is_running = False
        logger("🏁 Trading loop terminated")


def emergency_cleanup():
    """Emergency cleanup function"""
    try:
        # Import necessary functions here to avoid circular dependencies or load issues
        from risk_management import emergency_close_all_positions, reset_order_count
        from trading_operations import close_all_orders # This might be redundant if emergency_close_all_positions handles it

        logger("🚨 Performing emergency cleanup...")

        # Close all positions if needed
        # Assuming emergency_close_all_positions is more specific for emergencies
        emergency_close_all_positions()

        # Reset counters
        reset_order_count()

        logger("✅ Emergency cleanup completed")

    except Exception as e:
        logger(f"❌ Emergency cleanup error: {str(e)}")


def start_auto_recovery_monitor():
    """Background monitoring thread for auto-recovery"""
    global recovery_thread, is_running

    if recovery_thread and recovery_thread.is_alive():
        logger("ℹ️ Recovery monitor already running.")
        return

    def recovery_monitor():
        while True:
            try:
                if is_running: # Check the global is_running flag
                    auto_recovery_check()

                # Add a condition to break if bot is stopped to prevent infinite loop
                if not is_running:
                    logger("🛑 Recovery monitor stopping as bot is not running.")
                    break

                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger(f"❌ Recovery monitor error: {str(e)}")
                time.sleep(60) # Wait longer if an error occurs

    recovery_thread = threading.Thread(target=recovery_monitor, daemon=True, name="RecoveryMonitor")
    recovery_thread.start()
    logger("🔄 Auto-recovery monitor started")


def get_bot_status() -> Dict[str, Any]:
    """Get current bot status information"""
    try:
        from risk_management import get_current_risk_metrics

        risk_metrics = get_current_risk_metrics()

        status = {
            'running': is_running, # Changed bot_running to is_running
            'current_strategy': current_strategy,
            'mt5_connected': check_mt5_status(),
            'trading_time_ok': check_trading_time(),
            'risk_check_ok': risk_management_check(),
            'daily_trades': risk_metrics.get('daily_trades', 0),
            'open_positions': risk_metrics.get('open_positions', 0),
            'last_update': datetime.datetime.now().strftime('%H:%M:%S')
        }

        return status

    except Exception as e:
        logger(f"❌ Error getting bot status: {str(e)}")
        return {
            'running': is_running, # Changed bot_running to is_running
            'error': str(e)
        }


def stop_bot():
    """Stop the trading bot gracefully"""
    global is_running, bot_thread
    try:
        logger("🛑 Stopping trading bot...")
        is_running = False

        # Wait for bot thread to finish
        if bot_thread and bot_thread.is_alive():
            bot_thread.join(timeout=5)

        logger("✅ Trading bot stopped successfully")

    except Exception as e:
        logger(f"❌ Error stopping bot: {str(e)}")


def emergency_stop_all():
    """Emergency stop all operations"""
    global is_running # Changed bot_running to is_running
    try:
        logger("🚨 EMERGENCY STOP INITIATED!")

        # Stop bot
        is_running = False

        # Close all positions
        # Assuming emergency_cleanup already handles this, but can be called explicitly if needed
        emergency_cleanup()

        # Update GUI status if available
        try:
            main_module = __import__('__main__')
            if hasattr(main_module, 'gui') and main_module.gui:
                main_module.gui.bot_status_lbl.config(text="Bot: Emergency Stopped 🔴", foreground="red")
                if hasattr(main_module.gui, 'start_btn'):
                    main_module.gui.start_btn.config(state="normal")
                if hasattr(main_module.gui, 'stop_btn'):
                    main_module.gui.stop_btn.config(state="disabled")
        except Exception as gui_stop_e:
            logger(f"⚠️ GUI stop update error: {str(gui_stop_e)}")

        logger("✅ Emergency stop completed")

    except Exception as e:
        logger(f"❌ Error during emergency stop: {str(e)}")


def run_single_analysis(symbol: str, strategy: str = None) -> Dict[str, Any]:
    """Run single symbol analysis for testing purposes"""
    try:
        if strategy is None:
            strategy = current_strategy

        logger(f"🔍 Running single analysis: {symbol} with {strategy}")

        # Get data
        df = get_symbol_data(symbol, count=500)
        if df is None:
            logger(f"❌ No data available for {symbol}")
            return {'error': 'No data available', 'symbol': symbol}

        # Calculate indicators
        df_with_indicators = calculate_indicators(df)
        if df_with_indicators is None:
            logger(f"❌ Indicator calculation failed for {symbol}")
            return {'error': 'Indicator calculation failed', 'symbol': symbol}

        # Run strategy
        action, signals = run_strategy(strategy, df_with_indicators, symbol)

        # AI analysis
        ai_result = ai_market_analysis(symbol, df_with_indicators)

        result = {
            'symbol': symbol,
            'strategy': strategy,
            'action': action,
            'signals': signals,
            'signal_count': len(signals) if signals else 0,
            'ai_analysis': ai_result,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
            'data_bars': len(df)
        }

        return result

    except Exception as e:
        logger(f"❌ Error in single analysis for {symbol}: {str(e)}")
        return {'error': str(e), 'symbol': symbol}

# --- Original Placeholder Functions (If needed, ensure they exist or are imported) ---
# If 'trading_loop' or other functions used in the changes are defined elsewhere,
# ensure they are correctly imported or defined within this scope or accessible.
# For example, if 'trading_loop' is the original bot_thread logic:
def trading_loop():
    """
    Placeholder for the original trading loop logic.
    This function is called by safe_trading_loop.
    It should contain the core logic previously in bot_thread.
    """
    # Replicate the core logic from the original bot_thread function here
    global is_running, current_strategy

    try:
        logger("🚀 Trading bot thread (core logic) started")
        logger("🔍 Initializing automated trading system...")

        # Reset daily counters
        check_daily_limits()

        # Main trading loop - FIXED stop mechanism
        while True:
            try:
                # Single bot running check per iteration
                if not is_running:
                    logger("🛑 Bot stopped")
                    break

                # Risk management checks (non-blocking)
                if not risk_management_check():
                    logger("⚠️ Risk management warning - continuing with caution")

                # Check daily limits (now includes user-configurable daily order limit)
                if not check_daily_limits():
                    from risk_management import get_daily_trade_status
                    status = get_daily_trade_status()
                    logger(f"📊 Daily order limit reached ({status['current_count']}/{status['max_limit']}) - pausing for today")
                    time.sleep(300)  # Wait 5 minutes then check again
                    continue

                # Check trading session
                if not check_trading_time():
                    logger("⏰ Outside trading hours - waiting...")
                    time.sleep(60)
                    continue

                # Get current strategy from GUI
                try:
                    main_module = __import__('__main__')
                    if hasattr(main_module, 'gui') and main_module.gui:
                        gui_strategy = main_module.gui.current_strategy
                        if gui_strategy != current_strategy:
                            current_strategy = gui_strategy
                            logger(f"🔄 Strategy updated from GUI to: {current_strategy}")
                except Exception as gui_e:
                    logger(f"⚠️ GUI connection issue: {str(gui_e)}")
                    current_strategy = "Scalping"

                # Check MT5 connection status
                if not check_mt5_status():
                    logger("❌ MT5 connection lost, attempting recovery...")
                    from mt5_connection import connect_mt5
                    if not connect_mt5():
                        logger("🔄 Waiting 30 seconds before retry...")
                        for wait_second in range(30):
                            if not is_running:
                                logger("🛑 Bot stopped during MT5 reconnection wait")
                                return
                            time.sleep(1)
                        continue

                # Get trading symbols
                try:
                    main_module = __import__('__main__')
                    if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'symbol_combo') and main_module.gui.symbol_combo.get():
                        trading_symbols = [main_module.gui.symbol_combo.get()]
                    else:
                        trading_symbols = DEFAULT_SYMBOLS[:3]  # Use first 3 default symbols
                except Exception as gui_sym_e:
                    logger(f"⚠️ GUI symbol retrieval issue: {str(gui_sym_e)}")
                    trading_symbols = DEFAULT_SYMBOLS[:3]

                logger(f"📊 Analyzing {len(trading_symbols)} symbols with {current_strategy} strategy")

                symbol_data = get_multiple_symbols_data(trading_symbols, count=500)

                if not symbol_data:
                    logger("❌ No symbol data available, waiting...")
                    time.sleep(60)
                    continue

                signals_found = 0
                for symbol, df in symbol_data.items():
                    try:
                        df_with_indicators = calculate_indicators(df)
                        if df_with_indicators is None:
                            logger(f"⚠️ Indicator calculation failed for {symbol}")
                            continue

                        action, signals = run_strategy(current_strategy, df_with_indicators, symbol)

                        if action and len(signals) > 0:
                            signals_found += 1
                            logger(f"🎯 Signal detected for {symbol}: {action}")

                            conditions_ok, condition_msg = validate_trading_conditions(symbol)
                            if not conditions_ok:
                                logger(f"⚠️ Trading conditions not met for {symbol}: {condition_msg}")
                                continue

                            current_session = get_current_trading_session()
                            session_adjustments = adjust_strategy_for_session(current_strategy, current_session)

                            signal_threshold = 1 + session_adjustments.get("signal_threshold_modifier", 0)
                            if len(signals) < signal_threshold:
                                logger(f"⚪ {symbol}: Signal strength {len(signals)} below threshold {signal_threshold}")
                                continue

                            try:
                                if not is_running:
                                    logger(f"🛑 Bot stopped before executing trade for {symbol}")
                                    return

                                if not check_order_limit():
                                    logger(f"⚠️ Order limit reached but FORCING execution for maximum opportunities")

                                # Get GUI instance for parameter retrieval
                                gui = None
                                try:
                                    main_module = __import__('__main__')
                                    if hasattr(main_module, 'gui'):
                                        gui = main_module.gui
                                except Exception as gui_e:
                                    logger(f"⚠️ GUI instance retrieval failed: {str(gui_e)}")

                                # Get trading parameters from GUI with proper defaults
                                lot_size = 0.01
                                tp_value = "20"
                                sl_value = "10"
                                tp_unit = "pips"
                                sl_unit = "pips"

                                if gui:
                                    try:
                                        lot_size = float(gui.get_current_lot() or 0.01)
                                        tp_value = gui.get_current_tp() or "20"
                                        sl_value = gui.get_current_sl() or "10"
                                        tp_unit = gui.get_current_tp_unit() or "pips"
                                        sl_unit = gui.get_current_sl_unit() or "pips"
                                    except:
                                        pass  # Use defaults

                                # Set strategy-specific defaults if empty
                                if not tp_value or tp_value == "0":
                                    tp_value = {
                                        "Scalping": "15",
                                        "HFT": "8",
                                        "Intraday": "50",
                                        "Arbitrage": "25"
                                    }.get(current_strategy, "20")

                                if not sl_value or sl_value == "0":
                                    sl_value = {
                                        "Scalping": "8",
                                        "HFT": "4",
                                        "Intraday": "25",
                                        "Arbitrage": "10"
                                    }.get(current_strategy, "10")

                                success = execute_trade_signal(symbol, action, lot_size, tp_value, sl_value, tp_unit, sl_unit, current_strategy)

                                if success:
                                    increment_daily_trade_count()
                                    logger(f"✅ Trade executed successfully for {symbol}")
                                    try:
                                        main_module = __import__('__main__')
                                        if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'update_order_count_display'):
                                            main_module.gui.update_order_count_display()
                                    except Exception as gui_update_e:
                                        logger(f"⚠️ GUI update error: {str(gui_update_e)}")
                                else:
                                    logger(f"❌ Trade execution failed for {symbol}")

                            except Exception as trade_e:
                                logger(f"❌ Trade execution error for {symbol}: {str(trade_e)}")

                        time.sleep(2)

                    except Exception as symbol_e:
                        logger(f"❌ Error processing {symbol}: {str(symbol_e)}")
                        continue

                if signals_found > 0:
                    logger(f"📊 Scan complete: {signals_found} signals found from {len(symbol_data)} symbols")
                else:
                    logger(f"📊 Scan complete: No signals found from {len(symbol_data)} symbols")

                auto_recovery_check()

                current_time = datetime.datetime.now()
                if current_time.minute == 0:
                    send_hourly_report()

                scan_interval = 15  # More aggressive scanning
                try:
                    main_module = __import__('__main__')
                    if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'interval_entry'):
                        interval_text = main_module.gui.interval_entry.get().strip()
                        if interval_text and interval_text.isdigit():
                            scan_interval = max(5, min(int(interval_text), 300))
                except Exception as gui_interval_e:
                    logger(f"⚠️ GUI interval retrieval issue: {str(gui_interval_e)}")
                    pass

                logger(f"⏳ Waiting {scan_interval} seconds before next scan...")
                for wait_second in range(scan_interval):
                    if not is_running:
                        logger("🛑 Bot stopped during scan interval wait")
                        return
                    time.sleep(1)

            except KeyboardInterrupt:
                logger("⚠️ Bot interrupted by user")
                break

            except Exception as cycle_e:
                logger(f"❌ Error in trading cycle: {str(cycle_e)}")
                import traceback
                logger(f"📝 Traceback: {traceback.format_exc()}")
                time.sleep(60)

    except Exception as e:
        logger(f"❌ Critical error in bot thread: {str(e)}")
        import traceback
        logger(f"📝 Critical traceback: {traceback.format_exc()}")
    finally:
        is_running = False
        logger("🛑 Bot thread stopped")
        try:
            main_module = __import__('__main__')
            if hasattr(main_module, 'gui') and main_module.gui and hasattr(main_module.gui, 'bot_status_lbl'):
                main_module.gui.bot_status_lbl.config(text="Bot: Stopped 🔴", foreground="red")
        except Exception as gui_status_e:
            logger(f"⚠️ GUI status update error: {str(gui_status_e)}")