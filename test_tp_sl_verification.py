
# --- TP/SL Direction & Calculation Verification Test ---
"""
Comprehensive test to verify TP/SL calculations are correct for all modes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_operations import calculate_tp_sl_all_modes
from logger_utils import logger

def test_tp_sl_directions():
    """Test TP/SL direction logic for all calculation modes"""
    
    print("🧪 COMPREHENSIVE TP/SL DIRECTION & CALCULATION TEST")
    print("=" * 60)
    
    # Test parameters
    test_symbol = "EURUSD"
    test_current_price = 1.1000
    test_lot_size = 0.01
    
    # Test cases: [input_value, unit, order_type, expected_direction]
    test_cases = [
        # PIPS MODE
        ("20", "pips", "BUY", "TP_ABOVE"),     # TP should be above entry
        ("-10", "pips", "BUY", "SL_BELOW"),    # SL should be below entry
        ("20", "pips", "SELL", "TP_BELOW"),    # TP should be below entry
        ("-10", "pips", "SELL", "SL_ABOVE"),   # SL should be above entry
        
        # PRICE MODE
        ("1.1020", "price", "BUY", "TP_ABOVE"),   # Direct price above
        ("1.0980", "price", "BUY", "SL_BELOW"),   # Direct price below
        ("1.0980", "price", "SELL", "TP_BELOW"),  # Direct price below
        ("1.1020", "price", "SELL", "SL_ABOVE"),  # Direct price above
        
        # PERCENT MODE
        ("1.0", "percent", "BUY", "TP_ABOVE"),    # 1% above entry
        ("-0.5", "percent", "BUY", "SL_BELOW"),   # 0.5% below entry
        ("1.0", "percent", "SELL", "TP_BELOW"),   # 1% below entry
        ("-0.5", "percent", "SELL", "SL_ABOVE"),  # 0.5% above entry
        
        # BALANCE% MODE
        ("2.0", "balance%", "BUY", "TP_ABOVE"),   # 2% balance above
        ("-1.0", "balance%", "BUY", "SL_BELOW"),  # 1% balance below
        ("2.0", "balance%", "SELL", "TP_BELOW"),  # 2% balance below
        ("-1.0", "balance%", "SELL", "SL_ABOVE"), # 1% balance above
        
        # EQUITY% MODE  
        ("2.5", "equity%", "BUY", "TP_ABOVE"),    # 2.5% equity above
        ("-1.5", "equity%", "BUY", "SL_BELOW"),   # 1.5% equity below
        ("2.5", "equity%", "SELL", "TP_BELOW"),   # 2.5% equity below
        ("-1.5", "equity%", "SELL", "SL_ABOVE"),  # 1.5% equity above
        
        # MONEY MODE
        ("100", "money", "BUY", "TP_ABOVE"),      # $100 profit above
        ("-50", "money", "BUY", "SL_BELOW"),      # $50 loss below
        ("100", "money", "SELL", "TP_BELOW"),     # $100 profit below
        ("-50", "money", "SELL", "SL_ABOVE"),     # $50 loss above
    ]
    
    results = {"PASS": 0, "FAIL": 0}
    
    for i, (input_value, unit, order_type, expected_direction) in enumerate(test_cases, 1):
        try:
            print(f"\n📋 Test {i:2d}: {input_value:>6} {unit:>8} {order_type:>4} → {expected_direction}")
            
            # Calculate TP/SL price
            calculated_price = calculate_tp_sl_all_modes(
                input_value, unit, test_symbol, order_type, test_current_price, test_lot_size
            )
            
            if calculated_price <= 0:
                print(f"   ❌ FAIL: Invalid calculated price: {calculated_price}")
                results["FAIL"] += 1
                continue
            
            # Verify direction
            price_diff = calculated_price - test_current_price
            is_above = price_diff > 0
            is_below = price_diff < 0
            
            # Check expected direction
            direction_correct = False
            
            if expected_direction == "TP_ABOVE" and is_above:
                direction_correct = True
            elif expected_direction == "SL_BELOW" and is_below:
                direction_correct = True
            elif expected_direction == "TP_BELOW" and is_below:
                direction_correct = True
            elif expected_direction == "SL_ABOVE" and is_above:
                direction_correct = True
            
            if direction_correct:
                print(f"   ✅ PASS: {calculated_price:.5f} (Δ{price_diff:+.5f})")
                results["PASS"] += 1
            else:
                print(f"   ❌ FAIL: {calculated_price:.5f} (Δ{price_diff:+.5f}) - Wrong direction!")
                results["FAIL"] += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results["FAIL"] += 1
    
    # Results summary
    print("\n" + "=" * 60)
    print(f"🧪 TEST RESULTS SUMMARY:")
    print(f"   ✅ PASSED: {results['PASS']:2d}")
    print(f"   ❌ FAILED: {results['FAIL']:2d}")
    print(f"   📊 SUCCESS RATE: {(results['PASS']/(results['PASS']+results['FAIL']))*100:.1f}%")
    
    if results["FAIL"] == 0:
        print(f"\n🎉 ALL TESTS PASSED! TP/SL calculations are correct!")
        return True
    else:
        print(f"\n⚠️  {results['FAIL']} tests failed - requires attention!")
        return False

def test_extreme_values():
    """Test edge cases and extreme values"""
    
    print(f"\n🎯 TESTING EXTREME VALUES & EDGE CASES")
    print("-" * 40)
    
    edge_cases = [
        ("0", "pips", "BUY"),           # Zero value
        ("0.1", "pips", "BUY"),         # Very small value
        ("1000", "pips", "BUY"),        # Very large value
        ("50", "balance%", "BUY"),      # High percentage
        ("0.01", "percent", "SELL"),    # Tiny percentage
    ]
    
    for input_value, unit, order_type in edge_cases:
        try:
            result = calculate_tp_sl_all_modes(
                input_value, unit, "EURUSD", order_type, 1.1000, 0.01
            )
            print(f"   {input_value:>6} {unit:>8} {order_type:>4} → {result:.5f} ✅")
        except Exception as e:
            print(f"   {input_value:>6} {unit:>8} {order_type:>4} → ERROR: {str(e)} ❌")

if __name__ == "__main__":
    try:
        # Run comprehensive tests
        success = test_tp_sl_directions()
        test_extreme_values()
        
        if success:
            print(f"\n🏆 VERIFICATION COMPLETE: TP/SL calculations are CORRECT!")
        else:
            print(f"\n🔧 ATTENTION NEEDED: Some TP/SL calculations require fixes!")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
