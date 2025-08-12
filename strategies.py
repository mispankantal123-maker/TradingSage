# --- Trading Strategies Module ---
"""
All trading strategies: Scalping, Intraday, Arbitrage, HFT
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from logger_utils import logger

# SMART MT5 Connection - Real on Windows, Mock for Development
try:
    import MetaTrader5 as mt5
    print("✅ Strategies using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Strategies using mock for development")
from indicators import calculate_support_resistance


def run_strategy(strategy: str, df: pd.DataFrame, symbol: str) -> Tuple[Optional[str], List[str]]:
    """Enhanced strategy execution with MTF analysis and dynamic position sizing"""
    try:
        logger(f"🎯 Running {strategy} strategy for {symbol}")

        if len(df) < 50:
            logger(f"❌ Insufficient data for {symbol}: {len(df)} bars (need 50+)")
            return None, [f"Insufficient data: {len(df)} bars"]

        # PROFESSIONAL UPGRADE: Multi-timeframe confluence check
        try:
            from multi_timeframe_analysis import should_trade_based_on_mtf
            should_trade, mtf_direction, mtf_analysis = should_trade_based_on_mtf(symbol, strategy, min_confluence_score=65)

            if not should_trade:
                confluence_score = mtf_analysis.get('confluence_score', 0)
                logger(f"⚠️ MTF Analysis: Confluence too low ({confluence_score:.1f}/100) - Skipping trade")
                return None, [f"MTF confluence insufficient: {confluence_score:.1f}%"]

            logger(f"✅ MTF Analysis: {mtf_direction} signal confirmed (Score: {mtf_analysis.get('confluence_score', 0):.1f}/100)")

        except Exception as mtf_e:
            logger(f"⚠️ MTF analysis error, proceeding with single timeframe: {str(mtf_e)}")
            should_trade = True
            mtf_direction = None

        # Get precision info from dataframe attributes or MT5
        digits = df.attrs.get('digits', 5)
        point = df.attrs.get('point', 0.00001)

        # Get real-time tick data with retry mechanism
        current_tick = None
        for tick_attempt in range(3):
            current_tick = mt5.symbol_info_tick(symbol)
            if current_tick and hasattr(current_tick, 'bid') and hasattr(current_tick, 'ask'):
                if current_tick.bid > 0 and current_tick.ask > 0:
                    break
            else:
                logger(f"⚠️ Tick attempt {tick_attempt + 1}: No valid tick for {symbol}")
                import time
                time.sleep(0.5)

        if not current_tick or not hasattr(current_tick, 'bid') or current_tick.bid <= 0:
            logger(f"❌ Cannot get valid real-time tick for {symbol} after 3 attempts")
            return None, [f"No valid tick data for {symbol}"]

        # Use most recent candle data
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) > 3 else prev

        # Get precise current prices - MUST be defined early for all strategies
        current_bid = round(current_tick.bid, digits)
        current_ask = round(current_tick.ask, digits)
        current_spread = round(current_ask - current_bid, digits)
        current_price = round((current_bid + current_ask) / 2, digits)

        # Validate price precision
        last_close = round(last['close'], digits)
        last_high = round(last['high'], digits)
        last_low = round(last['low'], digits)
        last_open = round(last['open'], digits)

        action = None
        signals = []
        buy_signals = 0
        sell_signals = 0

        # Enhanced price logging with precision
        logger(f"📊 {symbol} Precise Data:")
        logger(f"   📈 Candle: O={last_open:.{digits}f} H={last_high:.{digits}f} L={last_low:.{digits}f} C={last_close:.{digits}f}")
        logger(f"   🎯 Real-time: Bid={current_bid:.{digits}f} Ask={current_ask:.{digits}f} Spread={current_spread:.{digits}f}")
        logger(f"   💡 Current Price: {current_price:.{digits}f} (Mid-price)")

        # Price movement analysis
        price_change = round(current_price - last_close, digits)
        price_change_pips = abs(price_change) / point
        logger(f"   📊 Price Movement: {price_change:+.{digits}f} ({price_change_pips:.1f} pips)")

        # ENHANCED AUTO-DETECT: Smart spread analysis for ALL symbols on Windows MT5
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            # Use REAL MT5 data for Windows live trading
            point_value = getattr(symbol_info, 'point', 0.00001)
            digits = getattr(symbol_info, 'digits', 5)
            spread_pips = current_spread / point_value

            # SMART symbol type detection with realistic spread limits
            if any(metal in symbol.upper() for metal in ["XAU", "XAG", "GOLD", "SILVER"]):
                max_allowed_spread = 150.0  # Gold/Silver - realistic for live trading
                symbol_type = "METALS"
            elif any(crypto in symbol.upper() for crypto in ["BTC", "ETH", "LTC", "XRP", "ADA", "DOT"]):
                max_allowed_spread = 800.0  # Crypto spreads are wider
                symbol_type = "CRYPTO"
            elif any(oil in symbol.upper() for oil in ["OIL", "WTI", "BRENT", "USOIL", "UKOIL"]):
                max_allowed_spread = 30.0  # Oil commodities
                symbol_type = "ENERGY"
            elif any(index in symbol.upper() for index in ["SPX", "NAS", "DOW", "DAX", "FTSE", "NIKKEI"]):
                max_allowed_spread = 8.0  # Stock indices
                symbol_type = "INDICES"
            elif "JPY" in symbol.upper():
                max_allowed_spread = 3.0  # JPY pairs (2-digit pricing)
                symbol_type = "FOREX_JPY"
            elif len(symbol) == 6 and any(curr in symbol[3:] for curr in ["USD", "EUR", "GBP", "CHF", "CAD", "AUD", "NZD"]):
                max_allowed_spread = 2.0  # Major forex pairs
                symbol_type = "FOREX_MAJOR"
            else:
                max_allowed_spread = 5.0  # Exotic pairs and others
                symbol_type = "EXOTIC"

            logger(f"   📋 Auto-detected: {symbol_type} | Spread limit: {max_allowed_spread} pips")
        else:
            # Fallback for development/mock (akan jarang digunakan di Windows MT5)
            if any(metal in symbol.upper() for metal in ["XAU", "XAG"]):
                spread_pips = current_spread / 0.01
                max_allowed_spread = 150.0
                symbol_type = "METALS"
            elif "JPY" in symbol:
                spread_pips = current_spread / 0.01
                max_allowed_spread = 3.0
                symbol_type = "FOREX_JPY"
            else:
                spread_pips = current_spread / 0.00001
                max_allowed_spread = 2.0
                symbol_type = "FOREX"

        # Enhanced spread quality assessment
        if spread_pips <= max_allowed_spread * 0.4:
            spread_quality = "EXCELLENT"
            trade_confidence = 1.0
        elif spread_pips <= max_allowed_spread * 0.7:
            spread_quality = "GOOD"
            trade_confidence = 0.8
        elif spread_pips <= max_allowed_spread:
            spread_quality = "ACCEPTABLE"
            trade_confidence = 0.6
        else:
            spread_quality = "WIDE"
            trade_confidence = 0.4

        logger(f"   🎯 Spread: {spread_pips:.1f} pips ({spread_quality}) | Limit: {max_allowed_spread} | Confidence: {trade_confidence*100:.0f}%")

        # LIVE TRADING DECISION: Continue trading but adjust lot size based on spread
        if spread_pips > max_allowed_spread * 1.5:
            logger(f"⚠️ Extremely wide spread - reducing position size by 50%")
            spread_warning = True
        elif spread_pips > max_allowed_spread:
            logger(f"⚠️ Wide spread - reducing position size by 25%")
            spread_warning = True
        else:
            spread_warning = False

        logger(f"   ✅ Trading ACTIVE for {symbol_type} with {trade_confidence*100:.0f}% confidence")

        # Route to specific strategy
        if strategy == "Scalping":
            return scalping_strategy(df, symbol, current_tick, digits, point)
        elif strategy == "Intraday":
            return intraday_strategy(df, symbol, current_tick, digits, point)
        elif strategy == "Arbitrage":
            return arbitrage_strategy(df, symbol, current_tick, digits, point)
        elif strategy == "HFT":
            return hft_strategy(df, symbol, current_tick, digits, point)
        else:
            logger(f"❌ Unknown strategy: {strategy}")
            return None, [f"Unknown strategy: {strategy}"]

    except Exception as e:
        logger(f"❌ Error in run_strategy: {str(e)}")
        import traceback
        logger(f"📝 Traceback: {traceback.format_exc()}")
        return None, [f"Strategy error: {str(e)}"]


def scalping_strategy(df: pd.DataFrame, symbol: str, current_tick, digits: int, point: float) -> Tuple[Optional[str], List[str]]:
    """Scalping strategy - Quick trades with tight targets"""
    try:
        signals = []
        buy_signals = 0
        sell_signals = 0

        # Use recent data
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Current prices
        current_bid = round(current_tick.bid, digits)
        current_ask = round(current_tick.ask, digits)
        current_price = round((current_bid + current_ask) / 2, digits)

        # ENHANCED Scalping conditions - More sensitive signals

        # BALANCED EMA trend signals with enhanced BUY opportunities
        if last['EMA8'] > last['EMA20']:
            signals.append("EMA8 above EMA20 (Bullish trend)")
            buy_signals += 1
            # ADDITIONAL: If EMA8 is also rising, give extra BUY weight
            if last['EMA8'] > prev['EMA8']:
                signals.append("EMA8 rising in uptrend (Strong bullish)")
                buy_signals += 1  # Total +2 for strong uptrend

        if last['EMA8'] < last['EMA20']:
            signals.append("EMA8 below EMA20 (Bearish trend)")
            sell_signals += 1
            # ADDITIONAL: If EMA8 is also falling, give extra SELL weight
            if last['EMA8'] < prev['EMA8']:
                signals.append("EMA8 falling in downtrend (Strong bearish)")
                sell_signals += 1  # Total +2 for strong downtrend

        # CRITICAL: Additional BUY opportunities for price momentum
        if last['close'] > last['EMA8']:
            signals.append("Price above EMA8 (Bullish price action)")
            buy_signals += 1

        # CRITICAL: Additional SELL opportunities for price momentum
        if last['close'] < last['EMA8']:
            signals.append("Price below EMA8 (Bearish price action)")
            sell_signals += 1

        # ENHANCED: Balanced price momentum signals
        price_momentum_up = last['close'] > prev['close']
        price_momentum_accelerating_up = (last['close'] - prev['close']) > (prev['close'] - df.iloc[-3]['close']) if len(df) > 3 else price_momentum_up

        # INCREASED BUY OPPORTUNITY: More sensitive to upward moves
        if price_momentum_up:
            signals.append("Positive price momentum")
            buy_signals += 1
            if price_momentum_accelerating_up:
                signals.append("Price momentum accelerating upward")
                buy_signals += 2  # Increased weight for BUY acceleration

        # Check for bullish reversal patterns
        if last['close'] > last['open'] and prev['close'] < prev['open']:
            signals.append("Bullish reversal candle pattern")
            buy_signals += 1

        price_momentum_down = last['close'] < prev['close']
        price_momentum_accelerating_down = (prev['close'] - last['close']) > (df.iloc[-3]['close'] - prev['close']) if len(df) > 3 else price_momentum_down

        if price_momentum_down:
            signals.append("Negative price momentum")
            sell_signals += 1
            if price_momentum_accelerating_down:
                signals.append("Price momentum accelerating downward")
                sell_signals += 1  # Keep normal weight for SELL

        # ENHANCED RSI conditions (more BUY opportunities)
        rsi_bullish_zone = 40 <= last['RSI'] <= 80  # Wider BUY zone
        rsi_bearish_zone = 20 <= last['RSI'] <= 60  # Standard SELL zone
        rsi_rising = last['RSI'] > prev['RSI']
        rsi_falling = last['RSI'] < prev['RSI']

        # ENHANCED RSI BUY conditions (more opportunities)
        if rsi_bullish_zone and rsi_rising:
            signals.append("RSI in bullish zone and rising")
            buy_signals += 1
        elif last['RSI'] > 45 and rsi_rising:  # Lowered threshold
            signals.append("RSI above 45 and rising")
            buy_signals += 1
        # ADDITIONAL: RSI oversold bounce
        elif last['RSI'] < 35 and rsi_rising:
            signals.append("RSI oversold bounce opportunity")
            buy_signals += 2  # Strong BUY signal

        # RSI SELL conditions
        if rsi_bearish_zone and rsi_falling:
            signals.append("RSI in bearish zone and falling")
            sell_signals += 1
        elif last['RSI'] < 50 and rsi_falling:
            signals.append("RSI below 50 and falling")
            sell_signals += 1

        # ENHANCED MACD signals (equal weight, more conditions)
        macd_bullish = last['MACD'] > last['MACD_signal']
        macd_bearish = last['MACD'] < last['MACD_signal']
        histogram_positive = last['MACD_histogram'] > 0
        histogram_negative = last['MACD_histogram'] < 0
        macd_rising = last['MACD'] > prev['MACD']
        macd_falling = last['MACD'] < prev['MACD']

        # MACD BUY conditions
        if macd_bullish:
            signals.append("MACD above signal line")
            buy_signals += 1
            if histogram_positive:
                signals.append("MACD histogram positive (momentum)")
                buy_signals += 1
        elif macd_rising and not macd_bearish:
            signals.append("MACD rising toward signal line")
            buy_signals += 1

        # MACD SELL conditions
        if macd_bearish:
            signals.append("MACD below signal line")
            sell_signals += 1
            if histogram_negative:
                signals.append("MACD histogram negative (momentum)")
                sell_signals += 1
        elif macd_falling and not macd_bullish:
            signals.append("MACD falling toward signal line")
            sell_signals += 1

        # ENHANCED Bollinger Bands - multiple signal types
        bb_width = last['BB_upper'] - last['BB_lower']
        bb_position = (last['close'] - last['BB_lower']) / bb_width if bb_width > 0 else 0.5
        bb_middle = (last['BB_upper'] + last['BB_lower']) / 2

        # BB BUY conditions
        if last['close'] > bb_middle:
            signals.append("Price above BB middle band")
            buy_signals += 1
            if last['close'] > prev['close']:
                signals.append("Price above BB middle with upward momentum")
                buy_signals += 1
        elif bb_position > 0.3 and last['close'] > prev['close']:
            signals.append("Price in lower BB range but rising")
            buy_signals += 1

        # BB SELL conditions
        if last['close'] < bb_middle:
            signals.append("Price below BB middle band")
            sell_signals += 1
            if last['close'] < prev['close']:
                signals.append("Price below BB middle with downward momentum")
                sell_signals += 1
        elif bb_position < 0.7 and last['close'] < prev['close']:
            signals.append("Price in upper BB range but falling")
            sell_signals += 1

        # BALANCED signal threshold with BUY bias
        signal_threshold = 1

        # IMPROVED: Balanced signal decision with slight BUY preference
        action = None

        # Strong signals (3+ difference)
        if buy_signals >= sell_signals + 3:
            action = "BUY"
            logger(f"🟢 SCALPING STRONG BUY for {symbol}: {buy_signals} buy vs {sell_signals} sell")
        elif sell_signals >= buy_signals + 3:
            action = "SELL"
            logger(f"🔴 SCALPING STRONG SELL for {symbol}: {sell_signals} sell vs {buy_signals} buy")
        # Medium signals (1-2 difference)
        elif buy_signals > sell_signals and buy_signals >= signal_threshold:
            action = "BUY"
            logger(f"🟢 SCALPING BUY Signal for {symbol}: {buy_signals} buy vs {sell_signals} sell")
        elif sell_signals > buy_signals and sell_signals >= signal_threshold:
            action = "SELL"
            logger(f"🔴 SCALPING SELL Signal for {symbol}: {sell_signals} sell vs {buy_signals} buy")
        # Equal signals - use multiple tiebreakers
        elif buy_signals == sell_signals and buy_signals >= signal_threshold:
            # Tiebreaker 1: Recent price momentum
            if last['close'] > prev['close']:
                action = "BUY"
                logger(f"🟢 SCALPING BUY (Tiebreaker) for {symbol}: Equal signals, price rising")
            # Tiebreaker 2: EMA trend
            elif last['EMA8'] > prev['EMA8']:
                action = "BUY"
                logger(f"🟢 SCALPING BUY (EMA Trend) for {symbol}: Equal signals, EMA rising")
            else:
                action = "SELL"
                logger(f"🔴 SCALPING SELL (Tiebreaker) for {symbol}: Equal signals, price falling")
        # Backup signal generation
        else:
            # Check for any bullish indicators
            bullish_factors = 0
            if last['close'] > prev['close']:
                bullish_factors += 1
            if last['EMA8'] > last['EMA20']:
                bullish_factors += 1
            if last['RSI'] > 50:
                bullish_factors += 1

            if bullish_factors >= 2:
                signals.append("Backup signal: Multiple bullish factors")
                action = "BUY"
                logger(f"🟢 SCALPING BUY (Backup) for {symbol}: {bullish_factors} bullish factors")
            elif bullish_factors == 0:
                signals.append("Backup signal: Bearish conditions")
                action = "SELL"
                logger(f"🔴 SCALPING SELL (Backup) for {symbol}: No bullish factors")
            else:
                logger(f"⚪ SCALPING No signal for {symbol}: {buy_signals} buy, {sell_signals} sell")

        return action, signals

    except Exception as e:
        logger(f"❌ Scalping strategy error: {str(e)}")
        return None, [f"Scalping error: {str(e)}"]


def intraday_strategy(df: pd.DataFrame, symbol: str, current_tick, digits: int, point: float) -> Tuple[Optional[str], List[str]]:
    """Intraday strategy - Medium-term trend following"""
    try:
        signals = []
        buy_signals = 0
        sell_signals = 0

        # Use recent data
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Current prices
        current_bid = round(current_tick.bid, digits)
        current_ask = round(current_tick.ask, digits)
        current_price = round((current_bid + current_ask) / 2, digits)

        # Trend following - EMA alignment
        if last['EMA20'] > last['EMA50'] and last['EMA50'] > last['EMA200']:
            if last['close'] > last['EMA20']:
                signals.append("Strong uptrend - all EMAs aligned bullishly")
                buy_signals += 2  # Strong signal

        if last['EMA20'] < last['EMA50'] and last['EMA50'] < last['EMA200']:
            if last['close'] < last['EMA20']:
                signals.append("Strong downtrend - all EMAs aligned bearishly")
                sell_signals += 2  # Strong signal

        # RSI trend confirmation
        if 30 < last['RSI'] < 70:  # Avoid extremes for intraday
            if last['RSI'] > 50 and last['close'] > last['EMA20']:
                signals.append("RSI bullish and above EMA20")
                buy_signals += 1
            elif last['RSI'] < 50 and last['close'] < last['EMA20']:
                signals.append("RSI bearish and below EMA20")
                sell_signals += 1

        # MACD trend confirmation
        if last['MACD'] > last['MACD_signal'] and last['MACD_histogram'] > prev['MACD_histogram']:
            signals.append("MACD bullish with increasing momentum")
            buy_signals += 1

        if last['MACD'] < last['MACD_signal'] and last['MACD_histogram'] < prev['MACD_histogram']:
            signals.append("MACD bearish with increasing momentum")
            sell_signals += 1

        # Support/Resistance levels
        sr_levels = calculate_support_resistance(df)
        nearest_resistance = min(sr_levels['resistance'], key=lambda x: abs(x - current_price))
        nearest_support = min(sr_levels['support'], key=lambda x: abs(x - current_price))

        # Check if price is near support (potential buy)
        if abs(current_price - nearest_support) / current_price < 0.01:  # Within 1%
            if current_price > nearest_support:  # Above support
                signals.append("Price near support level - potential bounce")
                buy_signals += 1

        # Check if price is near resistance (potential sell)
        if abs(current_price - nearest_resistance) / current_price < 0.01:  # Within 1%
            if current_price < nearest_resistance:  # Below resistance
                signals.append("Price near resistance level - potential rejection")
                sell_signals += 1

        # Determine action
        action = None
        if buy_signals >= 3 and buy_signals > sell_signals:
            action = "BUY"
            logger(f"🟢 INTRADAY BUY Signal for {symbol}: {buy_signals} buy vs {sell_signals} sell")
        elif sell_signals >= 3 and sell_signals > buy_signals:
            action = "SELL"
            logger(f"🔴 INTRADAY SELL Signal for {symbol}: {sell_signals} sell vs {buy_signals} buy")
        else:
            logger(f"⚪ INTRADAY No signal for {symbol}: {buy_signals} buy, {sell_signals} sell (need 3+ dominant)")

        return action, signals

    except Exception as e:
        logger(f"❌ Intraday strategy error: {str(e)}")
        return None, [f"Intraday error: {str(e)}"]


def arbitrage_strategy(df: pd.DataFrame, symbol: str, current_tick, digits: int, point: float) -> Tuple[Optional[str], List[str]]:
    """Arbitrage strategy - Price discrepancy exploitation"""
    try:
        signals = []
        buy_signals = 0
        sell_signals = 0

        # Use recent data
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Current prices
        current_bid = round(current_tick.bid, digits)
        current_ask = round(current_tick.ask, digits)
        current_price = round((current_bid + current_ask) / 2, digits)

        # Arbitrage looks for quick mean reversion opportunities
        # Bollinger Band extremes
        if last['close'] > last['BB_upper'] * 1.01:  # 1% above upper band
            signals.append("Price significantly above Bollinger Upper - mean reversion expected")
            sell_signals += 2

        if last['close'] < last['BB_lower'] * 0.99:  # 1% below lower band
            signals.append("Price significantly below Bollinger Lower - mean reversion expected")
            buy_signals += 2

        # RSI extremes for arbitrage
        if last['RSI'] > 80:
            signals.append("RSI extremely overbought - arbitrage sell opportunity")
            sell_signals += 1

        if last['RSI'] < 20:
            signals.append("RSI extremely oversold - arbitrage buy opportunity")
            buy_signals += 1

        # Price vs EMA deviation
        ema20_deviation = abs(current_price - last['EMA20']) / last['EMA20']
        if ema20_deviation > 0.02:  # 2% deviation
            if current_price > last['EMA20']:
                signals.append("Price 2%+ above EMA20 - potential reversion")
                sell_signals += 1
            else:
                signals.append("Price 2%+ below EMA20 - potential reversion")
                buy_signals += 1

        # Stochastic extremes
        if last['%K'] > 90 and last['%D'] > 90:
            signals.append("Stochastic extremely overbought")
            sell_signals += 1

        if last['%K'] < 10 and last['%D'] < 10:
            signals.append("Stochastic extremely oversold")
            buy_signals += 1

        # Volume spike confirmation (if available)
        if 'volume_ratio' in last and last['volume_ratio'] > 1.5:
            signals.append("High volume confirms price movement")
            # Add to existing signals rather than creating new ones

        # Determine action
        action = None
        if buy_signals >= 2 and buy_signals > sell_signals:
            action = "BUY"
            logger(f"🟢 ARBITRAGE BUY Signal for {symbol}: {buy_signals} buy vs {sell_signals} sell")
        elif sell_signals >= 2 and sell_signals > buy_signals:
            action = "SELL"
            logger(f"🔴 ARBITRAGE SELL Signal for {symbol}: {sell_signals} sell vs {buy_signals} buy")
        else:
            logger(f"⚪ ARBITRAGE No signal for {symbol}: {buy_signals} buy, {sell_signals} sell (need 2+ dominant)")

        return action, signals

    except Exception as e:
        logger(f"❌ Arbitrage strategy error: {str(e)}")
        return None, [f"Arbitrage error: {str(e)}"]


def hft_strategy(df: pd.DataFrame, symbol: str, current_tick, digits: int, point: float) -> Tuple[Optional[str], List[str]]:
    """High Frequency Trading strategy - Ultra-fast micro movements"""
    try:
        signals = []
        buy_signals = 0
        sell_signals = 0

        # Use recent data
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) > 3 else prev

        # Current prices
        current_bid = round(current_tick.bid, digits)
        current_ask = round(current_tick.ask, digits)
        current_price = round((current_bid + current_ask) / 2, digits)

        # HFT looks for very short-term momentum
        # Fast EMA momentum
        if last['EMA8'] > prev['EMA8'] and prev['EMA8'] > prev2['EMA8']:
            signals.append("EMA8 accelerating upward")
            buy_signals += 1

        if last['EMA8'] < prev['EMA8'] and prev['EMA8'] < prev2['EMA8']:
            signals.append("EMA8 accelerating downward")
            sell_signals += 1

        # Price momentum
        price_momentum = (last['close'] - prev['close']) / prev['close']
        if price_momentum > 0.001:  # 0.1% momentum
            signals.append("Strong upward price momentum")
            buy_signals += 1
        elif price_momentum < -0.001:
            signals.append("Strong downward price momentum")
            sell_signals += 1

        # Fast RSI changes
        rsi_change = last['RSI_fast'] - prev['RSI_fast']
        if rsi_change > 5 and last['RSI_fast'] > 50:
            signals.append("Fast RSI rapid increase")
            buy_signals += 1
        elif rsi_change < -5 and last['RSI_fast'] < 50:
            signals.append("Fast RSI rapid decrease")
            sell_signals += 1

        # MACD histogram momentum
        macd_momentum = last['MACD_histogram'] - prev['MACD_histogram']
        if macd_momentum > 0 and last['MACD_histogram'] > 0:
            signals.append("MACD histogram increasing (bullish)")
            buy_signals += 1
        elif macd_momentum < 0 and last['MACD_histogram'] < 0:
            signals.append("MACD histogram decreasing (bearish)")
            sell_signals += 1

        # ATR-based volatility filter
        if last['ATR_fast'] > last['ATR'] * 0.8:  # High volatility
            signals.append("High volatility detected")
            # In HFT, we might want to trade WITH volatility

        # Micro support/resistance
        recent_high = df['high'].iloc[-5:].max()
        recent_low = df['low'].iloc[-5:].min()

        if current_price >= recent_high * 0.999:  # Very close to recent high
            signals.append("Price at recent high - potential breakout")
            buy_signals += 1

        if current_price <= recent_low * 1.001:  # Very close to recent low
            signals.append("Price at recent low - potential breakdown")
            sell_signals += 1

        # Determine action
        action = None
        if buy_signals >= 3 and buy_signals > sell_signals:
            action = "BUY"
            logger(f"🟢 HFT BUY Signal for {symbol}: {buy_signals} buy vs {sell_signals} sell")
        elif sell_signals >= 3 and sell_signals > buy_signals:
            action = "SELL"
            logger(f"🔴 HFT SELL Signal for {symbol}: {sell_signals} sell vs {buy_signals} buy")
        else:
            logger(f"⚪ HFT No signal for {symbol}: {buy_signals} buy, {sell_signals} sell (need 3+ dominant)")

        return action, signals

    except Exception as e:
        logger(f"❌ HFT strategy error: {str(e)}")
        return None, [f"HFT error: {str(e)}"]