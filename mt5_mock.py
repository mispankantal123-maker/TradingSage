# --- Mock MetaTrader5 Module for Testing ---
"""
Mock implementation of MetaTrader5 for cross-platform testing
This allows development and testing on non-Windows platforms
"""

import random
import datetime
import os
from typing import Optional, List, Any, NamedTuple
from logger_utils import logger


class SymbolInfo(NamedTuple):
    name: str
    visible: bool = True
    digits: int = 5
    point: float = 0.00001
    trade_stops_level: int = 10
    trade_mode: int = 4  # SYMBOL_TRADE_MODE_FULL


class TickInfo(NamedTuple):
    time: int
    bid: float
    ask: float
    last: float = 0.0
    volume: int = 100


class AccountInfo(NamedTuple):
    login: int = 12345678
    server: str = "MockServer-Live"
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    margin_free: float = 10000.0
    margin_level: float = 0.0
    currency: str = "USD"
    trade_allowed: bool = True
    leverage: int = 100
    profit: float = 0.0


class TerminalInfo(NamedTuple):
    name: str = "MetaTrader 5 (Mock)"
    path: str = "/mock/terminal"
    build: int = 4400
    connected: bool = True


class Position(NamedTuple):
    ticket: int
    symbol: str
    type: int  # 0=BUY, 1=SELL
    volume: float
    price_open: float
    price_current: float
    profit: float
    comment: str = "Mock Position"


# Global state for mock
_connected = False
_symbols_data = {}
_positions = []
_last_error = (0, "No error")


def initialize(path: str = None) -> bool:
    """Mock MT5 initialization"""
    global _connected
    _connected = True
    logger("🎯 Mock MT5 initialized successfully")
    
    # Initialize some default symbols
    default_symbols = {
        "EURUSD": {"bid": 1.0850, "ask": 1.0852, "digits": 5, "point": 0.00001},
        "GBPUSD": {"bid": 1.2650, "ask": 1.2652, "digits": 5, "point": 0.00001},
        "USDJPY": {"bid": 149.50, "ask": 149.52, "digits": 3, "point": 0.01},
        "XAUUSD": {"bid": 2020.50, "ask": 2021.00, "digits": 2, "point": 0.01},
        "AUDUSD": {"bid": 0.6750, "ask": 0.6752, "digits": 5, "point": 0.00001},
        "USDCAD": {"bid": 1.3450, "ask": 1.3452, "digits": 5, "point": 0.00001}
    }
    
    for symbol, data in default_symbols.items():
        _symbols_data[symbol] = data
    
    return True


def shutdown():
    """Mock MT5 shutdown"""
    global _connected
    _connected = False
    logger("🎯 Mock MT5 shutdown")


def terminal_info() -> Optional[TerminalInfo]:
    """Mock terminal info"""
    if not _connected:
        return None
    return TerminalInfo()


def account_info() -> Optional[AccountInfo]:
    """Mock account info"""
    if not _connected:
        return None
    return AccountInfo()


def symbol_info(symbol: str) -> Optional[SymbolInfo]:
    """Mock symbol info"""
    if not _connected or symbol not in _symbols_data:
        return None
    
    data = _symbols_data[symbol]
    return SymbolInfo(
        name=symbol,
        digits=data["digits"],
        point=data["point"]
    )


def symbol_info_tick(symbol: str) -> Optional[TickInfo]:
    """Mock symbol tick info with realistic price movements"""
    if not _connected or symbol not in _symbols_data:
        return None
    
    data = _symbols_data[symbol]
    base_bid = data["bid"]
    base_ask = data["ask"]
    
    # Add small random price movement
    price_change = random.uniform(-0.001, 0.001)  # ±0.1%
    current_bid = base_bid + (base_bid * price_change)
    current_ask = base_ask + (base_ask * price_change)
    
    # Update stored prices for next call
    data["bid"] = current_bid
    data["ask"] = current_ask
    
    return TickInfo(
        time=int(datetime.datetime.now().timestamp()),
        bid=round(current_bid, data["digits"]),
        ask=round(current_ask, data["digits"]),
        last=round((current_bid + current_ask) / 2, data["digits"]),
        volume=random.randint(50, 200)
    )


def symbols_get() -> Optional[List[SymbolInfo]]:
    """Mock symbols list"""
    if not _connected:
        return None
    
    symbols = []
    for symbol_name in _symbols_data.keys():
        data = _symbols_data[symbol_name]
        symbols.append(SymbolInfo(
            name=symbol_name,
            digits=data["digits"],
            point=data["point"]
        ))
    
    return symbols


def symbol_select(symbol: str, enable: bool = True) -> bool:
    """Mock symbol selection"""
    if not _connected:
        return False
    
    if symbol in _symbols_data:
        logger(f"🎯 Mock: Symbol {symbol} {'enabled' if enable else 'disabled'}")
        return True
    return False


def copy_rates_from_pos(symbol: str, timeframe, start_pos: int, count: int) -> Optional[List]:
    """Mock historical data generation"""
    if not _connected or symbol not in _symbols_data:
        return None
    
    # Generate realistic OHLC data
    data = _symbols_data[symbol]
    base_price = (data["bid"] + data["ask"]) / 2
    
    rates = []
    current_price = base_price
    
    for i in range(count):
        # Generate realistic OHLC with some volatility
        price_change = random.uniform(-0.002, 0.002)  # ±0.2%
        open_price = current_price
        
        high_offset = random.uniform(0, 0.001)
        low_offset = random.uniform(-0.001, 0)
        close_offset = random.uniform(-0.001, 0.001)
        
        high_price = open_price + (open_price * high_offset)
        low_price = open_price + (open_price * low_offset)
        close_price = open_price + (open_price * close_offset)
        
        # Ensure OHLC logic
        high_price = max(open_price, high_price, low_price, close_price)
        low_price = min(open_price, high_price, low_price, close_price)
        
        rates.append({
            'time': int(datetime.datetime.now().timestamp()) - (count - i) * 60,
            'open': round(open_price, data["digits"]),
            'high': round(high_price, data["digits"]),
            'low': round(low_price, data["digits"]),
            'close': round(close_price, data["digits"]),
            'tick_volume': random.randint(50, 500),
            'real_volume': 0
        })
        
        current_price = close_price
    
    return rates


def order_send(request: dict) -> dict:
    """Mock order sending"""
    if not _connected:
        return {"retcode": 10004, "comment": "Not connected"}
    
    # Simulate successful order
    ticket = random.randint(100000, 999999)
    
    logger(f"🎯 Mock Order Sent: {request.get('action')} {request.get('symbol')} "
           f"{request.get('volume')} lots at {request.get('price', 'market')}")
    
    return {
        "retcode": 10009,  # TRADE_RETCODE_DONE
        "deal": ticket,
        "order": ticket,
        "volume": request.get("volume", 0.01),
        "price": request.get("price", 0.0),
        "bid": 0.0,
        "ask": 0.0,
        "comment": "Mock order executed",
        "request_id": random.randint(1000, 9999),
        "retcode_external": 0
    }


def positions_get(symbol: str = None) -> Optional[List[Position]]:
    """Mock positions"""
    if not _connected:
        return None
    
    # Return empty list for mock (no open positions)
    return []


def orders_get(symbol: str = None) -> Optional[List]:
    """Mock pending orders"""
    if not _connected:
        return None
    
    # Return empty list for mock (no pending orders)
    return []


def last_error() -> tuple:
    """Mock last error"""
    return _last_error


# Timeframe constants
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 60
TIMEFRAME_H4 = 240
TIMEFRAME_D1 = 1440

# Order types
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5

# Trade operations
TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8

# Order filling modes
ORDER_FILLING_FOK = 0
ORDER_FILLING_IOC = 1
ORDER_FILLING_RETURN = 2

# Order time types - CRITICAL FIX: These were missing!
ORDER_TIME_GTC = 0  # Good Till Cancelled
ORDER_TIME_DAY = 1  # Good for Day
ORDER_TIME_SPECIFIED = 2  # Good Till Specified Time
ORDER_TIME_SPECIFIED_DAY = 3  # Good Till Specified Day