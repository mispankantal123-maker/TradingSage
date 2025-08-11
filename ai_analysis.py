# --- AI Market Analysis Module ---
"""
Advanced AI-powered market analysis and pattern recognition
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from logger_utils import logger


def ai_market_analysis(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Advanced AI market analysis with pattern recognition and sentiment scoring"""
    try:
        if len(df) < 50:
            return {
                'recommendation': 'INSUFFICIENT_DATA',
                'confidence': 0,
                'signals': [],
                'risk_level': 'HIGH'
            }
        
        # Initialize scoring system
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        # Get recent data
        recent_data = df.tail(20)
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. TREND ANALYSIS with AI-like scoring
        trend_signals = analyze_trend_patterns(recent_data)
        bullish_score += trend_signals['bullish']
        bearish_score += trend_signals['bearish']
        signals.extend(trend_signals['signals'])
        
        # 2. MOMENTUM ANALYSIS
        momentum_signals = analyze_momentum_patterns(recent_data)
        bullish_score += momentum_signals['bullish']
        bearish_score += momentum_signals['bearish']
        signals.extend(momentum_signals['signals'])
        
        # 3. VOLATILITY ANALYSIS
        volatility_signals = analyze_volatility_patterns(recent_data)
        bullish_score += volatility_signals['bullish']
        bearish_score += volatility_signals['bearish']
        signals.extend(volatility_signals['signals'])
        
        # 4. PATTERN RECOGNITION
        pattern_signals = recognize_chart_patterns(recent_data)
        bullish_score += pattern_signals['bullish']
        bearish_score += pattern_signals['bearish']
        signals.extend(pattern_signals['signals'])
        
        # 5. SUPPORT/RESISTANCE ANALYSIS
        sr_signals = analyze_support_resistance(df)
        bullish_score += sr_signals['bullish']
        bearish_score += sr_signals['bearish']
        signals.extend(sr_signals['signals'])
        
        # 6. VOLUME ANALYSIS (if available)
        if 'tick_volume' in df.columns:
            volume_signals = analyze_volume_patterns(recent_data)
            bullish_score += volume_signals['bullish']
            bearish_score += volume_signals['bearish']
            signals.extend(volume_signals['signals'])
        
        # Calculate final recommendation
        total_score = bullish_score + bearish_score
        if total_score == 0:
            recommendation = 'NEUTRAL'
            confidence = 0
        else:
            bullish_ratio = bullish_score / total_score
            bearish_ratio = bearish_score / total_score
            
            if bullish_ratio > 0.6:
                recommendation = 'BULLISH'
                confidence = int(bullish_ratio * 100)
            elif bearish_ratio > 0.6:
                recommendation = 'BEARISH'
                confidence = int(bearish_ratio * 100)
            else:
                recommendation = 'NEUTRAL'
                confidence = int(abs(bullish_ratio - bearish_ratio) * 50)
        
        # Risk assessment
        if confidence >= 80:
            risk_level = 'LOW'
        elif confidence >= 60:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        # Market regime detection
        regime = detect_market_regime(df)
        
        result = {
            'recommendation': recommendation,
            'confidence': confidence,
            'signals': signals[:10],  # Top 10 signals
            'risk_level': risk_level,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'market_regime': regime,
            'analysis_timestamp': pd.Timestamp.now().strftime('%H:%M:%S')
        }
        
        logger(f"🤖 AI Analysis for {symbol}: {recommendation} ({confidence}% confidence)")
        
        return result
        
    except Exception as e:
        logger(f"❌ AI analysis error for {symbol}: {str(e)}")
        return {
            'recommendation': 'ERROR',
            'confidence': 0,
            'signals': [f"Analysis error: {str(e)}"],
            'risk_level': 'HIGH'
        }


def analyze_trend_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze trend patterns with AI-like scoring"""
    try:
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # EMA trend analysis
        if 'EMA20' in last and 'EMA50' in last:
            if last['EMA20'] > last['EMA50']:
                if last['close'] > last['EMA20']:
                    bullish_score += 2
                    signals.append("Strong uptrend: Price above EMA20 > EMA50")
                else:
                    bullish_score += 1
                    signals.append("Uptrend: EMA20 > EMA50, price testing trend")
            else:
                if last['close'] < last['EMA20']:
                    bearish_score += 2
                    signals.append("Strong downtrend: Price below EMA20 < EMA50")
                else:
                    bearish_score += 1
                    signals.append("Downtrend: EMA20 < EMA50, price testing trend")
        
        # Price action trend
        recent_highs = df['high'].tail(5)
        recent_lows = df['low'].tail(5)
        
        if recent_highs.is_monotonic_increasing:
            bullish_score += 1
            signals.append("Higher highs pattern detected")
        elif recent_highs.is_monotonic_decreasing:
            bearish_score += 1
            signals.append("Lower highs pattern detected")
            
        if recent_lows.is_monotonic_increasing:
            bullish_score += 1
            signals.append("Higher lows pattern detected")
        elif recent_lows.is_monotonic_decreasing:
            bearish_score += 1
            signals.append("Lower lows pattern detected")
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Trend analysis error: {str(e)}")
        return {'bullish': 0, 'bearish': 0, 'signals': []}


def analyze_momentum_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze momentum indicators with AI scoring"""
    try:
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # RSI momentum
        if 'RSI' in last:
            if 30 < last['RSI'] < 70:  # Healthy range
                if last['RSI'] > prev['RSI'] and last['RSI'] > 50:
                    bullish_score += 1
                    signals.append("RSI increasing in bullish zone")
                elif last['RSI'] < prev['RSI'] and last['RSI'] < 50:
                    bearish_score += 1
                    signals.append("RSI declining in bearish zone")
        
        # MACD momentum
        if 'MACD_histogram' in last:
            if last['MACD_histogram'] > prev['MACD_histogram']:
                if last['MACD_histogram'] > 0:
                    bullish_score += 1
                    signals.append("MACD histogram increasing (bullish)")
                else:
                    bearish_score -= 1  # Reducing bearish momentum
                    signals.append("MACD histogram recovering")
            else:
                if last['MACD_histogram'] < 0:
                    bearish_score += 1
                    signals.append("MACD histogram declining (bearish)")
                else:
                    bullish_score -= 1  # Reducing bullish momentum
                    signals.append("MACD histogram weakening")
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Momentum analysis error: {str(e)}")
        return {'bullish': 0, 'bearish': 0, 'signals': []}


def analyze_volatility_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze volatility patterns"""
    try:
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        # ATR analysis
        if 'ATR' in df.columns:
            recent_atr = df['ATR'].tail(5)
            atr_trend = recent_atr.diff().sum()
            
            if atr_trend > 0:
                signals.append("Volatility increasing - potential breakout")
                # Increasing volatility can be bullish or bearish
                bullish_score += 0.5
                bearish_score += 0.5
            else:
                signals.append("Volatility decreasing - consolidation phase")
        
        # Bollinger Band squeeze detection
        if 'BB_width' in df.columns:
            bb_width = df['BB_width'].iloc[-1]
            avg_bb_width = df['BB_width'].tail(20).mean()
            
            if bb_width < avg_bb_width * 0.8:
                signals.append("Bollinger Band squeeze - breakout pending")
                bullish_score += 0.5
                bearish_score += 0.5
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Volatility analysis error: {str(e)}")
        return {'bullish': 0, 'bearish': 0, 'signals': []}


def recognize_chart_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Basic chart pattern recognition"""
    try:
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        if len(df) < 10:
            return {'bullish': 0, 'bearish': 0, 'signals': []}
        
        recent_prices = df['close'].tail(10)
        
        # Simple pattern detection
        # Double bottom pattern (simplified)
        lows = df['low'].tail(10)
        if len(lows) >= 5:
            min_indices = lows.nsmallest(2).index
            if len(min_indices) >= 2:
                if abs(lows[min_indices[0]] - lows[min_indices[1]]) < lows.mean() * 0.01:
                    bullish_score += 1
                    signals.append("Potential double bottom pattern")
        
        # Simple support/resistance breaks
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        current_price = df['close'].iloc[-1]
        
        if current_price > recent_high * 0.999:  # Close to breaking high
            bullish_score += 1
            signals.append("Price testing resistance - potential breakout")
        elif current_price < recent_low * 1.001:  # Close to breaking low
            bearish_score += 1
            signals.append("Price testing support - potential breakdown")
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Pattern recognition error: {str(e)}")
        return {'bullish': 0, 'bearish': 0, 'signals': []}


def analyze_support_resistance(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze support and resistance levels"""
    try:
        from indicators import calculate_support_resistance
        
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        sr_levels = calculate_support_resistance(df)
        current_price = sr_levels['current_price']
        
        # Check proximity to support/resistance
        for resistance in sr_levels['resistance']:
            distance_pct = abs(current_price - resistance) / current_price
            if distance_pct < 0.005:  # Within 0.5%
                if current_price > resistance:
                    bullish_score += 1
                    signals.append(f"Broke resistance at {resistance:.5f}")
                else:
                    bearish_score += 0.5
                    signals.append(f"Approaching resistance at {resistance:.5f}")
        
        for support in sr_levels['support']:
            distance_pct = abs(current_price - support) / current_price
            if distance_pct < 0.005:  # Within 0.5%
                if current_price < support:
                    bearish_score += 1
                    signals.append(f"Broke support at {support:.5f}")
                else:
                    bullish_score += 0.5
                    signals.append(f"Holding above support at {support:.5f}")
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Support/Resistance analysis error: {str(e)}")
        return {'bullish': 0, 'bearish': 0, 'signals': []}


def analyze_volume_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze volume patterns if available"""
    try:
        bullish_score = 0
        bearish_score = 0
        signals = []
        
        if 'volume_ratio' in df.columns:
            last_volume_ratio = df['volume_ratio'].iloc[-1]
            price_change = df['close'].iloc[-1] - df['close'].iloc[-2]
            
            if last_volume_ratio > 1.5:  # High volume
                if price_change > 0:
                    bullish_score += 1
                    signals.append("High volume on price increase")
                else:
                    bearish_score += 1
                    signals.append("High volume on price decrease")
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Volume analysis error: {str(e)}")
        return {'bullish': 0, 'bearish': 0, 'signals': []}


def detect_market_regime(df: pd.DataFrame) -> str:
    """Detect current market regime (trending, ranging, volatile)"""
    try:
        if len(df) < 20:
            return 'INSUFFICIENT_DATA'
        
        # Calculate regime indicators
        recent_data = df.tail(20)
        price_range = recent_data['high'].max() - recent_data['low'].min()
        avg_price = recent_data['close'].mean()
        range_pct = price_range / avg_price
        
        # Trend strength
        trend_slope = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / len(recent_data)
        trend_strength = abs(trend_slope) / avg_price
        
        # Volatility measure
        if 'ATR' in recent_data.columns:
            volatility = recent_data['ATR'].mean() / avg_price
        else:
            volatility = recent_data['close'].std() / avg_price
        
        # Classify regime
        if trend_strength > 0.001 and volatility > 0.01:
            regime = 'TRENDING_VOLATILE'
        elif trend_strength > 0.001:
            regime = 'TRENDING'
        elif volatility > 0.015:
            regime = 'VOLATILE_RANGING'
        elif range_pct < 0.02:
            regime = 'LOW_VOLATILITY_RANGING'
        else:
            regime = 'RANGING'
        
        return regime
        
    except Exception as e:
        logger(f"❌ Market regime detection error: {str(e)}")
        return 'UNKNOWN'