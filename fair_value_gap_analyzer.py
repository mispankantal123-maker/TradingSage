
# --- Fair Value Gap Analyzer ---
"""
Fair Value Gap (FVG) detection and analysis untuk Smart Money Concepts
Identifies imbalance areas yang sering menjadi target institutional money
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import logger
import datetime

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class FairValueGapAnalyzer:
    """Professional Fair Value Gap analyzer untuk institutional trading"""
    
    def __init__(self):
        # FVG detection parameters
        self.min_gap_size = {
            'XAUUSD': 0.5,      # 50 cents for Gold
            'EURUSD': 0.0010,   # 10 pips for major pairs
            'GBPUSD': 0.0010,   # 10 pips
            'USDJPY': 0.10,     # 10 pips (JPY pairs)
            'BTCUSD': 50.0,     # $50 for crypto
            'DEFAULT': 0.0005   # 5 pips default
        }
        
        # FVG quality grades
        self.quality_grades = {
            'PREMIUM': {'min_size_multiplier': 3.0, 'min_volume_ratio': 2.0},
            'HIGH': {'min_size_multiplier': 2.0, 'min_volume_ratio': 1.5},
            'MEDIUM': {'min_size_multiplier': 1.5, 'min_volume_ratio': 1.2},
            'LOW': {'min_size_multiplier': 1.0, 'min_volume_ratio': 1.0}
        }
        
        # FVG effectiveness tracking
        self.fvg_database = []
        
    def detect_fair_value_gaps(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Detect Fair Value Gaps dengan precision tinggi"""
        try:
            if len(df) < 10:
                return {'valid': False, 'reason': 'Insufficient data'}
            
            logger(f"🔍 FVG Analysis: Scanning {symbol} for Fair Value Gaps")
            
            bullish_fvgs = []
            bearish_fvgs = []
            current_price = df['close'].iloc[-1]
            
            # Get minimum gap size for symbol
            min_gap = self._get_min_gap_size(symbol)
            
            # Scan for FVGs in recent data (last 100 bars)
            scan_data = df.tail(100) if len(df) > 100 else df
            
            for i in range(2, len(scan_data)):
                try:
                    # Get three consecutive candles
                    candle1 = scan_data.iloc[i-2]  # First candle
                    candle2 = scan_data.iloc[i-1]  # Gap candle (impulse)
                    candle3 = scan_data.iloc[i]    # Third candle
                    
                    # BULLISH FVG Detection
                    # Condition: candle1 high < candle3 low (gap between them)
                    if candle1['high'] < candle3['low']:
                        gap_size = candle3['low'] - candle1['high']
                        
                        if gap_size >= min_gap:
                            # Calculate FVG quality
                            fvg_quality = self._calculate_fvg_quality(
                                candle1, candle2, candle3, gap_size, min_gap, 'BULLISH'
                            )
                            
                            bullish_fvg = {
                                'type': 'BULLISH',
                                'start_time': candle1.name,
                                'end_time': candle3.name,
                                'top': candle3['low'],
                                'bottom': candle1['high'],
                                'size': gap_size,
                                'size_pips': self._convert_to_pips(gap_size, symbol),
                                'quality': fvg_quality['grade'],
                                'volume_ratio': fvg_quality['volume_ratio'],
                                'impulse_strength': fvg_quality['impulse_strength'],
                                'distance_from_current': abs(current_price - ((candle3['low'] + candle1['high']) / 2)),
                                'is_active': self._is_fvg_active(candle1['high'], candle3['low'], current_price, 'BULLISH'),
                                'fill_percentage': self._calculate_fill_percentage(candle1['high'], candle3['low'], current_price, 'BULLISH'),
                                'created_at': datetime.datetime.now()
                            }
                            
                            bullish_fvgs.append(bullish_fvg)
                    
                    # BEARISH FVG Detection  
                    # Condition: candle1 low > candle3 high (gap between them)
                    if candle1['low'] > candle3['high']:
                        gap_size = candle1['low'] - candle3['high']
                        
                        if gap_size >= min_gap:
                            # Calculate FVG quality
                            fvg_quality = self._calculate_fvg_quality(
                                candle1, candle2, candle3, gap_size, min_gap, 'BEARISH'
                            )
                            
                            bearish_fvg = {
                                'type': 'BEARISH',
                                'start_time': candle1.name,
                                'end_time': candle3.name,
                                'top': candle1['low'],
                                'bottom': candle3['high'],
                                'size': gap_size,
                                'size_pips': self._convert_to_pips(gap_size, symbol),
                                'quality': fvg_quality['grade'],
                                'volume_ratio': fvg_quality['volume_ratio'],
                                'impulse_strength': fvg_quality['impulse_strength'],
                                'distance_from_current': abs(current_price - ((candle1['low'] + candle3['high']) / 2)),
                                'is_active': self._is_fvg_active(candle3['high'], candle1['low'], current_price, 'BEARISH'),
                                'fill_percentage': self._calculate_fill_percentage(candle3['high'], candle1['low'], current_price, 'BEARISH'),
                                'created_at': datetime.datetime.now()
                            }
                            
                            bearish_fvgs.append(bearish_fvg)
                            
                except Exception as candle_e:
                    continue
            
            # Sort FVGs by quality and proximity to current price
            bullish_fvgs = sorted(bullish_fvgs, key=lambda x: (
                self._quality_score(x['quality']),
                -x['distance_from_current']
            ), reverse=True)
            
            bearish_fvgs = sorted(bearish_fvgs, key=lambda x: (
                self._quality_score(x['quality']),
                -x['distance_from_current']
            ), reverse=True)
            
            # Get most relevant FVGs
            active_bullish = [fvg for fvg in bullish_fvgs if fvg['is_active']][:5]
            active_bearish = [fvg for fvg in bearish_fvgs if fvg['is_active']][:5]
            
            total_fvgs = len(active_bullish) + len(active_bearish)
            
            logger(f"✅ FVG Detection Complete: {len(active_bullish)} bullish, {len(active_bearish)} bearish")
            
            if total_fvgs > 0:
                for fvg in active_bullish[:3]:  # Log top 3
                    logger(f"   🟢 BULLISH FVG: {fvg['size_pips']:.1f} pips ({fvg['quality']}) - Fill: {fvg['fill_percentage']:.1f}%")
                
                for fvg in active_bearish[:3]:  # Log top 3
                    logger(f"   🔴 BEARISH FVG: {fvg['size_pips']:.1f} pips ({fvg['quality']}) - Fill: {fvg['fill_percentage']:.1f}%")
            
            return {
                'valid': True,
                'bullish_fvgs': active_bullish,
                'bearish_fvgs': active_bearish,
                'total_active_fvgs': total_fvgs,
                'analysis_timestamp': datetime.datetime.now(),
                'symbol': symbol,
                'current_price': current_price
            }
            
        except Exception as e:
            logger(f"❌ FVG detection error for {symbol}: {str(e)}")
            return {'valid': False, 'error': str(e)}

    def get_fvg_trading_signals(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Generate trading signals based on FVG analysis"""
        try:
            fvg_analysis = self.detect_fair_value_gaps(df, symbol)
            
            if not fvg_analysis['valid']:
                return {'signal': None, 'confidence': 0, 'reason': 'FVG analysis failed'}
            
            current_price = fvg_analysis['current_price']
            signals = []
            signal_strength = 0
            
            # Analyze bullish FVG opportunities
            for fvg in fvg_analysis['bullish_fvgs']:
                if self._is_price_approaching_fvg(current_price, fvg, 'BULLISH'):
                    quality_weight = self._quality_score(fvg['quality']) / 4.0
                    proximity_weight = max(0.2, 1.0 - (fvg['distance_from_current'] / current_price))
                    
                    fvg_signal_strength = quality_weight * proximity_weight * 2
                    signal_strength += fvg_signal_strength
                    
                    signals.append(f"Bullish FVG support at {fvg['bottom']:.5f}-{fvg['top']:.5f} ({fvg['quality']})")
            
            # Analyze bearish FVG opportunities  
            for fvg in fvg_analysis['bearish_fvgs']:
                if self._is_price_approaching_fvg(current_price, fvg, 'BEARISH'):
                    quality_weight = self._quality_score(fvg['quality']) / 4.0
                    proximity_weight = max(0.2, 1.0 - (fvg['distance_from_current'] / current_price))
                    
                    fvg_signal_strength = quality_weight * proximity_weight * 2
                    signal_strength -= fvg_signal_strength  # Negative for bearish
                    
                    signals.append(f"Bearish FVG resistance at {fvg['bottom']:.5f}-{fvg['top']:.5f} ({fvg['quality']})")
            
            # Determine final signal
            if signal_strength > 1.0:
                return {
                    'signal': 'BUY',
                    'confidence': min(0.85, signal_strength / 3.0),
                    'reason': 'Strong bullish FVG confluence',
                    'signals': signals,
                    'fvg_analysis': fvg_analysis
                }
            elif signal_strength < -1.0:
                return {
                    'signal': 'SELL',
                    'confidence': min(0.85, abs(signal_strength) / 3.0),
                    'reason': 'Strong bearish FVG confluence',
                    'signals': signals,
                    'fvg_analysis': fvg_analysis
                }
            else:
                return {
                    'signal': None,
                    'confidence': abs(signal_strength) / 3.0,
                    'reason': 'Insufficient FVG signal strength',
                    'signals': signals,
                    'fvg_analysis': fvg_analysis
                }
                
        except Exception as e:
            logger(f"❌ FVG trading signals error: {str(e)}")
            return {'signal': None, 'confidence': 0, 'error': str(e)}

    def _get_min_gap_size(self, symbol: str) -> float:
        """Get minimum gap size for symbol"""
        symbol_upper = symbol.upper()
        
        for key in self.min_gap_size:
            if key in symbol_upper:
                return self.min_gap_size[key]
        
        return self.min_gap_size['DEFAULT']

    def _calculate_fvg_quality(self, candle1: pd.Series, candle2: pd.Series, 
                              candle3: pd.Series, gap_size: float, 
                              min_gap: float, fvg_type: str) -> Dict[str, Any]:
        """Calculate FVG quality based on multiple factors"""
        try:
            # Size factor
            size_multiplier = gap_size / min_gap
            
            # Volume factor (if available)
            volume_ratio = 1.0
            if 'tick_volume' in candle2:
                avg_volume = (candle1.get('tick_volume', 1000) + candle3.get('tick_volume', 1000)) / 2
                volume_ratio = candle2.get('tick_volume', 1000) / avg_volume if avg_volume > 0 else 1.0
            
            # Impulse strength (based on candle2 - the gap-creating candle)
            candle2_body = abs(candle2['close'] - candle2['open'])
            candle2_range = candle2['high'] - candle2['low']
            impulse_strength = candle2_body / candle2_range if candle2_range > 0 else 0.5
            
            # Determine quality grade
            quality_grade = 'LOW'
            for grade, criteria in self.quality_grades.items():
                if (size_multiplier >= criteria['min_size_multiplier'] and 
                    volume_ratio >= criteria['min_volume_ratio']):
                    quality_grade = grade
                    break
            
            return {
                'grade': quality_grade,
                'size_multiplier': size_multiplier,
                'volume_ratio': volume_ratio,
                'impulse_strength': impulse_strength
            }
            
        except Exception as e:
            return {'grade': 'LOW', 'size_multiplier': 1.0, 'volume_ratio': 1.0, 'impulse_strength': 0.5}

    def _is_fvg_active(self, fvg_bottom: float, fvg_top: float, 
                      current_price: float, fvg_type: str) -> bool:
        """Check if FVG is still active (not fully filled)"""
        if fvg_type == 'BULLISH':
            # Bullish FVG is active if price hasn't fully closed above it
            return current_price <= fvg_top * 1.001  # Small buffer
        else:  # BEARISH
            # Bearish FVG is active if price hasn't fully closed below it
            return current_price >= fvg_bottom * 0.999  # Small buffer

    def _calculate_fill_percentage(self, fvg_bottom: float, fvg_top: float, 
                                  current_price: float, fvg_type: str) -> float:
        """Calculate how much of the FVG has been filled"""
        try:
            fvg_size = abs(fvg_top - fvg_bottom)
            
            if fvg_type == 'BULLISH':
                if current_price <= fvg_bottom:
                    return 0.0  # Not filled at all
                elif current_price >= fvg_top:
                    return 100.0  # Completely filled
                else:
                    filled_amount = current_price - fvg_bottom
                    return (filled_amount / fvg_size) * 100.0
            else:  # BEARISH
                if current_price >= fvg_top:
                    return 0.0  # Not filled at all
                elif current_price <= fvg_bottom:
                    return 100.0  # Completely filled
                else:
                    filled_amount = fvg_top - current_price
                    return (filled_amount / fvg_size) * 100.0
                    
        except Exception as e:
            return 0.0

    def _is_price_approaching_fvg(self, current_price: float, fvg: Dict, fvg_type: str) -> bool:
        """Check if price is approaching an FVG (within reasonable distance)"""
        try:
            fvg_center = (fvg['top'] + fvg['bottom']) / 2
            distance_ratio = abs(current_price - fvg_center) / current_price
            
            # Consider FVG relevant if within 2% of current price
            return distance_ratio <= 0.02
            
        except Exception as e:
            return False

    def _quality_score(self, quality: str) -> int:
        """Convert quality grade to numerical score"""
        scores = {'PREMIUM': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        return scores.get(quality, 1)

    def _convert_to_pips(self, value: float, symbol: str) -> float:
        """Convert price difference to pips"""
        try:
            if 'JPY' in symbol.upper():
                return value * 100  # JPY pairs: 1 pip = 0.01
            elif any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'LTC']):
                return value  # Crypto in absolute value
            else:
                return value * 10000  # Major pairs: 1 pip = 0.0001
        except:
            return value * 10000


# Global instance
fvg_analyzer = FairValueGapAnalyzer()


def get_fair_value_gap_analysis(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Get comprehensive Fair Value Gap analysis"""
    return fvg_analyzer.detect_fair_value_gaps(df, symbol)


def get_fvg_trading_signals(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Get trading signals based on Fair Value Gap analysis"""
    return fvg_analyzer.get_fvg_trading_signals(df, symbol)
