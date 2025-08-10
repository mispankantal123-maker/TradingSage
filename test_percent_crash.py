#!/usr/bin/env python3
"""
Test script khusus untuk simulasi crash saat menggunakan unit "percent"
"""

import sys
import tkinter as tk
from tkinter import messagebox
from gui import TradingBotGUI
from trading import TradingEngine
from utils import ConfigManager, Logger

def test_percent_crash():
    """Test specific scenario yang menyebabkan crash dengan percent unit"""
    print("🚀 Testing percent TP/SL crash scenario...")
    
    try:
        # Setup like main.py
        config = ConfigManager()
        logger = Logger()
        
        # Create main window (hide it for testing)
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        # Initialize trading engine and GUI
        trading_engine = TradingEngine(logger, config)
        app = TradingBotGUI(root, trading_engine, config, logger)
        
        # Force connection
        print("1. Testing MT5 connection...")
        success = trading_engine.connect_mt5()
        print(f"   Connection result: {success}")
        
        if not success:
            print("❌ Cannot connect to MT5")
            root.destroy()
            return False
        
        # Set specific settings that cause crash
        print("2. Setting up crash scenario settings...")
        
        # Simulate GUI settings that cause crash
        app.strategy_var.set("Scalping")
        app.symbol_var.set("EURUSD")
        app.lot_var.set("0.01")
        app.tp_value_var.set("1.0")    # 1%
        app.tp_unit_var.set("percent")  # This is the key!
        app.sl_value_var.set("0.5")    # 0.5%
        app.sl_unit_var.set("percent")  # This too!
        app.interval_var.set("10")
        
        # Get settings like GUI does
        settings = app.get_current_settings()
        print(f"   Settings: {settings}")
        
        # Test TP/SL calculation with percent units
        print("3. Testing percent TP/SL calculation...")
        try:
            current_price = 1.1000
            tp, sl = trading_engine.calculate_tp_sl(current_price, "BUY", settings)
            print(f"   ✅ TP: {tp}, SL: {sl}")
        except Exception as calc_e:
            print(f"   ❌ TP/SL calculation error: {str(calc_e)}")
            import traceback
            print(f"   🔧 Traceback: {traceback.format_exc()}")
            root.destroy()
            return False
        
        # Test start trading with percent settings  
        print("4. Testing start_trading with percent settings...")
        try:
            # This is where the crash likely occurs
            success = trading_engine.start_trading(settings)
            print(f"   Start trading result: {success}")
            
            # Let it run for a few seconds to see if it crashes
            print("5. Letting trading loop run for 5 seconds...")
            root.after(5000, lambda: print("   Trading loop completed 5 seconds"))
            root.after(5100, root.quit)  # Quit after 5.1 seconds
            
            # Run main loop briefly
            root.mainloop()
            
            # Stop trading
            trading_engine.stop_trading()
            print("   ✅ No crash detected!")
            
        except Exception as start_e:
            print(f"   ❌ Start trading error: {str(start_e)}")
            import traceback
            print(f"   🔧 Traceback: {traceback.format_exc()}")
            root.destroy()
            return False
        
        # Cleanup
        trading_engine.disconnect_mt5()
        root.destroy()
        print("\n🎉 PERCENT TEST COMPLETED - No crash!")
        return True
        
    except Exception as e:
        print(f"\n💥 CRASH DETECTED: {str(e)}")
        import traceback
        print(f"🔧 Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🧪 Starting percent crash test...")
    
    success = test_percent_crash()
    
    if success:
        print("\n✅ Test completed successfully - No crash found!")
    else:
        print("\n❌ CRASH REPRODUCED - Found the issue!")
    
    print("🏁 Test finished.")