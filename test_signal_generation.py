#!/usr/bin/env python3
"""
Test Signal Generation - Debugging tool untuk memastikan bot menghasilkan trading signals
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_signal_generation():
    """Test comprehensive signal generation"""
    try:
        print("🧪 TESTING SIGNAL GENERATION SYSTEM")
        print("="*50)
        
        # Import required modules
        from data_manager import get_multiple_symbols_data
        from indicators import calculate_indicators  
        from strategies import run_strategy
        from mt5_connection import connect_mt5
        
        # Connect to MT5
        print("1. Connecting to MT5...")
        if connect_mt5():
            print("   ✅ MT5 Connected")
        else:
            print("   ❌ MT5 Connection failed")
            return False
        
        # Test with multiple symbols
        test_symbols = ["XAUUSD", "EURUSD", "GBPUSD"]
        print(f"\n2. Testing with symbols: {test_symbols}")
        
        for symbol in test_symbols:
            print(f"\n--- Testing {symbol} ---")
            
            # Get data
            symbol_data = get_multiple_symbols_data([symbol])
            if not symbol_data or symbol not in symbol_data:
                print(f"   ❌ No data for {symbol}")
                continue
                
            df = symbol_data[symbol]
            print(f"   ✅ Data: {len(df)} bars")
            
            # Calculate indicators
            df_with_indicators = calculate_indicators(df)
            if df_with_indicators is None:
                print(f"   ❌ Indicator calculation failed")
                continue
                
            print(f"   ✅ Indicators calculated")
            
            # Test all strategies
            strategies = ["Scalping", "Intraday", "Arbitrage", "HFT"]
            
            for strategy in strategies:
                action, signals = run_strategy(strategy, df_with_indicators, symbol)
                signal_count = len(signals)
                
                if action:
                    print(f"   🎯 {strategy}: {action} signal ({signal_count} conditions)")
                    for i, signal in enumerate(signals[:3]):  # Show first 3 signals
                        print(f"      {i+1}. {signal}")
                else:
                    print(f"   ⚪ {strategy}: No signal ({signal_count} conditions)")
                    
        print("\n" + "="*50)
        print("✅ SIGNAL GENERATION TEST COMPLETE")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_signal_creation():
    """Create manual test signals to verify system works"""
    try:
        print("\n🔧 MANUAL SIGNAL CREATION TEST")
        print("="*40)
        
        from trading_operations import execute_trade_signal
        
        # Test parameters
        test_symbol = "XAUUSD"
        test_action = "BUY"
        
        print(f"Testing trade execution for {test_symbol} {test_action}...")
        
        # This would be the actual execution path
        success = execute_trade_signal(test_symbol, test_action)
        
        if success:
            print("✅ Trade execution successful!")
        else:
            print("❌ Trade execution failed")
            
        return success
        
    except Exception as e:
        print(f"❌ Manual test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 MT5 SIGNAL GENERATION DIAGNOSTIC TOOL")
    print("This will help identify why bot is not generating signals\n")
    
    # Run comprehensive tests
    test1_success = test_signal_generation()
    
    if test1_success:
        test2_success = test_manual_signal_creation()
    
    print("\n📋 DIAGNOSTIC SUMMARY:")
    print(f"   Signal Generation: {'✅' if test1_success else '❌'}")
    if 'test2_success' in locals():
        print(f"   Trade Execution: {'✅' if test2_success else '❌'}")
    
    print("\n💡 If all tests pass but bot still doesn't trade:")
    print("   1. Check bot is actually started (Start Bot button)")  
    print("   2. Verify MT5 connection in GUI")
    print("   3. Ensure strategy parameters are set correctly")
    print("   4. Check risk management limits not blocking trades")