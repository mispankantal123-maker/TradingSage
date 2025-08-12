# --- Enhanced Analysis Engine ---
"""
Robust analysis system untuk improve signal quality dan order execution
Advanced technical analysis dengan multi-layer validation
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from logger_utils import logger
from datetime import datetime, timedelta

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class EnhancedAnalysisEngine:
    """Professional analysis engine dengan robust signal generation"""
    
    def __init__(self):
        self.analysis_cache = {}
        self.last_analysis_time = {}
        self.signal_history = {}
        self.market_conditions = {}
        
        # Analysis parameters
        self.min_data_points = 50
        self.signal_confirmation_levels = 3
        self.volatility_threshold = 0.02
        self.trend_strength_min = 0.6
        
    def analyze_market_structure(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive market structure analysis"""
        try:
            if len(df) < self.min_data_points:
                return {"error": f"Insufficient data: {len(df)} bars"}
            
            analysis = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "data_quality": self._assess_data_quality(df),
                "trend_analysis": self._analyze_trend(df),
                "volatility_analysis": self._analyze_volatility(df),
                "momentum_analysis": self._analyze_momentum(df),
                "support_resistance": self._find_support_resistance(df),
                "market_regime": self._detect_market_regime(df),
                "signal_strength": 0
            }
            
            # Calculate overall signal strength
            analysis["signal_strength"] = self._calculate_signal_strength(analysis)
            
            # Cache analysis
            self.analysis_cache[symbol] = analysis
            self.last_analysis_time[symbol] = datetime.now()
            
            return analysis
            
        except Exception as e:
            logger(f"❌ Market structure analysis error for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality and completeness"""
        try:
            quality = {
                "total_bars": len(df),
                "missing_data": df.isnull().sum().sum(),
                "price_gaps": 0,
                "outliers": 0,
                "quality_score": 0
            }
            
            # Check for price gaps
            if len(df) > 1:
                price_changes = df['close'].pct_change().abs()
                quality["price_gaps"] = len(price_changes[price_changes > 0.05])  # 5% gaps
            
            # Check for outliers using IQR
            Q1 = df['close'].quantile(0.25)
            Q3 = df['close'].quantile(0.75)
            IQR = Q3 - Q1
            outlier_bounds = [Q1 - 1.5 * IQR, Q3 + 1.5 * IQR]
            quality["outliers"] = len(df[(df['close'] < outlier_bounds[0]) | (df['close'] > outlier_bounds[1])])
            
            # Calculate quality score (0-100)
            score = 100
            score -= min(quality["missing_data"] * 5, 30)  # Penalize missing data
            score -= min(quality["price_gaps"] * 10, 30)   # Penalize gaps
            score -= min(quality["outliers"] * 2, 20)      # Penalize outliers
            quality["quality_score"] = max(0, score)
            
            return quality
            
        except Exception as e:
            logger(f"❌ Data quality assessment error: {str(e)}")
            return {"quality_score": 0, "error": str(e)}
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced trend analysis dengan multiple timeframes"""
        try:
            trend = {
                "direction": "NEUTRAL",
                "strength": 0.0,
                "ema_trend": "NEUTRAL",
                "price_trend": "NEUTRAL",
                "trend_duration": 0,
                "trend_confidence": 0.0
            }
            
            # EMA trend analysis
            if 'EMA20' in df.columns and 'EMA50' in df.columns:
                ema20_slope = self._calculate_slope(df['EMA20'].tail(10))
                ema50_slope = self._calculate_slope(df['EMA50'].tail(10))
                
                if ema20_slope > 0 and ema50_slope > 0 and df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
                    trend["ema_trend"] = "BULLISH"
                elif ema20_slope < 0 and ema50_slope < 0 and df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]:
                    trend["ema_trend"] = "BEARISH"
            
            # Price trend analysis
            recent_prices = df['close'].tail(20)
            price_slope = self._calculate_slope(recent_prices)
            
            if price_slope > 0.001:
                trend["price_trend"] = "BULLISH"
            elif price_slope < -0.001:
                trend["price_trend"] = "BEARISH"
            
            # Overall trend determination
            bullish_signals = sum([
                trend["ema_trend"] == "BULLISH",
                trend["price_trend"] == "BULLISH",
                df['close'].iloc[-1] > df['close'].iloc[-20]  # Price above 20 bars ago
            ])
            
            bearish_signals = sum([
                trend["ema_trend"] == "BEARISH", 
                trend["price_trend"] == "BEARISH",
                df['close'].iloc[-1] < df['close'].iloc[-20]  # Price below 20 bars ago
            ])
            
            if bullish_signals >= 2:
                trend["direction"] = "BULLISH"
                trend["strength"] = bullish_signals / 3.0
            elif bearish_signals >= 2:
                trend["direction"] = "BEARISH"
                trend["strength"] = bearish_signals / 3.0
            
            # Calculate trend confidence
            trend["trend_confidence"] = trend["strength"] * 100
            
            return trend
            
        except Exception as e:
            logger(f"❌ Trend analysis error: {str(e)}")
            return {"direction": "NEUTRAL", "strength": 0.0, "error": str(e)}
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced volatility analysis"""
        try:
            volatility = {
                "current_atr": 0.0,
                "atr_percentile": 0.0,
                "volatility_regime": "NORMAL",
                "volatility_trend": "STABLE"
            }
            
            if 'ATR' in df.columns:
                current_atr = df['ATR'].iloc[-1]
                atr_series = df['ATR'].tail(50)
                
                volatility["current_atr"] = current_atr
                volatility["atr_percentile"] = (atr_series <= current_atr).mean() * 100
                
                # Volatility regime classification
                if volatility["atr_percentile"] > 80:
                    volatility["volatility_regime"] = "HIGH"
                elif volatility["atr_percentile"] < 20:
                    volatility["volatility_regime"] = "LOW"
                
                # Volatility trend
                atr_slope = self._calculate_slope(atr_series.tail(10))
                if atr_slope > 0.01:
                    volatility["volatility_trend"] = "INCREASING"
                elif atr_slope < -0.01:
                    volatility["volatility_trend"] = "DECREASING"
            
            return volatility
            
        except Exception as e:
            logger(f"❌ Volatility analysis error: {str(e)}")
            return {"volatility_regime": "NORMAL", "error": str(e)}
    
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced momentum analysis"""
        try:
            momentum = {
                "rsi_momentum": "NEUTRAL",
                "macd_momentum": "NEUTRAL", 
                "price_momentum": "NEUTRAL",
                "momentum_strength": 0.0,
                "momentum_divergence": False
            }
            
            # RSI momentum
            if 'RSI' in df.columns:
                rsi = df['RSI'].iloc[-1]
                rsi_prev = df['RSI'].iloc[-5]
                
                if rsi > 60 and rsi > rsi_prev:
                    momentum["rsi_momentum"] = "BULLISH"
                elif rsi < 40 and rsi < rsi_prev:
                    momentum["rsi_momentum"] = "BEARISH"
            
            # MACD momentum
            if 'MACD' in df.columns and 'MACD_signal' in df.columns:
                macd = df['MACD'].iloc[-1]
                macd_signal = df['MACD_signal'].iloc[-1]
                macd_prev = df['MACD'].iloc[-3]
                signal_prev = df['MACD_signal'].iloc[-3]
                
                if macd > macd_signal and macd > macd_prev:
                    momentum["macd_momentum"] = "BULLISH"
                elif macd < macd_signal and macd < macd_prev:
                    momentum["macd_momentum"] = "BEARISH"
            
            # Price momentum
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
            if price_change > 0.005:  # 0.5% change
                momentum["price_momentum"] = "BULLISH"
            elif price_change < -0.005:
                momentum["price_momentum"] = "BEARISH"
            
            # Overall momentum strength
            bullish_momentum = sum([
                momentum["rsi_momentum"] == "BULLISH",
                momentum["macd_momentum"] == "BULLISH",
                momentum["price_momentum"] == "BULLISH"
            ])
            
            bearish_momentum = sum([
                momentum["rsi_momentum"] == "BEARISH",
                momentum["macd_momentum"] == "BEARISH", 
                momentum["price_momentum"] == "BEARISH"
            ])
            
            if bullish_momentum >= 2:
                momentum["momentum_strength"] = bullish_momentum / 3.0
            elif bearish_momentum >= 2:
                momentum["momentum_strength"] = -bearish_momentum / 3.0
            
            return momentum
            
        except Exception as e:
            logger(f"❌ Momentum analysis error: {str(e)}")
            return {"momentum_strength": 0.0, "error": str(e)}
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced support and resistance detection"""
        try:
            sr_levels = {
                "support_levels": [],
                "resistance_levels": [],
                "current_level": "BETWEEN",
                "distance_to_support": 0.0,
                "distance_to_resistance": 0.0
            }
            
            # Use recent data for S/R calculation
            recent_data = df.tail(100)
            current_price = df['close'].iloc[-1]
            
            # Find local highs and lows
            from scipy.signal import argrelextrema
            
            # Local highs (resistance)
            high_indices = argrelextrema(recent_data['high'].values, np.greater, order=5)[0]
            if len(high_indices) > 0:
                resistance_levels = recent_data['high'].iloc[high_indices].values
                # Keep levels above current price
                resistance_levels = resistance_levels[resistance_levels > current_price]
                sr_levels["resistance_levels"] = sorted(resistance_levels)[:3]  # Top 3
            
            # Local lows (support)
            low_indices = argrelextrema(recent_data['low'].values, np.less, order=5)[0]
            if len(low_indices) > 0:
                support_levels = recent_data['low'].iloc[low_indices].values
                # Keep levels below current price
                support_levels = support_levels[support_levels < current_price]
                sr_levels["support_levels"] = sorted(support_levels, reverse=True)[:3]  # Top 3
            
            # Calculate distances
            if sr_levels["support_levels"]:
                nearest_support = sr_levels["support_levels"][0]
                sr_levels["distance_to_support"] = (current_price - nearest_support) / current_price * 100
            
            if sr_levels["resistance_levels"]:
                nearest_resistance = sr_levels["resistance_levels"][0]
                sr_levels["distance_to_resistance"] = (nearest_resistance - current_price) / current_price * 100
            
            return sr_levels
            
        except Exception as e:
            logger(f"❌ Support/Resistance analysis error: {str(e)}")
            return {"support_levels": [], "resistance_levels": [], "error": str(e)}
    
    def _detect_market_regime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Market regime detection (trending vs ranging)"""
        try:
            regime = {
                "regime": "RANGING",
                "regime_confidence": 0.0,
                "trend_strength": 0.0,
                "volatility_level": "NORMAL"
            }
            
            # Calculate trend strength using ADX if available
            if 'ADX' in df.columns:
                adx = df['ADX'].iloc[-1]
                if adx > 30:
                    regime["regime"] = "TRENDING"
                    regime["trend_strength"] = min(adx / 50, 1.0)  # Normalize to 0-1
                else:
                    regime["trend_strength"] = adx / 30
            
            # Alternative: Use price movement efficiency
            price_range = df['high'].tail(20).max() - df['low'].tail(20).min()
            price_movement = abs(df['close'].iloc[-1] - df['close'].iloc[-20])
            
            if price_range > 0:
                efficiency = price_movement / price_range
                if efficiency > 0.6:  # 60% efficiency suggests trending
                    regime["regime"] = "TRENDING"
                    regime["regime_confidence"] = efficiency
                else:
                    regime["regime_confidence"] = 1 - efficiency
            
            # Volatility level
            if 'ATR' in df.columns:
                atr_current = df['ATR'].iloc[-1]
                atr_average = df['ATR'].tail(50).mean()
                
                if atr_current > atr_average * 1.5:
                    regime["volatility_level"] = "HIGH"
                elif atr_current < atr_average * 0.7:
                    regime["volatility_level"] = "LOW"
            
            return regime
            
        except Exception as e:
            logger(f"❌ Market regime detection error: {str(e)}")
            return {"regime": "RANGING", "error": str(e)}
    
    def _calculate_signal_strength(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall signal strength from analysis components"""
        try:
            strength = 0.0
            
            # Data quality weight (20%)
            data_quality = analysis.get("data_quality", {}).get("quality_score", 0) / 100
            strength += data_quality * 0.2
            
            # Trend strength weight (30%)
            trend_strength = analysis.get("trend_analysis", {}).get("strength", 0)
            strength += trend_strength * 0.3
            
            # Momentum strength weight (25%)
            momentum_strength = abs(analysis.get("momentum_analysis", {}).get("momentum_strength", 0))
            strength += momentum_strength * 0.25
            
            # Volatility appropriateness weight (15%)
            volatility = analysis.get("volatility_analysis", {})
            if volatility.get("volatility_regime") == "NORMAL":
                strength += 0.15
            elif volatility.get("volatility_regime") in ["HIGH", "LOW"]:
                strength += 0.10  # Moderate score for extreme volatility
            
            # Market regime clarity weight (10%)
            regime_confidence = analysis.get("market_regime", {}).get("regime_confidence", 0)
            strength += regime_confidence * 0.1
            
            return min(1.0, strength)  # Cap at 1.0
            
        except Exception as e:
            logger(f"❌ Signal strength calculation error: {str(e)}")
            return 0.0
    
    def _calculate_slope(self, series: pd.Series) -> float:
        """Calculate slope of a time series"""
        try:
            if len(series) < 2:
                return 0.0
            
            x = np.arange(len(series))
            y = series.values
            
            # Remove NaN values
            mask = ~np.isnan(y)
            if mask.sum() < 2:
                return 0.0
            
            x = x[mask]
            y = y[mask]
            
            # Calculate slope using linear regression
            slope = np.polyfit(x, y, 1)[0]
            return slope
            
        except Exception as e:
            logger(f"❌ Slope calculation error: {str(e)}")
            return 0.0
    
    def get_enhanced_trading_signal(self, symbol: str, strategy: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Get enhanced trading signal dengan robust analysis"""
        try:
            # Perform comprehensive analysis
            analysis = self.analyze_market_structure(symbol, df)
            
            if "error" in analysis:
                return {
                    "signal": None,
                    "confidence": 0.0,
                    "reason": analysis["error"],
                    "analysis": analysis
                }
            
            # Strategy-specific signal generation
            signal_result = self._generate_strategy_signal(symbol, strategy, df, analysis)
            
            # Add analysis to result
            signal_result["analysis"] = analysis
            signal_result["timestamp"] = datetime.now()
            
            # Log enhanced signal
            if signal_result["signal"]:
                logger(f"🎯 Enhanced {strategy} signal for {symbol}: {signal_result['signal']}")
                logger(f"   📊 Confidence: {signal_result['confidence']:.1%}")
                logger(f"   🔍 Analysis Score: {analysis['signal_strength']:.1%}")
            
            return signal_result
            
        except Exception as e:
            logger(f"❌ Enhanced signal generation error: {str(e)}")
            return {
                "signal": None,
                "confidence": 0.0,
                "reason": str(e),
                "analysis": {}
            }
    
    def _generate_strategy_signal(self, symbol: str, strategy: str, df: pd.DataFrame, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategy-specific signals dengan enhanced logic"""
        try:
            # Base signal result
            result = {
                "signal": None,
                "confidence": 0.0,
                "reason": "",
                "entry_price": 0.0,
                "suggested_tp": 0.0,
                "suggested_sl": 0.0
            }
            
            # Get current price
            current_price = df['close'].iloc[-1]
            result["entry_price"] = current_price
            
            # Strategy-specific logic
            if strategy == "HFT":
                return self._hft_enhanced_signal(df, analysis, result)
            elif strategy == "Scalping":
                return self._scalping_enhanced_signal(df, analysis, result)
            elif strategy == "Intraday":
                return self._intraday_enhanced_signal(df, analysis, result)
            elif strategy == "Arbitrage":
                return self._arbitrage_enhanced_signal(df, analysis, result)
            else:
                result["reason"] = f"Unknown strategy: {strategy}"
                return result
            
        except Exception as e:
            logger(f"❌ Strategy signal generation error: {str(e)}")
            return {"signal": None, "confidence": 0.0, "reason": str(e)}
    
    def _hft_enhanced_signal(self, df: pd.DataFrame, analysis: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced HFT signal dengan ultra-precise analysis"""
        try:
            # HFT requires very high data quality
            data_quality = analysis.get("data_quality", {}).get("quality_score", 0)
            if data_quality < 80:
                result["reason"] = f"Data quality too low for HFT: {data_quality:.0f}%"
                return result
            
            # HFT looks for micro momentum with high confidence
            momentum = analysis.get("momentum_analysis", {})
            volatility = analysis.get("volatility_analysis", {})
            
            # Micro trend detection
            last_3_closes = df['close'].tail(3).values
            micro_trend = (last_3_closes[-1] - last_3_closes[0]) / last_3_closes[0]
            
            # HFT signal conditions
            hft_signals = []
            
            # 1. Micro momentum
            if abs(micro_trend) > 0.0005:  # 0.05% micro movement
                direction = "BUY" if micro_trend > 0 else "SELL"
                hft_signals.append(f"Micro momentum {direction}")
            
            # 2. RSI micro divergence
            if 'RSI_fast' in df.columns:
                rsi_change = df['RSI_fast'].iloc[-1] - df['RSI_fast'].iloc[-3]
                if abs(rsi_change) > 2:  # Rapid RSI change
                    direction = "BUY" if rsi_change > 0 else "SELL"
                    hft_signals.append(f"RSI micro divergence {direction}")
            
            # 3. MACD histogram acceleration
            if 'MACD_histogram' in df.columns:
                macd_accel = (df['MACD_histogram'].iloc[-1] - df['MACD_histogram'].iloc[-2])
                if abs(macd_accel) > 0.00001:
                    direction = "BUY" if macd_accel > 0 else "SELL"
                    hft_signals.append(f"MACD acceleration {direction}")
            
            # Determine HFT signal
            buy_signals = len([s for s in hft_signals if "BUY" in s])
            sell_signals = len([s for s in hft_signals if "SELL" in s])
            
            if buy_signals >= 2 and buy_signals > sell_signals:
                result["signal"] = "BUY"
                result["confidence"] = min(0.95, buy_signals / 3.0 * data_quality / 100)
                result["reason"] = f"HFT BUY: {', '.join(hft_signals)}"
            elif sell_signals >= 2 and sell_signals > buy_signals:
                result["signal"] = "SELL"
                result["confidence"] = min(0.95, sell_signals / 3.0 * data_quality / 100)
                result["reason"] = f"HFT SELL: {', '.join(hft_signals)}"
            else:
                result["reason"] = f"HFT: Insufficient micro signals ({buy_signals} buy, {sell_signals} sell)"
            
            # HFT TP/SL suggestions (very tight)
            if result["signal"]:
                current_price = result["entry_price"]
                atr = analysis.get("volatility_analysis", {}).get("current_atr", current_price * 0.001)
                
                tp_distance = atr * 1.5  # 1.5x ATR for TP
                sl_distance = atr * 1.0  # 1x ATR for SL
                
                if result["signal"] == "BUY":
                    result["suggested_tp"] = current_price + tp_distance
                    result["suggested_sl"] = current_price - sl_distance
                else:
                    result["suggested_tp"] = current_price - tp_distance
                    result["suggested_sl"] = current_price + sl_distance
            
            return result
            
        except Exception as e:
            result["reason"] = f"HFT analysis error: {str(e)}"
            return result
    
    def _scalping_enhanced_signal(self, df: pd.DataFrame, analysis: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced Scalping signal"""
        # Implementation for scalping with enhanced analysis
        result["reason"] = "Scalping enhanced signal - implementation pending"
        return result
    
    def _intraday_enhanced_signal(self, df: pd.DataFrame, analysis: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced Intraday signal"""
        # Implementation for intraday with enhanced analysis
        result["reason"] = "Intraday enhanced signal - implementation pending"
        return result
    
    def _arbitrage_enhanced_signal(self, df: pd.DataFrame, analysis: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced Arbitrage signal"""
        # Implementation for arbitrage with enhanced analysis
        result["reason"] = "Arbitrage enhanced signal - implementation pending"
        return result


# Global instance
enhanced_analysis_engine = EnhancedAnalysisEngine()


def get_enhanced_analysis(symbol: str, strategy: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Get enhanced analysis for trading signal"""
    return enhanced_analysis_engine.get_enhanced_trading_signal(symbol, strategy, df)


def analyze_market_conditions(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze current market conditions"""
    return enhanced_analysis_engine.analyze_market_structure(symbol, df)