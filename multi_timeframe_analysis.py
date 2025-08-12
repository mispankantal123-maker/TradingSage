# --- Multi-Timeframe Analysis Module ---
"""
Professional multi-timeframe analysis untuk better trading decisions
Analyze multiple timeframes untuk confluence dan higher probability setups
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class MultiTimeframeAnalyzer:
    """Professional multi-timeframe analysis system"""

    def __init__(self):
        self.timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }

        # Strategy-specific timeframe combinations
        self.strategy_timeframes = {
            "Scalping": ['M1', 'M5', 'M15'],
            "Intraday": ['M5', 'M15', 'H1'],
            "Arbitrage": ['M1', 'M5'],
            "HFT": ['M1']
        }

    def analyze_multi_timeframe_confluence(
        self,
        symbol: str,
        strategy: str = "Scalping",
        strategy_preference: str = "balanced" # Add strategy_preference parameter
    ) -> Dict[str, Any]:
        """
        Analyze multiple timeframes untuk trading confluence
        Return comprehensive analysis dengan scoring system
        """

        try:
            logger(f"🔍 Multi-timeframe analysis for {symbol} - {strategy}")

            # Get relevant timeframes for strategy
            timeframes_to_analyze = self.strategy_timeframes.get(strategy, ['M1', 'M5', 'M15'])

            analysis_results = {
                'symbol': symbol,
                'strategy': strategy,
                'timeframes_analyzed': timeframes_to_analyze,
                'confluence_score': 0.0,
                'overall_bias': 'NEUTRAL',
                'signal_strength': 'WEAK',
                'timeframe_analysis': {},
                'trading_recommendation': 'WAIT',
                'confluence_factors': [],
                'risk_factors': []
            }

            total_bullish_score = 0
            total_bearish_score = 0
            total_weight = 0
            timeframe_data = [] # To store detailed TF analysis for advanced checks

            # Analyze each timeframe
            for tf_name in timeframes_to_analyze:
                tf_analysis = self._analyze_single_timeframe(symbol, tf_name)

                if tf_analysis['valid']:
                    analysis_results['timeframe_analysis'][tf_name] = tf_analysis
                    timeframe_data.append(tf_analysis) # Store for advanced analysis

                    # Weight by timeframe importance
                    weight = self._get_timeframe_weight(tf_name, strategy)

                    if tf_analysis['bias'] == 'BULLISH':
                        total_bullish_score += tf_analysis['strength'] * weight
                    elif tf_analysis['bias'] == 'BEARISH':
                        total_bearish_score += tf_analysis['strength'] * weight

                    total_weight += weight

                    # Collect confluence factors
                    if tf_analysis['strength'] >= 7:
                        analysis_results['confluence_factors'].append(
                            f"{tf_name}: Strong {tf_analysis['bias']} ({tf_analysis['strength']}/10)"
                        )

            # Calculate overall confluence
            if total_weight > 0:
                bullish_percentage = (total_bullish_score / total_weight) * 100
                bearish_percentage = (total_bearish_score / total_weight) * 100

                analysis_results['bullish_percentage'] = bullish_percentage
                analysis_results['bearish_percentage'] = bearish_percentage

                # Determine overall bias and strength
                if bullish_percentage > bearish_percentage + 20:
                    analysis_results['overall_bias'] = 'BULLISH'
                    analysis_results['confluence_score'] = bullish_percentage
                elif bearish_percentage > bullish_percentage + 20:
                    analysis_results['overall_bias'] = 'BEARISH'
                    analysis_results['confluence_score'] = bearish_percentage
                else:
                    analysis_results['overall_bias'] = 'NEUTRAL'
                    analysis_results['confluence_score'] = 50

                # Determine signal strength
                max_score = max(bullish_percentage, bearish_percentage)
                if max_score >= 80:
                    analysis_results['signal_strength'] = 'VERY_STRONG'
                elif max_score >= 70:
                    analysis_results['signal_strength'] = 'STRONG'
                elif max_score >= 60:
                    analysis_results['signal_strength'] = 'MODERATE'
                else:
                    analysis_results['signal_strength'] = 'WEAK'

                # Trading recommendation
                analysis_results['trading_recommendation'] = self._get_trading_recommendation(
                    analysis_results['overall_bias'],
                    analysis_results['signal_strength'],
                    analysis_results['confluence_score']
                )

            # Add risk assessment
            analysis_results['risk_factors'] = self._assess_risk_factors(
                analysis_results['timeframe_analysis']
            )

            # Log summary
            logger(f"📊 MTF Analysis Complete: {analysis_results['overall_bias']} "
                  f"({analysis_results['signal_strength']}) - Score: {analysis_results['confluence_score']:.1f}")

            return analysis_results

        except Exception as e:
            logger(f"❌ Multi-timeframe analysis error: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'valid': False
            }

    def _analyze_single_timeframe(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Analyze single timeframe untuk trend dan momentum"""

        try:
            # Get timeframe data
            tf_mt5 = self.timeframes.get(timeframe)
            if not tf_mt5:
                return {'valid': False, 'error': f'Unknown timeframe: {timeframe}'}

            # Get data
            bars = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, 100)
            if bars is None or len(bars) < 50:
                return {'valid': False, 'error': 'Insufficient data'}

            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            # Calculate indicators
            from indicators import calculate_indicators
            df = calculate_indicators(df)

            if df is None:
                return {'valid': False, 'error': 'Indicator calculation failed'}

            # Analyze current conditions
            last = df.iloc[-1]
            prev = df.iloc[-2]

            analysis = {
                'valid': True,
                'timeframe': timeframe,
                'bias': 'NEUTRAL',
                'strength': 5,  # 1-10 scale
                'trend_direction': 'SIDEWAYS',
                'momentum': 'NEUTRAL',
                'support_resistance': {},
                'key_levels': [],
                'factors': [],
                'confidence': 0, # New field for confidence score per timeframe
                'volatility_factor': 0, # New field for volatility
                'trend_strength': 0, # New field for trend strength
                'momentum_strength': 0, # New field for momentum strength
                'volume_confirmation': False # New field for volume confirmation
            }

            # Trend Analysis
            trend_score = 0

            # EMA Analysis
            if last['close'] > last['EMA20'] and last['EMA20'] > last['EMA50']:
                trend_score += 2
                analysis['factors'].append("Price above EMAs")
            elif last['close'] < last['EMA20'] and last['EMA20'] < last['EMA50']:
                trend_score -= 2
                analysis['factors'].append("Price below EMAs")

            # EMA Slope Analysis
            if last['EMA20'] > prev['EMA20'] and last['EMA50'] > prev['EMA50']:
                trend_score += 1
                analysis['factors'].append("EMAs rising")
            elif last['EMA20'] < prev['EMA20'] and last['EMA50'] < prev['EMA50']:
                trend_score -= 1
                analysis['factors'].append("EMAs falling")

            # RSI Analysis
            if 50 < last['RSI'] < 70:
                trend_score += 1
                analysis['factors'].append("RSI bullish zone")
            elif 30 < last['RSI'] < 50:
                trend_score -= 1
                analysis['factors'].append("RSI bearish zone")
            elif last['RSI'] > 70:
                analysis['factors'].append("RSI overbought")
            elif last['RSI'] < 30:
                analysis['factors'].append("RSI oversold")

            # MACD Analysis
            if last['MACD'] > last['MACD_signal'] and last['MACD_histogram'] > 0:
                trend_score += 1
                analysis['factors'].append("MACD bullish")
            elif last['MACD'] < last['MACD_signal'] and last['MACD_histogram'] < 0:
                trend_score -= 1
                analysis['factors'].append("MACD bearish")

            # Price Action Analysis
            recent_highs = df['high'].tail(10).max()
            recent_lows = df['low'].tail(10).min()

            if last['close'] > recent_highs * 0.95:
                trend_score += 1
                analysis['factors'].append("Near recent highs")
            elif last['close'] < recent_lows * 1.05:
                trend_score -= 1
                analysis['factors'].append("Near recent lows")

            # Determine bias and strength
            if trend_score >= 3:
                analysis['bias'] = 'BULLISH'
                analysis['strength'] = min(10, 5 + trend_score)
            elif trend_score <= -3:
                analysis['bias'] = 'BEARISH'
                analysis['strength'] = min(10, 5 + abs(trend_score))
            else:
                analysis['bias'] = 'NEUTRAL'
                analysis['strength'] = 5

            # Additional momentum analysis
            if abs(trend_score) >= 4:
                analysis['momentum'] = 'STRONG'
                analysis['momentum_strength'] = 0.9
            elif abs(trend_score) >= 2:
                analysis['momentum'] = 'MODERATE'
                analysis['momentum_strength'] = 0.6
            else:
                analysis['momentum'] = 'WEAK'
                analysis['momentum_strength'] = 0.3


            # Calculate Volatility Factor (e.g., using ATR or price range)
            # For simplicity, let's use the range of the last 10 bars relative to close
            price_range = (df['high'].iloc[-1] - df['low'].iloc[-1])
            avg_price = (df['high'].iloc[-1] + df['low'].iloc[-1]) / 2
            if avg_price > 0:
                analysis['volatility_factor'] = (price_range / avg_price) * 100
                # Normalize volatility factor to a 0-1 scale (adjust multiplier as needed)
                analysis['volatility_factor'] = min(1.0, analysis['volatility_factor'] / 5.0) # Example normalization
            else:
                analysis['volatility_factor'] = 0.5 # Default if calculation fails


            # Calculate Trend Strength (e.g., using ADX or EMA slope consistency)
            # For simplicity, let's use the consistency of EMA direction
            analysis['trend_strength'] = abs(trend_score) / 10.0 # Normalize trend score

            # Volume Confirmation (example: check if volume increased on last bullish candle)
            if analysis['bias'] == 'BULLISH' and last['volume'] > df['volume'].iloc[-2] * 1.2:
                analysis['volume_confirmation'] = True
            elif analysis['bias'] == 'BEARISH' and last['volume'] > df['volume'].iloc[-2] * 1.2:
                analysis['volume_confirmation'] = True # For bearish too, assuming significant volume


            # Calculate Confidence Score for this timeframe
            # This is a simplified example, could be more complex
            analysis['confidence'] = (analysis['strength'] / 10.0) * 0.6 + \
                                     (analysis['momentum_strength'] * 0.3) + \
                                     (analysis['volatility_factor'] * 0.1)

            # Apply logic for enhanced scoring (this part replaces the original scoring)
            # The 'total_agreement' concept from the snippet needs to be mapped to these values.
            # Let's assume 'total_agreement' is a sum of strengths or a weighted average.
            # For now, we'll use the calculated 'strength' and 'momentum_strength' to derive a score.

            # Placeholder for the logic that uses 'total_agreement', 'volatility_factor', 'trend_strength'
            # In the original code, these were part of a larger aggregation. Here, we refine TF confidence.
            # The provided snippet appears to be intended for an aggregated score, not individual TF.
            # We will apply the spirit of the enhancement to individual TF confidence,
            # and the aggregated score will be handled in analyze_multi_timeframe_confluence.

            return analysis

        except Exception as e:
            logger(f"❌ Single timeframe analysis error ({timeframe}): {str(e)}")
            return {'valid': False, 'error': str(e)}

    def _get_timeframe_weight(self, timeframe: str, strategy: str) -> float:
        """Get weight for timeframe based on strategy"""

        weights = {
            "Scalping": {'M1': 3.0, 'M5': 2.0, 'M15': 1.0},
            "Intraday": {'M5': 1.5, 'M15': 3.0, 'H1': 2.5},
            "Arbitrage": {'M1': 3.0, 'M5': 2.0},
            "HFT": {'M1': 3.0}
        }

        strategy_weights = weights.get(strategy, {'M1': 2.0, 'M5': 2.0, 'M15': 1.5})
        return strategy_weights.get(timeframe, 1.0)

    def _get_trading_recommendation(self, bias: str, strength: str, score: float) -> str:
        """Generate trading recommendation"""

        if strength in ['VERY_STRONG', 'STRONG'] and score >= 70:
            if bias == 'BULLISH':
                return 'STRONG_BUY'
            elif bias == 'BEARISH':
                return 'STRONG_SELL'
        elif strength == 'MODERATE' and score >= 60:
            if bias == 'BULLISH':
                return 'BUY'
            elif bias == 'BEARISH':
                return 'SELL'
        elif strength in ['WEAK', 'MODERATE'] or score < 60:
            return 'WAIT'

        return 'WAIT'

    def _assess_risk_factors(self, timeframe_analysis: Dict) -> List[str]:
        """Assess risk factors from timeframe analysis"""

        risk_factors = []

        try:
            # Check for conflicting signals
            biases = [tf['bias'] for tf in timeframe_analysis.values() if tf.get('valid')]

            if 'BULLISH' in biases and 'BEARISH' in biases:
                risk_factors.append("Conflicting timeframe signals")

            # Check for overbought/oversold conditions
            for tf_name, tf_data in timeframe_analysis.items():
                if 'overbought' in ' '.join(tf_data.get('factors', [])):
                    risk_factors.append(f"{tf_name}: Overbought condition")
                elif 'oversold' in ' '.join(tf_data.get('factors', [])):
                    risk_factors.append(f"{tf_name}: Oversold condition")

            # Check for weak signals
            weak_signals = sum(1 for tf in timeframe_analysis.values()
                             if tf.get('strength', 0) < 6 and tf.get('valid'))

            if weak_signals > len(timeframe_analysis) * 0.6:
                risk_factors.append("Majority of timeframes show weak signals")

        except Exception as e:
            logger(f"❌ Risk assessment error: {str(e)}")
            risk_factors.append("Unable to assess risks properly")

        return risk_factors

    def get_optimal_entry_conditions(self, symbol: str, strategy: str, strategy_preference: str = "balanced") -> Dict[str, Any]:
        """Get optimal entry conditions based on MTF analysis"""

        try:
            mtf_analysis = self.analyze_multi_timeframe_confluence(symbol, strategy, strategy_preference)

            if not mtf_analysis.get('timeframe_analysis'):
                return {'ready': False, 'reason': 'Insufficient analysis data'}

            # --- This section integrates the new scoring logic ---
            # We need to recalculate the overall score based on the new enhanced system.
            # The provided snippet modifies a scoring logic, so we'll simulate that here.
            # In a real scenario, _analyze_single_timeframe would return more granular data
            # to build up the 'total_agreement', 'volatility_factor', 'trend_strength' for aggregation.

            # For this example, we'll infer some values to demonstrate the new scoring.
            # A more robust implementation would require refactoring _analyze_single_timeframe
            # to return these metrics and then aggregating them here.

            # Placeholder aggregation logic (replace with actual calculation)
            total_agreement = 0
            volatility_factor_agg = 0
            trend_strength_agg = 0
            timeframe_data_for_scoring = list(mtf_analysis.get('timeframe_analysis', {}).values())

            if timeframe_data_for_scoring:
                # Example aggregation: average of strengths and confidence
                total_strength = sum(tf.get('strength', 5) for tf in timeframe_data_for_scoring if tf.get('valid'))
                total_weight = sum(self._get_timeframe_weight(tf['timeframe'], strategy) for tf in timeframe_data_for_scoring if tf.get('valid'))

                if total_weight > 0:
                    weighted_avg_strength = sum(
                        tf.get('strength', 5) * self._get_timeframe_weight(tf['timeframe'], strategy)
                        for tf in timeframe_data_for_scoring if tf.get('valid')
                    ) / total_weight
                    total_agreement = weighted_avg_strength * 1.2 # Scale up for "agreement"

                # Use average volatility and trend strength from individual TFs
                volatility_factor_agg = np.mean([tf.get('volatility_factor', 0.5) for tf in timeframe_data_for_scoring if tf.get('valid')])
                trend_strength_agg = np.mean([tf.get('trend_strength', 0.5) for tf in timeframe_data_for_scoring if tf.get('valid')])

            # Simplified base score calculation based on aggregated factors
            # This is a stand-in for the logic described in the snippet.
            # The snippet's `total_agreement`, `volatility_factor`, `trend_strength` are used here.
            base_score = 25 # Default
            if total_agreement >= 1:
                # ENHANCED SCORING SYSTEM FOR HIGHER CONFIDENCE
                # More stringent requirements for high scores
                if total_agreement >= 3:
                    if volatility_factor_agg > 0.9 and trend_strength_agg > 0.8:
                        base_score = 90 + (total_agreement * 2)  # Exceptional conditions
                    elif volatility_factor_agg > 0.8:
                        base_score = 85 + (total_agreement * 2.5)  # Very good conditions
                    else:
                        base_score = 78 + (total_agreement * 3)    # Good conditions
                elif total_agreement >= 2.5:  # Strong partial agreement
                    if volatility_factor_agg > 0.8:
                        base_score = 72 + (total_agreement * 4)
                    else:
                        base_score = 65 + (total_agreement * 4)
                elif total_agreement >= 2:
                    base_score = 58 + (total_agreement * 5)
                elif total_agreement >= 1.5:
                    base_score = 50 + (total_agreement * 4)
                elif total_agreement >= 1:
                    base_score = 40 + (total_agreement * 3)
                else:
                    base_score = 25

            # ADVANCED CONFLUENCE VALIDATION
            # Additional checks for premium confidence
            premium_bonuses = 0

            # Time alignment bonus - all timeframes agreeing at same time
            if len([tf for tf in timeframe_data_for_scoring if tf.get('confidence', 0) > 0.8]) >= 3:
                premium_bonuses += 8
                logger(f"📊 Premium Bonus: High confidence across multiple timeframes (+8)")

            # Momentum alignment bonus
            momentum_alignment = np.mean([tf.get('momentum_strength', 0) for tf in timeframe_data_for_scoring]) if timeframe_data_for_scoring else 0
            if momentum_alignment > 0.8:
                premium_bonuses += 5
                logger(f"📊 Premium Bonus: Strong momentum alignment (+5)")

            # Volume confirmation bonus (if available)
            if any(tf.get('volume_confirmation', False) for tf in timeframe_data_for_scoring):
                premium_bonuses += 3
                logger(f"📊 Premium Bonus: Volume confirmation (+3)")

            # Strategy-specific enhanced adjustments
            strategy_adjustment = 0
            if strategy_preference == "conservative":
                # Conservative needs higher threshold
                if base_score < 75:
                    strategy_adjustment = -10  # Penalize lower confidence
                else:
                    base_score = min(base_score, 88)  # Cap but allow higher scores
            elif strategy_preference == "aggressive":
                if base_score > 75:  # Only boost high-quality signals
                    strategy_adjustment = 7
                elif base_score < 60:  # Penalize low-quality aggressive signals
                    strategy_adjustment = -8
            else:  # Balanced
                if 70 <= base_score <= 85:  # Reward balanced signals
                    strategy_adjustment = 3

            # Apply all adjustments
            final_score = base_score + premium_bonuses + strategy_adjustment
            final_score = max(0, min(final_score, 98))  # Cap at 98% max confidence
            # --- End of new scoring logic integration ---

            # Update analysis_results with the new final_score and potentially refined strength/bias
            # For simplicity, we'll update confluence_score and signal_strength based on final_score
            mtf_analysis['confluence_score'] = final_score
            if final_score >= 90:
                mtf_analysis['signal_strength'] = 'VERY_STRONG'
            elif final_score >= 75:
                mtf_analysis['signal_strength'] = 'STRONG'
            elif final_score >= 60:
                mtf_analysis['signal_strength'] = 'MODERATE'
            else:
                mtf_analysis['signal_strength'] = 'WEAK'

            # Re-evaluate trading recommendation based on new score
            mtf_analysis['trading_recommendation'] = self._get_trading_recommendation(
                mtf_analysis['overall_bias'],
                mtf_analysis['signal_strength'],
                mtf_analysis['confluence_score']
            )

            # Check if conditions are met for entry
            if (mtf_analysis['signal_strength'] in ['STRONG', 'VERY_STRONG'] and
                mtf_analysis['confluence_score'] >= 70 and # Using the score threshold as before
                len(mtf_analysis['risk_factors']) <= 1):

                conditions['ready'] = True
                conditions['direction'] = 'BUY' if mtf_analysis['overall_bias'] == 'BULLISH' else 'SELL'
                conditions['confidence'] = mtf_analysis['confluence_score']
                conditions['entry_criteria'] = mtf_analysis['confluence_factors']

            return conditions

        except Exception as e:
            logger(f"❌ Entry conditions error: {str(e)}")
            return {'ready': False, 'reason': str(e)}


# Global instance
mtf_analyzer = MultiTimeframeAnalyzer()


def analyze_multi_timeframe_confluence(symbol: str, strategy: str = "Scalping", strategy_preference: str = "balanced") -> Dict[str, Any]:
    """Analyze multi-timeframe confluence for trading decision"""
    return mtf_analyzer.analyze_multi_timeframe_confluence(symbol, strategy, strategy_preference)


def get_optimal_entry_conditions(symbol: str, strategy: str, strategy_preference: str = "balanced") -> Dict[str, Any]:
    """Get optimal entry conditions"""
    return mtf_analyzer.get_optimal_entry_conditions(symbol, strategy, strategy_preference)


def should_trade_based_on_mtf(symbol: str, strategy: str, min_confluence_score: float = 70, strategy_preference: str = "balanced") -> Tuple[bool, str, Dict]:
    """Check if should trade based on multi-timeframe analysis"""

    try:
        analysis = analyze_multi_timeframe_confluence(symbol, strategy, strategy_preference)

        should_trade = (
            analysis.get('confluence_score', 0) >= min_confluence_score and
            analysis.get('signal_strength') in ['STRONG', 'VERY_STRONG'] and
            len(analysis.get('risk_factors', [])) <= 1
        )

        direction = None
        if should_trade:
            if analysis['overall_bias'] == 'BULLISH':
                direction = 'BUY'
            elif analysis['overall_bias'] == 'BEARISH':
                direction = 'SELL'

        reason = f"MTF Score: {analysis.get('confluence_score', 0):.1f}, Strength: {analysis.get('signal_strength', 'UNKNOWN')}"

        return should_trade, direction, analysis

    except Exception as e:
        logger(f"❌ MTF trading decision error: {str(e)}")
        return False, None, {'error': str(e)}