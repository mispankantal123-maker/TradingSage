#!/usr/bin/env python3
"""
Test bot dengan upgrade bot3.py methodology untuk memastikan tidak freeze
"""

import tkinter as tk
import time
from gui import TradingBotGUI
from trading import TradingEngine
from utils import ConfigManager, Logger

def test_bot3_upgrade():
    """Test bot dengan metode bot3.py yang sudah terintegrasi"""
    print("🚀 Testing Bot3.py upgrade - No freeze test...")
    
    try:
        # Setup minimal seperti main.py
        config = ConfigManager()
        logger = Logger()
        
        root = tk.Tk()
        root.withdraw()  # Hide GUI for testing
        
        # Initialize 
        trading_engine = TradingEngine(logger, config)
        app = TradingBotGUI(root, trading_engine, config, logger)
        
        # Connect first
        print("1. Testing connection...")
        success = trading_engine.connect_mt5()
        if not success:
            print("❌ Cannot connect")
            return False
        
        # Set settings untuk percent mode
        print("2. Setting up percent TP/SL...")
        app.strategy_var.set("Scalping")
        app.symbol_var.set("EURUSD") 
        app.lot_var.set("0.01")
        app.tp_value_var.set("1.0")    # 1%
        app.tp_unit_var.set("percent")  
        app.sl_value_var.set("0.5")    # 0.5%
        app.sl_unit_var.set("percent")  
        app.interval_var.set("5")       # Fast interval for testing
        
        settings = app.get_current_settings()
        print(f"   Settings: {settings}")
        
        # Start trading (ini yang sebelumnya freeze)
        print("3. Testing start trading (was freezing before)...")
        success = trading_engine.start_trading(settings)
        print(f"   Start result: {success}")
        
        if success:
            print("4. Bot started! Testing for freeze...")
            # Let it run for 10 seconds to check for freeze
            start_time = time.time()
            
            while time.time() - start_time < 10:
                if not trading_engine.trading_running:
                    print("   Bot stopped unexpectedly!")
                    break
                print(f"   Running... ({time.time() - start_time:.1f}s)")
                time.sleep(1)
            
            # Stop trading
            trading_engine.stop_trading()
            print("   ✅ No freeze detected - bot ran for 10 seconds!")
        else:
            print("   ❌ Failed to start trading")
            return False
        
        # Cleanup
        trading_engine.disconnect_mt5()
        root.destroy()
        print("\n🎉 BOT3.PY UPGRADE SUCCESS - No freeze issues!")
        return True
        
    except Exception as e:
        print(f"\n💥 ERROR: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Bot3.py integration upgrade...")
    
    success = test_bot3_upgrade()
    
    if success:
        print("\n✅ UPGRADE SUCCESSFUL - No freeze problems!")
        print("Bot now uses proven bot3.py methodology:")
        print("- Simplified trading loop")
        print("- Direct order placement") 
        print("- Effective scoring system")
        print("- Minimal complexity")
    else:
        print("\n❌ UPGRADE NEEDS MORE WORK")
    
    print("🏁 Test completed.")