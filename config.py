# --- Configuration Module ---
"""
Configuration constants and settings for the trading bot
"""

# Trading Strategies
STRATEGIES = ["Scalping", "Intraday", "Arbitrage", "HFT"]

# Default Trading Parameters
DEFAULT_PARAMS = {
    "Scalping": {
        "tp_pips": "20",
        "sl_pips": "10",
        "tp_unit": "pips",
        "sl_unit": "pips",
        "lot_size": "0.01"
    },
    "Intraday": {
        "tp_pips": "50",
        "sl_pips": "25",
        "tp_unit": "pips",
        "sl_unit": "pips",
        "lot_size": "0.02"
    },
    "Arbitrage": {
        "tp_pips": "10",
        "sl_pips": "5",
        "tp_unit": "pips",
        "sl_unit": "pips",
        "lot_size": "0.05"
    },
    "HFT": {
        "tp_pips": "5",
        "sl_pips": "3",
        "tp_unit": "pips",
        "sl_unit": "pips",
        "lot_size": "0.01"
    }
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

# Symbol Settings
DEFAULT_SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD"]
PRECIOUS_METALS = ["XAU", "XAG", "GOLD", "SILVER"]
FOREX_MAJORS = ["EUR", "GBP", "USD", "JPY", "AUD", "CAD", "CHF", "NZD"]

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