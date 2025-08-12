# --- Universal Symbol Manager ---
"""
Comprehensive symbol management for ALL trading instruments:
Forex, Crypto, Metals, Indices, Commodities, Stocks, CFDs
Ensures maximum compatibility across ALL symbols without errors
"""

import re
from typing import Dict, Any, List, Optional, Set
from logger_utils import logger

class UniversalSymbolManager:
    """Universal symbol support for maximum market coverage"""
    
    def __init__(self):
        # Comprehensive symbol database for ALL markets
        self.symbol_database = {
            # FOREX MAJORS
            'EURUSD': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 2.0, 'min_lot': 0.01, 'aggressiveness': 1.4},
            'GBPUSD': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 2.0, 'min_lot': 0.01, 'aggressiveness': 1.3},
            'USDJPY': {'type': 'FOREX_JPY', 'pip_value': 0.01, 'spread_limit': 3.0, 'min_lot': 0.01, 'aggressiveness': 1.2},
            'USDCHF': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 2.5, 'min_lot': 0.01, 'aggressiveness': 1.1},
            'USDCAD': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 2.5, 'min_lot': 0.01, 'aggressiveness': 1.2},
            'AUDUSD': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 3.0, 'min_lot': 0.01, 'aggressiveness': 1.1},
            'NZDUSD': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 3.5, 'min_lot': 0.01, 'aggressiveness': 1.0},
            
            # FOREX CROSSES
            'EURJPY': {'type': 'FOREX_JPY', 'pip_value': 0.01, 'spread_limit': 3.5, 'min_lot': 0.01, 'aggressiveness': 1.2},
            'GBPJPY': {'type': 'FOREX_JPY', 'pip_value': 0.01, 'spread_limit': 4.0, 'min_lot': 0.01, 'aggressiveness': 1.3},
            'EURGBP': {'type': 'FOREX_CROSS', 'pip_value': 0.0001, 'spread_limit': 2.5, 'min_lot': 0.01, 'aggressiveness': 1.1},
            'EURAUD': {'type': 'FOREX_CROSS', 'pip_value': 0.0001, 'spread_limit': 3.0, 'min_lot': 0.01, 'aggressiveness': 1.0},
            'EURCHF': {'type': 'FOREX_CROSS', 'pip_value': 0.0001, 'spread_limit': 3.0, 'min_lot': 0.01, 'aggressiveness': 1.0},
            'AUDCAD': {'type': 'FOREX_CROSS', 'pip_value': 0.0001, 'spread_limit': 4.0, 'min_lot': 0.01, 'aggressiveness': 0.9},
            
            # CRYPTO MAJORS  
            'BTCUSD': {'type': 'CRYPTO_MAJOR', 'pip_value': 1.0, 'spread_limit': 10.0, 'min_lot': 0.01, 'aggressiveness': 1.8},
            'ETHUSD': {'type': 'CRYPTO_MAJOR', 'pip_value': 0.1, 'spread_limit': 5.0, 'min_lot': 0.1, 'aggressiveness': 1.7},
            'XRPUSD': {'type': 'CRYPTO_ALT', 'pip_value': 0.0001, 'spread_limit': 8.0, 'min_lot': 1.0, 'aggressiveness': 1.5},
            'ADAUSD': {'type': 'CRYPTO_ALT', 'pip_value': 0.0001, 'spread_limit': 10.0, 'min_lot': 1.0, 'aggressiveness': 1.4},
            'DOTUSD': {'type': 'CRYPTO_ALT', 'pip_value': 0.001, 'spread_limit': 12.0, 'min_lot': 0.1, 'aggressiveness': 1.3},
            'LINKUSD': {'type': 'CRYPTO_ALT', 'pip_value': 0.001, 'spread_limit': 8.0, 'min_lot': 0.1, 'aggressiveness': 1.3},
            'LTCUSD': {'type': 'CRYPTO_ALT', 'pip_value': 0.01, 'spread_limit': 6.0, 'min_lot': 0.01, 'aggressiveness': 1.2},
            
            # METALS
            'XAUUSD': {'type': 'METALS', 'pip_value': 0.01, 'spread_limit': 5.0, 'min_lot': 0.01, 'aggressiveness': 1.6},
            'XAGUSD': {'type': 'METALS', 'pip_value': 0.001, 'spread_limit': 8.0, 'min_lot': 0.01, 'aggressiveness': 1.4},
            'XPTUSD': {'type': 'METALS', 'pip_value': 0.01, 'spread_limit': 15.0, 'min_lot': 0.01, 'aggressiveness': 1.2},
            'XPDUSD': {'type': 'METALS', 'pip_value': 0.01, 'spread_limit': 20.0, 'min_lot': 0.01, 'aggressiveness': 1.1},
            
            # INDICES
            'US30': {'type': 'INDICES', 'pip_value': 1.0, 'spread_limit': 5.0, 'min_lot': 0.01, 'aggressiveness': 1.3},
            'US500': {'type': 'INDICES', 'pip_value': 0.1, 'spread_limit': 3.0, 'min_lot': 0.01, 'aggressiveness': 1.2},
            'NAS100': {'type': 'INDICES', 'pip_value': 0.1, 'spread_limit': 4.0, 'min_lot': 0.01, 'aggressiveness': 1.4},
            'GER30': {'type': 'INDICES', 'pip_value': 1.0, 'spread_limit': 6.0, 'min_lot': 0.01, 'aggressiveness': 1.1},
            'UK100': {'type': 'INDICES', 'pip_value': 1.0, 'spread_limit': 4.0, 'min_lot': 0.01, 'aggressiveness': 1.0},
            'JPN225': {'type': 'INDICES', 'pip_value': 1.0, 'spread_limit': 8.0, 'min_lot': 0.01, 'aggressiveness': 1.0},
            
            # COMMODITIES
            'USOIL': {'type': 'COMMODITIES', 'pip_value': 0.01, 'spread_limit': 8.0, 'min_lot': 0.01, 'aggressiveness': 1.3},
            'UKOIL': {'type': 'COMMODITIES', 'pip_value': 0.01, 'spread_limit': 10.0, 'min_lot': 0.01, 'aggressiveness': 1.2},
            'NATGAS': {'type': 'COMMODITIES', 'pip_value': 0.001, 'spread_limit': 15.0, 'min_lot': 0.1, 'aggressiveness': 1.1},
        }
        
        # Dynamic pattern recognition for unknown symbols
        self.symbol_patterns = {
            # Forex patterns
            r'^[A-Z]{3}USD$': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 3.0, 'aggressiveness': 1.0},
            r'^USD[A-Z]{3}$': {'type': 'FOREX_MAJOR', 'pip_value': 0.0001, 'spread_limit': 3.0, 'aggressiveness': 1.0},
            r'^[A-Z]{3}JPY$': {'type': 'FOREX_JPY', 'pip_value': 0.01, 'spread_limit': 4.0, 'aggressiveness': 1.0},
            r'^[A-Z]{6}$': {'type': 'FOREX_CROSS', 'pip_value': 0.0001, 'spread_limit': 4.0, 'aggressiveness': 0.9},
            
            # Crypto patterns  
            r'^BTC.*': {'type': 'CRYPTO_MAJOR', 'pip_value': 1.0, 'spread_limit': 10.0, 'aggressiveness': 1.8},
            r'^ETH.*': {'type': 'CRYPTO_MAJOR', 'pip_value': 0.1, 'spread_limit': 5.0, 'aggressiveness': 1.7},
            r'.*USD$': {'type': 'CRYPTO_ALT', 'pip_value': 0.001, 'spread_limit': 8.0, 'aggressiveness': 1.2},
            
            # Metals patterns
            r'^XAU.*': {'type': 'METALS', 'pip_value': 0.01, 'spread_limit': 5.0, 'aggressiveness': 1.6},
            r'^XAG.*': {'type': 'METALS', 'pip_value': 0.001, 'spread_limit': 8.0, 'aggressiveness': 1.4},
            r'^X[A-Z]{2}.*': {'type': 'METALS', 'pip_value': 0.01, 'spread_limit': 10.0, 'aggressiveness': 1.2},
            
            # Indices patterns
            r'^US\d+$': {'type': 'INDICES', 'pip_value': 1.0, 'spread_limit': 5.0, 'aggressiveness': 1.3},
            r'^NAS\d+$': {'type': 'INDICES', 'pip_value': 0.1, 'spread_limit': 4.0, 'aggressiveness': 1.4},
            r'^[A-Z]{3}\d+$': {'type': 'INDICES', 'pip_value': 1.0, 'spread_limit': 6.0, 'aggressiveness': 1.1},
            
            # Commodities patterns
            r'^.*OIL$': {'type': 'COMMODITIES', 'pip_value': 0.01, 'spread_limit': 8.0, 'aggressiveness': 1.3},
            r'^.*GAS$': {'type': 'COMMODITIES', 'pip_value': 0.001, 'spread_limit': 15.0, 'aggressiveness': 1.1},
        }

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive symbol information with fallback detection"""
        try:
            symbol = symbol.upper().strip()
            
            # Direct database lookup
            if symbol in self.symbol_database:
                info = self.symbol_database[symbol].copy()
                info['symbol'] = symbol
                logger(f"📋 Symbol {symbol}: {info['type']} (Database)")
                return info
            
            # Pattern-based detection for unknown symbols
            for pattern, default_info in self.symbol_patterns.items():
                if re.match(pattern, symbol):
                    info = default_info.copy()
                    info['symbol'] = symbol
                    info['min_lot'] = 0.01  # Safe default
                    logger(f"📋 Symbol {symbol}: {info['type']} (Pattern: {pattern})")
                    return info
            
            # Universal fallback for any unknown symbol
            fallback_info = {
                'symbol': symbol,
                'type': 'UNIVERSAL',
                'pip_value': 0.0001,
                'spread_limit': 5.0,
                'min_lot': 0.01,
                'aggressiveness': 1.0
            }
            
            logger(f"📋 Symbol {symbol}: UNIVERSAL (Fallback)")
            return fallback_info
            
        except Exception as e:
            logger(f"❌ Symbol info error for {symbol}: {str(e)}")
            # Emergency fallback
            return {
                'symbol': symbol,
                'type': 'EMERGENCY_FALLBACK', 
                'pip_value': 0.0001,
                'spread_limit': 10.0,
                'min_lot': 0.01,
                'aggressiveness': 0.8
            }

    def calculate_pip_value(self, symbol: str, price: float = None) -> float:
        """Calculate pip value for any symbol"""
        try:
            info = self.get_symbol_info(symbol)
            base_pip = info['pip_value']
            
            # Special handling for JPY pairs
            if 'JPY' in symbol.upper():
                return 0.01
            
            # Special handling for crypto
            if info['type'].startswith('CRYPTO'):
                if 'BTC' in symbol.upper():
                    return 1.0
                elif 'ETH' in symbol.upper():
                    return 0.1
                else:
                    return 0.001
            
            # Special handling for metals
            if info['type'] == 'METALS':
                if 'XAU' in symbol.upper():  # Gold
                    return 0.01
                elif 'XAG' in symbol.upper():  # Silver
                    return 0.001
            
            return base_pip
            
        except Exception as e:
            logger(f"❌ Pip value calculation error: {str(e)}")
            return 0.0001  # Safe default

    def get_spread_limit(self, symbol: str) -> float:
        """Get spread limit for any symbol"""
        try:
            info = self.get_symbol_info(symbol)
            return info['spread_limit']
        except:
            return 5.0  # Conservative default

    def get_aggressiveness_factor(self, symbol: str) -> float:
        """Get aggressiveness factor for any symbol"""
        try:
            info = self.get_symbol_info(symbol)
            return info['aggressiveness']
        except:
            return 1.0  # Neutral default

    def get_minimum_lot_size(self, symbol: str) -> float:
        """Get minimum lot size for any symbol"""
        try:
            info = self.get_symbol_info(symbol)
            return info['min_lot']
        except:
            return 0.01  # Standard default

    def is_symbol_supported(self, symbol: str) -> bool:
        """Check if symbol is supported (always True for universal support)"""
        try:
            # Universal support - we support ALL symbols
            info = self.get_symbol_info(symbol)
            return info['type'] != 'EMERGENCY_FALLBACK'
        except:
            return True  # Always support everything

    def get_supported_symbols(self) -> List[str]:
        """Get list of explicitly supported symbols"""
        return list(self.symbol_database.keys())

    def validate_symbol_for_trading(self, symbol: str, spread: float = None, 
                                  price: float = None) -> Dict[str, Any]:
        """Comprehensive symbol validation for trading"""
        try:
            info = self.get_symbol_info(symbol)
            
            validation_result = {
                'symbol': symbol,
                'is_valid': True,
                'symbol_type': info['type'],
                'spread_ok': True,
                'confidence': 100,
                'warnings': [],
                'trading_allowed': True
            }
            
            # Spread validation
            if spread is not None:
                spread_limit = info['spread_limit']
                spread_pips = spread / info['pip_value']
                
                if spread_pips > spread_limit:
                    validation_result['spread_ok'] = False
                    validation_result['confidence'] = max(40, int(100 - (spread_pips - spread_limit) * 10))
                    validation_result['warnings'].append(f"Wide spread: {spread_pips:.1f} pips (limit: {spread_limit})")
                    
                    if spread_pips > spread_limit * 3:  # Extremely wide spread
                        validation_result['trading_allowed'] = False
                        validation_result['warnings'].append("Spread too wide for safe trading")
            
            # Additional validations based on symbol type
            if info['type'] == 'CRYPTO_ALT' and not validation_result['warnings']:
                validation_result['warnings'].append("Crypto altcoin - increased volatility expected")
            
            if info['type'] == 'EMERGENCY_FALLBACK':
                validation_result['confidence'] = 60
                validation_result['warnings'].append("Unknown symbol - using fallback parameters")
            
            logger(f"✅ Symbol validation: {symbol} - {validation_result['confidence']}% confidence")
            return validation_result
            
        except Exception as e:
            logger(f"❌ Symbol validation error: {str(e)}")
            return {
                'symbol': symbol,
                'is_valid': False,
                'symbol_type': 'ERROR',
                'spread_ok': False,
                'confidence': 0,
                'warnings': [f"Validation error: {str(e)}"],
                'trading_allowed': False
            }


# Global instance for universal access
universal_symbol_manager = UniversalSymbolManager()


def get_symbol_info(symbol: str) -> Dict[str, Any]:
    """Get symbol information - Universal function"""
    return universal_symbol_manager.get_symbol_info(symbol)


def validate_symbol_for_trading(symbol: str, spread: float = None, price: float = None) -> Dict[str, Any]:
    """Validate symbol for trading - Universal function"""
    return universal_symbol_manager.validate_symbol_for_trading(symbol, spread, price)


def get_all_supported_symbols() -> List[str]:
    """Get all supported symbols"""
    return universal_symbol_manager.get_supported_symbols()


def calculate_symbol_pip_value(symbol: str, price: float = None) -> float:
    """Calculate pip value for symbol"""
    return universal_symbol_manager.calculate_pip_value(symbol, price)