"""
MT5 Trading Bot - Trading Engine Module
Enhanced trading functionality with multiple strategies and robust MT5 integration
"""

# Try to import MT5, fallback to mock for development
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    print("✅ Real MetaTrader5 library loaded")
except ImportError:
    import mt5_mock as mt5
    MT5_AVAILABLE = False
    print("🎭 Mock MetaTrader5 library loaded (development mode)")

import numpy as np
import threading
import time
import datetime
from typing import Dict, List, Optional, Any

class TradingEngine:
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.is_mt5_connected = False
        self.trading_running = False
        self.trading_thread = None
        self.current_settings = {}
        
        # Trading parameters
        self.order_counter = 0
        self.last_reset_date = datetime.date.today()
        self.max_orders_per_session = 10
        self.reset_order_hour = 0
        self.min_balance = 1000
        self.price_spike_threshold = 10
        self.min_score = 4
        
        # Strategy configurations
        self.strategy_configs = {
            'Scalping': {
                'tp': 5, 'sl': 3, 'interval': 5, 'timeframe': mt5.TIMEFRAME_M1,
                'description': 'Quick trades with small profits'
            },
            'Intraday': {
                'tp': 20, 'sl': 10, 'interval': 10, 'timeframe': mt5.TIMEFRAME_M5,
                'description': 'Day trading with medium-term holds'
            },
            'Arbitrage': {
                'tp': 15, 'sl': 8, 'interval': 3, 'timeframe': mt5.TIMEFRAME_M1,
                'description': 'Price difference exploitation'
            },
            'High Frequency Trading': {
                'tp': 2, 'sl': 1, 'interval': 1, 'timeframe': mt5.TIMEFRAME_M1,
                'description': 'Ultra-fast automated trading'
            }
        }
        
    def connect_mt5(self) -> bool:
        """Connect to MetaTrader 5"""
        try:
            if not mt5.initialize():
                self.logger.log("ERROR: Failed to initialize MT5")
                return False
                
            # Check connection
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.log("ERROR: Failed to get account info")
                mt5.shutdown()
                return False
                
            self.is_mt5_connected = True
            self.logger.log(f"✅ MT5 REAL TRADING connected successfully")
            self.logger.log(f"🔥 LIVE ACCOUNT: {account_info.login} | Balance: ${account_info.balance:.2f}")
            self.logger.log(f"⚠️  WARNING: This is REAL MONEY trading - be careful!")
            
            return True
            
        except Exception as e:
            self.logger.log(f"ERROR connecting to MT5: {str(e)}")
            return False
            
    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5"""
        try:
            if self.trading_running:
                self.stop_trading()
                
            if self.is_mt5_connected:
                mt5.shutdown()
                self.is_mt5_connected = False
                self.logger.log("MT5 disconnected")
                
        except Exception as e:
            self.logger.log(f"ERROR disconnecting MT5: {str(e)}")
            
    def is_connected(self) -> bool:
        """Check if MT5 is connected"""
        return self.is_mt5_connected
        
    def is_running(self) -> bool:
        """Check if trading is running"""
        return self.trading_running
        
    def get_account_info(self) -> Optional[Dict]:
        """Get MT5 account information"""
        if not self.is_mt5_connected:
            return None
            
        try:
            account = mt5.account_info()
            if account is None:
                return None
                
            return {
                'login': account.login,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'free_margin': account.margin_free,
                'margin_level': account.margin_level
            }
            
        except Exception as e:
            self.logger.log(f"ERROR getting account info: {str(e)}")
            return None
            
    def get_symbols(self) -> List[str]:
        """Get list of available symbols"""
        if not self.is_mt5_connected:
            return []
            
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
                
            # Filter and return symbol names
            symbol_names = []
            for symbol in symbols:
                if symbol.visible:
                    symbol_names.append(symbol.name)
                    
            return sorted(symbol_names)
            
        except Exception as e:
            self.logger.log(f"ERROR getting symbols: {str(e)}")
            return []
            
    def get_symbol_info(self, symbol: str):
        """Get detailed symbol information"""
        if not self.is_mt5_connected:
            return None
            
        try:
            return mt5.symbol_info(symbol)
        except Exception as e:
            self.logger.log(f"ERROR getting symbol info for {symbol}: {str(e)}")
            return None
            
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists and is tradeable"""
        if not self.is_mt5_connected:
            return False
            
        try:
            # Try direct symbol first
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                if not symbol_info.visible:
                    # Try to enable symbol
                    if mt5.symbol_select(symbol, True):
                        self.logger.log(f"Symbol {symbol} enabled")
                        return True
                else:
                    return True
                    
            # Try common variations for crypto and other instruments
            variations = [
                symbol,
                symbol + "m",
                symbol + ".a",
                symbol + "_",
                symbol.replace("USD", "USDm"),
                symbol.replace("m", ""),
                symbol.replace(".a", ""),
                symbol.replace("_", "")
            ]
            
            for variation in variations:
                symbol_info = mt5.symbol_info(variation)
                if symbol_info is not None:
                    if not symbol_info.visible:
                        if mt5.symbol_select(variation, True):
                            self.logger.log(f"Symbol variation {variation} found and enabled")
                            return True
                    else:
                        self.logger.log(f"Symbol variation {variation} found")
                        return True
                        
            self.logger.log(f"ERROR: Symbol {symbol} not found or not tradeable")
            return False
            
        except Exception as e:
            self.logger.log(f"ERROR validating symbol {symbol}: {str(e)}")
            return False
            
    def auto_detect_symbol(self) -> Optional[str]:
        """Auto-detect currently active symbol"""
        if not self.is_mt5_connected:
            self.logger.log("MT5 not connected - cannot auto-detect symbol")
            return None
            
        try:
            # Get all positions and orders to find active symbols
            positions = mt5.positions_get()
            if positions:
                symbol = positions[0].symbol
                self.logger.log(f"Active position found: {symbol}")
                return symbol
                
            # If no positions, try to get market watch symbols
            symbols = mt5.symbols_get()
            if symbols:
                # Filter for commonly traded symbols first
                priority_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'USDCAD', 'AUDUSD']
                
                # Check priority symbols first
                for priority_symbol in priority_symbols:
                    for symbol in symbols:
                        if symbol.visible and symbol.name == priority_symbol:
                            tick = mt5.symbol_info_tick(symbol.name)
                            if tick and tick.ask > 0:
                                self.logger.log(f"Priority symbol detected: {symbol.name}")
                                return symbol.name
                
                # Then check any visible symbol
                for symbol in symbols:
                    if symbol.visible:
                        tick = mt5.symbol_info_tick(symbol.name)
                        if tick and tick.ask > 0:
                            self.logger.log(f"Available symbol detected: {symbol.name}")
                            return symbol.name
            
            # Fallback to most common symbol if nothing found
            fallback_symbol = 'EURUSD'
            if self.validate_symbol(fallback_symbol):
                self.logger.log(f"Using fallback symbol: {fallback_symbol}")
                return fallback_symbol
                            
            self.logger.log("No active symbols detected")
            return None
            
        except Exception as e:
            self.logger.log(f"ERROR auto-detecting symbol: {str(e)}")
            return None
            
    def get_strategy_defaults(self, strategy: str) -> Dict:
        """Get default settings for strategy"""
        return self.strategy_configs.get(strategy, {})
        
    def start_trading(self, settings: Dict) -> bool:
        """Start automated trading with enhanced error handling"""
        try:
            if self.trading_running:
                self.logger.log("⚠️ Trading is already running")
                return False
                
            if not self.is_mt5_connected:
                self.logger.log("❌ ERROR: MT5 not connected - cannot start trading")
                return False
                
            # Double check MT5 connection
            try:
                # Try to access MT5 functions to verify real connection
                account_info = mt5.account_info()
                if not account_info:
                    self.logger.log("❌ ERROR: MT5 connection invalid")
                    self.is_mt5_connected = False
                    return False
                    
                self.logger.log(f"✅ MT5 connected - Account: {account_info.login}")
                
            except Exception as e:
                self.logger.log(f"❌ ERROR: Cannot access MT5: {str(e)}")
                self.is_mt5_connected = False
                return False
                
            # Validate settings with detailed debugging
            self.logger.log("🔄 Validating trading settings...")
            if not self.validate_trading_settings(settings):
                self.logger.log("❌ ERROR: Invalid trading settings")
                return False
            
            self.logger.log("✅ Trading settings validated successfully")
            self.current_settings = settings.copy()
            
            # Pre-check trading loop requirements
            self.logger.log("🔄 Pre-checking trading requirements...")
            try:
                # Test symbol price access
                tick = mt5.symbol_info_tick(settings['symbol'])
                if not tick:
                    self.logger.log(f"❌ Cannot access price data for {settings['symbol']}")
                    return False
                self.logger.log(f"✅ Symbol {settings['symbol']} price accessible: {tick.ask}")
                
                # Test basic indicator calculation to prevent crash
                test_rates = mt5.copy_rates_from_pos(settings['symbol'], mt5.TIMEFRAME_M1, 0, 10)
                if test_rates is None:
                    self.logger.log(f"❌ Cannot access historical data for {settings['symbol']}")
                    return False
                self.logger.log(f"✅ Historical data accessible: {len(test_rates)} bars")
                
            except Exception as e:
                self.logger.log(f"❌ Pre-check failed: {str(e)}")
                return False
            
            # Start trading thread with error handling
            self.logger.log("🔄 Starting trading thread...")
            self.trading_running = True
            
            try:
                self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
                self.trading_thread.start()
                
                self.logger.log(f"🔥 Started {settings['strategy']} trading for {settings['symbol']}")
                self.logger.log(f"⚠️ WARNING: REAL MONEY TRADING ACTIVE!")
                return True
                
            except Exception as e:
                self.logger.log(f"❌ CRITICAL: Error starting trading thread: {str(e)}")
                self.trading_running = False
                return False
                
        except Exception as e:
            self.logger.log(f"❌ CRITICAL ERROR in start_trading: {str(e)}")
            self.trading_running = False
            return False
        
    def stop_trading(self):
        """Stop automated trading with enhanced error handling"""
        try:
            if not self.trading_running:
                self.logger.log("⚠️ Trading is not currently running")
                return
                
            self.logger.log("🔄 Stopping automated trading...")
            self.trading_running = False
            
            # Wait for trading thread to finish gracefully
            if self.trading_thread and self.trading_thread.is_alive():
                self.logger.log("⏳ Waiting for trading thread to finish...")
                self.trading_thread.join(timeout=5)
                
                # Force cleanup if thread still alive
                if self.trading_thread.is_alive():
                    self.logger.log("⚠️ Trading thread still running - forcing cleanup")
                    
            self.logger.log("✅ Automated trading stopped successfully")
            
        except Exception as e:
            self.logger.log(f"❌ Error stopping trading: {str(e)}")
            # Force stop even if error occurs
            self.trading_running = False
            raise e
            
    def validate_trading_settings(self, settings: Dict) -> bool:
        """Validate trading settings with enhanced debugging"""
        try:
            self.logger.log("🔍 Checking required fields...")
            # Check required fields
            required_fields = ['strategy', 'symbol', 'lot_size', 'tp_value', 'sl_value']
            for field in required_fields:
                if field not in settings:
                    self.logger.log(f"❌ Missing required field: {field}")
                    return False
                self.logger.log(f"✅ Field {field}: {settings[field]}")
                    
            # Validate symbol with timeout protection
            self.logger.log(f"🔍 Validating symbol {settings['symbol']}...")
            try:
                if not self.validate_symbol(settings['symbol']):
                    self.logger.log(f"❌ Symbol validation failed for {settings['symbol']}")
                    return False
                self.logger.log(f"✅ Symbol {settings['symbol']} validated")
            except Exception as e:
                self.logger.log(f"❌ Symbol validation error: {str(e)}")
                return False
                
            # Validate numeric values
            self.logger.log("🔍 Validating numeric values...")
            try:
                lot_size = float(settings['lot_size'])
                tp_value = float(settings['tp_value'])
                sl_value = float(settings['sl_value'])
                
                if lot_size <= 0:
                    self.logger.log(f"❌ Invalid lot size: {lot_size}")
                    return False
                    
                if tp_value <= 0:
                    self.logger.log(f"❌ Invalid TP value: {tp_value}")
                    return False
                    
                if sl_value <= 0:
                    self.logger.log(f"❌ Invalid SL value: {sl_value}")
                    return False
                    
                self.logger.log(f"✅ Numeric values valid - Lot: {lot_size}, TP: {tp_value}, SL: {sl_value}")
                
            except ValueError as e:
                self.logger.log(f"❌ Invalid numeric format: {str(e)}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"❌ CRITICAL: Settings validation error: {str(e)}")
            return False
            
    def place_manual_order(self, order_type: str, settings: Dict) -> bool:
        """Place manual BUY or SELL order"""
        if not self.is_mt5_connected:
            self.logger.log("ERROR: MT5 not connected")
            return False
            
        try:
            symbol = settings['symbol']
            lot_size = float(settings['lot_size'])
            
            # Validate symbol and get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                self.logger.log(f"❌ Symbol {symbol} not found")
                return False
                
            # Check if trading is enabled for this symbol
            if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                self.logger.log(f"❌ Trading disabled for {symbol}")
                return False
            
            # Validate lot size against symbol requirements
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            if lot_size < min_lot:
                self.logger.log(f"❌ Lot size {lot_size} too small. Minimum: {min_lot}")
                return False
            elif lot_size > max_lot:
                self.logger.log(f"❌ Lot size {lot_size} too large. Maximum: {max_lot}")
                return False
            
            # Adjust lot size to step if needed
            if lot_step > 0:
                adjusted_lot = round(lot_size / lot_step) * lot_step
                if adjusted_lot != lot_size:
                    lot_size = adjusted_lot
                    self.logger.log(f"⚠️ Lot size adjusted to {lot_size} (step: {lot_step})")
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.logger.log(f"❌ Cannot get price for {symbol}")
                return False
                
            # Calculate TP and SL
            if order_type == "BUY":
                price = tick.ask
                tp, sl = self.calculate_tp_sl(price, "BUY", settings)
                mt5_order_type = mt5.ORDER_TYPE_BUY
            else:  # SELL
                price = tick.bid
                tp, sl = self.calculate_tp_sl(price, "SELL", settings)
                mt5_order_type = mt5.ORDER_TYPE_SELL
                
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5_order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 123456,
                "comment": f"Manual {order_type}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # Provide detailed error messages for common error codes
                error_messages = {
                    10004: "TRADE_RETCODE_REQUOTE - Price has changed",
                    10006: "TRADE_RETCODE_REJECT - Trade rejected",
                    10007: "TRADE_RETCODE_CANCEL - Trade canceled", 
                    10008: "TRADE_RETCODE_PLACED - Order placed",
                    10009: "TRADE_RETCODE_DONE_PARTIAL - Partial execution",
                    10010: "TRADE_RETCODE_ERROR - Common error",
                    10011: "TRADE_RETCODE_TIMEOUT - Request timeout",
                    10012: "TRADE_RETCODE_INVALID - Invalid request",
                    10013: "TRADE_RETCODE_INVALID_VOLUME - Invalid volume (lot size)",
                    10014: "TRADE_RETCODE_INVALID_PRICE - Invalid price",
                    10015: "TRADE_RETCODE_INVALID_STOPS - Invalid stop levels",
                    10016: "TRADE_RETCODE_TRADE_DISABLED - Trading disabled for symbol",
                    10017: "TRADE_RETCODE_MARKET_CLOSED - Market is closed",
                    10018: "TRADE_RETCODE_NO_MONEY - Not enough money",
                    10019: "TRADE_RETCODE_POSITION_CLOSED - Position closed",
                    10020: "TRADE_RETCODE_INVALID_EXPIRATION - Invalid expiration",
                    10021: "TRADE_RETCODE_ORDER_CHANGED - Order changed",
                    10025: "TRADE_RETCODE_TOO_MANY_REQUESTS - Too many requests"
                }
                
                error_desc = error_messages.get(result.retcode, f"Unknown error code {result.retcode}")
                self.logger.log(f"❌ Manual {order_type} failed: {error_desc}")
                
                # Additional info for common errors
                if result.retcode == 10016:  # TRADE_DISABLED
                    self.logger.log(f"⚠️ Trading disabled for {symbol} - check broker settings or market hours")
                elif result.retcode == 10013:  # INVALID_VOLUME
                    self.logger.log(f"⚠️ Invalid lot size {lot_size} for {symbol} - check minimum lot size")
                elif result.retcode == 10018:  # NO_MONEY
                    self.logger.log("⚠️ Insufficient balance for this trade")
                elif result.retcode == 10017:  # MARKET_CLOSED
                    self.logger.log(f"⚠️ Market closed for {symbol}")
                
                return False
            else:
                self.logger.log(f"Manual {order_type} order successful at {price:.5f}")
                return True
                
        except Exception as e:
            self.logger.log(f"ERROR placing manual order: {str(e)}")
            return False
            
    def calculate_tp_sl(self, price: float, order_type: str, settings: Dict) -> tuple:
        """Calculate Take Profit and Stop Loss based on settings with enhanced debugging"""
        try:
            tp_value = float(settings.get('tp_value', 20))
            sl_value = float(settings.get('sl_value', 10))
            tp_unit = settings.get('tp_unit', 'pips')
            sl_unit = settings.get('sl_unit', 'pips')
            symbol = settings.get('symbol', 'EURUSD')
            
            self.logger.log(f"🔧 Calculating TP/SL: {order_type} {symbol} at {price}")
            self.logger.log(f"📋 Settings: TP={tp_value} {tp_unit}, SL={sl_value} {sl_unit}")
            
            # Validate inputs
            if not tp_unit in ['pips', 'price', 'percent', 'money']:
                self.logger.log(f"⚠️ Invalid TP unit '{tp_unit}', defaulting to pips")
                tp_unit = 'pips'
                
            if not sl_unit in ['pips', 'price', 'percent', 'money']:
                self.logger.log(f"⚠️ Invalid SL unit '{sl_unit}', defaulting to pips")  
                sl_unit = 'pips'
            
            # Get symbol info for calculations
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                raise Exception(f"Cannot get symbol info for {symbol}")
                
            point = symbol_info.point
            digits = symbol_info.digits
            
            tp = 0
            sl = 0
            
            # Calculate TP
            if tp_unit == "pips":
                if order_type == "BUY":
                    tp = price + (tp_value * point * 10)
                else:
                    tp = price - (tp_value * point * 10)
            elif tp_unit == "price":
                tp = tp_value
            elif tp_unit == "percent":
                # Calculate TP based on percentage of account balance (money target)
                if tp_value <= 0 or tp_value > 50:
                    self.logger.log(f"⚠️ Invalid TP percent value: {tp_value}%, using default 2%")
                    tp_value = 2.0
                
                # Get account balance
                account_info = mt5.account_info()
                if not account_info:
                    self.logger.log("⚠️ Cannot get account info, using price-based percent")
                    if order_type == "BUY":
                        tp = price * (1 + tp_value / 100)
                    else:
                        tp = price * (1 - tp_value / 100)
                else:
                    balance = account_info.balance
                    currency = account_info.currency
                    profit_target = balance * (tp_value / 100)
                    
                    self.logger.log(f"💰 Balance: {balance} {currency}")
                    self.logger.log(f"🎯 TP Target: {profit_target} {currency} ({tp_value}%)")
                    
                    # Calculate pip value and required pips for profit target
                    try:
                        pip_value = self.calculate_pip_value(symbol, settings['lot_size'])
                        if pip_value > 0:
                            pips_needed = profit_target / pip_value
                            if order_type == "BUY":
                                tp = price + (pips_needed * point * 10)
                            else:
                                tp = price - (pips_needed * point * 10)
                            
                            self.logger.log(f"📊 TP calculated: {profit_target} {currency} = {pips_needed:.1f} pips = {tp}")
                        else:
                            self.logger.log("⚠️ Cannot calculate pip value, using default TP")
                            if order_type == "BUY":
                                tp = price + (20 * point * 10)  # 20 pips default
                            else:
                                tp = price - (20 * point * 10)
                    except Exception as tp_calc_e:
                        self.logger.log(f"❌ TP calculation error: {str(tp_calc_e)}")
                        if order_type == "BUY":
                            tp = price + (20 * point * 10)
                        else:
                            tp = price - (20 * point * 10)
            elif tp_unit == "money":
                # Simplified money calculation (would need more complex logic for accuracy)
                pip_value = self.calculate_pip_value(symbol, settings['lot_size'])
                if pip_value > 0:
                    pips_needed = tp_value / pip_value
                    if order_type == "BUY":
                        tp = price + (pips_needed * point * 10)
                    else:
                        tp = price - (pips_needed * point * 10)
                        
            # Calculate SL
            if sl_unit == "pips":
                if order_type == "BUY":
                    sl = price - (sl_value * point * 10)
                else:
                    sl = price + (sl_value * point * 10)
            elif sl_unit == "price":
                sl = sl_value
            elif sl_unit == "percent":
                # Calculate SL based on percentage of account balance (loss limit)
                if sl_value <= 0 or sl_value > 50:
                    self.logger.log(f"⚠️ Invalid SL percent value: {sl_value}%, using default 1%")
                    sl_value = 1.0
                
                # Get account balance
                account_info = mt5.account_info()
                if not account_info:
                    self.logger.log("⚠️ Cannot get account info, using price-based percent")
                    if order_type == "BUY":
                        sl = price * (1 - sl_value / 100)
                    else:
                        sl = price * (1 + sl_value / 100)
                else:
                    balance = account_info.balance
                    currency = account_info.currency
                    loss_limit = balance * (sl_value / 100)
                    
                    self.logger.log(f"💰 Balance: {balance} {currency}")
                    self.logger.log(f"🛡️ SL Limit: {loss_limit} {currency} ({sl_value}%)")
                    
                    # Calculate pip value and required pips for loss limit
                    try:
                        pip_value = self.calculate_pip_value(symbol, settings['lot_size'])
                        if pip_value > 0:
                            pips_needed = loss_limit / pip_value
                            if order_type == "BUY":
                                sl = price - (pips_needed * point * 10)
                            else:
                                sl = price + (pips_needed * point * 10)
                            
                            self.logger.log(f"📊 SL calculated: {loss_limit} {currency} = {pips_needed:.1f} pips = {sl}")
                        else:
                            self.logger.log("⚠️ Cannot calculate pip value, using default SL")
                            if order_type == "BUY":
                                sl = price - (10 * point * 10)  # 10 pips default
                            else:
                                sl = price + (10 * point * 10)
                    except Exception as sl_calc_e:
                        self.logger.log(f"❌ SL calculation error: {str(sl_calc_e)}")
                        if order_type == "BUY":
                            sl = price - (10 * point * 10)
                        else:
                            sl = price + (10 * point * 10)
            elif sl_unit == "money":
                # Simplified money calculation
                pip_value = self.calculate_pip_value(symbol, settings['lot_size'])
                if pip_value > 0:
                    pips_needed = sl_value / pip_value
                    if order_type == "BUY":
                        sl = price - (pips_needed * point * 10)
                    else:
                        sl = price + (pips_needed * point * 10)
                        
            # Round to symbol digits and ensure valid values
            if tp > 0:
                tp = round(tp, digits)
            else:
                tp = 0
                
            if sl > 0:
                sl = round(sl, digits)
            else:
                # For invalid SL, use fallback calculation
                if order_type == "BUY":
                    sl = round(price - (10 * point * 10), digits)  # 10 pips default
                else:
                    sl = round(price + (10 * point * 10), digits)
                self.logger.log(f"⚠️ Using fallback SL: {sl}")
            
            return tp, sl
            
        except Exception as e:
            self.logger.log(f"❌ CRITICAL ERROR calculating TP/SL: {str(e)}")
            self.logger.log(f"🔧 Using fallback TP/SL calculation")
            # Return safe fallback values
            try:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    point = symbol_info.point
                    digits = symbol_info.digits
                    # Safe fallback: 20 pips TP, 10 pips SL
                    if order_type == "BUY":
                        tp = round(price + (20 * point * 10), digits)
                        sl = round(price - (10 * point * 10), digits)
                    else:
                        tp = round(price - (20 * point * 10), digits)
                        sl = round(price + (10 * point * 10), digits)
                    self.logger.log(f"✅ Fallback TP/SL: TP={tp}, SL={sl}")
                    return tp, sl
                else:
                    return 0, 0
            except:
                return 0, 0
            
    def calculate_pip_value(self, symbol: str, lot_size: float) -> float:
        """Calculate pip value for money-based TP/SL calculations with enhanced accuracy"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                self.logger.log(f"⚠️ Cannot get symbol info for {symbol}")
                return 0
                
            point = symbol_info.point
            contract_size = symbol_info.trade_contract_size
            
            # Get account currency for proper conversion
            account_info = mt5.account_info()
            account_currency = account_info.currency if account_info else "USD"
            
            self.logger.log(f"🔧 Calculating pip value: {symbol}, lot: {lot_size}")
            self.logger.log(f"📋 Point: {point}, Contract: {contract_size}, Account: {account_currency}")
            
            # Basic pip value calculation (1 pip = 10 * point for most instruments)
            pip_value = point * 10 * contract_size * lot_size
            
            # For JPY pairs, adjustment might be needed
            if "JPY" in symbol:
                pip_value = point * contract_size * lot_size
                
            # For precious metals and indices, different calculation
            if symbol.startswith("XAU") or symbol.startswith("XAG") or "Gold" in symbol:
                pip_value = point * contract_size * lot_size * 10
            elif "US30" in symbol or "SPX" in symbol or "NAS" in symbol:
                pip_value = point * contract_size * lot_size
                
            # Ensure pip value is reasonable
            if pip_value <= 0 or pip_value > 1000000:
                self.logger.log(f"⚠️ Unreasonable pip value {pip_value}, using default")
                pip_value = 10
                
            self.logger.log(f"✅ Pip value calculated: {pip_value} {account_currency}")
            return pip_value
            
        except Exception as e:
            self.logger.log(f"❌ ERROR calculating pip value: {str(e)}")
            import traceback
            self.logger.log(f"🔧 Traceback: {traceback.format_exc()}")
            return 10  # Return reasonable default for most cases
            
    def _trading_loop(self):
        """Simplified trading loop based on successful bot3.py approach"""
        try:
            strategy = self.current_settings['strategy']
            symbol = self.current_settings['symbol']
            interval = self.current_settings.get('interval', 10)
            lot_size = self.current_settings.get('lot_size', 0.01)
            tp_value = self.current_settings.get('tp_value', 1.0)
            sl_value = self.current_settings.get('sl_value', 0.5)
            tp_unit = self.current_settings.get('tp_unit', 'percent')
            sl_unit = self.current_settings.get('sl_unit', 'percent')
            
            self.logger.log(f"🔥 Trading started: {strategy} on {symbol}")
            self.logger.log("⚠️ WARNING: REAL MONEY trading!")
            
            last_price = None
            
            while self.trading_running:
                try:
                    # Basic checks (like bot3.py)
                    self._check_session_limits()
                    
                    if self._get_open_positions_count() >= self.max_orders_per_session:
                        self.logger.log("Max orders reached, waiting...")
                        time.sleep(60)
                        continue
                    
                    # Get price (simplified like bot3.py)
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick or tick.ask == 0.0:
                        self.logger.log("No price data, retrying...")
                        time.sleep(interval)
                        continue
                    
                    current_price = tick.ask
                    
                    # Spike protection
                    if last_price and abs(current_price - last_price) > self.price_spike_threshold:
                        self.logger.log("Price spike detected, skipping...")
                        last_price = current_price
                        time.sleep(interval)
                        continue
                    
                    last_price = current_price
                    
                    # Get indicators (direct calls like bot3.py)
                    ma10 = self._get_ma(symbol, 10, mt5.TIMEFRAME_M1)
                    ema9 = self._get_ema(symbol, 9, mt5.TIMEFRAME_M1) 
                    ema21 = self._get_ema(symbol, 21, mt5.TIMEFRAME_M1)
                    ema50 = self._get_ema(symbol, 50, mt5.TIMEFRAME_M1)
                    wma5 = self._get_wma(symbol, 5, mt5.TIMEFRAME_M1)
                    wma10 = self._get_wma(symbol, 10, mt5.TIMEFRAME_M1)
                    rsi = self._get_rsi(symbol, 14, mt5.TIMEFRAME_M1)
                    bb_upper, bb_lower = self._get_bollinger_bands(symbol, 20, mt5.TIMEFRAME_M1)
                    
                    # Check indicators (like bot3.py)
                    if None in [ma10, ema9, ema21, ema50, wma5, wma10, rsi, bb_upper, bb_lower]:
                        self.logger.log("Indicator data incomplete, retrying...")
                        time.sleep(interval)
                        continue
                    
                    # Simple signal generation (bot3.py style scoring)
                    signal = None
                    buy_score = sum([
                        rsi >= 20,
                        current_price > ema50,
                        current_price > ema9,
                        ema9 > ema21,
                        current_price > wma5,
                        current_price < bb_upper
                    ])
                    
                    sell_score = sum([
                        rsi <= 80,
                        current_price < ema50,
                        current_price < ema9,
                        ema9 < ema21,
                        current_price < wma5,
                        current_price > bb_lower
                    ])
                    
                    # Signal decision (minimum 4 points like bot3.py)
                    if buy_score >= 4:
                        signal = "BUY"
                    elif sell_score >= 4:
                        signal = "SELL"
                    
                    if signal:
                        self.logger.log(f"Signal: {signal} (Score: {buy_score if signal=='BUY' else sell_score})")
                        
                        # Calculate TP/SL (based on settings)
                        if tp_unit == "percent" and sl_unit == "percent":
                            # Use percent of balance like bot3.py
                            account_info = mt5.account_info()
                            if account_info and account_info.balance >= 1000:
                                if signal == "BUY":
                                    sl_price = current_price * (1 - sl_value / 100)
                                    tp_price = current_price * (1 + tp_value / 100)
                                else:
                                    sl_price = current_price * (1 + sl_value / 100)
                                    tp_price = current_price * (1 - tp_value / 100)
                                
                                # Execute order directly (like bot3.py)
                                success = self._execute_direct_order(signal, symbol, lot_size, current_price, tp_price, sl_price)
                                if success:
                                    self.order_counter += 1
                                    self.logger.log(f"✅ {signal} order placed successfully!")
                                else:
                                    self.logger.log(f"❌ Failed to place {signal} order")
                            else:
                                self.logger.log("Insufficient balance")
                        else:
                            # Use current complex TP/SL calculation
                            success = self._execute_strategy_trade(signal, current_price)
                            if success:
                                self.order_counter += 1
                                self.logger.log(f"✅ {signal} order placed successfully!")
                    else:
                        self.logger.log("No valid signal, waiting...")
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    self.logger.log(f"Error in cycle: {str(e)}")
                    time.sleep(interval)
                    
        except Exception as e:
            self.logger.log(f"Critical error in trading loop: {str(e)}")
        finally:
            self.trading_running = False
            self.logger.log("Trading loop ended")
            
        
    def _check_session_limits(self):
        """Check and reset session limits"""
        now = datetime.datetime.now()
        if now.hour == self.reset_order_hour and now.date() != self.last_reset_date:
            self.order_counter = 0
            self.last_reset_date = now.date()
            self.logger.log("Order counter reset for new session")
            
    def _get_open_positions_count(self) -> int:
        """Get number of open positions"""
        try:
            positions = mt5.positions_get()
            return len(positions) if positions else 0
        except:
            return 0
    
    def _execute_direct_order(self, signal: str, symbol: str, lot_size: float, price: float, tp: float, sl: float) -> bool:
        """Execute order directly like bot3.py - simplified approach"""
        try:
            order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL
            
            order_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 123456,
                "comment": f"Bot3 {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(order_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.log(f"Order {signal} success! Price: {price:.5f}")
                return True
            else:
                error_code = result.retcode if result else "No result"
                self.logger.log(f"Order {signal} failed: {error_code}")
                return False
                
        except Exception as e:
            self.logger.log(f"Direct order error: {str(e)}")
            return False
            
    def _get_technical_indicators(self, symbol: str, strategy: str) -> Optional[Dict]:
        """Get technical indicators for analysis with enhanced debugging"""
        try:
            self.logger.log(f"🔍 Debug: Entering _get_technical_indicators for {symbol}")
            
            strategy_config = self.strategy_configs.get(strategy, {})
            timeframe = strategy_config.get('timeframe', mt5.TIMEFRAME_M1)
            
            self.logger.log(f"🔄 Loading indicators for {symbol} on {timeframe} timeframe...")
            
            # Get different periods of data for various indicators with detailed logging
            self.logger.log(f"🔍 Debug: Calculating MA10...")
            ma10 = self._get_ma(symbol, 10, timeframe)
            self.logger.log(f"🔍 Debug: MA10 result: {ma10}")
            
            self.logger.log(f"🔍 Debug: Calculating EMA9...")
            ema9 = self._get_ema(symbol, 9, timeframe)
            self.logger.log(f"🔍 Debug: EMA9 result: {ema9}")
            
            self.logger.log(f"🔍 Debug: Calculating EMA21...")
            ema21 = self._get_ema(symbol, 21, timeframe)
            self.logger.log(f"🔍 Debug: EMA21 result: {ema21}")
            
            self.logger.log(f"🔍 Debug: Calculating EMA50...")
            ema50 = self._get_ema(symbol, 50, timeframe)
            self.logger.log(f"🔍 Debug: EMA50 result: {ema50}")
            
            self.logger.log(f"🔍 Debug: Calculating WMA5...")
            wma5 = self._get_wma(symbol, 5, timeframe)
            self.logger.log(f"🔍 Debug: WMA5 result: {wma5}")
            
            self.logger.log(f"🔍 Debug: Calculating WMA10...")
            wma10 = self._get_wma(symbol, 10, timeframe)
            self.logger.log(f"🔍 Debug: WMA10 result: {wma10}")
            
            self.logger.log(f"🔍 Debug: Calculating RSI...")
            rsi = self._get_rsi(symbol, 14, timeframe)
            self.logger.log(f"🔍 Debug: RSI result: {rsi}")
            
            self.logger.log(f"🔍 Debug: Calculating Bollinger Bands...")
            bb_upper, bb_lower = self._get_bollinger_bands(symbol, 20, timeframe)
            self.logger.log(f"🔍 Debug: BB results: upper={bb_upper}, lower={bb_lower}")
            
            # Debug which indicators failed
            failed_indicators = []
            if ma10 is None: failed_indicators.append("MA10")
            if ema9 is None: failed_indicators.append("EMA9")
            if ema21 is None: failed_indicators.append("EMA21")
            if ema50 is None: failed_indicators.append("EMA50")
            if wma5 is None: failed_indicators.append("WMA5")
            if wma10 is None: failed_indicators.append("WMA10")
            if rsi is None: failed_indicators.append("RSI")
            if bb_upper is None or bb_lower is None: failed_indicators.append("Bollinger")
            
            if failed_indicators:
                self.logger.log(f"⚠️ Failed indicators for {symbol}: {', '.join(failed_indicators)}")
                return None
                
            self.logger.log(f"✅ All indicators loaded for {symbol}")
            return {
                'ma10': ma10,
                'ema9': ema9,
                'ema21': ema21,
                'ema50': ema50,
                'wma5': wma5,
                'wma10': wma10,
                'rsi': rsi,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower
            }
            
        except Exception as e:
            self.logger.log(f"❌ CRITICAL: Error getting indicators for {symbol}: {str(e)}")
            import traceback
            self.logger.log(f"🔧 Full traceback: {traceback.format_exc()}")
            return None
            
    def _get_ma(self, symbol: str, period: int, timeframe) -> Optional[float]:
        """Calculate Moving Average with enhanced error handling"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 5)  # Get extra data for safety
            if rates is None:
                self.logger.log(f"⚠️ No rate data for MA({period}) on {symbol}")
                return None
            if len(rates) < period:
                self.logger.log(f"⚠️ Insufficient data for MA({period}) on {symbol}: got {len(rates)}, need {period}")
                return None
            closes = [r['close'] for r in rates[-period:]]  # Use last period bars only
            return float(np.mean(closes))
        except Exception as e:
            self.logger.log(f"❌ Error calculating MA for {symbol}: {str(e)}")
            return None
            
    def _get_ema(self, symbol: str, period: int, timeframe) -> Optional[float]:
        """Calculate Exponential Moving Average with enhanced error handling"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 10)
            if rates is None:
                self.logger.log(f"⚠️ No rate data for EMA({period}) on {symbol}")
                return None
            if len(rates) < period:
                self.logger.log(f"⚠️ Insufficient data for EMA({period}) on {symbol}: got {len(rates)}, need {period}")
                return None
            
            # Simplified EMA calculation
            closes = [r['close'] for r in rates[-period:]]
            multiplier = 2.0 / (period + 1)
            ema = closes[0]  # Start with first price
            for price in closes[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            return float(ema)
        except Exception as e:
            self.logger.log(f"❌ Error calculating EMA for {symbol}: {str(e)}")
            return None
            
    def _get_wma(self, symbol: str, period: int, timeframe) -> Optional[float]:
        """Calculate Weighted Moving Average"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
            if rates is None or len(rates) < period:
                return None
            prices = np.array([r['close'] for r in rates])
            weights = np.arange(1, period + 1)
            return float(np.dot(prices, weights) / weights.sum())
        except:
            return None
            
    def _get_rsi(self, symbol: str, period: int, timeframe) -> Optional[float]:
        """Calculate Relative Strength Index with enhanced error handling"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 10)
            if rates is None:
                self.logger.log(f"⚠️ No rate data for RSI({period}) on {symbol}")
                return None
            if len(rates) < period + 1:
                self.logger.log(f"⚠️ Insufficient data for RSI({period}) on {symbol}: got {len(rates)}, need {period + 1}")
                return None
            
            closes = [r['close'] for r in rates[-(period + 1):]]
            gains = []
            losses = []
            
            for i in range(1, len(closes)):
                diff = closes[i] - closes[i-1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(diff))
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi)
        except Exception as e:
            self.logger.log(f"❌ Error calculating RSI for {symbol}: {str(e)}")
            return None
            
    def _get_bollinger_bands(self, symbol: str, period: int, timeframe) -> tuple:
        """Calculate Bollinger Bands with enhanced error handling"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 5)
            if rates is None:
                self.logger.log(f"⚠️ No rate data for Bollinger({period}) on {symbol}")
                return None, None
            if len(rates) < period:
                self.logger.log(f"⚠️ Insufficient data for Bollinger({period}) on {symbol}: got {len(rates)}, need {period}")
                return None, None
            
            closes = [r['close'] for r in rates[-period:]]
            sma = np.mean(closes)
            std = np.std(closes)
            
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            
            return float(upper_band), float(lower_band)
        except Exception as e:
            self.logger.log(f"❌ Error calculating Bollinger Bands for {symbol}: {str(e)}")
            return None, None
            
    def _generate_signal(self, strategy: str, price: float, indicators: Dict) -> Optional[str]:
        """Generate trading signal based on strategy and indicators"""
        try:
            # Extract indicators
            ma10 = indicators['ma10']
            ema9 = indicators['ema9']
            ema21 = indicators['ema21']
            ema50 = indicators['ema50']
            wma5 = indicators['wma5']
            wma10 = indicators['wma10']
            rsi = indicators['rsi']
            bb_upper = indicators['bb_upper']
            bb_lower = indicators['bb_lower']
            
            # Strategy-specific signal generation
            if strategy == "Scalping":
                return self._scalping_signal(price, indicators)
            elif strategy == "Intraday":
                return self._intraday_signal(price, indicators)
            elif strategy == "Arbitrage":
                return self._arbitrage_signal(price, indicators)
            elif strategy == "High Frequency Trading":
                return self._hft_signal(price, indicators)
            else:
                # Default signal logic from original bot
                buy_score = sum([
                    rsi >= 20,
                    price > ema50,
                    price > ema9,
                    ema9 > ema21,
                    price > wma5,
                    price < bb_upper
                ])
                
                sell_score = sum([
                    rsi <= 80,
                    price < ema50,
                    price < ema9,
                    ema9 < ema21,
                    price < wma5,
                    price > bb_lower
                ])
                
                if buy_score >= self.min_score:
                    return "BUY"
                elif sell_score >= self.min_score:
                    return "SELL"
                    
            return None
            
        except Exception as e:
            self.logger.log(f"ERROR generating signal: {str(e)}")
            return None
            
    def _scalping_signal(self, price: float, indicators: Dict) -> Optional[str]:
        """Generate scalping strategy signal"""
        rsi = indicators['rsi']
        ema9 = indicators['ema9']
        ema21 = indicators['ema21']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        
        # Scalping focuses on quick moves with tight conditions
        if rsi < 30 and price < bb_lower and ema9 > ema21:
            return "BUY"
        elif rsi > 70 and price > bb_upper and ema9 < ema21:
            return "SELL"
            
        return None
        
    def _intraday_signal(self, price: float, indicators: Dict) -> Optional[str]:
        """Generate intraday strategy signal"""
        rsi = indicators['rsi']
        ema50 = indicators['ema50']
        wma5 = indicators['wma5']
        wma10 = indicators['wma10']
        
        # Intraday uses medium-term trends
        buy_conditions = [
            rsi > 40 and rsi < 60,
            price > ema50,
            wma5 > wma10,
            price > wma5
        ]
        
        sell_conditions = [
            rsi > 40 and rsi < 60,
            price < ema50,
            wma5 < wma10,
            price < wma5
        ]
        
        if sum(buy_conditions) >= 3:
            return "BUY"
        elif sum(sell_conditions) >= 3:
            return "SELL"
            
        return None
        
    def _arbitrage_signal(self, price: float, indicators: Dict) -> Optional[str]:
        """Generate arbitrage strategy signal"""
        ma10 = indicators['ma10']
        ema9 = indicators['ema9']
        rsi = indicators['rsi']
        
        # Arbitrage looks for price discrepancies
        price_vs_ma_diff = abs(price - ma10) / ma10 * 100
        price_vs_ema_diff = abs(price - ema9) / ema9 * 100
        
        if price_vs_ma_diff > 0.1 or price_vs_ema_diff > 0.1:
            if price < ma10 and price < ema9 and rsi < 50:
                return "BUY"
            elif price > ma10 and price > ema9 and rsi > 50:
                return "SELL"
                
        return None
        
    def _hft_signal(self, price: float, indicators: Dict) -> Optional[str]:
        """Generate high frequency trading signal"""
        ema9 = indicators['ema9']
        wma5 = indicators['wma5']
        rsi = indicators['rsi']
        
        # HFT uses very short-term indicators
        if price > ema9 and price > wma5 and rsi > 45:
            return "BUY"
        elif price < ema9 and price < wma5 and rsi < 55:
            return "SELL"
            
        return None
        
    def _execute_strategy_trade(self, signal: str, price: float) -> bool:
        """Execute trade based on strategy signal with enhanced validation"""
        try:
            symbol = self.current_settings['symbol']
            
            # Check account balance
            account_info = self.get_account_info()
            if not account_info or account_info['balance'] < self.min_balance:
                self.logger.log("❌ Insufficient balance for trading")
                return False
            
            # Validate symbol and get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                self.logger.log(f"❌ Symbol {symbol} not found for auto trading")
                return False
                
            # Check if trading is enabled for this symbol
            if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                self.logger.log(f"❌ Auto trading disabled for {symbol}")
                return False
                
            # Calculate and validate lot size
            lot_size = float(self.current_settings['lot_size'])
            if self.current_settings.get('auto_lot', False):
                lot_size = self._calculate_auto_lot()
            
            # Validate lot size against symbol requirements
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            if lot_size < min_lot:
                self.logger.log(f"❌ Auto lot size {lot_size} too small. Using minimum: {min_lot}")
                lot_size = min_lot
            elif lot_size > max_lot:
                self.logger.log(f"❌ Auto lot size {lot_size} too large. Using maximum: {max_lot}")
                lot_size = max_lot
            
            # Adjust lot size to step if needed
            if lot_step > 0:
                adjusted_lot = round(lot_size / lot_step) * lot_step
                if adjusted_lot != lot_size:
                    lot_size = adjusted_lot
                    self.logger.log(f"⚠️ Auto lot size adjusted to {lot_size} (step: {lot_step})")
                
            # Calculate TP and SL
            if signal == "BUY":
                tp, sl = self.calculate_tp_sl(price, "BUY", self.current_settings)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                tp, sl = self.calculate_tp_sl(price, "SELL", self.current_settings)
                order_type = mt5.ORDER_TYPE_SELL
                
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 123456,
                "comment": f"{self.current_settings['strategy']} {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order with detailed error handling
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_messages = {
                    10013: "Invalid volume (lot size)",
                    10016: "Trading disabled for symbol", 
                    10017: "Market is closed",
                    10018: "Not enough money"
                }
                error_desc = error_messages.get(result.retcode, f"Error code {result.retcode}")
                self.logger.log(f"❌ Auto {signal} failed: {error_desc}")
                return False
            else:
                self.logger.log(f"✅ Auto {signal} executed at {price:.5f} with lot {lot_size}")
                return True
            
        except Exception as e:
            self.logger.log(f"❌ CRITICAL: Error executing auto trade: {str(e)}")
            return False
            
    def _calculate_auto_lot(self) -> float:
        """Calculate lot size based on risk percentage"""
        try:
            account_info = self.get_account_info()
            if not account_info:
                return 0.01
                
            risk_percent = self.current_settings.get('risk_percent', 2.0)
            balance = account_info['balance']
            
            # Calculate risk amount
            risk_amount = balance * (risk_percent / 100)
            
            # Get symbol info for calculation
            symbol = self.current_settings['symbol']
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0.01
                
            # Simplified lot calculation
            # This would need more sophisticated calculation in real implementation
            contract_size = symbol_info.trade_contract_size
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            # Basic calculation
            calculated_lot = risk_amount / (contract_size * 0.0001)  # Simplified
            
            # Round to lot step
            calculated_lot = round(calculated_lot / lot_step) * lot_step
            
            # Ensure within limits
            calculated_lot = max(min_lot, min(calculated_lot, max_lot))
            
            return calculated_lot
            
        except Exception as e:
            self.logger.log(f"ERROR calculating auto lot: {str(e)}")
            return 0.01
