# --- Enhanced Analysis Engine ---
"""
Professional trading analysis engine untuk multi-strategy optimization
Implements advanced technical analysis untuk professional trading
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


def get_enhanced_analysis(symbol: str, strategy: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Enhanced analysis engine untuk professional trading decisions"""
    try:
        logger(f"🔍 Enhanced Analysis Engine: {symbol} - {strategy}")
        
        if len(df) < 50:
            return {
                "signal": None,
                "confidence": 0,
                "reason": "Insufficient data for enhanced analysis"
            }
        
        # Get current session for context
        current_hour = datetime.datetime.utcnow().hour
        session_context = get_trading_session_context(current_hour)
        
        # Multi-timeframe analysis
        mtf_signals = analyze_mtf_confluence(symbol, strategy)
        
        # Technical confluence analysis  
        tech_signals = analyze_technical_confluence(df, strategy)
        
        # Risk assessment
        risk_assessment = analyze_risk_factors(symbol, df, session_context)
        
        # Combine all analyses
        combined_analysis = combine_analysis_results(
            mtf_signals, tech_signals, risk_assessment, strategy
        )
        
        # ULTRA ENHANCEMENT: Apply advanced signal optimization
        if combined_analysis['signal'] and combined_analysis['confidence'] > 0:
            try:
                from advanced_signal_optimizer import optimize_trading_signal
                
                optimized_result = optimize_trading_signal(
                    symbol, strategy, df, combined_analysis['signal'], combined_analysis['confidence']
                )
                
                if optimized_result['optimized_signal']:
                    # Update with optimized results
                    combined_analysis['signal'] = optimized_result['optimized_signal']
                    combined_analysis['confidence'] = optimized_result['optimized_confidence']
                    combined_analysis['quality_level'] = optimized_result['quality_level']
                    combined_analysis['enhancement_factors'] = optimized_result.get('enhancement_factors', [])
                    combined_analysis['position_size_multiplier'] = optimized_result.get('position_size_multiplier', 1.0)
                    combined_analysis['tp_multiplier'] = optimized_result.get('recommended_tp_multiplier', 1.0)
                    combined_analysis['sl_multiplier'] = optimized_result.get('recommended_sl_multiplier', 1.0)
                    
                    logger(f"🚀 ULTRA-OPTIMIZED: {optimized_result['quality_level']} quality signal")
                    logger(f"   📈 Confidence boost: {optimized_result.get('improvement', 0)*100:.1f}%")
                    
                    # Log enhancement factors
                    for factor in optimized_result.get('enhancement_factors', []):
                        logger(f"   ✅ {factor}")
                        
                else:
                    # Signal was rejected by advanced optimizer
                    combined_analysis['signal'] = None
                    combined_analysis['confidence'] = optimized_result['optimized_confidence']
                    combined_analysis['reason'] = optimized_result.get('reason', 'Advanced optimization rejected signal')
                    
                    logger(f"🛑 ADVANCED FILTER: Signal rejected - {optimized_result.get('reason', 'Quality too low')}")
                    
            except Exception as opt_e:
                logger(f"⚠️ Advanced optimization error: {str(opt_e)}")
        
        # FINAL STEP: Ultra-Precise Confidence Calibration
        if combined_analysis['signal'] and combined_analysis['confidence'] > 0:
            try:
                from confidence_calibration_system import calibrate_signal_confidence
                
                calibration_result = calibrate_signal_confidence(symbol, strategy, combined_analysis)
                
                if calibration_result['recommended_action'] != 'REJECT':
                    # Apply ultra-precise calibration
                    combined_analysis['confidence'] = calibration_result['calibrated_confidence']
                    combined_analysis['quality_grade'] = calibration_result['quality_grade']
                    combined_analysis['recommended_action'] = calibration_result['recommended_action']
                    combined_analysis['position_sizing_factor'] = calibration_result['position_sizing_factor']
                    combined_analysis['tp_sl_adjustments'] = calibration_result['tp_sl_adjustments']
                    combined_analysis['calibration_factors'] = calibration_result.get('calibration_factors', [])
                    
                    logger(f"🎯 ULTRA-CALIBRATED: {calibration_result['quality_grade']} grade signal")
                    logger(f"   📊 Gates passed: {len(calibration_result.get('quality_gates_passed', []))}")
                    logger(f"   🚀 Action: {calibration_result['recommended_action']}")
                    
                else:
                    # Signal rejected by ultra-precise calibration
                    combined_analysis['signal'] = None
                    combined_analysis['confidence'] = calibration_result['calibrated_confidence']
                    combined_analysis['reason'] = calibration_result.get('rejection_reason', 'Ultra-calibration rejected signal')
                    
                    logger(f"🛑 ULTRA-FILTER: Signal rejected - {calibration_result.get('rejection_reason', 'Quality insufficient')}")
                    
            except Exception as cal_e:
                logger(f"⚠️ Ultra-calibration error: {str(cal_e)}")
        
        logger(f"✅ Enhanced Analysis Complete: {combined_analysis['signal']} (Confidence: {combined_analysis['confidence']:.1%})")
        
        return combined_analysis
        
    except Exception as e:
        logger(f"❌ Enhanced analysis error for {symbol}: {str(e)}")
        return {
            "signal": None,
            "confidence": 0,
            "reason": f"Analysis error: {str(e)}"
        }


def get_trading_session_context(hour: int) -> Dict[str, Any]:
    """Get current trading session context"""
    sessions = {
        'ASIAN': {'hours': range(0, 8), 'volatility': 'LOW', 'spread_factor': 1.2},
        'LONDON': {'hours': range(8, 16), 'volatility': 'HIGH', 'spread_factor': 0.8},
        'NEW_YORK': {'hours': range(13, 21), 'volatility': 'HIGH', 'spread_factor': 0.9},
        'OVERLAP': {'hours': range(13, 16), 'volatility': 'EXTREME', 'spread_factor': 0.7}
    }
    
    for session_name, session_data in sessions.items():
        if hour in session_data['hours']:
            return {
                'name': session_name,
                'volatility': session_data['volatility'],
                'spread_factor': session_data['spread_factor'],
                'trading_recommended': session_data['volatility'] in ['HIGH', 'EXTREME']
            }
    
    return {
        'name': 'OFF_HOURS',
        'volatility': 'VERY_LOW',
        'spread_factor': 1.5,
        'trading_recommended': False
    }


def analyze_mtf_confluence(symbol: str, strategy: str) -> Dict[str, Any]:
    """Multi-timeframe confluence analysis"""
    try:
        timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1
        }
        
        tf_signals = {}
        total_bullish = 0
        total_bearish = 0
        
        for tf_name, tf_value in timeframes.items():
            try:
                rates = mt5.copy_rates_from_pos(symbol, tf_value, 0, 100)
                if rates is not None and len(rates) >= 50:
                    tf_df = pd.DataFrame(rates)
                    tf_df['time'] = pd.to_datetime(tf_df['time'], unit='s')
                    
                    # Calculate indicators
                    from indicators import calculate_indicators
                    tf_df = calculate_indicators(tf_df)
                    
                    if tf_df is not None:
                        tf_analysis = analyze_timeframe_signals(tf_df, tf_name)
                        tf_signals[tf_name] = tf_analysis
                        
                        weight = get_timeframe_weight(tf_name, strategy)
                        if tf_analysis['bias'] == 'BULLISH':
                            total_bullish += tf_analysis['strength'] * weight
                        elif tf_analysis['bias'] == 'BEARISH':
                            total_bearish += tf_analysis['strength'] * weight
            except Exception as tf_e:
                logger(f"⚠️ MTF analysis error for {tf_name}: {str(tf_e)}")
        
        # Calculate confluence
        total_signals = total_bullish + total_bearish
        if total_signals > 0:
            bullish_ratio = total_bullish / total_signals
            bearish_ratio = total_bearish / total_signals
            
            if bullish_ratio > 0.65:
                bias = 'BULLISH'
                confidence = bullish_ratio
            elif bearish_ratio > 0.65:
                bias = 'BEARISH'
                confidence = bearish_ratio
            else:
                bias = 'NEUTRAL'
                confidence = abs(bullish_ratio - bearish_ratio)
        else:
            bias = 'NEUTRAL'
            confidence = 0
        
        return {
            'bias': bias,
            'confidence': confidence,
            'timeframe_signals': tf_signals
        }
        
    except Exception as e:
        logger(f"❌ MTF confluence error: {str(e)}")
        return {'bias': 'NEUTRAL', 'confidence': 0}


def analyze_timeframe_signals(df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
    """Analyze signals for specific timeframe"""
    try:
        if len(df) < 20:
            return {'bias': 'NEUTRAL', 'strength': 0}
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA trend analysis
        if 'EMA20' in df.columns and 'EMA50' in df.columns:
            if last['close'] > last['EMA20'] > last['EMA50']:
                bullish_signals += 2
            elif last['close'] < last['EMA20'] < last['EMA50']:
                bearish_signals += 2
        
        # RSI momentum
        if 'RSI' in df.columns:
            rsi = last['RSI']
            if 50 < rsi < 70:
                bullish_signals += 1
            elif 30 < rsi < 50:
                bearish_signals += 1
        
        # MACD signals
        if 'MACD' in df.columns and 'MACD_signal' in df.columns:
            if (last['MACD'] > last['MACD_signal'] and 
                prev['MACD'] <= prev['MACD_signal']):
                bullish_signals += 3  # Strong signal
            elif (last['MACD'] < last['MACD_signal'] and 
                  prev['MACD'] >= prev['MACD_signal']):
                bearish_signals += 3
        
        # Volume confirmation
        if 'volume_ratio' in df.columns and last['volume_ratio'] > 1.2:
            if last['close'] > prev['close']:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Determine bias and strength
        total_signals = bullish_signals + bearish_signals
        if bullish_signals > bearish_signals:
            bias = 'BULLISH'
            strength = min(10, bullish_signals)
        elif bearish_signals > bullish_signals:
            bias = 'BEARISH'
            strength = min(10, bearish_signals)
        else:
            bias = 'NEUTRAL'
            strength = 1
        
        return {
            'bias': bias,
            'strength': strength,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals
        }
        
    except Exception as e:
        logger(f"❌ Timeframe analysis error: {str(e)}")
        return {'bias': 'NEUTRAL', 'strength': 0}


def get_timeframe_weight(timeframe: str, strategy: str) -> float:
    """Get timeframe weight based on strategy"""
    weights = {
        'Scalping': {
            'M1': 1.5,
            'M5': 2.0,
            'M15': 1.0,
            'H1': 0.5
        },
        'Intraday': {
            'M1': 0.5,
            'M5': 1.0,
            'M15': 2.0,
            'H1': 1.5
        },
        'HFT': {
            'M1': 3.0,
            'M5': 1.0,
            'M15': 0.5,
            'H1': 0.2
        },
        'Arbitrage': {
            'M1': 2.0,
            'M5': 1.5,
            'M15': 1.0,
            'H1': 0.5
        }
    }
    
    return weights.get(strategy, {}).get(timeframe, 1.0)


def analyze_technical_confluence(df: pd.DataFrame, strategy: str) -> Dict[str, Any]:
    """Technical confluence analysis"""
    try:
        if len(df) < 20:
            return {'signal': None, 'strength': 0}
        
        last = df.iloc[-1]
        signals = []
        bullish_score = 0
        bearish_score = 0
        
        # Price action analysis
        if 'EMA8' in df.columns and 'EMA20' in df.columns:
            if last['close'] > last['EMA8'] > last['EMA20']:
                bullish_score += 3
                signals.append("Bullish EMA alignment")
            elif last['close'] < last['EMA8'] < last['EMA20']:
                bearish_score += 3
                signals.append("Bearish EMA alignment")
        
        # Momentum confluence
        if 'RSI' in df.columns and 'MACD_histogram' in df.columns:
            rsi_bullish = 50 < last['RSI'] < 80
            macd_bullish = last['MACD_histogram'] > 0
            
            if rsi_bullish and macd_bullish:
                bullish_score += 2
                signals.append("RSI + MACD bullish confluence")
            elif not rsi_bullish and not macd_bullish:
                bearish_score += 2
                signals.append("RSI + MACD bearish confluence")
        
        # Volatility analysis
        if 'ATR' in df.columns and 'BB_width' in df.columns:
            atr_expanding = last['ATR'] > df['ATR'].rolling(10).mean().iloc[-1]
            bb_expanding = last['BB_width'] > df['BB_width'].rolling(10).mean().iloc[-1]
            
            if atr_expanding or bb_expanding:
                signals.append("Volatility expansion detected")
                # Add 1 point to stronger bias
                if bullish_score > bearish_score:
                    bullish_score += 1
                elif bearish_score > bullish_score:
                    bearish_score += 1
        
        # Determine final signal
        total_score = bullish_score + bearish_score
        if total_score > 0:
            if bullish_score > bearish_score:
                signal = 'BUY'
                strength = bullish_score / total_score
            else:
                signal = 'SELL'
                strength = bearish_score / total_score
        else:
            signal = None
            strength = 0
        
        return {
            'signal': signal,
            'strength': strength,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'signals': signals
        }
        
    except Exception as e:
        logger(f"❌ Technical confluence error: {str(e)}")
        return {'signal': None, 'strength': 0}


def analyze_risk_factors(symbol: str, df: pd.DataFrame, session: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze risk factors"""
    try:
        risk_factors = []
        risk_score = 0  # Lower is better
        
        # Session risk assessment
        if not session['trading_recommended']:
            risk_factors.append(f"Low volatility session: {session['name']}")
            risk_score += 3
        
        # Spread analysis
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            spread = tick.ask - tick.bid
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                # Calculate spread in pips
                point = getattr(symbol_info, 'point', 0.00001)
                spread_pips = spread / point
                
                if symbol.upper() in ['EURUSD', 'GBPUSD', 'USDJPY'] and spread_pips > 3:
                    risk_factors.append(f"Wide spread: {spread_pips:.1f} pips")
                    risk_score += 2
                elif symbol.upper() == 'XAUUSD' and spread_pips > 50:
                    risk_factors.append(f"Wide XAU spread: {spread_pips:.1f} pips")
                    risk_score += 2
        
        # Volatility risk
        if 'ATR' in df.columns:
            current_atr = df['ATR'].iloc[-1]
            avg_atr = df['ATR'].rolling(20).mean().iloc[-1]
            
            if current_atr > avg_atr * 1.5:
                risk_factors.append("High volatility environment")
                risk_score += 1
            elif current_atr < avg_atr * 0.5:
                risk_factors.append("Low volatility environment")
                risk_score += 1
        
        # News/Event risk (simplified)
        # In real implementation, integrate with economic calendar
        if datetime.datetime.now().hour in [8, 9, 13, 14, 15]:  # Common news hours
            risk_factors.append("Potential news event hours")
            risk_score += 1
        
        return {
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'risk_level': 'LOW' if risk_score <= 2 else 'MEDIUM' if risk_score <= 5 else 'HIGH'
        }
        
    except Exception as e:
        logger(f"❌ Risk analysis error: {str(e)}")
        return {'risk_score': 10, 'risk_level': 'HIGH'}


def combine_analysis_results(mtf_signals: Dict, tech_signals: Dict, 
                           risk_assessment: Dict, strategy: str) -> Dict[str, Any]:
    """Combine all analysis results into final recommendation"""
    try:
        # Base confidence from technical and MTF analysis
        base_confidence = 0
        signal = None
        
        # MTF weight (60% of decision)
        mtf_weight = 0.6
        tech_weight = 0.4
        
        if mtf_signals['bias'] in ['BULLISH', 'BEARISH']:
            mtf_confidence = mtf_signals['confidence'] * mtf_weight
            mtf_signal = 'BUY' if mtf_signals['bias'] == 'BULLISH' else 'SELL'
        else:
            mtf_confidence = 0
            mtf_signal = None
        
        # Technical analysis weight
        if tech_signals['signal'] in ['BUY', 'SELL']:
            tech_confidence = tech_signals['strength'] * tech_weight
            tech_signal = tech_signals['signal']
        else:
            tech_confidence = 0
            tech_signal = None
        
        # Combine signals
        if mtf_signal == tech_signal and mtf_signal is not None:
            # Both agree
            signal = mtf_signal
            base_confidence = mtf_confidence + tech_confidence
        elif mtf_signal is not None and tech_signal is None:
            # Only MTF has signal
            signal = mtf_signal
            base_confidence = mtf_confidence * 0.8  # Reduce confidence
        elif tech_signal is not None and mtf_signal is None:
            # Only technical has signal
            signal = tech_signal
            base_confidence = tech_confidence * 0.8
        else:
            # No signal or conflicting signals
            signal = None
            base_confidence = 0
        
        # Apply risk adjustment
        risk_multiplier = {
            'LOW': 1.0,
            'MEDIUM': 0.8,
            'HIGH': 0.5
        }
        
        final_confidence = base_confidence * risk_multiplier.get(risk_assessment['risk_level'], 0.5)
        
        # Strategy-specific confidence threshold
        confidence_thresholds = {
            'Scalping': 0.7,
            'HFT': 0.8,
            'Intraday': 0.6,
            'Arbitrage': 0.75
        }
        
        min_confidence = confidence_thresholds.get(strategy, 0.7)
        
        # Final decision
        if final_confidence >= min_confidence and signal is not None:
            recommendation = signal
            confidence = final_confidence
            reason = f"Strong {signal} signal with {final_confidence:.1%} confidence"
        else:
            recommendation = None
            confidence = final_confidence
            if final_confidence < min_confidence:
                reason = f"Signal below confidence threshold ({final_confidence:.1%} < {min_confidence:.1%})"
            else:
                reason = "No clear signal detected"
        
        return {
            'signal': recommendation,
            'confidence': confidence,
            'reason': reason,
            'mtf_analysis': mtf_signals,
            'technical_analysis': tech_signals,
            'risk_assessment': risk_assessment,
            'strategy': strategy
        }
        
    except Exception as e:
        logger(f"❌ Analysis combination error: {str(e)}")
        return {
            'signal': None,
            'confidence': 0,
            'reason': f"Combination error: {str(e)}"
        }