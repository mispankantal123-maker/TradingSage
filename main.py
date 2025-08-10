"""
MT5 Trading Bot - Main Entry Point
Enhanced version of bot3.py with comprehensive GUI and advanced features
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# Import our modules
from gui import TradingBotGUI
from trading import TradingEngine
from utils import ConfigManager, Logger

def main():
    """Main application entry point"""
    try:
        # Initialize configuration manager
        config = ConfigManager()
        
        # Initialize logger
        logger = Logger()
        
        # Create main window
        root = tk.Tk()
        root.title("MT5 Trading Bot - REAL MONEY TRADING")
        root.geometry("1200x800")
        root.minsize(1000, 600)
        
        # Add warning color to title bar
        root.configure(bg='#FF4444')
        
        # Set icon and styling
        try:
            root.iconbitmap("icon.ico")  # Optional, will fail gracefully if not found
        except:
            pass
        
        # Initialize trading engine
        trading_engine = TradingEngine(logger, config)
        
        # Initialize GUI
        app = TradingBotGUI(root, trading_engine, config, logger)
        
        # Setup cleanup on close
        def on_closing():
            """Handle application closing"""
            if trading_engine.is_running():
                result = messagebox.askyesno(
                    "Confirm Exit", 
                    "Trading bot is still running. Stop it and exit?"
                )
                if result:
                    trading_engine.stop_trading()
                    # Wait a moment for trading to stop
                    time.sleep(1)
                else:
                    return
            
            # Save configuration
            config.save_config()
            
            # Shutdown MT5 if connected
            trading_engine.disconnect_mt5()
            
            # Close application
            root.destroy()
            sys.exit(0)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        logger.log("Application started successfully")
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Failed to start application: {str(e)}"
        print(error_msg)
        if 'root' in locals():
            messagebox.showerror("Startup Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
