
import json
import os
from typing import Dict, Any, Optional
from logger_utils import logger

class ConfigManager:
    """Robust configuration management with validation"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.config = {}
        self.default_config = {
            "max_orders": 10,
            "max_daily_trades": 50,
            "max_daily_orders": 50,  # User configurable daily order limit
            "max_risk_percentage": 2.0,
            "default_lot_size": 0.01,
            "tp_default": "20",
            "sl_default": "10",
            "tp_unit_default": "pips",
            "sl_unit_default": "pips",
            "auto_recovery": True,
            "telegram_enabled": False,
            "log_level": "INFO",
            "trading_enabled": True,
            "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
            "strategies": ["Scalping", "Intraday", "Arbitrage", "HFT"]
        }
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from file with fallback to defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Validate and merge with defaults
                self.config = self.default_config.copy()
                self.config.update(loaded_config)
                
                # Validate critical values
                self._validate_config()
                
                logger(f"✅ Configuration loaded from {self.config_file}")
                return True
            else:
                # Create default config file
                self.config = self.default_config.copy()
                self.save_config()
                logger(f"📝 Created default configuration: {self.config_file}")
                return True
                
        except Exception as e:
            logger(f"❌ Error loading config: {str(e)}")
            logger("🔄 Using default configuration")
            self.config = self.default_config.copy()
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger(f"💾 Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger(f"❌ Error saving config: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value with validation"""
        try:
            old_value = self.config.get(key)
            self.config[key] = value
            
            # Validate after setting
            if not self._validate_config():
                # Revert if validation fails
                if old_value is not None:
                    self.config[key] = old_value
                else:
                    del self.config[key]
                return False
            
            # Auto-save if critical setting
            if key in ["max_orders", "max_daily_trades", "max_daily_orders", "max_risk_percentage"]:
                self.save_config()
            
            return True
            
        except Exception as e:
            logger(f"❌ Error setting config {key}: {str(e)}")
            return False
    
    def _validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            # Validate numeric ranges
            if self.config.get("max_orders", 0) < 1 or self.config.get("max_orders", 0) > 100:
                logger("❌ Invalid max_orders: must be 1-100")
                return False
            
            if self.config.get("max_daily_trades", 0) < 1 or self.config.get("max_daily_trades", 0) > 1000:
                logger("❌ Invalid max_daily_trades: must be 1-1000")
                return False
            
            if self.config.get("max_daily_orders", 0) < 1 or self.config.get("max_daily_orders", 0) > 1000:
                logger("❌ Invalid max_daily_orders: must be 1-1000")
                return False
            
            if self.config.get("max_risk_percentage", 0) < 0.1 or self.config.get("max_risk_percentage", 0) > 10:
                logger("❌ Invalid max_risk_percentage: must be 0.1-10")
                return False
            
            if self.config.get("default_lot_size", 0) < 0.01 or self.config.get("default_lot_size", 0) > 100:
                logger("❌ Invalid default_lot_size: must be 0.01-100")
                return False
            
            return True
            
        except Exception as e:
            logger(f"❌ Config validation error: {str(e)}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = self.default_config.copy()
            return self.save_config()
        except Exception as e:
            logger(f"❌ Error resetting config: {str(e)}")
            return False


# Global config instance
config_manager = ConfigManager()
