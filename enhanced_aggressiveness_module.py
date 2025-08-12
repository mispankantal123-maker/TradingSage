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
    """Apply smart aggressiveness untuk maximize opportunities"""
    return aggressiveness_module.apply_smart_filters(symbol, strategy, analysis_result)


def get_dynamic_threshold(symbol: str, strategy: str, base_confidence: float) -> Dict[str, Any]:
    """Get dynamic threshold based on market conditions"""
    return aggressiveness_module.calculate_dynamic_threshold(symbol, strategy, base_confidence)