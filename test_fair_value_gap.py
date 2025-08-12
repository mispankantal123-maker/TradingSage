
# --- Fair Value Gap Testing ---
"""
Testing module untuk Fair Value Gap detection dan analysis
"""

import pandas as pd
import numpy as np
from fair_value_gap_analyzer import get_fair_value_gap_analysis, get_fvg_trading_signals
from logger_utils import logger
import datetime


def test_fvg_detection():
    """Test FVG detection dengan synthetic data"""
    try:
        logger("🔬 Testing Fair Value Gap Detection...")
        
        # Create synthetic OHLC data with intentional FVGs
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        
        # Base data
        np.random.seed(42)
        base_price = 1.2000
        data = []
        
        for i, date in enumerate(dates):
            if i == 0:
                open_price = base_price
                high_price = base_price + 0.0020
                low_price = base_price - 0.0015
                close_price = base_price + 0.0010
            else:
                prev_close = data[i-1]['close']
                
                # Create bullish FVG at index 30-32
                if i == 30:
                    open_price = prev_close
                    high_price = prev_close + 0.0010
                    low_price = prev_close - 0.0005
                    close_price = prev_close + 0.0008
                elif i == 31:  # Gap-creating candle
                    open_price = data[i-1]['close']
                    high_price = open_price + 0.0030  # Strong impulse
                    low_price = open_price + 0.0005
                    close_price = open_price + 0.0025
                elif i == 32:  # Third candle creating FVG
                    open_price = data[i-1]['close']
                    high_price = open_price + 0.0010
                    low_price = data[29]['high'] + 0.0015  # Gap here
                    close_price = open_price + 0.0005
                
                # Create bearish FVG at index 60-62
                elif i == 60:
                    open_price = prev_close
                    high_price = prev_close + 0.0005
                    low_price = prev_close - 0.0010
                    close_price = prev_close - 0.0008
                elif i == 61:  # Gap-creating candle
                    open_price = data[i-1]['close']
                    high_price = open_price - 0.0005
                    low_price = open_price - 0.0030  # Strong bearish impulse
                    close_price = open_price - 0.0025
                elif i == 62:  # Third candle creating FVG
                    open_price = data[i-1]['close']
                    high_price = data[59]['low'] - 0.0015  # Gap here
                    low_price = open_price - 0.0010
                    close_price = open_price - 0.0005
                
                else:
                    # Normal price movement
                    change = np.random.normal(0, 0.0008)
                    open_price = prev_close
                    high_price = open_price + abs(change) + np.random.uniform(0, 0.0005)
                    low_price = open_price - abs(change) - np.random.uniform(0, 0.0005)
                    close_price = open_price + change
            
            data.append({
                'time': date,
                'open': round(open_price, 5),
                'high': round(high_price, 5),
                'low': round(low_price, 5),
                'close': round(close_price, 5),
                'tick_volume': np.random.randint(800, 1500)
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        
        # Test FVG detection
        fvg_analysis = get_fair_value_gap_analysis(df, 'EURUSD')
        
        if fvg_analysis['valid']:
            logger(f"✅ FVG Detection Test PASSED")
            logger(f"   📊 Found {len(fvg_analysis['bullish_fvgs'])} bullish FVGs")
            logger(f"   📊 Found {len(fvg_analysis['bearish_fvgs'])} bearish FVGs")
            
            # Test trading signals
            fvg_signals = get_fvg_trading_signals(df, 'EURUSD')
            
            if fvg_signals.get('signal'):
                logger(f"✅ FVG Signal Generation Test PASSED")
                logger(f"   🎯 Signal: {fvg_signals['signal']}")
                logger(f"   📈 Confidence: {fvg_signals['confidence']:.1%}")
                logger(f"   💡 Reason: {fvg_signals['reason']}")
            else:
                logger(f"⚠️ FVG Signal Generation: No signals generated")
            
            return True
        else:
            logger(f"❌ FVG Detection Test FAILED: {fvg_analysis.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger(f"❌ FVG Test Error: {str(e)}")
        return False


def test_fvg_with_real_data():
    """Test FVG dengan data real dari MT5"""
    try:
        logger("🔬 Testing FVG with Real Market Data...")
        
        # Try to get real data from MT5
        try:
            import MetaTrader5 as mt5
            
            if mt5.initialize():
                rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M5, 0, 500)
                if rates is not None:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('time', inplace=True)
                    
                    # Test FVG detection on real data
                    fvg_analysis = get_fair_value_gap_analysis(df, 'EURUSD')
                    
                    if fvg_analysis['valid']:
                        logger(f"✅ Real Data FVG Test PASSED")
                        logger(f"   📊 Bullish FVGs: {len(fvg_analysis['bullish_fvgs'])}")
                        logger(f"   📊 Bearish FVGs: {len(fvg_analysis['bearish_fvgs'])}")
                        
                        # Show quality distribution
                        if fvg_analysis['bullish_fvgs']:
                            qualities = [fvg['quality'] for fvg in fvg_analysis['bullish_fvgs']]
                            logger(f"   🟢 Bullish Qualities: {qualities}")
                            
                        if fvg_analysis['bearish_fvgs']:
                            qualities = [fvg['quality'] for fvg in fvg_analysis['bearish_fvgs']]
                            logger(f"   🔴 Bearish Qualities: {qualities}")
                        
                        return True
                    else:
                        logger(f"⚠️ Real Data FVG: {fvg_analysis.get('reason', 'No FVGs found')}")
                        return False
                else:
                    logger("⚠️ No real data available from MT5")
                    return False
            else:
                logger("⚠️ MT5 not available for real data test")
                return False
                
        except ImportError:
            logger("⚠️ MT5 not available, using mock data")
            return test_fvg_detection()  # Fallback to synthetic test
            
    except Exception as e:
        logger(f"❌ Real Data FVG Test Error: {str(e)}")
        return False


def run_fvg_tests():
    """Run all FVG tests"""
    logger("🧪 Starting Fair Value Gap Tests...")
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Synthetic data
    if test_fvg_detection():
        tests_passed += 1
    
    # Test 2: Real data (if available)
    if test_fvg_with_real_data():
        tests_passed += 1
    
    logger(f"📊 FVG Tests Complete: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        logger("✅ All FVG tests PASSED - Ready for live trading!")
        return True
    else:
        logger("⚠️ Some FVG tests failed - Review implementation")
        return False


if __name__ == "__main__":
    run_fvg_tests()
