# FIXED Balance% Calculation Function

def calculate_tp_sl_balance_percentage(value, symbol, order_type, current_price, lot_size, account_info):
    """
    FIXED Balance% calculation that prevents extreme values and variable errors
    """
    try:
        from logger_utils import logger
        import mt5_connection as mt5
        
        abs_value = abs(float(value))
        is_stop_loss = float(value) < 0
        
        logger(f"🔍 Balance% calculation: {abs_value}% of ${account_info.balance:.2f} = ${account_info.balance * (abs_value / 100):.2f}")
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger(f"❌ Cannot get symbol info for {symbol}")
            return 0.0
            
        # CRITICAL FIX: Special handling for Gold (XAUUSDm)
        if 'XAU' in symbol.upper():
            contract_size = 100    # Gold CFD = 100 oz (not 100000)
            point = 0.01          # Gold point = 0.01
            digits = 2            # Gold = 2 decimal places
        else:
            contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
            point = getattr(symbol_info, 'point', 0.00001)
            digits = getattr(symbol_info, 'digits', 5)
        
        # Calculate percentage amount in currency
        percentage_amount = account_info.balance * (abs_value / 100)
        
        # Calculate pip value and distance
        pip_value = lot_size * contract_size * point
        if pip_value > 0:
            pip_distance = percentage_amount / pip_value
        else:
            pip_distance = abs_value  # Fallback
        
        # CRITICAL: Apply reasonable limits to prevent extreme values
        max_pips = 1000  # Maximum 1000 pips
        min_pips = 1     # Minimum 1 pip
        
        if pip_distance > max_pips:
            logger(f"⚠️ Balance% calculated {pip_distance:.1f} pips - limiting to {max_pips} pips")
            pip_distance = max_pips
        elif pip_distance < min_pips:
            logger(f"⚠️ Balance% calculated {pip_distance:.1f} pips - minimum {min_pips} pip applied")
            pip_distance = min_pips
            
        logger(f"🔧 Converting ${percentage_amount:.2f} to {pip_distance:.1f} pips for {symbol}")
        
        # Calculate final price
        if is_stop_loss:
            if order_type.upper() == "BUY":
                return round(current_price - (pip_distance * point), digits)  # SL below entry
            else:  # SELL
                return round(current_price + (pip_distance * point), digits)  # SL above entry
        else:  # Take Profit
            if order_type.upper() == "BUY":
                return round(current_price + (pip_distance * point), digits)  # TP above entry
            else:  # SELL
                return round(current_price - (pip_distance * point), digits)  # TP below entry
                
    except Exception as e:
        logger(f"❌ Error in balance% calculation: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


# Test the function
if __name__ == "__main__":
    class MockAccount:
        def __init__(self):
            self.balance = 10000.0
            self.equity = 10000.0
    
    mock_account = MockAccount()
    
    # Test cases
    test_cases = [
        (2.0, "XAUUSDm", "BUY", 3376.008, 0.01),   # 2% balance for Gold
        (-1.0, "XAUUSDm", "BUY", 3376.008, 0.01),  # 1% balance SL for Gold  
        (1.0, "EURUSD", "BUY", 1.10000, 0.1),      # 1% balance for Forex
        (-0.5, "EURUSD", "BUY", 1.10000, 0.1),     # 0.5% balance SL for Forex
    ]
    
    print("🧪 TESTING FIXED BALANCE% CALCULATION")
    print("="*50)
    
    for value, symbol, order_type, price, lot in test_cases:
        result = calculate_tp_sl_balance_percentage(value, symbol, order_type, price, lot, mock_account)
        print(f"{symbol} {order_type}: {value}% balance @ {price} = {result}")