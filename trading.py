"""
MT5 Trading Bot - Trading Engine Module
Enhanced trading functionality with multiple strategies and robust MT5 integration
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    # Create mock MT5 module for demo purposes
    class MockMT5:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        TRADE_ACTION_DEAL = 1
        ORDER_TIME_GTC = 0
        ORDER_FILLING_IOC = 1
        TRADE_RETCODE_DONE = 10009
        
        @staticmethod
        def initialize():
            return True
            
        @staticmethod
        def shutdown():
            pass
            
        @staticmethod
        def account_info():
            class MockAccount:
                login = 12345
                balance = 10000.0
                equity = 10000.0
                margin = 0.0
                margin_free = 10000.0
                margin_level = 0.0
            return MockAccount()
            
        @staticmethod
        def symbols_get():
            class MockSymbol:
                def __init__(self, name):
                    self.name = name
                    self.visible = True
            return [MockSymbol("EURUSD"), MockSymbol("GBPUSD"), MockSymbol("USDJPY"), 
                   MockSymbol("XAUUSD"), MockSymbol("BTCUSD")]
        
        @staticmethod
        def symbol_info(symbol):
            class MockSymbolInfo:
                point = 0.0001
                digits = 5
                visible = True
                trade_contract_size = 100000
                margin_initial = 100
                volume_min = 0.01
                volume_max = 1000
                volume_step = 0.01
            return MockSymbolInfo()
            
        @staticmethod
        def symbol_select(symbol, enable):
            return True
            
        @staticmethod
        def symbol_info_tick(symbol):
            import random
            class MockTick:
                ask = 1.1000 + random.uniform(-0.01, 0.01)
                bid = 1.0998 + random.uniform(-0.01, 0.01)
            return MockTick()
            
        @staticmethod
        def positions_get():
            return []
            
        @staticmethod
        def copy_rates_from_pos(symbol, timeframe, start, count):
            import random
            rates = []
            for i in range(count):
                rates.append({
                    'close': 1.1000 + random.uniform(-0.01, 0.01),
                    'high': 1.1005 + random.uniform(-0.01, 0.01),
                    'low': 1.0995 + random.uniform(-0.01, 0.01),
                    'open': 1.1000 + random.uniform(-0.01, 0.01)
                })
            return rates
            
        @staticmethod
        def order_send(request):
            class MockResult:
                retcode = MockMT5.TRADE_RETCODE_DONE
            return MockResult()
    
    mt5 = MockMT5()

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
            if MT5_AVAILABLE:
                self.logger.log(f"MT5 connected successfully")
            else:
                self.logger.log(f"MT5 Demo Mode - Simulation active")
            self.logger.log(f"Account: {account_info.login} | Balance: ${account_info.balance:.2f}")
            
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
        """Start automated trading"""
        if self.trading_running:
            self.logger.log("Trading is already running")
            return False
            
        if not self.is_mt5_connected:
            self.logger.log("ERROR: MT5 not connected")
            return False
            
        # Validate settings
        if not self.validate_trading_settings(settings):
            return False
            
        self.current_settings = settings.copy()
        self.trading_running = True
        
        # Start trading thread
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.trading_thread.start()
        
        self.logger.log(f"Started {settings['strategy']} trading for {settings['symbol']}")
        return True
        
    def stop_trading(self):
        """Stop automated trading"""
        if self.trading_running:
            self.trading_running = False
            self.logger.log("Stopping automated trading...")
            
            # Wait for trading thread to finish
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5)
                
            self.logger.log("Automated trading stopped")
            
    def validate_trading_settings(self, settings: Dict) -> bool:
        """Validate trading settings"""
        try:
            # Check required fields
            required_fields = ['strategy', 'symbol', 'lot_size', 'tp_value', 'sl_value']
            for field in required_fields:
                if field not in settings:
                    self.logger.log(f"ERROR: Missing required field: {field}")
                    return False
                    
            # Validate symbol
            if not self.validate_symbol(settings['symbol']):
                return False
                
            # Validate numeric values
            if settings['lot_size'] <= 0:
                self.logger.log("ERROR: Invalid lot size")
                return False
                
            if settings['tp_value'] <= 0 or settings['sl_value'] <= 0:
                self.logger.log("ERROR: Invalid TP/SL values")
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"ERROR validating settings: {str(e)}")
            return False
            
    def place_manual_order(self, order_type: str, settings: Dict) -> bool:
        """Place manual BUY or SELL order"""
        if not self.is_mt5_connected:
            self.logger.log("ERROR: MT5 not connected")
            return False
            
        try:
            symbol = settings['symbol']
            lot_size = settings['lot_size']
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.logger.log(f"ERROR: Cannot get price for {symbol}")
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
                self.logger.log(f"ERROR: Manual {order_type} failed - {result.retcode}")
                return False
            else:
                self.logger.log(f"Manual {order_type} order successful at {price:.5f}")
                return True
                
        except Exception as e:
            self.logger.log(f"ERROR placing manual order: {str(e)}")
            return False
            
    def calculate_tp_sl(self, price: float, order_type: str, settings: Dict) -> tuple:
        """Calculate Take Profit and Stop Loss based on settings"""
        try:
            tp_value = settings['tp_value']
            sl_value = settings['sl_value']
            tp_unit = settings['tp_unit']
            sl_unit = settings['sl_unit']
            symbol = settings['symbol']
            
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
                if order_type == "BUY":
                    tp = price * (1 + tp_value / 100)
                else:
                    tp = price * (1 - tp_value / 100)
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
                if order_type == "BUY":
                    sl = price * (1 - sl_value / 100)
                else:
                    sl = price * (1 + sl_value / 100)
            elif sl_unit == "money":
                # Simplified money calculation
                pip_value = self.calculate_pip_value(symbol, settings['lot_size'])
                if pip_value > 0:
                    pips_needed = sl_value / pip_value
                    if order_type == "BUY":
                        sl = price - (pips_needed * point * 10)
                    else:
                        sl = price + (pips_needed * point * 10)
                        
            # Round to symbol digits
            tp = round(tp, digits) if tp > 0 else 0
            sl = round(sl, digits) if sl > 0 else 0
            
            return tp, sl
            
        except Exception as e:
            self.logger.log(f"ERROR calculating TP/SL: {str(e)}")
            return 0, 0
            
    def calculate_pip_value(self, symbol: str, lot_size: float) -> float:
        """Calculate pip value for money-based TP/SL calculations"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0
                
            # Simplified pip value calculation
            # This is a basic implementation - real pip value calculation is more complex
            point = symbol_info.point
            contract_size = symbol_info.trade_contract_size
            
            # For most forex pairs, pip value = (point * contract_size * lot_size)
            pip_value = point * 10 * contract_size * lot_size
            
            return pip_value
            
        except Exception as e:
            self.logger.log(f"ERROR calculating pip value: {str(e)}")
            return 1  # Return default value
            
    def _trading_loop(self):
        """Main trading loop running in separate thread"""
        strategy = self.current_settings['strategy']
        symbol = self.current_settings['symbol']
        interval = self.current_settings.get('interval', 10)
        
        self.logger.log(f"Trading loop started for {strategy} on {symbol}")
        
        last_price = None
        
        while self.trading_running:
            try:
                # Check session limits
                self._check_session_limits()
                
                # Check if max orders reached
                if self._get_open_positions_count() >= self.max_orders_per_session:
                    self.logger.log("Maximum orders reached, waiting...")
                    time.sleep(interval)
                    continue
                    
                # Get current price
                tick = mt5.symbol_info_tick(symbol)
                if not tick or tick.ask == 0.0:
                    self.logger.log("Cannot get current price")
                    time.sleep(interval)
                    continue
                    
                current_price = tick.ask
                
                # Check for price spikes
                if last_price and abs(current_price - last_price) > self.price_spike_threshold:
                    self.logger.log("Price spike detected, skipping cycle")
                    last_price = current_price
                    time.sleep(interval)
                    continue
                    
                last_price = current_price
                
                # Get technical indicators
                indicators = self._get_technical_indicators(symbol, strategy)
                if not indicators:
                    self.logger.log("Cannot get technical indicators")
                    time.sleep(interval)
                    continue
                    
                # Generate trading signal
                signal = self._generate_signal(strategy, current_price, indicators)
                
                if signal:
                    # Execute trade
                    success = self._execute_strategy_trade(signal, current_price)
                    if success:
                        self.order_counter += 1
                        self.logger.log(f"{signal} order executed successfully")
                    else:
                        self.logger.log(f"Failed to execute {signal} order")
                        
                time.sleep(interval)
                
            except Exception as e:
                self.logger.log(f"ERROR in trading loop: {str(e)}")
                time.sleep(interval)
                
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
            
    def _get_technical_indicators(self, symbol: str, strategy: str) -> Optional[Dict]:
        """Get technical indicators for analysis"""
        try:
            strategy_config = self.strategy_configs.get(strategy, {})
            timeframe = strategy_config.get('timeframe', mt5.TIMEFRAME_M1)
            
            # Get different periods of data for various indicators
            ma10 = self._get_ma(symbol, 10, timeframe)
            ema9 = self._get_ema(symbol, 9, timeframe)
            ema21 = self._get_ema(symbol, 21, timeframe)
            ema50 = self._get_ema(symbol, 50, timeframe)
            wma5 = self._get_wma(symbol, 5, timeframe)
            wma10 = self._get_wma(symbol, 10, timeframe)
            rsi = self._get_rsi(symbol, 14, timeframe)
            bb_upper, bb_lower = self._get_bollinger_bands(symbol, 20, timeframe)
            
            # Check if all indicators are available
            if None in [ma10, ema9, ema21, ema50, wma5, wma10, rsi, bb_upper, bb_lower]:
                return None
                
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
            self.logger.log(f"ERROR getting technical indicators: {str(e)}")
            return None
            
    def _get_ma(self, symbol: str, period: int, timeframe) -> Optional[float]:
        """Calculate Moving Average"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
            if rates is None or len(rates) < period:
                return None
            return float(np.mean([r['close'] for r in rates]))
        except:
            return None
            
    def _get_ema(self, symbol: str, period: int, timeframe) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 1)
            if rates is None or len(rates) < period:
                return None
            prices = np.array([r['close'] for r in rates])
            weights = np.exp(np.linspace(-1., 0., period))
            weights /= weights.sum()
            result = np.convolve(prices, weights, mode='valid')
            return float(result[-1])
        except:
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
        """Calculate Relative Strength Index"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 1)
            if rates is None or len(rates) < period + 1:
                return None
            close = np.array([r['close'] for r in rates])
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            avg_gain = float(np.mean(gain))
            avg_loss = float(np.mean(loss))
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return float(100 - (100 / (1 + rs)))
        except:
            return None
            
    def _get_bollinger_bands(self, symbol: str, period: int, timeframe) -> tuple:
        """Calculate Bollinger Bands"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
            if rates is None or len(rates) < period:
                return None, None
            close = np.array([r['close'] for r in rates])
            sma = np.mean(close)
            std = np.std(close)
            return sma + (2 * std), sma - (2 * std)
        except:
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
        """Execute trade based on strategy signal"""
        try:
            # Check account balance
            account_info = self.get_account_info()
            if not account_info or account_info['balance'] < self.min_balance:
                self.logger.log("Insufficient balance for trading")
                return False
                
            # Calculate lot size
            lot_size = self.current_settings['lot_size']
            if self.current_settings.get('auto_lot', False):
                lot_size = self._calculate_auto_lot()
                
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
                "symbol": self.current_settings['symbol'],
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
            
            # Send order
            result = mt5.order_send(request)
            
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            self.logger.log(f"ERROR executing trade: {str(e)}")
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
