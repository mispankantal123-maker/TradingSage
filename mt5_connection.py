# --- MetaTrader 5 Connection Module ---
"""
MT5 connection, initialization, and symbol management
"""

import platform
import os

try:
    import MetaTrader5 as mt5
except ImportError:
    # Use mock MT5 for testing on non-Windows platforms
    import mt5_mock as mt5
from typing import List, Optional, Dict, Any
from logger_utils import logger


def connect_mt5() -> bool:
    """Enhanced MT5 connection with comprehensive error handling and logging"""
    try:
        # Import at function level to ensure module is loaded
        global mt5
        if 'mt5' not in globals():
            try:
                import MetaTrader5 as mt5
            except ImportError:
                import mt5_mock as mt5
        
        logger("🔄 Initializing MetaTrader 5 connection...")
        logger(f"🔍 Python: {platform.python_version()} ({platform.architecture()[0]})")
        logger(f"🔍 Platform: {platform.system()} {platform.release()}")
        
        # Check if MT5 is already initialized
        if mt5.initialize():
            logger("✅ MT5 initialization successful")
            
            # Get terminal info for debugging
            try:
                terminal_info = mt5.terminal_info()
                if terminal_info:
                    logger(f"📊 Terminal: {terminal_info.name}")
                    logger(f"📍 Path: {terminal_info.path}")
                    logger(f"🔢 Build: {terminal_info.build}")
                    logger(f"🌐 Connected: {'✅' if terminal_info.connected else '❌'}")
                    
                    if not terminal_info.connected:
                        logger("⚠️ Terminal not connected to server")
                        return False
                        
            except Exception as term_e:
                logger(f"⚠️ Could not get terminal info: {str(term_e)}")
            
            # Test connection with account info
            account_info = mt5.account_info()
            if account_info:
                logger(f"👤 Account: {account_info.login}")
                logger(f"🏦 Server: {account_info.server}")
                logger(f"💰 Balance: ${account_info.balance:.2f}")
                logger(f"💱 Currency: {account_info.currency}")
                logger(f"🔐 Trade Allowed: {'✅' if account_info.trade_allowed else '❌'}")
                
                if not account_info.trade_allowed:
                    logger("❌ Trading not allowed on this account")
                    return False
                    
                return True
            else:
                logger("❌ Cannot get account info - not logged in")
                return False
                
        else:
            error = mt5.last_error()
            logger(f"❌ MT5 initialization failed: {error}")
            logger("🔧 Troubleshooting checklist:")
            logger("   1. Ensure MT5 is running")
            logger("   2. Login to trading account")
            logger("   3. Run MT5 as Administrator")
            logger("   4. Check if Python and MT5 are same architecture (both 64-bit)")
            return False
            
    except ImportError:
        logger("❌ MetaTrader5 library not found")
        logger("💡 Installing MetaTrader5 library...")
        try:
            os.system("pip install MetaTrader5")
            import MetaTrader5 as mt5
            return connect_mt5()  # Retry after installation
        except Exception as install_e:
            logger(f"❌ Failed to install MetaTrader5: {str(install_e)}")
            return False
            
    except Exception as e:
        logger(f"❌ Unexpected error during MT5 connection: {str(e)}")
        return False


def check_mt5_status() -> bool:
    """Check current MT5 connection status"""
    try:
        # Ensure mt5 is available
        global mt5
        if 'mt5' not in globals():
            try:
                import MetaTrader5 as mt5
            except ImportError:
                import mt5_mock as mt5
        
        # Test with a simple account info call
        account_info = mt5.account_info()
        if account_info and account_info.trade_allowed:
            return True
        else:
            logger("⚠️ MT5 connection lost or trading not allowed")
            return False
    except Exception as e:
        logger(f"❌ MT5 status check failed: {str(e)}")
        return False


def get_symbols() -> List[str]:
    """Get available symbols from MT5 with error handling"""
    try:
        # Ensure mt5 is available
        global mt5
        if 'mt5' not in globals():
            try:
                import MetaTrader5 as mt5
            except ImportError:
                import mt5_mock as mt5
        
        symbols = mt5.symbols_get()
        if symbols:
            symbol_names = [symbol.name for symbol in symbols if symbol.visible]
            logger(f"📊 Found {len(symbol_names)} available symbols")
            return symbol_names
        else:
            logger("⚠️ No symbols found or MT5 not connected")
            return []
    except Exception as e:
        logger(f"❌ Error getting symbols: {str(e)}")
        return []


def validate_and_activate_symbol(symbol: str) -> Optional[str]:
    """Validate and activate symbol in MT5"""
    try:
        # Check if symbol exists
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ Symbol {symbol} not found")
            return None
            
        # Check if symbol is visible in Market Watch
        if not symbol_info.visible:
            logger(f"⚠️ Symbol {symbol} not visible, attempting to activate...")
            if mt5.symbol_select(symbol, True):
                logger(f"✅ Symbol {symbol} activated successfully")
            else:
                logger(f"❌ Failed to activate symbol {symbol}")
                return None
                
        # Verify symbol is ready for trading
        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.bid == 0 or tick.ask == 0:
            logger(f"⚠️ No quotes available for {symbol}")
            return None
            
        logger(f"✅ Symbol {symbol} validated and ready")
        return symbol
        
    except Exception as e:
        logger(f"❌ Error validating symbol {symbol}: {str(e)}")
        return None


def detect_gold_symbol() -> Optional[str]:
    """Enhanced gold symbol detection with multiple variations"""
    try:
        gold_variations = [
            "XAUUSD", "GOLD", "GOUSD", "XAU_USD", "XAU/USD",
            "GOLDUSD", "Gold", "gold", "GoldSpot", "SPOT_GOLD"
        ]
        
        available_symbols = get_symbols()
        
        for gold_var in gold_variations:
            if gold_var in available_symbols:
                validated = validate_and_activate_symbol(gold_var)
                if validated:
                    logger(f"🥇 Gold symbol detected: {validated}")
                    return validated
                    
        # If no exact match, search for symbols containing "XAU" or "GOLD"
        for symbol in available_symbols:
            if any(term in symbol.upper() for term in ["XAU", "GOLD"]):
                validated = validate_and_activate_symbol(symbol)
                if validated:
                    logger(f"🥇 Gold symbol found: {validated}")
                    return validated
                    
        logger("⚠️ No gold symbol found")
        return None
        
    except Exception as e:
        logger(f"❌ Error detecting gold symbol: {str(e)}")
        return None


def get_symbol_suggestions() -> List[str]:
    """Get suggested trading symbols with validation"""
    try:
        default_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        available_symbols = get_symbols()
        
        suggestions = []
        
        # Add default symbols if available
        for symbol in default_symbols:
            if symbol in available_symbols:
                validated = validate_and_activate_symbol(symbol)
                if validated:
                    suggestions.append(validated)
                    
        # Add gold if available
        gold_symbol = detect_gold_symbol()
        if gold_symbol and gold_symbol not in suggestions:
            suggestions.append(gold_symbol)
            
        # Add some popular major pairs if not already included
        major_pairs = ["EURGBP", "EURJPY", "GBPJPY", "USDCHF", "NZDUSD"]
        for symbol in major_pairs:
            if len(suggestions) >= 10:  # Limit suggestions
                break
            if symbol in available_symbols and symbol not in suggestions:
                validated = validate_and_activate_symbol(symbol)
                if validated:
                    suggestions.append(validated)
                    
        logger(f"💡 Symbol suggestions: {suggestions}")
        return suggestions
        
    except Exception as e:
        logger(f"❌ Error getting symbol suggestions: {str(e)}")
        return ["EURUSD", "GBPUSD", "USDJPY"]  # Fallback


def get_account_info() -> Optional[Dict[str, Any]]:
    """Get comprehensive account information"""
    try:
        # Ensure mt5 is available
        global mt5
        if 'mt5' not in globals():
            try:
                import MetaTrader5 as mt5
            except ImportError:
                import mt5_mock as mt5
        
        account_info = mt5.account_info()
        if not account_info:
            return None
            
        return {
            'login': account_info.login,
            'server': account_info.server,
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': account_info.margin_level if account_info.margin > 0 else 0,
            'currency': account_info.currency,
            'trade_allowed': account_info.trade_allowed,
            'leverage': account_info.leverage,
            'profit': account_info.profit
        }
        
    except Exception as e:
        logger(f"❌ Error getting account info: {str(e)}")
        return None


def get_positions() -> List[Any]:
    """Get current open positions"""
    try:
        # Ensure mt5 is available
        global mt5
        if 'mt5' not in globals():
            try:
                import MetaTrader5 as mt5
            except ImportError:
                import mt5_mock as mt5
        
        positions = mt5.positions_get()
        if positions is None:
            return []
        return list(positions)
    except Exception as e:
        logger(f"❌ Error getting positions: {str(e)}")
        return []