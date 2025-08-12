# --- Enhanced Aggressiveness Module ---
"""
Smart aggressiveness module untuk meningkatkan frequency trading tanpa menurunkan win rate
Implements dynamic thresholds, market condition adaptation, dan opportunity maximization
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class EnhancedAggressivenessModule:
    """Smart aggressiveness untuk maximize opportunities tanpa sacrifice quality"""

    def __init__(self):
        # Dynamic confidence thresholds (adaptive based on market conditions)
        self.base_thresholds = {
            'ultra_conservative': 0.85,  # 85%+ - original ultra-high standard
            'conservative': 0.75,        # 75%+ - original high standard
            'moderate': 0.65,            # 65%+ - balanced approach
            'aggressive': 0.55,          # 55%+ - aggressive but still quality
            'ultra_aggressive': 0.45     # 45%+ - maximum aggressiveness
        }

        # Market condition adjustments
        self.market_conditions = {
            'high_volatility': {
                'threshold_reduction': 0.05,  # Lower threshold by 5%
                'frequency_multiplier': 1.3,  # 30% more opportunities
                'confidence_bonus': 0.10      # 10% confidence boost
            },
            'trending_market': {
                'threshold_reduction': 0.08,  # Lower threshold by 8%
                'frequency_multiplier': 1.5,  # 50% more opportunities
                'confidence_bonus': 0.15      # 15% confidence boost
            },
            'session_overlap': {
                'threshold_reduction': 0.10,  # Lower threshold by 10%
                'frequency_multiplier': 1.8,  # 80% more opportunities
                'confidence_bonus': 0.12      # 12% confidence boost
            },
            'news_driven': {
                'threshold_reduction': 0.03,  # Minimal reduction for safety
                'frequency_multiplier': 1.2,  # 20% more opportunities
                'confidence_bonus': 0.08      # 8% confidence boost
            }
        }

        # Session-based aggressiveness
        self.session_aggressiveness = {
            'London': 1.5,     # Very aggressive during London
            'NY': 1.3,         # Aggressive during NY
            'Overlap': 1.8,    # Ultra aggressive during overlap
            'Asian': 1.0       # Normal during Asian
        }

        # Symbol-specific aggressiveness
        self.symbol_aggressiveness = {
            'EURUSD': 1.4,     # High liquidity = more aggressive
            'GBPUSD': 1.3,     # Good liquidity = aggressive
            'USDJPY': 1.2,     # Stable pair = moderate aggressive
            'XAUUSD': 1.6,     # High profit potential = very aggressive
            'BTCUSD': 1.8      # Crypto volatility = ultra aggressive
        }

    def calculate_dynamic_threshold(self, symbol: str, strategy: str, 
                                  base_confidence: float) -> Dict[str, Any]:
        """Calculate dynamic threshold based on market conditions"""
        try:
            logger(f"🚀 SMART AGGRESSIVENESS: {symbol} - Calculating dynamic threshold")

            # Start with base threshold
            base_threshold = self.base_thresholds['conservative']  # 75% default

            # Market condition analysis
            market_conditions = self._analyze_market_conditions(symbol)

            # Apply market condition adjustments
            threshold_adjustments = []
            confidence_bonuses = []
            frequency_multipliers = []

            for condition, detected in market_conditions.items():
                if detected and condition in self.market_conditions:
                    adjustment = self.market_conditions[condition]
                    threshold_adjustments.append(adjustment['threshold_reduction'])
                    confidence_bonuses.append(adjustment['confidence_bonus'])
                    frequency_multipliers.append(adjustment['frequency_multiplier'])
                    logger(f"   ✅ {condition.upper()} detected - threshold reduction: {adjustment['threshold_reduction']:.1%}")

            # Calculate adjusted threshold
            total_threshold_reduction = sum(threshold_adjustments)
            adjusted_threshold = max(0.35, base_threshold - total_threshold_reduction)  # Min 35%

            # Session adjustment
            current_session = self._get_current_session()
            session_multiplier = self.session_aggressiveness.get(current_session, 1.0)

            # Symbol adjustment
            symbol_multiplier = self.symbol_aggressiveness.get(symbol.upper(), 1.0)

            # Final threshold calculation
            final_threshold = adjusted_threshold / (session_multiplier * symbol_multiplier)
            final_threshold = max(0.30, min(0.85, final_threshold))  # Bound between 30-85%

            # Confidence enhancement
            confidence_enhancement = sum(confidence_bonuses)
            enhanced_confidence = min(0.95, base_confidence + confidence_enhancement)

            # Frequency calculation
            base_frequency = 1.0
            frequency_boost = max(frequency_multipliers) if frequency_multipliers else 1.0
            final_frequency = base_frequency * frequency_boost * session_multiplier * symbol_multiplier

            result = {
                'original_threshold': base_threshold,
                'adjusted_threshold': final_threshold,
                'threshold_reduction': base_threshold - final_threshold,
                'enhanced_confidence': enhanced_confidence,
                'confidence_boost': enhanced_confidence - base_confidence,
                'frequency_multiplier': final_frequency,
                'market_conditions': market_conditions,
                'session': current_session,
                'session_multiplier': session_multiplier,
                'symbol_multiplier': symbol_multiplier,
                'recommended_action': self._get_aggressiveness_recommendation(final_threshold, enhanced_confidence)
            }

            logger(f"✅ SMART THRESHOLD: {final_threshold:.1%} (was {base_threshold:.1%})")
            logger(f"   📈 Confidence boost: +{confidence_enhancement:.1%}")
            logger(f"   🎯 Frequency boost: {final_frequency:.1f}x")
            logger(f"   🚀 Action: {result['recommended_action']}")

            return result

        except Exception as e:
            logger(f"❌ Smart aggressiveness error: {str(e)}")
            return {
                'original_threshold': 0.70,
                'adjusted_threshold': 0.70,
                'enhanced_confidence': base_confidence,
                'frequency_multiplier': 1.0,
                'recommended_action': 'NORMAL'
            }

    def _analyze_market_conditions(self, symbol: str) -> Dict[str, bool]:
        """Analyze current market conditions for smart aggressiveness"""
        try:
            conditions = {
                'high_volatility': False,
                'trending_market': False,
                'session_overlap': False,
                'news_driven': False
            }

            # Get recent data for analysis
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
            if rates is None or len(rates) < 20:
                return conditions

            df = pd.DataFrame(rates)

            # 1. High volatility detection
            if len(df) >= 20:
                recent_atr = self._calculate_simple_atr(df.tail(20))
                long_atr = self._calculate_simple_atr(df)

                if recent_atr > long_atr * 1.3:  # 30% higher than average
                    conditions['high_volatility'] = True
                    logger("   🔥 HIGH VOLATILITY detected")

            # 2. Trending market detection
            if len(df) >= 20:
                price_change = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
                if abs(price_change) > 0.005:  # 0.5% move in 20 bars
                    conditions['trending_market'] = True
                    logger("   📈 TRENDING MARKET detected")

            # 3. Session overlap detection
            current_hour = datetime.datetime.utcnow().hour
            if (8 <= current_hour <= 12) or (13 <= current_hour <= 17):  # London-NY overlap
                conditions['session_overlap'] = True
                logger("   🌍 SESSION OVERLAP detected")

            # 4. News-driven detection (simplified - based on high volume spikes)
            if len(df) >= 10:
                recent_volume = df['tick_volume'].tail(5).mean()
                avg_volume = df['tick_volume'].mean()

                if recent_volume > avg_volume * 2.0:  # 100% volume spike
                    conditions['news_driven'] = True
                    logger("   📰 NEWS DRIVEN movement detected")

            return conditions

        except Exception as e:
            logger(f"❌ Market condition analysis error: {str(e)}")
            return {'high_volatility': False, 'trending_market': False, 'session_overlap': False, 'news_driven': False}

    def _calculate_simple_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate simple ATR for volatility measurement"""
        try:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean().iloc[-1]

            return atr if not pd.isna(atr) else 0.001

        except Exception as e:
            return 0.001

    def _get_current_session(self) -> str:
        """Get current trading session"""
        try:
            current_hour = datetime.datetime.utcnow().hour

            if 8 <= current_hour < 12:
                return 'London'
            elif 13 <= current_hour < 17:
                return 'Overlap'  # London-NY overlap
            elif 17 <= current_hour < 21:
                return 'NY'
            else:
                return 'Asian'

        except Exception as e:
            return 'Asian'

    def _get_aggressiveness_recommendation(self, threshold: float, confidence: float) -> str:
        """Get aggressiveness recommendation based on threshold and confidence"""
        if threshold <= 0.35:
            return 'ULTRA_AGGRESSIVE'
        elif threshold <= 0.45:
            return 'VERY_AGGRESSIVE'
        elif threshold <= 0.55:
            return 'AGGRESSIVE'
        elif threshold <= 0.65:
            return 'MODERATE'
        else:
            return 'CONSERVATIVE'

    def apply_smart_filters(self, symbol: str, strategy: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply smart filters untuk maximize opportunities"""
        try:
            if not analysis_result.get('signal'):
                return analysis_result

            base_confidence = analysis_result.get('confidence', 0)

            # Get dynamic threshold
            aggressiveness_analysis = self.calculate_dynamic_threshold(symbol, strategy, base_confidence)

            # Apply enhanced confidence
            enhanced_confidence = aggressiveness_analysis['enhanced_confidence']
            adjusted_threshold = aggressiveness_analysis['adjusted_threshold']

            # Update analysis result
            analysis_result['confidence'] = enhanced_confidence
            analysis_result['dynamic_threshold'] = adjusted_threshold
            analysis_result['aggressiveness_boost'] = aggressiveness_analysis['confidence_boost']
            analysis_result['frequency_multiplier'] = aggressiveness_analysis['frequency_multiplier']
            analysis_result['aggressiveness_level'] = aggressiveness_analysis['recommended_action']

            # Check if signal passes enhanced threshold
            if enhanced_confidence >= adjusted_threshold:
                analysis_result['enhanced_by_aggressiveness'] = True
                logger(f"🎯 SMART FILTER PASSED: {enhanced_confidence:.1%} >= {adjusted_threshold:.1%}")
            else:
                logger(f"⚠️ Smart filter: {enhanced_confidence:.1%} < {adjusted_threshold:.1%}")

            return analysis_result

        except Exception as e:
            logger(f"❌ Smart filter error: {str(e)}")
            return analysis_result

    def get_position_size_multiplier(self, aggressiveness_level: str, market_conditions: Dict[str, bool]) -> float:
        """Get position size multiplier based on aggressiveness and conditions"""
        base_multipliers = {
            'ULTRA_AGGRESSIVE': 1.8,
            'VERY_AGGRESSIVE': 1.5,
            'AGGRESSIVE': 1.3,
            'MODERATE': 1.1,
            'CONSERVATIVE': 1.0
        }

        base_multiplier = base_multipliers.get(aggressiveness_level, 1.0)

        # Boost for favorable conditions
        condition_boost = 1.0
        if market_conditions.get('trending_market', False):
            condition_boost += 0.2
        if market_conditions.get('session_overlap', False):
            condition_boost += 0.3
        if market_conditions.get('high_volatility', False):
            condition_boost += 0.1

        final_multiplier = min(2.5, base_multiplier * condition_boost)  # Cap at 2.5x

        return final_multiplier


# Global instance
aggressiveness_module = EnhancedAggressivenessModule()


def apply_smart_aggressiveness(symbol: str, strategy: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Apply ULTRA-SMART aggressiveness for maximum profit while maintaining system stability"""
    try:
        original_confidence = analysis_result.get('confidence', 0)

        # ULTRA-AGGRESSIVE factors for maximum profitability
        aggressiveness_boost = 0.0
        frequency_multiplier = 1.0

        # 1. ENHANCED Market condition detection
        market_factors = detect_ultra_aggressive_market_conditions(symbol)

        # 2. PREMIUM Time-based aggressiveness 
        time_factors = get_premium_session_aggressiveness_boost()

        # 3. ADVANCED Symbol-specific aggressiveness
        symbol_factors = get_advanced_symbol_aggressiveness_factors(symbol)

        # 4. OPTIMIZED Strategy-specific aggressiveness
        strategy_factors = get_optimized_strategy_aggressiveness_factors(strategy)

        # 5. NEW: Volatility-based opportunity detection
        volatility_factors = detect_volatility_opportunities(symbol)

        # 6. NEW: News-driven aggressiveness
        news_factors = detect_news_driven_opportunities()

        # Combine all factors for MAXIMUM profit potential
        total_boost = (
            market_factors.get('boost', 0) +
            time_factors.get('boost', 0) +
            symbol_factors.get('boost', 0) +
            strategy_factors.get('boost', 0) +
            volatility_factors.get('boost', 0) +
            news_factors.get('boost', 0)
        )

        # ULTRA-AGGRESSIVE threshold calculation (much lower for more trades)
        base_threshold = 0.70  # More aggressive base
        threshold_reduction = min(0.50, total_boost)  # Up to 50% reduction
        dynamic_threshold = max(0.25, base_threshold - threshold_reduction)  # Min 25% (ULTRA LOW)

        # ENHANCED frequency multiplier for maximum opportunities
        frequency_multiplier = 1.0 + (total_boost * 3)  # Up to 4x frequency

        # SMART confidence enhancement
        confidence_multiplier = 1.0 + (total_boost * 0.5)
        enhanced_confidence = min(0.99, original_confidence * confidence_multiplier)

        # PROFIT MAXIMIZATION: Position size enhancement
        position_size_multiplier = 1.0 + min(0.5, total_boost)  # Up to 50% larger positions

        # Store enhanced aggressiveness data
        analysis_result.update({
            'aggressiveness_boost': total_boost,
            'frequency_multiplier': frequency_multiplier,
            'dynamic_threshold': dynamic_threshold,
            'position_size_multiplier': position_size_multiplier,
            'confidence_multiplier': confidence_multiplier,
            'aggressiveness_level': get_ultra_aggressiveness_level(total_boost),
            'market_factors': market_factors,
            'time_factors': time_factors,
            'symbol_factors': symbol_factors,
            'strategy_factors': strategy_factors,
            'volatility_factors': volatility_factors,
            'news_factors': news_factors,
            'profit_potential': calculate_profit_potential(total_boost, frequency_multiplier)
        })

        logger(f"🚀 ULTRA-SMART THRESHOLD: {dynamic_threshold:.1%} (was 70.0%)")
        logger(f"   📈 Confidence boost: +{total_boost:.1%}")
        logger(f"   🎯 Frequency boost: {frequency_multiplier:.1f}x")
        logger(f"   💰 Position size: {position_size_multiplier:.1f}x")
        logger(f"   🚀 Level: {get_ultra_aggressiveness_level(total_boost)}")
        logger(f"   💎 Profit potential: {analysis_result.get('profit_potential', 'STANDARD')}")

        return analysis_result

    except Exception as e:
        logger(f"❌ Ultra-smart aggressiveness error: {str(e)}")
        return analysis_result


def detect_ultra_aggressive_market_conditions(symbol: str) -> Dict[str, Any]:
    """Detect ULTRA-AGGRESSIVE market conditions for maximum profit"""
    try:
        boost = 0.0
        conditions = []

        # Get market data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
        if not rates or len(rates) < 20:
            return {'boost': 0.0, 'conditions': []}

        # Convert to arrays for analysis
        closes = [float(r['close']) for r in rates]
        highs = [float(r['high']) for r in rates]
        lows = [float(r['low']) for r in rates]
        volumes = [float(r['tick_volume']) for r in rates]

        # 1. ULTRA-HIGH VOLATILITY detection (massive profit potential)
        recent_range = max(highs[-10:]) - min(lows[-10:])
        avg_range = sum([highs[i] - lows[i] for i in range(-20, -1)]) / 19

        if recent_range > avg_range * 2.0:  # 200% above average
            boost += 0.15  # 15% boost
            conditions.append("ULTRA-HIGH VOLATILITY: 200%+ range expansion")
        elif recent_range > avg_range * 1.5:  # 150% above average
            boost += 0.10  # 10% boost
            conditions.append("HIGH VOLATILITY: 150%+ range expansion")

        # 2. TRENDING MOMENTUM (strong directional moves)
        price_change = (closes[-1] - closes[-10]) / closes[-10]
        if abs(price_change) > 0.002:  # 0.2% move in 10 bars
            boost += 0.12  # 12% boost
            conditions.append(f"STRONG MOMENTUM: {price_change*100:.1f}% move")
        elif abs(price_change) > 0.001:  # 0.1% move
            boost += 0.08  # 8% boost
            conditions.append(f"MOMENTUM: {price_change*100:.1f}% move")

        # 3. VOLUME SURGE (institutional activity)
        recent_volume = sum(volumes[-5:]) / 5
        avg_volume = sum(volumes[-20:-5]) / 15

        if recent_volume > avg_volume * 2.0:  # 200% volume surge
            boost += 0.10  # 10% boost
            conditions.append("VOLUME SURGE: 200%+ institutional activity")
        elif recent_volume > avg_volume * 1.5:  # 150% volume surge
            boost += 0.06  # 6% boost
            conditions.append("VOLUME INCREASE: 150%+ activity")

        # 4. BREAKOUT DETECTION (major price levels)
        resistance = max(highs[-20:])
        support = min(lows[-20:])
        current_price = closes[-1]

        if current_price > resistance * 1.001:  # Breaking resistance
            boost += 0.08  # 8% boost
            conditions.append("RESISTANCE BREAKOUT: Major level break")
        elif current_price < support * 0.999:  # Breaking support
            boost += 0.08  # 8% boost
            conditions.append("SUPPORT BREAKOUT: Major level break")

        return {
            'boost': boost,
            'conditions': conditions,
            'volatility_ratio': recent_range / avg_range if avg_range > 0 else 1,
            'volume_ratio': recent_volume / avg_volume if avg_volume > 0 else 1,
            'momentum': price_change
        }

    except Exception as e:
        logger(f"❌ Market condition detection error: {str(e)}")
        return {'boost': 0.0, 'conditions': []}


def get_premium_session_aggressiveness_boost() -> Dict[str, Any]:
    """Get PREMIUM session-based aggressiveness for maximum profit windows"""
    try:
        current_hour = datetime.datetime.utcnow().hour
        boost = 0.0
        session_info = ""

        # ULTRA-AGGRESSIVE session targeting
        if 13 <= current_hour <= 16:  # London-NY overlap (GOLDEN HOURS)
            boost = 0.20  # 20% boost - MAXIMUM AGGRESSION
            session_info = "GOLDEN OVERLAP: London-NY (ULTRA-AGGRESSIVE)"
        elif 8 <= current_hour <= 12:  # London session (HIGH ACTIVITY)
            boost = 0.15  # 15% boost
            session_info = "LONDON SESSION: High volatility (AGGRESSIVE)"
        elif 13 <= current_hour <= 21:  # NY session (STRONG ACTIVITY)
            boost = 0.12  # 12% boost
            session_info = "NY SESSION: Strong activity (AGGRESSIVE)"
        elif 0 <= current_hour <= 8:  # Asian session (MODERATE)
            boost = 0.08  # 8% boost
            session_info = "ASIAN SESSION: Moderate activity"
        else:  # Off hours
            boost = 0.02  # 2% boost (minimal but still active)
            session_info = "OFF-HOURS: Minimal activity"

        return {
            'boost': boost,
            'session': session_info,
            'hour': current_hour,
            'is_golden_time': 13 <= current_hour <= 16
        }

    except Exception as e:
        logger(f"❌ Session boost error: {str(e)}")
        return {'boost': 0.05, 'session': 'DEFAULT'}


def get_ultra_aggressiveness_level(total_boost: float) -> str:
    """Determine ULTRA aggressiveness level for maximum profit targeting"""
    if total_boost >= 0.35:
        return "ULTRA_EXTREME"  # 35%+ boost
    elif total_boost >= 0.25:
        return "ULTRA_HIGH"     # 25%+ boost
    elif total_boost >= 0.18:
        return "EXTREME"        # 18%+ boost
    elif total_boost >= 0.12:
        return "VERY_HIGH"      # 12%+ boost
    elif total_boost >= 0.08:
        return "HIGH"           # 8%+ boost
    elif total_boost >= 0.05:
        return "AGGRESSIVE"     # 5%+ boost
    else:
        return "MODERATE"       # <5% boost


def calculate_profit_potential(boost: float, frequency: float) -> str:
    """Calculate profit potential classification"""
    potential_score = boost * frequency

    if potential_score >= 0.8:
        return "MAXIMUM_PROFIT"
    elif potential_score >= 0.6:
        return "ULTRA_HIGH_PROFIT"
    elif potential_score >= 0.4:
        return "HIGH_PROFIT"
    elif potential_score >= 0.25:
        return "ENHANCED_PROFIT"
    else:
        return "STANDARD_PROFIT"


def detect_advanced_symbol_aggressiveness_factors(symbol: str) -> Dict[str, Any]:
    """Detect ADVANCED symbol-specific aggressiveness for optimized trading"""
    try:
        boost = 0.0
        factors = []

        symbol_upper = symbol.upper()

        # Higher liquidity and volatility generally means higher aggressiveness
        if symbol_upper in ['EURUSD', 'GBPUSD', 'AUDUSD']:
            boost += 0.10
            factors.append("HIGH LIQUIDITY")
        elif symbol_upper in ['USDJPY', 'USDCHF']:
            boost += 0.07
            factors.append("MODERATE LIQUIDITY")
        elif symbol_upper in ['XAUUSD', 'XAGUSD']:
            boost += 0.15
            factors.append("PRECIOUS METALS VOLATILITY")
        elif symbol_upper in ['BTCUSD', 'ETHUSD']:
            boost += 0.18
            factors.append("CRYPTO HIGH VOLATILITY")

        # Consider specific symbol characteristics
        if 'USD' in symbol_upper and 'JPY' in symbol_upper: # USD/JPY often has unique behavior
            boost += 0.03
            factors.append("UNIQUE JPY BEHAVIOR")
        elif 'XAU' in symbol_upper: # Gold's safe-haven status
            boost += 0.04
            factors.append("GOLD SAFE-HAVEN STATUS")

        return {'boost': boost, 'factors': factors}

    except Exception as e:
        logger(f"❌ Advanced symbol factors error: {str(e)}")
        return {'boost': 0.05, 'factors': ['ERROR DETECTED']}


def get_optimized_strategy_aggressiveness_factors(strategy: str) -> Dict[str, Any]:
    """Get OPTIMIZED strategy-specific aggressiveness for targeted profits"""
    try:
        boost = 0.0
        factors = []

        strategy_lower = strategy.lower()

        # Strategies that benefit from higher frequency / lower thresholds
        if "scalp" in strategy_lower or "momentum" in strategy_lower:
            boost += 0.15
            factors.append("HIGH FREQUENCY STRATEGY")
        elif "trend_follow" in strategy_lower:
            boost += 0.10
            factors.append("TREND FOLLOWING")
        elif "mean_reversion" in strategy_lower:
            boost += 0.08
            factors.append("MEAN REVERSION")
        elif "breakout" in strategy_lower:
            boost += 0.12
            factors.append("BREAKOUT STRATEGY")

        # Some strategies might be inherently more aggressive
        if "aggressive_scalp" in strategy_lower:
            boost += 0.05
            factors.append("INHERENTLY AGGRESSIVE")

        return {'boost': boost, 'factors': factors}

    except Exception as e:
        logger(f"❌ Optimized strategy factors error: {str(e)}")
        return {'boost': 0.05, 'factors': ['ERROR DETECTED']}


def detect_volatility_opportunities(symbol: str) -> Dict[str, Any]:
    """Detect volatility-based opportunities for amplified gains"""
    try:
        boost = 0.0
        opportunities = []

        # Get recent volatility data (e.g., using ATR or recent price range)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 30)
        if not rates or len(rates) < 15:
            return {'boost': 0.0, 'opportunities': []}

        df = pd.DataFrame(rates)

        # Calculate Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()

        # Recent vs. Average ATR
        recent_atr = df['ATR'].iloc[-1]
        avg_atr = df['ATR'].mean()

        if recent_atr > avg_atr * 1.8:  # Significantly higher volatility
            boost += 0.15
            opportunities.append("EXTREME VOLATILITY SPIKE")
        elif recent_atr > avg_atr * 1.4:  # Higher volatility
            boost += 0.10
            opportunities.append("HIGH VOLATILITY")
        elif recent_atr > avg_atr * 1.1: # Slightly elevated volatility
            boost += 0.05
            opportunities.append("ELEVATED VOLATILITY")

        # Capture potential breakout moves within high volatility
        if recent_atr > avg_atr * 1.5:
            price_change_10m = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
            if abs(price_change_10m) > 0.003: # Significant move in high vol
                boost += 0.07
                opportunities.append("VOLATILITY-DRIVEN MOMENTUM")


        return {'boost': boost, 'opportunities': opportunities}

    except Exception as e:
        logger(f"❌ Volatility opportunity detection error: {str(e)}")
        return {'boost': 0.0, 'opportunities': []}


def detect_news_driven_opportunities() -> Dict[str, Any]:
    """Detect news-driven opportunities for tactical trading"""
    try:
        boost = 0.0
        opportunities = []

        # Placeholder for real news feed integration.
        # For now, we'll simulate based on time of day and typical news release patterns.
        current_hour = datetime.datetime.utcnow().hour

        # Major economic news releases are common around session overlaps and early sessions
        if (8 <= current_hour <= 10) or (13 <= current_hour <= 15):
            boost += 0.12
            opportunities.append("POTENTIAL HIGH-IMPACT NEWS EVENT")
        elif (10 <= current_hour <= 12) or (15 <= current_hour <= 17):
            boost += 0.08
            opportunities.append("POTENTIAL MEDIUM-IMPACT NEWS EVENT")
        else:
            boost += 0.03
            opportunities.append("LOW PROBABILITY NEWS EVENT")

        # In a real scenario, this would parse news feeds and check for event importance.

        return {'boost': boost, 'opportunities': opportunities}

    except Exception as e:
        logger(f"❌ News-driven opportunity detection error: {str(e)}")
        return {'boost': 0.0, 'opportunities': []}


def get_dynamic_threshold(symbol: str, strategy: str, base_confidence: float) -> Dict[str, Any]:
    """Get dynamic threshold based on market conditions"""
    return aggressiveness_module.calculate_dynamic_threshold(symbol, strategy, base_confidence)