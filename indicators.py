# --- Technical Indicators Module ---
"""
Technical analysis indicators and calculations
"""

import pandas as pd
import numpy as np
from logger_utils import logger
from typing import Any


def calculate_indicators(df: Any) -> Any:
    """Enhanced technical indicators calculation with comprehensive market analysis"""
    try:
        # Skip problematic bot running check that was causing failures

        if df is None or len(df) < 20:
            logger("⚠️ Insufficient data for indicator calculation")
            return None

        # Core EMA indicators with optimized periods for each strategy
        df['EMA8'] = df['close'].ewm(span=8, adjust=False).mean()  # Additional EMA for better signals
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA100'] = df['close'].ewm(span=100, adjust=False).mean()
        df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()

        # Price position relative to EMAs
        df['price_above_ema20'] = df['close'] > df['EMA20']
        df['price_above_ema50'] = df['close'] > df['EMA50']
        df['price_above_ema200'] = df['close'] > df['EMA200']

        # EMA slopes for trend strength
        df['ema20_slope'] = df['EMA20'].diff()
        df['ema50_slope'] = df['EMA50'].diff()

        # WMA calculations
        def wma(series, period):
            weights = np.arange(1, period + 1)
            return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

        df['WMA8'] = wma(df['close'], 8)
        df['WMA14'] = wma(df['close'], 14)
        df['WMA21'] = wma(df['close'], 21)

        # RSI calculation with multiple periods
        df['RSI'] = calculate_rsi(df['close'], 14)
        df['RSI_fast'] = calculate_rsi(df['close'], 7)  # Faster RSI for scalping
        df['RSI_slow'] = calculate_rsi(df['close'], 21)  # Slower RSI for trends

        # RSI overbought/oversold levels
        df['RSI_oversold'] = df['RSI'] < 30
        df['RSI_overbought'] = df['RSI'] > 70
        df['RSI_neutral'] = (df['RSI'] >= 30) & (df['RSI'] <= 70)

        # MACD with enhanced parameters
        df['MACD'], df['MACD_signal'], df['MACD_histogram'] = macd_enhanced(
            df['close'], fast=12, slow=26, signal=9)

        # MACD signals
        df['MACD_bullish'] = (df['MACD'] > df['MACD_signal']) & (df['MACD_histogram'] > 0)
        df['MACD_bearish'] = (df['MACD'] < df['MACD_signal']) & (df['MACD_histogram'] < 0)

        # Stochastic
        df['%K'], df['%D'] = stochastic_enhanced(df, k_period=14, d_period=3)
        df['stoch_oversold'] = df['%K'] < 20
        df['stoch_overbought'] = df['%K'] > 80

        # ATR for volatility
        df['ATR'] = atr(df, period=14)
        df['ATR_fast'] = atr(df, period=7)  # Faster ATR for scalping

        # Bollinger Bands
        df['BB_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']

        # Price position relative to Bollinger Bands
        df['price_above_bb_upper'] = df['close'] > df['BB_upper']
        df['price_below_bb_lower'] = df['close'] < df['BB_lower']
        df['price_near_bb_middle'] = abs(df['close'] - df['BB_middle']) / df['BB_middle'] < 0.002

        # Volume analysis (if available)
        if 'tick_volume' in df.columns:
            df['volume_ma'] = df['tick_volume'].rolling(20).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_ma']

        # Trend indicators
        df['uptrend'] = (df['EMA8'] > df['EMA20']) & (df['EMA20'] > df['EMA50'])
        df['downtrend'] = (df['EMA8'] < df['EMA20']) & (df['EMA20'] < df['EMA50'])

        # Combined signals
        df['strong_buy'] = (df['uptrend'] &
                           (df['RSI'] > 50) &
                           (df['MACD'] > df['MACD_signal']))
        df['strong_sell'] = (df['downtrend'] &
                            (df['RSI'] < 50) &
                            (df['MACD'] < df['MACD_signal']))

        return df

    except Exception as e:
        logger(f"❌ Error calculating indicators: {str(e)}")
        return df


def calculate_rsi(data, period=14):
    """RSI calculation with proper numpy array handling"""
    try:
        import pandas as pd
        import numpy as np

        if len(data) < period:
            return [None] * len(data)

        # Ensure data is pandas Series
        if not isinstance(data, pd.Series):
            data = pd.Series(data)

        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Handle division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            rs = gain / loss
            rs = rs.fillna(0)  # Replace NaN with 0

        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # Replace NaN with neutral 50

    except Exception as e:
        logger(f"❌ RSI calculation error: {str(e)}")
        return [50] * len(data)  # Return neutral RSI on error


def macd_enhanced(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Calculate MACD with signal line and histogram"""
    try:
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line.fillna(0), signal_line.fillna(0), histogram.fillna(0)
    except Exception as e:
        logger(f"❌ Error calculating MACD: {str(e)}")
        return pd.Series([0] * len(series)), pd.Series([0] * len(series)), pd.Series([0] * len(series))


def stochastic_enhanced(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple:
    """Calculate Stochastic oscillator"""
    try:
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent.fillna(50), d_percent.fillna(50)
    except Exception as e:
        logger(f"❌ Error calculating Stochastic: {str(e)}")
        return pd.Series([50] * len(df)), pd.Series([50] * len(df))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range with enhanced error handling"""
    try:
        import pandas as pd
        import numpy as np

        if len(df) < period:
            return pd.Series([None] * len(df))

        # Ensure required columns exist
        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                logger(f"❌ Missing column '{col}' for ATR calculation")
                return pd.Series([0.001] * len(df))  # Return small default ATR

        high = pd.Series(df['high']).astype(float)
        low = pd.Series(df['low']).astype(float)
        close = pd.Series(df['close']).astype(float)

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        # Handle NaN values
        tr1 = tr1.fillna(0)
        tr2 = tr2.fillna(0)
        tr3 = tr3.fillna(0)

        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr_series = tr.rolling(window=period, min_periods=1).mean()

        # Fill any remaining NaN with small positive values
        atr_series = atr_series.fillna(0.001)

        return atr_series

    except Exception as e:
        logger(f"❌ ATR calculation error: {str(e)}")
        return pd.Series([0.001] * len(df))  # Return small default ATR


def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    """Calculate support and resistance levels"""
    try:
        # Use rolling windows to find local highs and lows
        highs = df['high'].rolling(window, center=True).max()
        lows = df['low'].rolling(window, center=True).min()

        # Find resistance (local highs)
        resistance_levels = []
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == highs.iloc[i]:
                resistance_levels.append(df['high'].iloc[i])

        # Find support (local lows)
        support_levels = []
        for i in range(window, len(df) - window):
            if df['low'].iloc[i] == lows.iloc[i]:
                support_levels.append(df['low'].iloc[i])

        # Get most relevant levels (recent and significant)
        if resistance_levels:
            resistance = sorted(resistance_levels[-10:])[-3:]  # Last 3 significant resistance
        else:
            resistance = [df['high'].iloc[-20:].max()]

        if support_levels:
            support = sorted(support_levels[-10:])[:3]  # Last 3 significant support
        else:
            support = [df['low'].iloc[-20:].min()]

        return {
            'resistance': resistance,
            'support': support,
            'current_price': df['close'].iloc[-1]
        }

    except Exception as e:
        logger(f"❌ Error calculating support/resistance: {str(e)}")
        return {
            'resistance': [df['high'].iloc[-20:].max()],
            'support': [df['low'].iloc[-20:].min()],
            'current_price': df['close'].iloc[-1]
        }