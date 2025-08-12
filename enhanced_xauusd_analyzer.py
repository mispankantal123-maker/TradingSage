# --- Enhanced XAU/USD Professional Analyzer ---
"""
Professional XAU/USD analysis engine untuk scalping dengan:
- Multi-timeframe confluence
- Session-based trading
- Smart Money Concepts
- Volume Profile Analysis
- DXY Correlation
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


class XAUUSDProfessionalAnalyzer:
    """Professional XAU/USD analysis untuk 2 miliar profit/month target"""
    
    def __init__(self):
        self.symbol = "XAUUSD"
        self.timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4
        }
        
        # Professional trading sessions (UTC)
        self.sessions = {
            'ASIAN': {'start': 0, 'end': 8, 'volatility': 'LOW'},
            'LONDON': {'start': 8, 'end': 16, 'volatility': 'HIGH'},
            'NEW_YORK': {'start': 13, 'end': 21, 'volatility': 'HIGH'},
            'OVERLAP': {'start': 13, 'end': 16, 'volatility': 'EXTREME'}  # London-NY overlap
        }
        
        # XAU/USD specific parameters
        self.xau_config = {
            'spread_limit': 5.0,  # Maximum spread in USD
            'min_atr_pips': 200,  # Minimum volatility for trading
            'max_atr_pips': 800,  # Maximum volatility threshold
            'optimal_sessions': ['LONDON', 'NEW_YORK', 'OVERLAP'],
            'correlation_threshold': 0.7  # DXY correlation threshold
        }

    def get_current_session(self) -> Dict[str, Any]:
        """Get current trading session dengan volatility assessment"""
        try:
            current_hour = datetime.datetime.utcnow().hour
            
            for session_name, session_info in self.sessions.items():
                start = session_info['start']
                end = session_info['end']
                
                if start <= current_hour < end:
                    return {
                        'name': session_name,
                        'volatility': session_info['volatility'],
                        'hour': current_hour,
                        'trading_recommended': session_name in self.xau_config['optimal_sessions']
                    }
            
            return {
                'name': 'OFF_HOURS',
                'volatility': 'VERY_LOW',
                'hour': current_hour,
                'trading_recommended': False
            }
            
        except Exception as e:
            logger(f"❌ Error getting session: {str(e)}")
            return {'name': 'UNKNOWN', 'volatility': 'UNKNOWN', 'trading_recommended': False}

    def analyze_multi_timeframe_confluence(self) -> Dict[str, Any]:
        """Professional multi-timeframe analysis untuk XAU/USD"""
        try:
            logger(f"🔍 XAU/USD Multi-Timeframe Professional Analysis")
            
            confluence_analysis = {
                'timeframes': {},
                'overall_bias': 'NEUTRAL',
                'confluence_score': 0,
                'signal_strength': 'WEAK',
                'trading_recommendation': 'WAIT',
                'confluence_factors': [],
                'risk_factors': []
            }
            
            # Analyze each timeframe with XAU/USD specific logic
            timeframe_scores = {}
            
            for tf_name, tf_value in self.timeframes.items():
                tf_analysis = self._analyze_xauusd_timeframe(tf_name, tf_value)
                confluence_analysis['timeframes'][tf_name] = tf_analysis
                
                if tf_analysis['valid']:
                    # Weight by timeframe importance for XAU/USD scalping
                    weight = self._get_xauusd_timeframe_weight(tf_name)
                    timeframe_scores[tf_name] = {
                        'bias': tf_analysis['bias'],
                        'strength': tf_analysis['strength'],
                        'weight': weight
                    }
            
            # Calculate confluence
            total_bullish = 0
            total_bearish = 0
            total_weight = 0
            
            for tf_data in timeframe_scores.values():
                if tf_data['bias'] == 'BULLISH':
                    total_bullish += tf_data['strength'] * tf_data['weight']
                elif tf_data['bias'] == 'BEARISH':
                    total_bearish += tf_data['strength'] * tf_data['weight']
                total_weight += tf_data['weight']
            
            if total_weight > 0:
                bullish_percentage = (total_bullish / total_weight) * 100
                bearish_percentage = (total_bearish / total_weight) * 100
                
                # XAU/USD specific confluence logic
                if bullish_percentage > bearish_percentage + 30:  # Higher threshold for XAU/USD
                    confluence_analysis['overall_bias'] = 'BULLISH'
                    confluence_analysis['confluence_score'] = bullish_percentage
                elif bearish_percentage > bullish_percentage + 30:
                    confluence_analysis['overall_bias'] = 'BEARISH'
                    confluence_analysis['confluence_score'] = bearish_percentage
                
                # Signal strength untuk XAU/USD
                max_score = max(bullish_percentage, bearish_percentage)
                if max_score >= 80:
                    confluence_analysis['signal_strength'] = 'VERY_STRONG'
                    confluence_analysis['trading_recommendation'] = 'STRONG_ENTRY'
                elif max_score >= 70:
                    confluence_analysis['signal_strength'] = 'STRONG'
                    confluence_analysis['trading_recommendation'] = 'ENTRY'
                elif max_score >= 60:
                    confluence_analysis['signal_strength'] = 'MODERATE'
                    confluence_analysis['trading_recommendation'] = 'CAREFUL_ENTRY'
                else:
                    confluence_analysis['trading_recommendation'] = 'WAIT'
            
            return confluence_analysis
            
        except Exception as e:
            logger(f"❌ XAU/USD MTF analysis error: {str(e)}")
            return {
                'overall_bias': 'NEUTRAL',
                'confluence_score': 0,
                'trading_recommendation': 'ERROR',
                'error': str(e)
            }

    def _analyze_xauusd_timeframe(self, tf_name: str, tf_value: int) -> Dict[str, Any]:
        """Analyze single timeframe untuk XAU/USD dengan professional logic"""
        try:
            # Get data for timeframe
            rates = mt5.copy_rates_from_pos(self.symbol, tf_value, 0, 200)
            
            if rates is None or len(rates) < 50:
                return {'valid': False, 'error': 'Insufficient data'}
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate XAU/USD specific indicators
            from indicators import calculate_indicators
            df = calculate_indicators(df)
            
            if df is None:
                return {'valid': False, 'error': 'Indicator calculation failed'}
            
            # XAU/USD specific analysis
            analysis = {
                'valid': True,
                'timeframe': tf_name,
                'bias': 'NEUTRAL',
                'strength': 0,
                'factors': []
            }
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            bullish_signals = 0
            bearish_signals = 0
            
            # 1. Trend Analysis (Higher weight for higher timeframes)
            if 'EMA20' in df.columns and 'EMA50' in df.columns:
                if last['close'] > last['EMA20'] > last['EMA50']:
                    bullish_signals += 2 if tf_name in ['H1', 'H4'] else 1
                    analysis['factors'].append(f"{tf_name}: Bullish EMA alignment")
                elif last['close'] < last['EMA20'] < last['EMA50']:
                    bearish_signals += 2 if tf_name in ['H1', 'H4'] else 1
                    analysis['factors'].append(f"{tf_name}: Bearish EMA alignment")
            
            # 2. Momentum Analysis
            if 'RSI' in df.columns:
                rsi = last['RSI']
                if 30 < rsi < 70:  # Not in extreme territory
                    if rsi > 55:
                        bullish_signals += 1
                    elif rsi < 45:
                        bearish_signals += 1
            
            # 3. MACD Analysis
            if 'MACD' in df.columns and 'MACD_signal' in df.columns:
                if last['MACD'] > last['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
                    bullish_signals += 2  # MACD crossover bullish
                    analysis['factors'].append(f"{tf_name}: MACD bullish crossover")
                elif last['MACD'] < last['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
                    bearish_signals += 2  # MACD crossover bearish
                    analysis['factors'].append(f"{tf_name}: MACD bearish crossover")
            
            # 4. Volume Analysis (for XAU/USD momentum)
            if 'tick_volume' in df.columns and 'volume_ratio' in df.columns:
                if last['volume_ratio'] > 1.5:  # High volume
                    if last['close'] > prev['close']:
                        bullish_signals += 1
                    else:
                        bearish_signals += 1
            
            # Determine bias and strength
            total_signals = bullish_signals + bearish_signals
            if total_signals > 0:
                if bullish_signals > bearish_signals:
                    analysis['bias'] = 'BULLISH'
                    analysis['strength'] = min(10, bullish_signals)
                elif bearish_signals > bullish_signals:
                    analysis['bias'] = 'BEARISH'
                    analysis['strength'] = min(10, bearish_signals)
                else:
                    analysis['bias'] = 'NEUTRAL'
                    analysis['strength'] = 2
            
            return analysis
            
        except Exception as e:
            logger(f"❌ Error analyzing {tf_name}: {str(e)}")
            return {'valid': False, 'error': str(e)}

    def _get_xauusd_timeframe_weight(self, tf_name: str) -> float:
        """Get timeframe weight untuk XAU/USD scalping"""
        weights = {
            'M1': 1.0,   # Entry timing
            'M5': 1.5,   # Signal confirmation
            'M15': 2.0,  # Trend direction
            'H1': 3.0,   # Major trend filter
            'H4': 2.5    # Long-term bias
        }
        return weights.get(tf_name, 1.0)

    def analyze_smart_money_concepts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Smart Money Concepts untuk XAU/USD"""
        try:
            if len(df) < 50:
                return {'valid': False}
            
            smart_money = {
                'order_blocks': self._detect_order_blocks(df),
                'supply_demand': self._detect_supply_demand_zones(df),
                'liquidity_pools': self._detect_liquidity_pools(df),
                'market_structure': self._analyze_market_structure(df)
            }
            
            return smart_money
            
        except Exception as e:
            logger(f"❌ Smart Money analysis error: {str(e)}")
            return {'valid': False, 'error': str(e)}

    def _detect_order_blocks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect institutional order blocks"""
        order_blocks = []
        
        try:
            # Look for significant price moves with volume
            for i in range(10, len(df) - 5):
                current = df.iloc[i]
                prev_5 = df.iloc[i-5:i]
                next_5 = df.iloc[i+1:i+6]
                
                # Bullish order block detection
                if (current['close'] > current['open'] and
                    current['high'] - current['low'] > prev_5['high'].max() - prev_5['low'].min() and
                    'volume_ratio' in df.columns and current['volume_ratio'] > 1.5):
                    
                    order_blocks.append({
                        'type': 'BULLISH_OB',
                        'level': current['low'],
                        'strength': current['volume_ratio'],
                        'time': current.get('time', i)
                    })
                
                # Bearish order block detection
                elif (current['close'] < current['open'] and
                      current['high'] - current['low'] > prev_5['high'].max() - prev_5['low'].min() and
                      'volume_ratio' in df.columns and current['volume_ratio'] > 1.5):
                    
                    order_blocks.append({
                        'type': 'BEARISH_OB',
                        'level': current['high'],
                        'strength': current['volume_ratio'],
                        'time': current.get('time', i)
                    })
            
            return order_blocks[-10:]  # Last 10 order blocks
            
        except Exception as e:
            logger(f"❌ Order block detection error: {str(e)}")
            return []

    def _detect_supply_demand_zones(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect supply and demand zones"""
        zones = []
        
        try:
            # Look for significant levels where price reacted multiple times
            highs = df['high'].rolling(window=10).max()
            lows = df['low'].rolling(window=10).min()
            
            # Find potential supply zones (resistance)
            for i in range(20, len(df) - 10):
                level = highs.iloc[i]
                touches = 0
                
                # Count how many times price touched this level
                for j in range(max(0, i-20), min(len(df), i+20)):
                    if abs(df.iloc[j]['high'] - level) < level * 0.001:  # Within 0.1%
                        touches += 1
                
                if touches >= 3:
                    zones.append({
                        'type': 'SUPPLY',
                        'level': level,
                        'strength': touches,
                        'zone_range': [level * 0.999, level * 1.001]
                    })
            
            # Find potential demand zones (support)
            for i in range(20, len(df) - 10):
                level = lows.iloc[i]
                touches = 0
                
                for j in range(max(0, i-20), min(len(df), i+20)):
                    if abs(df.iloc[j]['low'] - level) < level * 0.001:
                        touches += 1
                
                if touches >= 3:
                    zones.append({
                        'type': 'DEMAND',
                        'level': level,
                        'strength': touches,
                        'zone_range': [level * 0.999, level * 1.001]
                    })
            
            return zones[-5:]  # Last 5 zones
            
        except Exception as e:
            logger(f"❌ Supply/Demand detection error: {str(e)}")
            return []

    def _detect_liquidity_pools(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect liquidity pools (stop hunting zones)"""
        pools = []
        
        try:
            # Find swing highs and lows (potential stop hunting areas)
            for i in range(10, len(df) - 10):
                current = df.iloc[i]
                prev_window = df.iloc[i-10:i]
                next_window = df.iloc[i+1:i+11]
                
                # Swing high detection
                if (current['high'] > prev_window['high'].max() and
                    current['high'] > next_window['high'].max()):
                    pools.append({
                        'type': 'LIQUIDITY_HIGH',
                        'level': current['high'],
                        'potential_target': current['high'] + (current['high'] * 0.001)
                    })
                
                # Swing low detection
                if (current['low'] < prev_window['low'].min() and
                    current['low'] < next_window['low'].min()):
                    pools.append({
                        'type': 'LIQUIDITY_LOW',
                        'level': current['low'],
                        'potential_target': current['low'] - (current['low'] * 0.001)
                    })
            
            return pools[-10:]  # Last 10 liquidity pools
            
        except Exception as e:
            logger(f"❌ Liquidity pool detection error: {str(e)}")
            return []

    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market structure (HH/HL, LH/LL)"""
        try:
            structure = {
                'trend': 'RANGING',
                'structure_breaks': [],
                'key_levels': []
            }
            
            # Find recent swing points
            swing_highs = []
            swing_lows = []
            
            for i in range(5, len(df) - 5):
                window = df.iloc[i-5:i+6]
                current = df.iloc[i]
                
                if current['high'] == window['high'].max():
                    swing_highs.append({'index': i, 'price': current['high']})
                
                if current['low'] == window['low'].min():
                    swing_lows.append({'index': i, 'price': current['low']})
            
            # Analyze trend structure
            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                recent_highs = swing_highs[-3:]
                recent_lows = swing_lows[-3:]
                
                # Check for higher highs and higher lows (uptrend)
                if (len(recent_highs) >= 2 and recent_highs[-1]['price'] > recent_highs[-2]['price'] and
                    len(recent_lows) >= 2 and recent_lows[-1]['price'] > recent_lows[-2]['price']):
                    structure['trend'] = 'UPTREND'
                
                # Check for lower highs and lower lows (downtrend)
                elif (len(recent_highs) >= 2 and recent_highs[-1]['price'] < recent_highs[-2]['price'] and
                      len(recent_lows) >= 2 and recent_lows[-1]['price'] < recent_lows[-2]['price']):
                    structure['trend'] = 'DOWNTREND'
            
            return structure
            
        except Exception as e:
            logger(f"❌ Market structure analysis error: {str(e)}")
            return {'trend': 'UNKNOWN'}

    def get_xauusd_trading_recommendation(self) -> Dict[str, Any]:
        """Get comprehensive XAU/USD trading recommendation"""
        try:
            # Get session info
            session = self.get_current_session()
            
            # Get multi-timeframe analysis
            mtf_analysis = self.analyze_multi_timeframe_confluence()
            
            # Get current tick
            tick = mt5.symbol_info_tick(self.symbol)
            spread = (tick.ask - tick.bid) if tick else 999
            
            recommendation = {
                'symbol': self.symbol,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'session': session,
                'mtf_analysis': mtf_analysis,
                'spread_analysis': {
                    'current_spread': spread,
                    'spread_acceptable': spread <= self.xau_config['spread_limit'],
                    'spread_quality': 'GOOD' if spread <= 3 else 'ACCEPTABLE' if spread <= 5 else 'POOR'
                },
                'trading_decision': 'WAIT',
                'confidence': 0,
                'risk_level': 'HIGH'
            }
            
            # Make trading decision
            if (session['trading_recommended'] and 
                mtf_analysis['trading_recommendation'] in ['ENTRY', 'STRONG_ENTRY'] and
                recommendation['spread_analysis']['spread_acceptable']):
                
                recommendation['trading_decision'] = mtf_analysis['overall_bias']
                recommendation['confidence'] = mtf_analysis['confluence_score']
                recommendation['risk_level'] = 'MEDIUM' if mtf_analysis['signal_strength'] == 'VERY_STRONG' else 'HIGH'
            
            return recommendation
            
        except Exception as e:
            logger(f"❌ XAU/USD recommendation error: {str(e)}")
            return {
                'trading_decision': 'ERROR',
                'error': str(e),
                'confidence': 0
            }


# Global instance
xauusd_analyzer = XAUUSDProfessionalAnalyzer()


def get_xauusd_professional_analysis(symbol: str = "XAUUSD") -> Dict[str, Any]:
    """Main function untuk mendapatkan XAU/USD professional analysis"""
    if symbol.upper() in ['XAUUSD', 'GOLD']:
        return xauusd_analyzer.get_xauusd_trading_recommendation()
    else:
        return {'error': 'This analyzer is specifically for XAU/USD'}