"""
MT5 Mock Library for Development and Testing
This provides simulation for MT5 functionality when running on non-Windows platforms
"""
import random
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import numpy as np

# Mock MT5 Constants
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_H1 = 60

ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5

TRADE_ACTION_DEAL = 1
TRADE_RETCODE_DONE = 10009

SYMBOL_TRADE_MODE_FULL = 0
SYMBOL_TRADE_MODE_CLOSEONLY = 1
SYMBOL_TRADE_MODE_DISABLED = 3

class MockAccountInfo:
    def __init__(self):
        self.login = 12345678
        self.balance = 1000000.0  # 1M IDR
        self.equity = 1000000.0
        self.margin = 0.0
        self.margin_free = 1000000.0  # Fix missing attribute
        self.free_margin = 1000000.0  
        self.currency = "IDR"
        self.leverage = 100
        self.profit = 0.0
        self.margin_level = 0.0
        self.credit = 0.0
        self.margin_so_mode = 0
        self.margin_so_call = 50.0
        self.margin_so_so = 30.0

class MockSymbolInfo:
    def __init__(self, symbol_name: str):
        self.name = symbol_name
        self.visible = True
        self.trade_mode = SYMBOL_TRADE_MODE_FULL
        self.volume_min = 0.01
        self.volume_max = 100.0
        self.volume_step = 0.01
        self.point = 0.00001 if "JPY" not in symbol_name else 0.001
        self.trade_contract_size = 100000.0 if symbol_name.startswith("XAU") else 100000.0
        self.digits = 5 if "JPY" not in symbol_name else 3

class MockTick:
    def __init__(self, symbol_name: str):
        # Generate realistic price data based on symbol
        if symbol_name == "EURUSD":
            self.bid = round(random.uniform(1.0800, 1.1200), 5)
            self.ask = round(self.bid + 0.00020, 5)
        elif symbol_name == "XAUUSD" or symbol_name == "XAUUSDm":
            self.bid = round(random.uniform(1950.00, 2050.00), 2)
            self.ask = round(self.bid + 0.50, 2)
        elif symbol_name == "BTCUSD" or symbol_name == "BTCUSDm":
            self.bid = round(random.uniform(42000, 48000), 2)
            self.ask = round(self.bid + 50.0, 2)
        else:
            # Generic forex pair
            self.bid = round(random.uniform(1.2000, 1.3000), 5)
            self.ask = round(self.bid + 0.00020, 5)
        
        self.time = int(time.time())
        self.last = self.ask
        self.volume = random.randint(1, 100)

class MockRate:
    def __init__(self):
        base_price = random.uniform(1.1000, 1.1200)
        self.time = int(time.time())
        self.open = round(base_price + random.uniform(-0.0050, 0.0050), 5)
        self.high = round(self.open + random.uniform(0, 0.0030), 5)
        self.low = round(self.open - random.uniform(0, 0.0030), 5)
        self.close = round(random.uniform(self.low, self.high), 5)
        self.tick_volume = random.randint(100, 1000)
        self.spread = 20
        self.real_volume = 0

# Mock MT5 Functions
def initialize(path: str = "", login: int = 0, password: str = "", server: str = "", timeout: int = 10000, portable: bool = False) -> bool:
    """Mock MT5 initialize"""
    print(f"🎭 MOCK: MT5 initialized (development mode)")
    return True

def shutdown():
    """Mock MT5 shutdown"""
    print("🎭 MOCK: MT5 shutdown")
    return True

def login(login: int, password: str = "", server: str = "") -> bool:
    """Mock MT5 login"""
    print(f"🎭 MOCK: MT5 login successful - Account: {login}")
    return True

def account_info() -> Optional[MockAccountInfo]:
    """Mock account info"""
    return MockAccountInfo()

def terminal_info():
    """Mock terminal info"""
    return {
        'community_account': False,
        'community_connection': False,
        'connected': True,
        'dlls_allowed': True,
        'trade_allowed': True,
        'tradeapi_disabled': False,
        'email_enabled': False,
        'ftp_enabled': False,
        'notifications_enabled': False,
        'mqid': False,
        'build': 3540,
        'maxbars': 100000,
        'codepage': 1251,
        'ping_last': 123456,
        'community_balance': 0.0,
        'retransmission': 0.0,
        'company': 'Mock Broker Ltd',
        'name': 'MetaTrader 5',
        'language': 1033,
        'path': 'C:\\Program Files\\MetaTrader 5',
        'data_path': 'C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\Mock',
        'commondata_path': 'C:\\ProgramData\\MetaQuotes\\Terminal\\Common'
    }

def version() -> tuple:
    """Mock MT5 version"""
    return (500, 3540, "10 Aug 2025")

def symbol_info(symbol: str) -> Optional[MockSymbolInfo]:
    """Mock symbol info"""
    if symbol in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAUUSDm", "BTCUSD", "BTCUSDm"]:
        return MockSymbolInfo(symbol)
    return None

def symbol_info_tick(symbol: str) -> Optional[MockTick]:
    """Mock symbol tick"""
    if symbol_info(symbol):
        return MockTick(symbol)
    return None

def symbols_get() -> List[MockSymbolInfo]:
    """Mock symbols get"""
    common_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAUUSDm", "BTCUSD", "BTCUSDm", "USDCAD", "AUDUSD"]
    return [MockSymbolInfo(symbol) for symbol in common_symbols]

def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[np.ndarray]:
    """Mock historical rates"""
    if not symbol_info(symbol):
        return None
    
    # Generate mock historical data
    rates = []
    base_time = int(time.time()) - (count * timeframe * 60)
    
    for i in range(count):
        rate = MockRate()
        rate.time = base_time + (i * timeframe * 60)
        rates.append(rate)
    
    # Convert to numpy structured array to match MT5 format
    dt = np.dtype([
        ('time', 'i8'),
        ('open', 'f8'),
        ('high', 'f8'),
        ('low', 'f8'),
        ('close', 'f8'),
        ('tick_volume', 'i8'),
        ('spread', 'i4'),
        ('real_volume', 'i8')
    ])
    
    return np.array([(r.time, r.open, r.high, r.low, r.close, r.tick_volume, r.spread, r.real_volume) 
                     for r in rates], dtype=dt)

def positions_get() -> List:
    """Mock positions get"""
    # Return empty list (no open positions)
    return []

def orders_send(request: dict) -> dict:
    """Mock order send"""
    print(f"🎭 MOCK: Order sent - {request.get('action')} {request.get('symbol')} {request.get('volume')} lots")
    
    # Simulate random success/failure
    success = random.random() > 0.1  # 90% success rate
    
    if success:
        return {
            'retcode': TRADE_RETCODE_DONE,
            'deal': random.randint(100000, 999999),
            'order': random.randint(100000, 999999),
            'volume': request.get('volume', 0.01),
            'price': request.get('price', 1.1000),
            'comment': 'Mock trade executed',
            'request_id': random.randint(1000, 9999),
            'retcode_external': 0
        }
    else:
        return {
            'retcode': 10004,  # TRADE_RETCODE_REQUOTE
            'comment': 'Mock trade failed (requote)',
            'request_id': random.randint(1000, 9999)
        }

def orders_get() -> List:
    """Mock pending orders get"""
    return []

def history_deals_get() -> List:
    """Mock history deals"""
    return []

def history_orders_get() -> List:  
    """Mock history orders"""
    return []

# Export all mock functions to match MT5 API
__all__ = [
    'initialize', 'shutdown', 'login', 'account_info', 'terminal_info', 'version',
    'symbol_info', 'symbol_info_tick', 'symbols_get', 'copy_rates_from_pos',
    'positions_get', 'orders_send', 'orders_get', 'history_deals_get', 'history_orders_get',
    'TIMEFRAME_M1', 'TIMEFRAME_M5', 'TIMEFRAME_M15', 'TIMEFRAME_H1',
    'ORDER_TYPE_BUY', 'ORDER_TYPE_SELL', 'ORDER_TYPE_BUY_LIMIT', 'ORDER_TYPE_SELL_LIMIT',
    'ORDER_TYPE_BUY_STOP', 'ORDER_TYPE_SELL_STOP',
    'TRADE_ACTION_DEAL', 'TRADE_RETCODE_DONE',
    'SYMBOL_TRADE_MODE_FULL', 'SYMBOL_TRADE_MODE_CLOSEONLY', 'SYMBOL_TRADE_MODE_DISABLED'
]