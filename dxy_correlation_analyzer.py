# --- DXY Correlation Analyzer ---
"""
Professional DXY correlation analysis untuk XAU/USD trading
Implements correlation-based filtering untuk higher probability setups
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, Optional, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class DXYCorrelationAnalyzer:
    """Professional DXY correlation analysis untuk XAU/USD optimization"""
    
    def __init__(self):
        self.dxy_symbol = "USDX"  # Common DXY symbol
        self.correlation_window = 50  # Bars for correlation calculation
        self.correlation_threshold = 0.6  # Minimum correlation for signal validity
        
        # Historical correlation expectations
        self.expected_correlations = {
            'XAUUSD': -0.75,  # Negative correlation expected
            'EURUSD': -0.85,  # Strong negative correlation
            'GBPUSD': -0.70,
            'USDJPY': 0.65,   # Positive correlation
            'USDCHF': 0.80
        }

    def get_dxy_data(self, bars: int = 100) -> Optional[pd.DataFrame]:
        """Get DXY data dengan fallback methods"""
        try:
            # Try primary DXY symbol
            rates = mt5.copy_rates_from_pos(self.dxy_symbol, mt5.TIMEFRAME_H1, 0, bars)
            
            if rates is None or len(rates) < 20:
                # Try alternative symbols
                alternative_symbols = ["DXY", "USDX", "DX-1!", "US30"]
                
                for alt_symbol in alternative_symbols:
                    try:
                        rates = mt5.copy_rates_from_pos(alt_symbol, mt5.TIMEFRAME_H1, 0, bars)
                        if rates is not None and len(rates) >= 20:
                            logger(f"✅ Using {alt_symbol} as DXY proxy")
                            break
                    except:
                        continue
            
            if rates is None or len(rates) < 20:
                # Create synthetic DXY based on major pairs
                logger("⚠️ Creating synthetic DXY from major pairs")
                return self._create_synthetic_dxy(bars)
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            logger(f"❌ Error getting DXY data: {str(e)}")
            return None

    def _create_synthetic_dxy(self, bars: int) -> Optional[pd.DataFrame]:
        """Create synthetic DXY from major currency pairs"""
        try:
            # Get major pairs
            pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
            pair_data = {}
            
            for pair in pairs:
                rates = mt5.copy_rates_from_pos(pair, mt5.TIMEFRAME_H1, 0, bars)
                if rates is not None:
                    pair_data[pair] = pd.DataFrame(rates)
            
            if len(pair_data) < 2:
                return None
            
            # Create synthetic DXY index
            # Simplified formula based on major pairs
            base_times = None
            synthetic_values = []
            
            for pair, df in pair_data.items():
                df['time'] = pd.to_datetime(df['time'], unit='s')
                if base_times is None:
                    base_times = df['time']
                
                # Invert EUR and GBP (negative weight in DXY)
                if pair in ['EURUSD', 'GBPUSD']:
                    values = 1 / df['close']
                else:
                    values = df['close']
                
                synthetic_values.append(values)
            
            if len(synthetic_values) > 0:
                # Combine and normalize
                combined = np.array(synthetic_values).mean(axis=0)
                normalized = (combined / combined[0]) * 100  # Normalize to 100
                
                synthetic_df = pd.DataFrame({
                    'time': base_times[:len(normalized)],
                    'open': normalized,
                    'high': normalized * 1.001,
                    'low': normalized * 0.999,
                    'close': normalized,
                    'tick_volume': 1000
                })
                
                logger("✅ Synthetic DXY created from major pairs")
                return synthetic_df
            
            return None
            
        except Exception as e:
            logger(f"❌ Error creating synthetic DXY: {str(e)}")
            return None

    def calculate_correlation(self, symbol: str, symbol_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation between symbol and DXY"""
        try:
            # Get DXY data
            dxy_df = self.get_dxy_data(len(symbol_df))
            
            if dxy_df is None or len(dxy_df) < 20:
                return {
                    'correlation': 0,
                    'correlation_valid': False,
                    'signal_filter': 'NEUTRAL',
                    'reason': 'DXY data unavailable'
                }
            
            # Align timeframes
            min_length = min(len(symbol_df), len(dxy_df))
            if min_length < self.correlation_window:
                window = min_length - 1
            else:
                window = self.correlation_window
            
            # Calculate correlation on recent data
            symbol_prices = symbol_df['close'].tail(window).values
            dxy_prices = dxy_df['close'].tail(window).values
            
            if len(symbol_prices) != len(dxy_prices):
                min_len = min(len(symbol_prices), len(dxy_prices))
                symbol_prices = symbol_prices[-min_len:]
                dxy_prices = dxy_prices[-min_len:]
            
            # Calculate correlation
            correlation = np.corrcoef(symbol_prices, dxy_prices)[0, 1]
            
            if np.isnan(correlation):
                correlation = 0
            
            # Get expected correlation for this symbol
            expected_corr = self.expected_correlations.get(symbol.upper(), 0)
            
            # Analyze correlation strength and direction
            correlation_analysis = self._analyze_correlation_signals(
                symbol, correlation, expected_corr, symbol_df, dxy_df
            )
            
            return correlation_analysis
            
        except Exception as e:
            logger(f"❌ Correlation calculation error: {str(e)}")
            return {
                'correlation': 0,
                'correlation_valid': False,
                'signal_filter': 'NEUTRAL',
                'reason': f'Calculation error: {str(e)}'
            }

    def _analyze_correlation_signals(self, symbol: str, correlation: float, 
                                   expected_corr: float, symbol_df: pd.DataFrame, 
                                   dxy_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlation signals for trading decisions"""
        try:
            # Check if correlation is significant
            correlation_valid = abs(correlation) >= self.correlation_threshold
            
            # Get recent price movements
            symbol_recent_change = (symbol_df['close'].iloc[-1] - symbol_df['close'].iloc[-5]) / symbol_df['close'].iloc[-5]
            dxy_recent_change = (dxy_df['close'].iloc[-1] - dxy_df['close'].iloc[-5]) / dxy_df['close'].iloc[-5]
            
            # Analyze correlation-based signals
            signal_filter = 'NEUTRAL'
            confidence_multiplier = 1.0
            reason = f"Correlation: {correlation:.3f}"
            
            if correlation_valid:
                # For negative correlation (like XAU/USD)
                if expected_corr < 0:
                    if dxy_recent_change > 0.002:  # DXY rising
                        signal_filter = 'BEARISH'  # Expect symbol to fall
                        confidence_multiplier = abs(correlation)
                        reason += " - DXY rising, expect bearish move"
                    elif dxy_recent_change < -0.002:  # DXY falling
                        signal_filter = 'BULLISH'  # Expect symbol to rise
                        confidence_multiplier = abs(correlation)
                        reason += " - DXY falling, expect bullish move"
                
                # For positive correlation
                elif expected_corr > 0:
                    if dxy_recent_change > 0.002:  # DXY rising
                        signal_filter = 'BULLISH'  # Expect symbol to rise
                        confidence_multiplier = abs(correlation)
                        reason += " - DXY rising, expect bullish move"
                    elif dxy_recent_change < -0.002:  # DXY falling
                        signal_filter = 'BEARISH'  # Expect symbol to fall
                        confidence_multiplier = abs(correlation)
                        reason += " - DXY falling, expect bearish move"
            
            # Additional analysis
            correlation_strength = 'WEAK'
            if abs(correlation) >= 0.8:
                correlation_strength = 'VERY_STRONG'
            elif abs(correlation) >= 0.7:
                correlation_strength = 'STRONG'
            elif abs(correlation) >= 0.6:
                correlation_strength = 'MODERATE'
            
            return {
                'correlation': correlation,
                'expected_correlation': expected_corr,
                'correlation_valid': correlation_valid,
                'correlation_strength': correlation_strength,
                'signal_filter': signal_filter,
                'confidence_multiplier': confidence_multiplier,
                'dxy_trend': 'UP' if dxy_recent_change > 0 else 'DOWN',
                'dxy_change_pct': dxy_recent_change * 100,
                'reason': reason
            }
            
        except Exception as e:
            logger(f"❌ Correlation signal analysis error: {str(e)}")
            return {
                'correlation': correlation,
                'correlation_valid': False,
                'signal_filter': 'NEUTRAL',
                'reason': f'Analysis error: {str(e)}'
            }

    def get_dxy_filter_recommendation(self, symbol: str, signal: str, 
                                    confidence: float) -> Dict[str, Any]:
        """Get DXY-filtered trading recommendation"""
        try:
            # Get symbol data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
            if rates is None:
                return {
                    'filtered_signal': signal,
                    'filtered_confidence': confidence,
                    'dxy_filter': 'NO_DATA'
                }
            
            symbol_df = pd.DataFrame(rates)
            symbol_df['time'] = pd.to_datetime(symbol_df['time'], unit='s')
            
            # Get correlation analysis
            correlation_analysis = self.calculate_correlation(symbol, symbol_df)
            
            # Apply DXY filter
            if correlation_analysis['correlation_valid']:
                dxy_filter = correlation_analysis['signal_filter']
                
                # Check if DXY filter agrees with signal
                if signal == 'BUY' and dxy_filter == 'BULLISH':
                    # DXY supports BUY signal
                    filtered_confidence = confidence * correlation_analysis['confidence_multiplier']
                    filtered_signal = signal
                    filter_result = 'CONFIRMS'
                elif signal == 'SELL' and dxy_filter == 'BEARISH':
                    # DXY supports SELL signal
                    filtered_confidence = confidence * correlation_analysis['confidence_multiplier']
                    filtered_signal = signal
                    filter_result = 'CONFIRMS'
                elif dxy_filter == 'NEUTRAL':
                    # DXY neutral, keep original signal
                    filtered_confidence = confidence * 0.9  # Slight reduction
                    filtered_signal = signal
                    filter_result = 'NEUTRAL'
                else:
                    # DXY contradicts signal
                    filtered_confidence = confidence * 0.5  # Significant reduction
                    filtered_signal = signal  # Keep but with lower confidence
                    filter_result = 'CONTRADICTS'
            else:
                # Correlation not valid, keep original
                filtered_confidence = confidence
                filtered_signal = signal
                filter_result = 'INSUFFICIENT_DATA'
            
            return {
                'filtered_signal': filtered_signal,
                'filtered_confidence': min(1.0, filtered_confidence),  # Cap at 100%
                'original_confidence': confidence,
                'dxy_filter': filter_result,
                'correlation_analysis': correlation_analysis
            }
            
        except Exception as e:
            logger(f"❌ DXY filter recommendation error: {str(e)}")
            return {
                'filtered_signal': signal,
                'filtered_confidence': confidence,
                'dxy_filter': 'ERROR'
            }


# Global instance
dxy_analyzer = DXYCorrelationAnalyzer()


def apply_dxy_correlation_filter(symbol: str, signal: str, confidence: float) -> Dict[str, Any]:
    """Apply DXY correlation filter to trading signal"""
    return dxy_analyzer.get_dxy_filter_recommendation(symbol, signal, confidence)


def get_dxy_market_bias() -> Dict[str, Any]:
    """Get current DXY market bias untuk general market context"""
    try:
        dxy_df = dxy_analyzer.get_dxy_data(50)
        if dxy_df is None:
            return {'bias': 'UNKNOWN', 'strength': 0}
        
        # Simple trend analysis
        recent_change = (dxy_df['close'].iloc[-1] - dxy_df['close'].iloc[-10]) / dxy_df['close'].iloc[-10]
        
        if recent_change > 0.01:
            return {'bias': 'BULLISH', 'strength': min(abs(recent_change) * 100, 10)}
        elif recent_change < -0.01:
            return {'bias': 'BEARISH', 'strength': min(abs(recent_change) * 100, 10)}
        else:
            return {'bias': 'NEUTRAL', 'strength': 1}
            
    except Exception as e:
        logger(f"❌ DXY bias error: {str(e)}")
        return {'bias': 'UNKNOWN', 'strength': 0}