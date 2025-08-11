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
from risk_management import risk_management_check, check_daily_limits, increment_daily_trade_count, auto_recovery_check
from ai_analysis import ai_market_analysis
from performance_tracking import send_hourly_report
from validation_utils import validate_trading_conditions

# Global bot state
bot_running = False
current_strategy = "Scalping"


def bot_thread() -> None:
    """Main bot thread - identical logic to original but modular"""
    global bot_running, current_strategy
    
    try:
        logger("🚀 Trading bot thread started")
        logger("🔍 Initializing automated trading system...")
        
        # Reset daily counters
        check_daily_limits()
        
        # Main trading loop
        while bot_running:
            try:
                # Check if trading time is appropriate
                if not check_trading_time():
                    logger("⏰ Outside trading hours, waiting...")
                    time.sleep(60)  # Wait 1 minute before checking again
                    continue
                
                # Check MT5 connection status
                if not check_mt5_status():
                    logger("❌ MT5 connection lost, attempting recovery...")
                    from mt5_connection import connect_mt5
                    if not connect_mt5():
                        logger("🔄 Waiting 30 seconds before retry...")
                        time.sleep(30)
                        continue
                
                # Risk management check
                if not risk_management_check():
                    logger("🛡️ Risk management check failed, pausing trading...")
                    time.sleep(300)  # Wait 5 minutes
                    continue
                
                # Get current strategy from GUI at start
                try:
                    import __main__
                    if hasattr(__main__, 'gui') and __main__.gui:
                        gui_strategy = __main__.gui.current_strategy
                        if gui_strategy != current_strategy:
                            current_strategy = gui_strategy
                            logger(f"🔄 Strategy updated from GUI to: {current_strategy}")
                except Exception as gui_e:
                    logger(f"⚠️ GUI connection issue: {str(gui_e)}")
                    # Fallback to default strategy if GUI not accessible
                    current_strategy = "Scalping"
                
                # Get trading symbols
                try:
                    import __main__
                    if hasattr(__main__, 'gui') and __main__.gui and __main__.gui.symbol_combo.get():
                        trading_symbols = [__main__.gui.symbol_combo.get()]
                    else:
                        trading_symbols = DEFAULT_SYMBOLS[:3]  # Use first 3 default symbols
                except:
                    trading_symbols = DEFAULT_SYMBOLS[:3]
                
                logger(f"📊 Analyzing {len(trading_symbols)} symbols with {current_strategy} strategy")
                
                # Get data for all symbols
                symbol_data = get_multiple_symbols_data(trading_symbols)
                
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
                            
                            # FIXED: Apply more lenient signal filtering for live trading
                            signal_threshold = 1 + session_adjustments.get("signal_threshold_modifier", 0)
                            if len(signals) < signal_threshold:
                                logger(f"⚪ {symbol}: Signal strength {len(signals)} below threshold {signal_threshold}")
                                continue
                            
                            # Execute trading signals with proper GUI parameter integration
                            logger(f"🎯 Executing {action} signal for {symbol}")
                            logger(f"📋 Signals: {signals}")
                            
                            # DEBUG: Log current GUI settings before execution
                            try:
                                import __main__
                                if hasattr(__main__, 'gui') and __main__.gui:
                                    tp_val = __main__.gui.tp_entry.get()
                                    sl_val = __main__.gui.sl_entry.get()  
                                    tp_unit = __main__.gui.tp_unit_combo.get()
                                    sl_unit = __main__.gui.sl_unit_combo.get()
                                    lot_val = __main__.gui.lot_entry.get()
                                    
                                    logger(f"📊 GUI Settings at execution:")
                                    logger(f"   Symbol: {symbol}")
                                    logger(f"   Lot Size: {lot_val}")
                                    logger(f"   TP: {tp_val} {tp_unit}")
                                    logger(f"   SL: {sl_val} {sl_unit}")
                            except:
                                pass
                            
                            try:
                                # Get ALL parameters from GUI with proper validation
                                success = execute_trade_signal(symbol, action)
                                
                                if success:
                                    increment_daily_trade_count()
                                    logger(f"✅ Trade executed successfully for {symbol}")
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
                scan_interval = 30  # Default fallback
                try:
                    import __main__
                    if hasattr(__main__, 'gui') and __main__.gui and hasattr(__main__.gui, 'interval_entry'):
                        interval_text = __main__.gui.interval_entry.get().strip()
                        if interval_text and interval_text.isdigit():
                            scan_interval = max(5, min(int(interval_text), 300))  # 5-300 seconds range
                except:
                    pass
                
                # Wait before next cycle
                logger(f"⏳ Waiting {scan_interval} seconds before next scan...")
                time.sleep(scan_interval)
                
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
        bot_running = False
        logger("🛑 Bot thread stopped")
        
        # Update GUI status if available
        try:
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                __main__.gui.bot_status_lbl.config(text="Bot: Stopped 🔴", foreground="red")
        except:
            pass


def start_bot_thread():
    """Start the bot in a separate thread"""
    global bot_running
    
    if bot_running:
        logger("⚠️ Bot is already running")
        return False
    
    try:
        bot_running = True
        bot_worker = threading.Thread(target=bot_thread, daemon=True)
        bot_worker.start()
        logger("🚀 Bot thread launched successfully")
        return True
        
    except Exception as e:
        logger(f"❌ Error starting bot thread: {str(e)}")
        bot_running = False
        return False


def stop_bot():
    """Stop the trading bot"""
    global bot_running
    
    if not bot_running:
        logger("ℹ️ Bot is not running")
        return
    
    logger("🛑 Stopping trading bot...")
    bot_running = False
    
    # Give time for current operations to complete
    time.sleep(2)
    
    logger("✅ Trading bot stopped")


def start_auto_recovery_monitor():
    """Background monitoring thread for auto-recovery"""
    
    def recovery_monitor():
        while True:
            try:
                if bot_running:
                    auto_recovery_check()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger(f"❌ Recovery monitor error: {str(e)}")
                time.sleep(60)
    
    recovery_thread = threading.Thread(target=recovery_monitor, daemon=True)
    recovery_thread.start()
    logger("🔄 Auto-recovery monitor started")


def get_bot_status() -> Dict[str, Any]:
    """Get current bot status information"""
    try:
        from risk_management import get_current_risk_metrics
        
        risk_metrics = get_current_risk_metrics()
        
        status = {
            'running': bot_running,
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
            'running': bot_running,
            'error': str(e)
        }


def emergency_stop_all():
    """Emergency stop all operations"""
    try:
        logger("🚨 EMERGENCY STOP INITIATED!")
        
        # Stop bot
        global bot_running
        bot_running = False
        
        # Close all positions
        from trading_operations import close_all_orders
        close_all_orders()
        
        logger("🛑 Emergency stop completed")
        
    except Exception as e:
        logger(f"❌ Error during emergency stop: {str(e)}")


def run_single_analysis(symbol: str, strategy: str = None) -> Dict[str, Any]:
    """Run single symbol analysis for testing purposes"""
    try:
        if strategy is None:
            strategy = current_strategy
        
        logger(f"🔍 Running single analysis: {symbol} with {strategy}")
        
        # Get data
        df = get_symbol_data(symbol)
        if df is None:
            return {'error': 'No data available'}
        
        # Calculate indicators
        df_with_indicators = calculate_indicators(df)
        if df_with_indicators is None:
            return {'error': 'Indicator calculation failed'}
        
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
        logger(f"❌ Error in single analysis: {str(e)}")
        return {'error': str(e)}