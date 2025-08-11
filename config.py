# --- Configuration Module ---
"""
Configuration constants and settings for the trading bot
"""

# Trading Strategies
STRATEGIES = ["Scalping", "Intraday", "Arbitrage", "HFT"]

# Default Trading Parameters with Enhanced Options
DEFAULT_PARAMS = {
    "Scalping": {
        "tp_pips": "20",
        "sl_pips": "10", 
        "tp_unit": "pips",
        "sl_unit": "pips",
        "lot_size": "0.01",
        "signal_threshold": 2,
        "min_spread": 0.5,
        "max_spread": 5.0
    },
    "Intraday": {
        "tp_pips": "50",
        "sl_pips": "25",
        "tp_unit": "pips", 
        "sl_unit": "pips",
        "lot_size": "0.02",
        "signal_threshold": 3,
        "min_spread": 0.8,
        "max_spread": 8.0
    },
    "Arbitrage": {
        "tp_pips": "10",
        "sl_pips": "5",
        "tp_unit": "pips",
        "sl_unit": "pips", 
        "lot_size": "0.05",
        "signal_threshold": 2,
        "min_spread": 0.3,
        "max_spread": 3.0
    },
    "HFT": {
        "tp_pips": "5",
        "sl_pips": "3",
        "tp_unit": "pips",
        "sl_unit": "pips",
        "lot_size": "0.01",
        "signal_threshold": 3,
        "min_spread": 0.2,
        "max_spread": 2.0
    }
}

# TP/SL Unit Options - Enhanced with percentage support
TP_SL_UNITS = ["pips", "points", "price", "balance%", "equity%"]

# Balance percentage settings
BALANCE_PERCENTAGE_SETTINGS = {
    "min_percentage": 0.1,  # 0.1% minimum
    "max_percentage": 10.0, # 10% maximum
    "default_tp_percentage": 2.0,  # 2% default TP
    "default_sl_percentage": 1.0   # 1% default SL
}

# GUI Settings
GUI_UPDATE_INTERVAL = 1500  # milliseconds

# Risk Management
MAX_RISK_PERCENTAGE = 2.0
MAX_DAILY_TRADES = 50
MAX_OPEN_POSITIONS = 10

# Trading Sessions (UTC)
TRADING_SESSIONS = {
    "Asian": {"start": 0, "end": 9},
    "European": {"start": 8, "end": 17},
    "US": {"start": 13, "end": 22},
    "Pacific": {"start": 21, "end": 6}
}

# News Times (UTC) - High impact news to avoid
CRITICAL_NEWS_TIMES = [
    (8, 30, 9, 30),   # European session major news
    (12, 30, 14, 30), # US session major news (NFP, CPI, FOMC, etc)
    (16, 0, 16, 30),  # London Fix
]

# Symbol Settings - Comprehensive symbol support
DEFAULT_SYMBOLS = [
    # Forex Majors
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP",
    
    # Precious Metals with different suffixes
    "XAUUSD", "XAUUSDm", "XAUUSDc", "GOLD", "GOLDm", "XAGUSD", "XAGUSDm", "SILVER", "SILVERm",
    
    # Cryptocurrency
    "BTCUSD", "BTCUSDm", "BTCUSDc", "ETHUSD", "ETHUSDm", "LTCUSD", "LTCUSDm", "XRPUSD", "XRPUSDm",
    
    # Commodities & Oil
    "USOIL", "USOILm", "UKOIL", "UKOILm", "NGAS", "NGASm", 
    
    # Stock Indices
    "US30", "US30m", "US500", "US500m", "NAS100", "NAS100m", "GER30", "GER30m", "UK100", "UK100m", "JPN225", "JPN225m",
    
    # Exotic Pairs
    "USDZAR", "USDMXN", "USDTRY", "USDHKD", "USDSGD", "AUDCAD", "AUDJPY", "AUDNZD", "CADCHF", "CADJPY", "CHFJPY",
    
    # Cross Pairs
    "EURAUD", "EURCAD", "EURCHF", "EURNZD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY"
]

PRECIOUS_METALS = ["XAU", "XAG", "GOLD", "SILVER", "PLATINUM", "PALLADIUM"]
FOREX_MAJORS = ["EUR", "GBP", "USD", "JPY", "AUD", "CAD", "CHF", "NZD"]
CRYPTO_SYMBOLS = ["BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "LINK"]
COMMODITY_SYMBOLS = ["OIL", "USOIL", "UKOIL", "NGAS", "WHEAT", "CORN", "SUGAR"]
INDEX_SYMBOLS = ["US30", "US500", "NAS100", "GER30", "UK100", "JPN225", "AUS200", "FRA40"]

# Spread Limits (pips)
SPREAD_LIMITS = {
    "default": 5.0,
    "jpy": 8.0,
    "precious": 100.0
}

# Logging
LOG_DIR = "logs"
CSV_DIR = "csv_logs"

# Performance Tracking
PERFORMANCE_METRICS = [
    "total_trades",
    "winning_trades", 
    "losing_trades",
    "total_profit",
    "max_drawdown",
    "win_rate"
]