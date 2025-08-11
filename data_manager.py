# --- Data Manager Module ---
"""
Market data retrieval and management - REAL MT5 DATA ONLY
"""

import datetime
import pandas as pd
from typing import Optional, Dict, List
import numpy as np
from logger_utils import logger

# SMART MT5 Connection - Real on Windows, Mock for Development
try:
    import MetaTrader5 as mt5
    print("✅ Data Manager using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Data Manager using mock for development")


def get_symbol_data(symbol: str, timeframe: str = "M1", count: int = 500) -> Optional[pd.DataFrame]:
    """Get REAL market data from MT5"""
    try:
        # Map timeframe strings to MT5 constants
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }

        mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)

        # Get REAL market data
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

        if rates is None or len(rates) == 0:
            logger(f"❌ No live data available for {symbol}")
            return None

        # Convert to DataFrame with dynamic column handling
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        # Handle different column structures (mock vs real MT5) 
        # After setting time as index, remaining columns should be processed
        remaining_cols = len(df.columns)
        if remaining_cols == 6:
            # Mock MT5 format after time index: open, high, low, close, tick_volume, real_volume
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'real_volume']
        elif remaining_cols == 5:
            # Standard MT5 format: open, high, low, close, tick_volume  
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume']
        elif remaining_cols == 7:
            # Extended format: includes spread and real_volume
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        else:
            # Fallback - ensure minimum required columns
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume'] + [f'col_{i}' for i in range(5, remaining_cols)]

        logger(f"📊 Retrieved {len(df)} live bars for {symbol} ({timeframe})")
        return df

    except Exception as e:
        logger(f"❌ Error getting live data for {symbol}: {str(e)}")
        return None


def get_multiple_symbols_data(symbols: List[str], timeframe: str = "M1", count: int = 500) -> Dict[str, pd.DataFrame]:
    """Get REAL data for multiple symbols"""
    try:
        symbol_data = {}

        for symbol in symbols:
            df = get_symbol_data(symbol, timeframe, count)
            if df is not None:
                symbol_data[symbol] = df

        logger(f"📈 Retrieved live data for {len(symbol_data)}/{len(symbols)} symbols")
        return symbol_data

    except Exception as e:
        logger(f"❌ Error getting multiple symbols data: {str(e)}")
        return {}


def get_current_price(symbol: str) -> Optional[Dict[str, float]]:
    """Get current LIVE prices"""
    try:
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger(f"❌ No live tick for {symbol}")
            return None

        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'time': tick.time
        }

    except Exception as e:
        logger(f"❌ Error getting live price for {symbol}: {str(e)}")
        return None


def get_market_info(symbol: str) -> Optional[Dict[str, any]]:
    """Get REAL market information"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ No market info for {symbol}")
            return None

        return {
            'symbol': symbol_info.name,
            'digits': symbol_info.digits,
            'point': symbol_info.point,
            'spread': symbol_info.spread,
            'trade_contract_size': symbol_info.trade_contract_size,
            'trade_tick_value': symbol_info.trade_tick_value,
            'trade_tick_size': symbol_info.trade_tick_size,
            'minimum_volume': symbol_info.volume_min,
            'maximum_volume': symbol_info.volume_max,
            'volume_step': symbol_info.volume_step,
            'trade_stops_level': symbol_info.trade_stops_level
        }

    except Exception as e:
        logger(f"❌ Error getting market info for {symbol}: {str(e)}")
        return None


def validate_symbol_data(df: pd.DataFrame) -> bool:
    """Validate REAL market data quality"""
    try:
        if df is None or len(df) == 0:
            return False

        required_columns = ['open', 'high', 'low', 'close', 'tick_volume']
        if not all(col in df.columns for col in required_columns):
            return False

        # Check for valid OHLC data
        if not all(df['high'] >= df['low']):
            return False

        if not all((df['high'] >= df['open']) & (df['high'] >= df['close'])):
            return False

        if not all((df['low'] <= df['open']) & (df['low'] <= df['close'])):
            return False

        # Check for reasonable price movements (no extreme gaps)
        price_changes = df['close'].pct_change().abs()
        if (price_changes > 0.1).any():  # 10% single bar movement
            logger("⚠️ Extreme price movement detected in live data")

        return True

    except Exception as e:
        logger(f"❌ Error validating live data: {str(e)}")
        return False


def get_session_info() -> Dict[str, any]:
    """Get current trading session info"""
    try:
        now = datetime.datetime.now()
        hour = now.hour

        # Determine trading session
        if 0 <= hour < 6:
            session = "Asian"
        elif 6 <= hour < 14:
            session = "European"
        elif 14 <= hour < 22:
            session = "US"
        else:
            session = "Asian"

        return {
            'session': session,
            'hour': hour,
            'timestamp': now,
            'is_trading_hours': True  # 24/7 for forex
        }

    except Exception as e:
        logger(f"❌ Error getting session info: {str(e)}")
        return {'session': 'Unknown', 'hour': 0, 'is_trading_hours': True}


def calculate_volatility(df: pd.DataFrame, period: int = 14) -> float:
    """Calculate market volatility from REAL data"""
    try:
        if df is None or len(df) < period:
            return 0.0

        # Calculate Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]

        return atr if not np.isnan(atr) else 0.0

    except Exception as e:
        logger(f"❌ Error calculating volatility: {str(e)}")
        return 0.0


def get_spread_info(symbol: str) -> Dict[str, float]:
    """Get REAL spread information"""
    try:
        tick = mt5.symbol_info_tick(symbol)
        symbol_info = mt5.symbol_info(symbol)

        if not tick or not symbol_info:
            return {'spread_points': 0, 'spread_pips': 0}

        spread_points = tick.ask - tick.bid
        spread_pips = spread_points / symbol_info.point

        return {
            'spread_points': spread_points,
            'spread_pips': spread_pips,
            'bid': tick.bid,
            'ask': tick.ask
        }

    except Exception as e:
        logger(f"❌ Error getting spread info for {symbol}: {str(e)}")
        return {'spread_points': 0, 'spread_pips': 0}