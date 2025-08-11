
# --- MetaTrader 5 Connection Module ---
"""
MT5 connection, initialization, and symbol management - REAL TRADING ONLY
"""

import platform
import os
from typing import List, Optional, Dict, Any
from logger_utils import logger

# SMART MT5 Connection - Real on Windows, Mock for Development
try:
    import MetaTrader5 as mt5
    print("✅ Using REAL MetaTrader5 for Windows trading")
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Using mt5_mock for development")
    USING_REAL_MT5 = False


def connect_mt5() -> bool:
    """Enhanced MT5 connection for Windows live trading"""
    try:
        logger("🔄 Connecting to MetaTrader 5 for LIVE TRADING...")
        logger(f"🔍 Python: {platform.python_version()} ({platform.architecture()[0]})")
        logger(f"🔍 Platform: {platform.system()} {platform.release()}")
        
        # Detect platform for appropriate mode
        if platform.system() != "Windows":
            logger("⚠️ Running in development mode (non-Windows platform)")
            # Continue with mock MT5 for development
        
        # Check if MT5 is already initialized
        if mt5.initialize():
            logger("✅ MT5 initialization successful")
            
            # Get terminal info
            terminal_info = mt5.terminal_info()
            if terminal_info:
                logger(f"📊 Terminal: {terminal_info.name}")
                logger(f"📍 Path: {terminal_info.path}")
                logger(f"🔢 Build: {terminal_info.build}")
                logger(f"🌐 Connected: {'✅' if terminal_info.connected else '❌'}")
                
                if not terminal_info.connected:
                    logger("❌ Terminal not connected to server - check internet/login")
                    return False
                        
            # Test connection with account info
            account_info = mt5.account_info()
            if account_info:
                logger(f"👤 Account: {account_info.login}")
                logger(f"🏦 Server: {account_info.server}")
                logger(f"💰 Balance: ${account_info.balance:.2f}")
                logger(f"💱 Currency: {account_info.currency}")
                logger(f"🔐 Trade Allowed: {'✅' if account_info.trade_allowed else '❌'}")
                
                if not account_info.trade_allowed:
                    logger("❌ CRITICAL: Trading not allowed on this account")
                    return False
                    
                logger("🎯 READY FOR LIVE TRADING")
                return True
            else:
                logger("❌ Cannot get account info - login to MT5 first")
                return False
                
        else:
            error = mt5.last_error()
            logger(f"❌ MT5 initialization failed: {error}")
            logger("🔧 REQUIRED STEPS:")
            logger("   1. Run MT5 as Administrator")
            logger("   2. Login to your trading account")
            logger("   3. Enable AutoTrading in MT5")
            logger("   4. Ensure Python and MT5 are same architecture (64-bit)")
            return False
            
    except Exception as e:
        logger(f"❌ MT5 connection error: {str(e)}")
        return False


def check_mt5_status() -> bool:
    """Check current MT5 connection status for live trading"""
    try:
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
    """Get available symbols from real MT5"""
    try:
        symbols = mt5.symbols_get()
        if symbols:
            symbol_names = [symbol.name for symbol in symbols if symbol.visible]
            logger(f"📊 Found {len(symbol_names)} live trading symbols")
            return symbol_names
        else:
            logger("⚠️ No symbols found - check MT5 connection")
            return []
    except Exception as e:
        logger(f"❌ Error getting symbols: {str(e)}")
        return []


def validate_and_activate_symbol(symbol: str) -> Optional[str]:
    """Validate and activate symbol in MT5 for live trading"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ Symbol {symbol} not found")
            return None
            
        if not symbol_info.visible:
            logger(f"⚠️ Activating symbol {symbol}...")
            if mt5.symbol_select(symbol, True):
                logger(f"✅ Symbol {symbol} activated")
            else:
                logger(f"❌ Failed to activate symbol {symbol}")
                return None
                
        # Verify live quotes
        tick = mt5.symbol_info_tick(symbol)
        if not tick or tick.bid == 0 or tick.ask == 0:
            logger(f"⚠️ No live quotes for {symbol}")
            return None
            
        logger(f"✅ Symbol {symbol} ready for live trading")
        return symbol
        
    except Exception as e:
        logger(f"❌ Error validating symbol {symbol}: {str(e)}")
        return None


def detect_gold_symbol() -> Optional[str]:
    """Detect gold symbol for live trading"""
    try:
        gold_variations = [
            "XAUUSD", "GOLD", "GOUSD", "XAU_USD", "XAU/USD",
            "GOLDUSD", "Gold", "GoldSpot", "SPOT_GOLD"
        ]
        
        available_symbols = get_symbols()
        
        for gold_var in gold_variations:
            if gold_var in available_symbols:
                validated = validate_and_activate_symbol(gold_var)
                if validated:
                    logger(f"🥇 Live gold symbol: {validated}")
                    return validated
                    
        for symbol in available_symbols:
            if any(term in symbol.upper() for term in ["XAU", "GOLD"]):
                validated = validate_and_activate_symbol(symbol)
                if validated:
                    logger(f"🥇 Live gold symbol found: {validated}")
                    return validated
                    
        logger("⚠️ No gold symbol available")
        return None
        
    except Exception as e:
        logger(f"❌ Error detecting gold symbol: {str(e)}")
        return None


def get_symbol_suggestions() -> List[str]:
    """Get real trading symbol suggestions"""
    try:
        major_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        available_symbols = get_symbols()
        
        suggestions = []
        
        for symbol in major_symbols:
            if symbol in available_symbols:
                validated = validate_and_activate_symbol(symbol)
                if validated:
                    suggestions.append(validated)
                    
        gold_symbol = detect_gold_symbol()
        if gold_symbol and gold_symbol not in suggestions:
            suggestions.append(gold_symbol)
            
        cross_pairs = ["EURGBP", "EURJPY", "GBPJPY", "USDCHF", "NZDUSD"]
        for symbol in cross_pairs:
            if len(suggestions) >= 10:
                break
            if symbol in available_symbols and symbol not in suggestions:
                validated = validate_and_activate_symbol(symbol)
                if validated:
                    suggestions.append(validated)
                    
        logger(f"💡 Live trading symbols: {suggestions}")
        return suggestions
        
    except Exception as e:
        logger(f"❌ Error getting symbol suggestions: {str(e)}")
        return ["EURUSD", "GBPUSD", "USDJPY"]


def get_account_info() -> Optional[Dict[str, Any]]:
    """Get real account information"""
    try:
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
    """Get current live positions"""
    try:
        positions = mt5.positions_get()
        if positions is None:
            return []
        return list(positions)
    except Exception as e:
        logger(f"❌ Error getting positions: {str(e)}")
        return []
