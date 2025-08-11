
def test_balance_percentage():
    """Test the corrected balance% calculation"""
    
    # Test case: Balance 5,000,000, TP 0.02%, SL 0.04%
    balance = 5000000
    tp_percentage = 0.02
    sl_percentage = 0.04
    
    # Corrected formula: (balance * percentage) / 100
    tp_amount = (balance * tp_percentage) / 100
    sl_amount = (balance * sl_percentage) / 100
    
    print("=== Balance% Calculation Test ===")
    print(f"Balance: ${balance:,.2f}")
    print(f"TP {tp_percentage}%: (${balance:,.2f} * {tp_percentage}) / 100 = ${tp_amount:,.2f}")
    print(f"SL {sl_percentage}%: (${balance:,.2f} * {sl_percentage}) / 100 = ${sl_amount:,.2f}")
    
    # Expected results
    expected_tp = 1000.0  # (5,000,000 * 0.02) / 100 = 1000
    expected_sl = 2000.0  # (5,000,000 * 0.04) / 100 = 2000
    
    assert tp_amount == expected_tp, f"TP calculation error: {tp_amount} != {expected_tp}"
    assert sl_amount == expected_sl, f"SL calculation error: {sl_amount} != {expected_sl}"
    
    print("✅ All balance% calculations correct!")

if __name__ == "__main__":
    test_balance_percentage()
