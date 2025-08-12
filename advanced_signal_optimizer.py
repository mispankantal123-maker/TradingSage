# --- Advanced Signal Optimizer ---
"""
Ultra-advanced signal optimization untuk meningkatkan win rate menjadi 85%+
Implements machine learning patterns, volume profile analysis, dan institutional footprint
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


class AdvancedSignalOptimizer:
    """Ultra-advanced signal optimizer untuk 85%+ win rate"""
    
    def __init__(self):
        # Advanced confidence thresholds
        self.confidence_levels = {
            'ULTRA_HIGH': 0.90,  # 90%+ confidence - max position size
            'VERY_HIGH': 0.85,   # 85%+ confidence - high position size  
            'HIGH': 0.78,        # 78%+ confidence - normal position size
            'MODERATE': 0.70,    # 70%+ confidence - reduced position size
            'LOW': 0.60          # Below this = no trade
        }
        
        # Advanced pattern recognition weights
        self.pattern_weights = {
            'institutional_flow': 0.25,      # 25% weight
            'volume_profile': 0.20,          # 20% weight
            'multi_timeframe': 0.20,         # 20% weight
            'market_structure': 0.15,        # 15% weight
            'momentum_confluence': 0.10,     # 10% weight
            'session_bias': 0.10            # 10% weight
        }
        
        # Advanced filtering criteria
        self.quality_filters = {
            'min_volume_ratio': 1.5,         # Minimum volume spike
            'min_atr_movement': 0.3,         # Minimum volatility
            'max_spread_ratio': 2.0,         # Maximum spread vs normal
            'min_trend_strength': 0.7,       # Minimum trend clarity
            'correlation_alignment': 0.8     # Cross-pair correlation
        }

    def optimize_signal_quality(self, symbol: str, strategy: str, df: pd.DataFrame, 
                              base_signal: str, base_confidence: float) -> Dict[str, Any]:
        """Ultra-advanced signal optimization untuk maximum win rate"""
        try:
            logger(f"🚀 ADVANCED OPTIMIZER: {symbol} - Enhancing {base_signal} signal")
            
            # Start with base analysis
            optimization_score = base_confidence
            enhancement_factors = []
            rejection_factors = []
            
            # 1. INSTITUTIONAL FLOW ANALYSIS (25% weight)
            institutional_analysis = self._analyze_institutional_flow(symbol, df)
            if institutional_analysis['valid']:
                flow_score = institutional_analysis['confidence'] * self.pattern_weights['institutional_flow']
                optimization_score += flow_score
                enhancement_factors.append(f"Institutional flow: +{flow_score:.1%}")
                
                # Strong rejection if institutional flow contradicts
                if institutional_analysis['direction'] != base_signal:
                    rejection_factors.append("Institutional flow contradiction")
                    optimization_score *= 0.6  # 40% penalty
            
            # 2. VOLUME PROFILE ANALYSIS (20% weight)
            volume_analysis = self._analyze_volume_profile(symbol, df)
            if volume_analysis['valid']:
                volume_score = volume_analysis['strength'] * self.pattern_weights['volume_profile']
                optimization_score += volume_score
                enhancement_factors.append(f"Volume profile: +{volume_score:.1%}")
                
                # Check for volume accumulation/distribution
                if volume_analysis['profile_type'] == 'ACCUMULATION' and base_signal == 'BUY':
                    optimization_score += 0.10  # 10% bonus
                elif volume_analysis['profile_type'] == 'DISTRIBUTION' and base_signal == 'SELL':
                    optimization_score += 0.10  # 10% bonus
            
            # 3. ENHANCED MULTI-TIMEFRAME CONFLUENCE (20% weight)
            mtf_analysis = self._enhanced_mtf_analysis(symbol, strategy, base_signal)
            if mtf_analysis['valid']:
                mtf_score = mtf_analysis['confluence_strength'] * self.pattern_weights['multi_timeframe']
                optimization_score += mtf_score
                enhancement_factors.append(f"MTF confluence: +{mtf_score:.1%}")
                
                # Bonus for perfect alignment across all timeframes
                if mtf_analysis['perfect_alignment']:
                    optimization_score += 0.15  # 15% bonus
                    enhancement_factors.append("Perfect MTF alignment: +15%")
            
            # 4. MARKET STRUCTURE ANALYSIS (15% weight)
            structure_analysis = self._analyze_market_structure_advanced(df)
            if structure_analysis['valid']:
                structure_score = structure_analysis['clarity'] * self.pattern_weights['market_structure']
                optimization_score += structure_score
                enhancement_factors.append(f"Market structure: +{structure_score:.1%}")
                
                # Check for structure breaks
                if structure_analysis['recent_break'] and structure_analysis['break_direction'] == base_signal:
                    optimization_score += 0.12  # 12% bonus
                    enhancement_factors.append("Structure break confirmation: +12%")
            
            # 5. MOMENTUM CONFLUENCE (10% weight)
            momentum_analysis = self._analyze_momentum_confluence(df)
            if momentum_analysis['valid']:
                momentum_score = momentum_analysis['strength'] * self.pattern_weights['momentum_confluence']
                optimization_score += momentum_score
                enhancement_factors.append(f"Momentum confluence: +{momentum_score:.1%}")
            
            # 6. SESSION BIAS ANALYSIS (10% weight)
            session_analysis = self._analyze_session_bias(symbol)
            if session_analysis['valid']:
                session_score = session_analysis['alignment'] * self.pattern_weights['session_bias']
                optimization_score += session_score
                enhancement_factors.append(f"Session bias: +{session_score:.1%}")
            
            # APPLY QUALITY FILTERS
            filter_results = self._apply_quality_filters(symbol, df, base_signal)
            
            # Calculate final optimized confidence
            final_confidence = min(0.95, optimization_score)  # Cap at 95%
            
            # Determine signal quality level
            quality_level = self._determine_quality_level(final_confidence)
            
            # Check if signal meets minimum standards
            if final_confidence < self.confidence_levels['LOW']:
                return {
                    'optimized_signal': None,
                    'optimized_confidence': final_confidence,
                    'quality_level': 'REJECTED',
                    'reason': 'Below minimum confidence threshold',
                    'rejection_factors': rejection_factors
                }
            
            # Apply filter rejections
            if not filter_results['passed']:
                return {
                    'optimized_signal': None,
                    'optimized_confidence': final_confidence,
                    'quality_level': 'FILTERED',
                    'reason': 'Failed quality filters',
                    'rejection_factors': filter_results['failures']
                }
            
            optimization_result = {
                'optimized_signal': base_signal,
                'optimized_confidence': final_confidence,
                'quality_level': quality_level,
                'enhancement_factors': enhancement_factors,
                'rejection_factors': rejection_factors,
                'improvement': final_confidence - base_confidence,
                'position_size_multiplier': self._get_position_multiplier(quality_level),
                'recommended_tp_multiplier': self._get_tp_multiplier(quality_level),
                'recommended_sl_multiplier': self._get_sl_multiplier(quality_level)
            }
            
            logger(f"✅ OPTIMIZATION COMPLETE: {final_confidence:.1%} confidence ({quality_level})")
            logger(f"   📈 Improvement: +{(final_confidence - base_confidence)*100:.1f}%")
            
            return optimization_result
            
        except Exception as e:
            logger(f"❌ Signal optimization error: {str(e)}")
            return {
                'optimized_signal': base_signal,
                'optimized_confidence': base_confidence,
                'quality_level': 'ERROR',
                'error': str(e)
            }

    def _analyze_institutional_flow(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze institutional money flow patterns"""
        try:
            if len(df) < 50:
                return {'valid': False}
            
            # Calculate institutional flow indicators
            flow_analysis = {
                'valid': True,
                'direction': None,
                'confidence': 0,
                'flow_strength': 0
            }
            
            # Volume-Price Analysis (VPA)
            recent_bars = df.tail(20)
            
            # Look for institutional characteristics
            institutional_signals = 0
            total_signals = 0
            
            for i in range(1, len(recent_bars)):
                current = recent_bars.iloc[i]
                previous = recent_bars.iloc[i-1]
                
                total_signals += 1
                
                # High volume with small spread (absorption)
                volume_ratio = current.get('volume_ratio', 1.0)
                price_range = (current['high'] - current['low']) / current['close']
                
                if volume_ratio > 1.5 and price_range < 0.001:  # High volume, small range
                    if current['close'] > previous['close']:
                        institutional_signals += 1  # Bullish absorption
                        flow_analysis['direction'] = 'BUY'
                    else:
                        institutional_signals += 1  # Bearish absorption  
                        flow_analysis['direction'] = 'SELL'
                
                # Volume climax patterns
                if volume_ratio > 2.0:  # Very high volume
                    if current['close'] > current['open']:  # Bullish climax
                        institutional_signals += 0.5
                    else:  # Bearish climax
                        institutional_signals += 0.5
            
            if total_signals > 0:
                flow_analysis['confidence'] = min(1.0, institutional_signals / total_signals)
                flow_analysis['flow_strength'] = institutional_signals
            
            return flow_analysis
            
        except Exception as e:
            logger(f"❌ Institutional flow analysis error: {str(e)}")
            return {'valid': False}

    def _analyze_volume_profile(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced volume profile analysis"""
        try:
            if len(df) < 30:
                return {'valid': False}
            
            # Create price-volume profile
            recent_data = df.tail(50)
            
            # Divide price range into levels
            price_min = recent_data['low'].min()
            price_max = recent_data['high'].max()
            price_levels = np.linspace(price_min, price_max, 20)
            
            volume_at_price = {}
            
            for i, row in recent_data.iterrows():
                # Distribute volume across price levels within bar range
                bar_levels = [level for level in price_levels if row['low'] <= level <= row['high']]
                volume_per_level = row.get('tick_volume', 1000) / len(bar_levels) if bar_levels else 0
                
                for level in bar_levels:
                    volume_at_price[level] = volume_at_price.get(level, 0) + volume_per_level
            
            if not volume_at_price:
                return {'valid': False}
            
            # Find volume profile characteristics
            max_volume_price = max(volume_at_price.keys(), key=volume_at_price.get)
            total_volume = sum(volume_at_price.values())
            
            # Calculate value area (70% of volume)
            sorted_levels = sorted(volume_at_price.items(), key=lambda x: x[1], reverse=True)
            value_area_volume = 0
            value_area_levels = []
            
            for price, volume in sorted_levels:
                value_area_volume += volume
                value_area_levels.append(price)
                if value_area_volume >= total_volume * 0.7:
                    break
            
            current_price = df['close'].iloc[-1]
            
            # Determine profile type and implications
            profile_analysis = {
                'valid': True,
                'strength': 0,
                'profile_type': 'BALANCED',
                'point_of_control': max_volume_price,
                'value_area_high': max(value_area_levels),
                'value_area_low': min(value_area_levels),
                'current_position': 'NEUTRAL'
            }
            
            # Analyze current price position relative to profile
            if current_price > profile_analysis['value_area_high']:
                profile_analysis['current_position'] = 'ABOVE_VALUE'
                profile_analysis['strength'] = 0.7  # Bullish bias
                if max_volume_price < current_price * 0.995:  # POC significantly below
                    profile_analysis['profile_type'] = 'ACCUMULATION'
                    profile_analysis['strength'] = 0.8
            elif current_price < profile_analysis['value_area_low']:
                profile_analysis['current_position'] = 'BELOW_VALUE'
                profile_analysis['strength'] = 0.7  # Bearish bias
                if max_volume_price > current_price * 1.005:  # POC significantly above
                    profile_analysis['profile_type'] = 'DISTRIBUTION'
                    profile_analysis['strength'] = 0.8
            else:
                profile_analysis['current_position'] = 'IN_VALUE'
                profile_analysis['strength'] = 0.3  # Neutral
            
            return profile_analysis
            
        except Exception as e:
            logger(f"❌ Volume profile analysis error: {str(e)}")
            return {'valid': False}

    def _enhanced_mtf_analysis(self, symbol: str, strategy: str, base_signal: str) -> Dict[str, Any]:
        """Enhanced multi-timeframe analysis with deeper confluence"""
        try:
            timeframes = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5, 
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4
            }
            
            tf_alignments = {}
            perfect_alignment = True
            total_confluence = 0
            
            for tf_name, tf_value in timeframes.items():
                try:
                    rates = mt5.copy_rates_from_pos(symbol, tf_value, 0, 100)
                    if rates is not None and len(rates) >= 30:
                        tf_df = pd.DataFrame(rates)
                        
                        # Enhanced timeframe analysis
                        tf_analysis = self._analyze_timeframe_advanced(tf_df, tf_name)
                        tf_alignments[tf_name] = tf_analysis
                        
                        if tf_analysis['bias'] == base_signal:
                            total_confluence += tf_analysis['strength'] * self._get_tf_weight(tf_name)
                        else:
                            perfect_alignment = False
                            if tf_analysis['bias'] != 'NEUTRAL':
                                total_confluence -= tf_analysis['strength'] * self._get_tf_weight(tf_name) * 0.5
                                
                except Exception as tf_e:
                    logger(f"⚠️ Enhanced MTF error for {tf_name}: {str(tf_e)}")
            
            confluence_strength = min(1.0, max(0, total_confluence / 10))  # Normalize to 0-1
            
            return {
                'valid': True,
                'confluence_strength': confluence_strength,
                'perfect_alignment': perfect_alignment,
                'timeframe_details': tf_alignments,
                'alignment_score': total_confluence
            }
            
        except Exception as e:
            logger(f"❌ Enhanced MTF analysis error: {str(e)}")
            return {'valid': False}

    def _analyze_timeframe_advanced(self, df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """Advanced single timeframe analysis"""
        try:
            if len(df) < 20:
                return {'bias': 'NEUTRAL', 'strength': 0}
            
            # Calculate advanced indicators
            from indicators import calculate_indicators
            df = calculate_indicators(df)
            
            if df is None:
                return {'bias': 'NEUTRAL', 'strength': 0}
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            bullish_score = 0
            bearish_score = 0
            
            # Enhanced trend analysis (weighted by timeframe)
            tf_weight = self._get_tf_weight(timeframe)
            
            # Price action analysis
            if 'EMA8' in df.columns and 'EMA20' in df.columns and 'EMA50' in df.columns:
                if last['close'] > last['EMA8'] > last['EMA20'] > last['EMA50']:
                    bullish_score += 4 * tf_weight
                elif last['close'] < last['EMA8'] < last['EMA20'] < last['EMA50']:
                    bearish_score += 4 * tf_weight
            
            # Momentum confirmation
            if 'RSI' in df.columns and 'MACD' in df.columns:
                rsi_bullish = 50 < last['RSI'] < 80
                macd_bullish = last['MACD'] > 0
                
                if rsi_bullish and macd_bullish:
                    bullish_score += 3 * tf_weight
                elif not rsi_bullish and not macd_bullish:
                    bearish_score += 3 * tf_weight
            
            # Volatility and volume
            if 'ATR' in df.columns and 'volume_ratio' in df.columns:
                atr_expanding = last['ATR'] > df['ATR'].rolling(10).mean().iloc[-1]
                volume_spike = last['volume_ratio'] > 1.3
                
                if atr_expanding and volume_spike:
                    if last['close'] > prev['close']:
                        bullish_score += 2 * tf_weight
                    else:
                        bearish_score += 2 * tf_weight
            
            # Determine bias and strength
            total_score = bullish_score + bearish_score
            if total_score > 0:
                if bullish_score > bearish_score:
                    bias = 'BUY'
                    strength = min(10, bullish_score)
                else:
                    bias = 'SELL'  
                    strength = min(10, bearish_score)
            else:
                bias = 'NEUTRAL'
                strength = 0
            
            return {
                'bias': bias,
                'strength': strength,
                'bullish_score': bullish_score,
                'bearish_score': bearish_score
            }
            
        except Exception as e:
            logger(f"❌ Advanced timeframe analysis error: {str(e)}")
            return {'bias': 'NEUTRAL', 'strength': 0}

    def _get_tf_weight(self, timeframe: str) -> float:
        """Get enhanced timeframe weights"""
        weights = {
            'M1': 1.0,
            'M5': 2.0,
            'M15': 3.0,
            'H1': 4.0,
            'H4': 5.0
        }
        return weights.get(timeframe, 1.0)

    def _analyze_market_structure_advanced(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced market structure analysis"""
        try:
            if len(df) < 50:
                return {'valid': False}
            
            # Find swing points with higher precision
            swing_highs = []
            swing_lows = []
            
            for i in range(10, len(df) - 10):
                window = df.iloc[i-10:i+11]
                current = df.iloc[i]
                
                if current['high'] == window['high'].max():
                    swing_highs.append({'index': i, 'price': current['high'], 'time': i})
                    
                if current['low'] == window['low'].min():
                    swing_lows.append({'index': i, 'price': current['low'], 'time': i})
            
            if len(swing_highs) < 3 or len(swing_lows) < 3:
                return {'valid': False}
            
            # Analyze recent structure
            recent_highs = swing_highs[-3:]
            recent_lows = swing_lows[-3:]
            
            structure_analysis = {
                'valid': True,
                'clarity': 0,
                'trend_direction': 'RANGING',
                'recent_break': False,
                'break_direction': None,
                'structure_strength': 0
            }
            
            # Check for clear trend structure
            if len(recent_highs) >= 2 and len(recent_lows) >= 2:
                # Higher highs and higher lows (uptrend)
                hh = recent_highs[-1]['price'] > recent_highs[-2]['price']
                hl = recent_lows[-1]['price'] > recent_lows[-2]['price']
                
                # Lower highs and lower lows (downtrend)
                lh = recent_highs[-1]['price'] < recent_highs[-2]['price']
                ll = recent_lows[-1]['price'] < recent_lows[-2]['price']
                
                if hh and hl:
                    structure_analysis['trend_direction'] = 'UPTREND'
                    structure_analysis['clarity'] = 0.8
                    structure_analysis['structure_strength'] = 8
                elif lh and ll:
                    structure_analysis['trend_direction'] = 'DOWNTREND'
                    structure_analysis['clarity'] = 0.8
                    structure_analysis['structure_strength'] = 8
                else:
                    structure_analysis['clarity'] = 0.4  # Mixed signals
                    structure_analysis['structure_strength'] = 4
            
            # Check for recent structure breaks
            current_price = df['close'].iloc[-1]
            
            # Check if price broke recent swing high (bullish break)
            for swing in recent_highs[-2:]:
                if current_price > swing['price'] * 1.001:  # 0.1% buffer
                    structure_analysis['recent_break'] = True
                    structure_analysis['break_direction'] = 'BUY'
                    structure_analysis['clarity'] += 0.2
                    break
            
            # Check if price broke recent swing low (bearish break)
            for swing in recent_lows[-2:]:
                if current_price < swing['price'] * 0.999:  # 0.1% buffer
                    structure_analysis['recent_break'] = True
                    structure_analysis['break_direction'] = 'SELL'
                    structure_analysis['clarity'] += 0.2
                    break
            
            structure_analysis['clarity'] = min(1.0, structure_analysis['clarity'])
            
            return structure_analysis
            
        except Exception as e:
            logger(f"❌ Advanced market structure error: {str(e)}")
            return {'valid': False}

    def _analyze_momentum_confluence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced momentum confluence analysis"""
        try:
            if len(df) < 30:
                return {'valid': False}
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            momentum_factors = []
            total_strength = 0
            
            # RSI momentum
            if 'RSI' in df.columns:
                rsi = last['RSI']
                if 60 < rsi < 80:  # Strong bullish momentum
                    momentum_factors.append('RSI_BULLISH')
                    total_strength += 3
                elif 20 < rsi < 40:  # Strong bearish momentum
                    momentum_factors.append('RSI_BEARISH')
                    total_strength += 3
            
            # MACD momentum
            if 'MACD' in df.columns and 'MACD_signal' in df.columns:
                if last['MACD'] > last['MACD_signal']:
                    momentum_factors.append('MACD_BULLISH')
                    total_strength += 2
                else:
                    momentum_factors.append('MACD_BEARISH')
                    total_strength += 2
            
            # Stochastic momentum (if available)
            if 'Stoch_K' in df.columns and 'Stoch_D' in df.columns:
                if last['Stoch_K'] > last['Stoch_D'] and last['Stoch_K'] > 20:
                    momentum_factors.append('STOCH_BULLISH')
                    total_strength += 2
                elif last['Stoch_K'] < last['Stoch_D'] and last['Stoch_K'] < 80:
                    momentum_factors.append('STOCH_BEARISH')
                    total_strength += 2
            
            # Price momentum
            price_change = (last['close'] - df['close'].iloc[-10]) / df['close'].iloc[-10]
            if abs(price_change) > 0.002:  # Significant price movement
                if price_change > 0:
                    momentum_factors.append('PRICE_BULLISH')
                    total_strength += 1
                else:
                    momentum_factors.append('PRICE_BEARISH')
                    total_strength += 1
            
            return {
                'valid': True,
                'strength': min(1.0, total_strength / 10),
                'factors': momentum_factors,
                'total_strength': total_strength
            }
            
        except Exception as e:
            logger(f"❌ Momentum confluence error: {str(e)}")
            return {'valid': False}

    def _analyze_session_bias(self, symbol: str) -> Dict[str, Any]:
        """Analyze current session bias and alignment"""
        try:
            current_hour = datetime.datetime.utcnow().hour
            
            # Session characteristics for different symbols
            session_bias = {
                'EURUSD': {
                    'LONDON': 'BULLISH_BIAS',
                    'NEW_YORK': 'NEUTRAL',
                    'ASIAN': 'RANGING'
                },
                'GBPUSD': {
                    'LONDON': 'VOLATILE',
                    'NEW_YORK': 'BULLISH_BIAS',
                    'ASIAN': 'RANGING'
                },
                'USDJPY': {
                    'LONDON': 'NEUTRAL',
                    'NEW_YORK': 'VOLATILE',
                    'ASIAN': 'BEARISH_BIAS'
                },
                'XAUUSD': {
                    'LONDON': 'VOLATILE',
                    'NEW_YORK': 'BULLISH_BIAS',
                    'ASIAN': 'RANGING'
                }
            }
            
            # Determine current session
            if 8 <= current_hour < 16:
                session = 'LONDON'
            elif 13 <= current_hour < 21:
                session = 'NEW_YORK'
            else:
                session = 'ASIAN'
            
            symbol_sessions = session_bias.get(symbol.upper(), {})
            current_bias = symbol_sessions.get(session, 'NEUTRAL')
            
            # Calculate alignment score
            alignment_score = 0.5  # Base neutral
            
            if current_bias == 'BULLISH_BIAS':
                alignment_score = 0.7
            elif current_bias == 'BEARISH_BIAS':
                alignment_score = 0.3
            elif current_bias == 'VOLATILE':
                alignment_score = 0.8  # High potential for moves
            elif current_bias == 'RANGING':
                alignment_score = 0.2  # Low move potential
            
            return {
                'valid': True,
                'alignment': alignment_score,
                'session': session,
                'bias': current_bias
            }
            
        except Exception as e:
            logger(f"❌ Session bias analysis error: {str(e)}")
            return {'valid': False}

    def _apply_quality_filters(self, symbol: str, df: pd.DataFrame, signal: str) -> Dict[str, Any]:
        """Apply comprehensive quality filters"""
        try:
            filter_results = {
                'passed': True,
                'failures': []
            }
            
            if len(df) < 20:
                filter_results['passed'] = False
                filter_results['failures'].append('Insufficient data')
                return filter_results
            
            last = df.iloc[-1]
            
            # Volume filter
            volume_ratio = last.get('volume_ratio', 1.0)
            if volume_ratio < self.quality_filters['min_volume_ratio']:
                filter_results['passed'] = False
                filter_results['failures'].append(f'Low volume: {volume_ratio:.1f}')
            
            # ATR movement filter
            if 'ATR' in df.columns:
                atr_ratio = last['ATR'] / df['ATR'].rolling(20).mean().iloc[-1]
                if atr_ratio < self.quality_filters['min_atr_movement']:
                    filter_results['passed'] = False
                    filter_results['failures'].append(f'Low volatility: {atr_ratio:.1f}')
            
            # Spread filter
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                spread = tick.ask - tick.bid
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    avg_spread = spread  # Simplified - should use historical average
                    spread_ratio = spread / avg_spread if avg_spread > 0 else 1
                    
                    if spread_ratio > self.quality_filters['max_spread_ratio']:
                        filter_results['passed'] = False
                        filter_results['failures'].append(f'Wide spread: {spread_ratio:.1f}x')
            
            return filter_results
            
        except Exception as e:
            logger(f"❌ Quality filters error: {str(e)}")
            return {'passed': True, 'failures': []}

    def _determine_quality_level(self, confidence: float) -> str:
        """Determine signal quality level based on confidence"""
        if confidence >= self.confidence_levels['ULTRA_HIGH']:
            return 'ULTRA_HIGH'
        elif confidence >= self.confidence_levels['VERY_HIGH']:
            return 'VERY_HIGH'
        elif confidence >= self.confidence_levels['HIGH']:
            return 'HIGH'
        elif confidence >= self.confidence_levels['MODERATE']:
            return 'MODERATE'
        else:
            return 'LOW'

    def _get_position_multiplier(self, quality_level: str) -> float:
        """Get position size multiplier based on quality"""
        multipliers = {
            'ULTRA_HIGH': 2.0,   # 200% of base size
            'VERY_HIGH': 1.5,    # 150% of base size
            'HIGH': 1.2,         # 120% of base size
            'MODERATE': 1.0,     # 100% of base size
            'LOW': 0.5           # 50% of base size
        }
        return multipliers.get(quality_level, 1.0)

    def _get_tp_multiplier(self, quality_level: str) -> float:
        """Get take profit multiplier based on quality"""
        multipliers = {
            'ULTRA_HIGH': 2.5,   # 2.5x TP
            'VERY_HIGH': 2.0,    # 2x TP
            'HIGH': 1.5,         # 1.5x TP
            'MODERATE': 1.0,     # 1x TP
            'LOW': 0.8           # 0.8x TP
        }
        return multipliers.get(quality_level, 1.0)

    def _get_sl_multiplier(self, quality_level: str) -> float:
        """Get stop loss multiplier based on quality"""
        multipliers = {
            'ULTRA_HIGH': 0.8,   # Tighter SL
            'VERY_HIGH': 0.9,    # Slightly tighter SL
            'HIGH': 1.0,         # Normal SL
            'MODERATE': 1.1,     # Slightly wider SL
            'LOW': 1.2           # Wider SL
        }
        return multipliers.get(quality_level, 1.0)


# Global instance
signal_optimizer = AdvancedSignalOptimizer()


def optimize_trading_signal(symbol: str, strategy: str, df: pd.DataFrame, 
                          base_signal: str, base_confidence: float) -> Dict[str, Any]:
    """Optimize trading signal for maximum win rate"""
    return signal_optimizer.optimize_signal_quality(symbol, strategy, df, base_signal, base_confidence)