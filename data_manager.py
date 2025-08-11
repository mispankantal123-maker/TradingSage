# --- Data Management Module ---
"""
Market data fetching, caching, and management
"""

import pandas as pd
import datetime
from typing import Optional, Dict, Any, List
from logger_utils import logger
from config import DEFAULT_SYMBOLS

# REAL MT5 for Windows Trading (FIXED)
try:
    import MetaTrader5 as mt5
    print("✅ Data Manager using REAL MT5 for Windows")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Data Manager using mock - NOT for real trading!")


def get_currency_conversion_rate(from_currency: str, to_currency: str) -> float:
    """Get currency conversion rate between two currencies"""
    try:
        if from_currency == to_currency:
            return 1.0
            
        # Try direct symbol first
        symbol = f"{from_currency}{to_currency}"
        tick = mt5.symbol_info_tick(symbol)
        
        if tick and tick.bid > 0:
            return tick.bid
            
        # Try inverse symbol
        inverse_symbol = f"{to_currency}{from_currency}"
        inverse_tick = mt5.symbol_info_tick(inverse_symbol)
        
        if inverse_tick and inverse_tick.bid > 0:
            return 1.0 / inverse_tick.bid
            
        # Fallback through USD
        if from_currency != "USD" and to_currency != "USD":
            usd_from = get_currency_conversion_rate(from_currency, "USD")
            usd_to = get_currency_conversion_rate("USD", to_currency)
            if usd_from > 0 and usd_to > 0:
                return usd_from * usd_to
                
        logger(f"⚠️ Cannot find conversion rate for {from_currency}/{to_currency}")
        return 1.0
        
    except Exception as e:
        logger(f"❌ Error getting conversion rate: {str(e)}")
        return 1.0


def get_symbol_data(symbol: str, timeframe=None, count: int = 500) -> Optional[pd.DataFrame]:
    """Enhanced symbol data retrieval with error handling and validation"""
    try:
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_M5  # Default 5-minute timeframe
            
        logger(f"📊 Fetching data for {symbol} ({count} bars)")
        
        # Get rates from MT5
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        
        if rates is None or len(rates) == 0:
            logger(f"❌ No data received for {symbol}")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Convert time to datetime
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
        # Validate data quality
        if len(df) < 50:
            logger(f"⚠️ Insufficient data for {symbol}: {len(df)} bars")
            return None
            
        # Add symbol info as attributes
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            df.attrs['symbol'] = symbol
            df.attrs['digits'] = symbol_info.digits
            df.attrs['point'] = symbol_info.point
            df.attrs['spread'] = getattr(symbol_info, 'spread', 0)
        
        # Basic data validation
        if df['close'].isna().any():
            logger(f"⚠️ Missing close prices in {symbol} data")
            df['close'].fillna(method='ffill', inplace=True)
            
        # Ensure OHLC logic
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        logger(f"✅ Successfully fetched {len(df)} bars for {symbol}")
        
        # Log data summary
        latest = df.iloc[-1]
        logger(f"   Latest: O={latest['open']:.5f} H={latest['high']:.5f} "
               f"L={latest['low']:.5f} C={latest['close']:.5f}")
        
        return df
        
    except Exception as e:
        logger(f"❌ Error fetching data for {symbol}: {str(e)}")
        import traceback
        logger(f"📝 Traceback: {traceback.format_exc()}")
        return None


def validate_symbol_data(symbol: str, df: pd.DataFrame) -> bool:
    """Validate symbol data quality"""
    try:
        if df is None or len(df) == 0:
            logger(f"❌ {symbol}: No data")
            return False
            
        if len(df) < 50:
            logger(f"❌ {symbol}: Insufficient data ({len(df)} bars)")
            return False
            
        # Check for required columns
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger(f"❌ {symbol}: Missing columns: {missing_cols}")
            return False
            
        # Check for null values
        null_counts = df[required_cols].isnull().sum()
        if null_counts.any():
            logger(f"⚠️ {symbol}: Null values detected: {null_counts.to_dict()}")
            
        # Check OHLC logic
        invalid_bars = (df['high'] < df['low']) | (df['high'] < df['open']) | \
                       (df['high'] < df['close']) | (df['low'] > df['open']) | \
                       (df['low'] > df['close'])
        
        if invalid_bars.any():
            invalid_count = invalid_bars.sum()
            logger(f"⚠️ {symbol}: {invalid_count} bars with invalid OHLC logic")
            
        # Check for extreme price movements (potential errors)
        price_changes = df['close'].pct_change().abs()
        extreme_moves = price_changes > 0.1  # 10% moves
        if extreme_moves.any():
            extreme_count = extreme_moves.sum()
            logger(f"⚠️ {symbol}: {extreme_count} extreme price movements detected")
            
        return True
        
    except Exception as e:
        logger(f"❌ Error validating data for {symbol}: {str(e)}")
        return False


def get_multiple_symbols_data(symbols: List[str], timeframe=None, count: int = 500) -> Dict[str, pd.DataFrame]:
    """Get data for multiple symbols efficiently"""
    try:
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_M5
            
        data_dict = {}
        successful = 0
        
        logger(f"📊 Fetching data for {len(symbols)} symbols...")
        
        for symbol in symbols:
            df = get_symbol_data(symbol, timeframe, count)
            
            if df is not None and validate_symbol_data(symbol, df):
                data_dict[symbol] = df
                successful += 1
            else:
                logger(f"⚠️ Skipping {symbol} due to data issues")
                
        logger(f"✅ Successfully loaded {successful}/{len(symbols)} symbols")
        
        return data_dict
        
    except Exception as e:
        logger(f"❌ Error getting multiple symbols data: {str(e)}")
        return {}


def update_symbol_cache(symbols: List[str] = None, force_update: bool = False) -> Dict[str, bool]:
    """Update cached symbol data"""
    try:
        if symbols is None:
            symbols = DEFAULT_SYMBOLS
            
        logger(f"🔄 Updating symbol cache for {len(symbols)} symbols...")
        
        cache_status = {}
        
        for symbol in symbols:
            try:
                # Check if symbol is available and active
                symbol_info = mt5.symbol_info(symbol)
                if not symbol_info:
                    cache_status[symbol] = False
                    logger(f"⚠️ {symbol}: Symbol not available")
                    continue
                    
                # Get fresh data
                df = get_symbol_data(symbol, mt5.TIMEFRAME_M5, 200)
                
                if df is not None and len(df) >= 50:
                    cache_status[symbol] = True
                    logger(f"✅ {symbol}: Cache updated ({len(df)} bars)")
                else:
                    cache_status[symbol] = False
                    logger(f"❌ {symbol}: Cache update failed")
                    
            except Exception as symbol_e:
                cache_status[symbol] = False
                logger(f"❌ {symbol}: Cache error - {str(symbol_e)}")
                
        successful_updates = sum(1 for status in cache_status.values() if status)
        logger(f"🔄 Cache update complete: {successful_updates}/{len(symbols)} successful")
        
        return cache_status
        
    except Exception as e:
        logger(f"❌ Error updating symbol cache: {str(e)}")
        return {}


def get_market_hours_info() -> Dict[str, Any]:
    """Get market hours information for major sessions"""
    try:
        utc_now = datetime.datetime.now()
        current_hour = utc_now.hour
        
        sessions = {
            'Asian': {
                'start_utc': 0,
                'end_utc': 9,
                'active': 0 <= current_hour <= 9,
                'major_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD']
            },
            'European': {
                'start_utc': 8,
                'end_utc': 17,
                'active': 8 <= current_hour <= 17,
                'major_pairs': ['EURUSD', 'GBPUSD', 'EURGBP']
            },
            'US': {
                'start_utc': 13,
                'end_utc': 22,
                'active': 13 <= current_hour <= 22,
                'major_pairs': ['EURUSD', 'GBPUSD', 'USDCAD']
            }
        }
        
        # Determine most active session
        active_sessions = [name for name, info in sessions.items() if info['active']]
        
        return {
            'current_utc_hour': current_hour,
            'sessions': sessions,
            'active_sessions': active_sessions,
            'is_weekend': utc_now.weekday() >= 5
        }
        
    except Exception as e:
        logger(f"❌ Error getting market hours info: {str(e)}")
        return {}


def clean_old_data_files(days_to_keep: int = 7) -> None:
    """Clean old data and log files"""
    try:
        import glob
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.timestamp()
        
        # Clean log files
        log_patterns = ['logs/*.txt', 'logs/*.log', 'csv_logs/*.csv']
        
        files_deleted = 0
        
        for pattern in log_patterns:
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_timestamp:
                        os.remove(file_path)
                        files_deleted += 1
                        logger(f"🗑️ Deleted old file: {file_path}")
                        
                except Exception as file_e:
                    logger(f"⚠️ Could not delete {file_path}: {str(file_e)}")
                    
        if files_deleted > 0:
            logger(f"🧹 Cleanup complete: {files_deleted} old files deleted")
        else:
            logger("🧹 Cleanup complete: No old files to delete")
            
    except Exception as e:
        logger(f"❌ Error cleaning old data files: {str(e)}")