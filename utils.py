"""
MT5 Trading Bot - Utilities Module
Configuration management, logging, and helper functions
"""

import json
import os
import datetime
import threading
from typing import Dict, Any, Optional, Callable

class ConfigManager:
    """Manages bot configuration with persistence"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_data = {}
        self.load_config()
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            'strategy': 'Scalping',
            'symbol': 'EURUSD',
            'lot_size': 0.01,
            'auto_lot': False,
            'risk_percent': 2.0,
            'tp_value': 20,
            'tp_unit': 'pips',
            'sl_value': 10,
            'sl_unit': 'pips',
            'interval': 10,
            'max_orders_per_session': 10,
            'reset_order_hour': 0,
            'min_balance': 1000,
            'price_spike_threshold': 10,
            'min_score': 4,
            'telegram_bot_token': '',
            'telegram_chat_id': '',
            'enable_telegram': False,
            'log_level': 'INFO',
            'auto_save_config': True
        }
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    
                # Merge with defaults to ensure all keys exist
                self.config_data = self.get_default_config()
                self.config_data.update(loaded_config)
            else:
                # Use defaults if file doesn't exist
                self.config_data = self.get_default_config()
                self.save_config()  # Create file with defaults
                
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config_data = self.get_default_config()
            
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config_data.copy()
        
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        self.config_data.update(updates)
        if self.config_data.get('auto_save_config', True):
            self.save_config()
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get specific configuration value"""
        return self.config_data.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set specific configuration value"""
        self.config_data[key] = value
        if self.config_data.get('auto_save_config', True):
            self.save_config()
            
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config_data = self.get_default_config()
        self.save_config()

class Logger:
    """Enhanced logging with GUI integration and file output"""
    
    def __init__(self, log_file: str = "trading_bot.log"):
        self.log_file = log_file
        self.gui_callback = None
        self.log_lock = threading.Lock()
        self.telegram_config = {}
        
        # Ensure log file exists
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write(f"Trading Bot Log Started - {datetime.datetime.now()}\n")
                f.write("=" * 50 + "\n")
                
    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set GUI callback for displaying logs"""
        self.gui_callback = callback
        
    def set_telegram_config(self, bot_token: str, chat_id: str):
        """Set Telegram configuration for notifications"""
        self.telegram_config = {
            'bot_token': bot_token,
            'chat_id': chat_id
        }
        
    def log(self, message: str, level: str = "INFO", send_telegram: bool = False):
        """Log message to file and GUI"""
        with self.log_lock:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{level}] {message}"
            log_entry = f"{timestamp} - {formatted_message}"
            
            # Write to file
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry + "\n")
            except Exception as e:
                print(f"Error writing to log file: {e}")
                
            # Send to GUI if callback is set
            if self.gui_callback:
                try:
                    self.gui_callback(formatted_message)
                except Exception as e:
                    print(f"Error sending to GUI: {e}")
                    
            # Send to Telegram if requested and configured
            if send_telegram and self.telegram_config:
                self._send_telegram(formatted_message)
                
            # Also print to console for debugging
            print(log_entry)
            
    def error(self, message: str, send_telegram: bool = True):
        """Log error message"""
        self.log(message, "ERROR", send_telegram)
        
    def warning(self, message: str):
        """Log warning message"""
        self.log(message, "WARNING")
        
    def info(self, message: str):
        """Log info message"""
        self.log(message, "INFO")
        
    def debug(self, message: str):
        """Log debug message"""
        self.log(message, "DEBUG")
        
    def trade(self, message: str, send_telegram: bool = True):
        """Log trading activity"""
        self.log(message, "TRADE", send_telegram)
        
    def _send_telegram(self, message: str):
        """Send message to Telegram (if configured)"""
        try:
            import requests
            
            bot_token = self.telegram_config.get('bot_token')
            chat_id = self.telegram_config.get('chat_id')
            
            if not bot_token or not chat_id:
                return
                
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': f"🤖 Trading Bot: {message}",
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if not response.ok:
                self.log(f"Failed to send Telegram message: {response.status_code}")
                
        except Exception as e:
            self.log(f"Error sending Telegram message: {e}")
            
    def save_logs(self, backup_file: Optional[str] = None):
        """Save/backup current logs"""
        if not backup_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"trading_bot_backup_{timestamp}.log"
            
        try:
            import shutil
            shutil.copy2(self.log_file, backup_file)
            self.log(f"Logs backed up to {backup_file}")
            return backup_file
        except Exception as e:
            self.error(f"Failed to backup logs: {e}")
            return None
            
    def clear_logs(self):
        """Clear current log file (create backup first)"""
        try:
            # Create backup
            backup_file = self.save_logs()
            if backup_file:
                # Clear current log
                with open(self.log_file, 'w') as f:
                    f.write(f"Trading Bot Log Cleared - {datetime.datetime.now()}\n")
                    f.write("=" * 50 + "\n")
                self.log("Log file cleared (backup created)")
        except Exception as e:
            self.error(f"Failed to clear logs: {e}")

class TradingUtils:
    """Utility functions for trading operations"""
    
    @staticmethod
    def format_currency(amount: float, decimals: int = 2) -> str:
        """Format currency amount"""
        return f"${amount:,.{decimals}f}"
        
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Format percentage value"""
        return f"{value:.{decimals}f}%"
        
    @staticmethod
    def calculate_profit_loss(entry_price: float, current_price: float, 
                            lot_size: float, order_type: str) -> float:
        """Calculate current profit/loss for a position"""
        try:
            if order_type.upper() == "BUY":
                return (current_price - entry_price) * lot_size * 100000  # Simplified
            else:  # SELL
                return (entry_price - current_price) * lot_size * 100000  # Simplified
        except:
            return 0.0
            
    @staticmethod
    def calculate_margin_required(symbol_info, lot_size: float, price: float) -> float:
        """Calculate margin required for a position"""
        try:
            if symbol_info:
                contract_size = symbol_info.trade_contract_size
                margin_rate = symbol_info.margin_initial
                return (lot_size * contract_size * price) / margin_rate
            return 0.0
        except:
            return 0.0
            
    @staticmethod
    def validate_lot_size(lot_size: float, symbol_info) -> float:
        """Validate and adjust lot size according to symbol requirements"""
        try:
            if not symbol_info:
                return 0.01
                
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            # Ensure within bounds
            lot_size = max(min_lot, min(lot_size, max_lot))
            
            # Round to step
            lot_size = round(lot_size / lot_step) * lot_step
            
            return lot_size
            
        except:
            return 0.01
            
    @staticmethod
    def get_market_hours_info(symbol: str) -> Dict[str, Any]:
        """Get market hours information for symbol"""
        # This is a simplified implementation
        # Real implementation would need to check actual market hours
        forex_pairs = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
        
        if any(pair in symbol.upper() for pair in forex_pairs):
            return {
                'market_type': 'forex',
                'always_open': True,
                'description': 'Forex market (24/5)'
            }
        elif 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
            return {
                'market_type': 'precious_metals',
                'always_open': False,
                'description': 'Precious metals market'
            }
        elif 'BTC' in symbol.upper() or 'ETH' in symbol.upper():
            return {
                'market_type': 'crypto',
                'always_open': True,
                'description': 'Cryptocurrency market (24/7)'
            }
        else:
            return {
                'market_type': 'unknown',
                'always_open': False,
                'description': 'Unknown market type'
            }
            
    @staticmethod
    def format_time_duration(seconds: int) -> str:
        """Format duration in seconds to human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

class PerformanceTracker:
    """Track and analyze trading performance"""
    
    def __init__(self):
        self.trades = []
        self.session_start = datetime.datetime.now()
        
    def add_trade(self, trade_data: Dict[str, Any]):
        """Add trade to performance tracking"""
        trade_data['timestamp'] = datetime.datetime.now()
        self.trades.append(trade_data)
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'average_profit': 0.0,
                'session_duration': 0
            }
            
        total_trades = len(self.trades)
        profitable_trades = sum(1 for trade in self.trades if trade.get('profit', 0) > 0)
        losing_trades = total_trades - profitable_trades
        
        total_profit = sum(trade.get('profit', 0) for trade in self.trades)
        win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
        average_profit = total_profit / total_trades if total_trades > 0 else 0
        
        session_duration = (datetime.datetime.now() - self.session_start).total_seconds()
        
        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'average_profit': average_profit,
            'session_duration': int(session_duration)
        }
        
    def reset_session(self):
        """Reset session tracking"""
        self.trades = []
        self.session_start = datetime.datetime.now()
