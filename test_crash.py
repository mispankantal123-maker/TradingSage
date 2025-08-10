#!/usr/bin/env python3
"""
Test script untuk simulasi crash yang terjadi pada bot
"""

# Try to import MT5, fallback to mock for development
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    print("✅ Real MetaTrader5 library loaded")
except ImportError:
    import mt5_mock as mt5
    MT5_AVAILABLE = False
    print("🎭 Mock MetaTrader5 library loaded (development mode)")

import numpy as np
from typing import Dict, Optional

def test_indicators(symbol="EURUSD"):
    """Test technical indicators yang mungkin menyebabkan crash"""
    
    print(f"\n🧪 Testing technical indicators for {symbol}...")
    
    try:
        # Test basic data access
        print("1. Testing basic data access...")
        timeframe = mt5.TIMEFRAME_M1
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
        print(f"   ✅ Got {len(rates) if rates is not None else 0} bars")
        
        if rates is None or len(rates) < 50:
            print("   ❌ Insufficient data for indicators")
            return False
            
        # Test MA calculation
        print("2. Testing MA calculation...")
        period = 10
        closes = [r['close'] for r in rates[-period:]]
        ma_value = float(np.mean(closes))
        print(f"   ✅ MA10: {ma_value}")
        
        # Test EMA calculation
        print("3. Testing EMA calculation...")
        period = 9
        closes = [r['close'] for r in rates[-period:]]
        multiplier = 2.0 / (period + 1)
        ema = closes[0]
        for price in closes[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        print(f"   ✅ EMA9: {float(ema)}")
        
        # Test RSI calculation
        print("4. Testing RSI calculation...")
        period = 14
        closes = [r['close'] for r in rates[-(period + 1):]]
        gains, losses = [], []
        
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0
        
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
        print(f"   ✅ RSI14: {float(rsi)}")
        
        # Test Bollinger Bands
        print("5. Testing Bollinger Bands...")
        period = 20
        closes = [r['close'] for r in rates[-period:]]
        sma = np.mean(closes)
        std = np.std(closes)
        
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        print(f"   ✅ BB Upper: {float(upper_band)}, Lower: {float(lower_band)}")
        
        print("\n✅ ALL INDICATORS TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in indicator testing: {str(e)}")
        import traceback
        print(f"🔧 Full traceback: {traceback.format_exc()}")
        return False

def test_percent_tp_sl():
    """Test percent-based TP/SL calculations"""
    print(f"\n🧪 Testing percent TP/SL calculations...")
    
    try:
        # Mock account info
        balance = 1000000.0  # 1M IDR
        
        # Test 1% profit target
        tp_percent = 1.0
        tp_money = balance * (tp_percent / 100)
        print(f"   ✅ TP 1% = {tp_money} IDR")
        
        # Test 0.5% stop loss
        sl_percent = 0.5
        sl_money = balance * (sl_percent / 100)
        print(f"   ✅ SL 0.5% = {sl_money} IDR")
        
        # Test price conversion
        current_price = 1.1000
        lot_size = 0.01
        pip_value = 10  # For standard calculation
        
        # Calculate pip distance needed for money target
        tp_pips = tp_money / (lot_size * 100000 * 0.0001)  # Simplified
        sl_pips = sl_money / (lot_size * 100000 * 0.0001)
        
        print(f"   ✅ TP pips needed: {tp_pips}")
        print(f"   ✅ SL pips needed: {sl_pips}")
        
        print("\n✅ PERCENT TP/SL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR in percent TP/SL testing: {str(e)}")
        import traceback
        print(f"🔧 Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting crash diagnosis tests...")
    
    # Initialize MT5 (mock)
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        exit(1)
        
    print("✅ MT5 initialized successfully")
    
    # Run tests
    indicators_ok = test_indicators()
    percent_ok = test_percent_tp_sl()
    
    if indicators_ok and percent_ok:
        print("\n🎉 ALL TESTS PASSED - No obvious crash causes found!")
    else:
        print("\n💥 FOUND POTENTIAL CRASH CAUSES!")
    
    # Cleanup
    mt5.shutdown()
    print("✅ Tests completed")