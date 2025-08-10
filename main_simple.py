"""
MT5 Trading Bot - Ultra Simple Version
Exact copy of bot3.py approach to prevent any freeze
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
try:
    import MetaTrader5 as mt5
except ImportError:
    import mt5_mock as mt5

class SimpleTradingBot:
    def __init__(self):
        self.trading_running = False
        self.trading_thread = None
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Simple MT5 Bot - No Freeze Version")
        self.root.geometry("600x400")
        
        # Simple layout
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection
        ttk.Button(frame, text="Connect MT5", command=self.connect_mt5).pack(pady=5)
        
        # Strategy
        ttk.Label(frame, text="Strategy:").pack(pady=(10,0))
        self.strategy_var = tk.StringVar(value="Scalping")
        ttk.Combobox(frame, textvariable=self.strategy_var, values=["Scalping", "Intraday"]).pack(pady=5)
        
        # Symbol
        ttk.Label(frame, text="Symbol:").pack(pady=(10,0))
        self.symbol_var = tk.StringVar(value="EURUSD")
        ttk.Entry(frame, textvariable=self.symbol_var).pack(pady=5)
        
        # Lot size
        ttk.Label(frame, text="Lot Size:").pack(pady=(10,0))
        self.lot_var = tk.StringVar(value="0.01")
        ttk.Entry(frame, textvariable=self.lot_var).pack(pady=5)
        
        # Trading buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="START BOT", command=self.start_trading).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="STOP BOT", command=self.stop_trading).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var).pack(pady=10)
        
        # Log area
        self.log_text = tk.Text(frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.connected = False
        
    def log(self, message):
        """Add log message"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
    def connect_mt5(self):
        """Connect to MT5"""
        try:
            if mt5.initialize():
                self.connected = True
                self.status_var.set("Connected")
                self.log("MT5 connected successfully")
                return True
            else:
                self.log("Failed to connect MT5")
                return False
        except Exception as e:
            self.log(f"Connection error: {str(e)}")
            return False
            
    def start_trading(self):
        """Start trading - ultra simple version"""
        if self.trading_running:
            self.log("Trading already running")
            return
            
        if not self.connected:
            messagebox.showerror("Error", "Connect to MT5 first")
            return
            
        # Simple confirmation
        if messagebox.askyesno("Confirm", "Start automated trading?"):
            self.trading_running = True
            self.status_var.set("Trading Active")
            self.log("Trading started")
            
            # Start simple trading thread
            self.trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
            self.trading_thread.start()
            
    def stop_trading(self):
        """Stop trading"""
        self.trading_running = False
        self.status_var.set("Trading Stopped")
        self.log("Trading stopped")
        
    def trading_loop(self):
        """Ultra simple trading loop"""
        symbol = self.symbol_var.get()
        lot_size = float(self.lot_var.get())
        
        self.log(f"Trading loop started for {symbol}")
        
        while self.trading_running:
            try:
                # Get price
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    self.log("No price data")
                    time.sleep(10)
                    continue
                    
                price = tick.ask
                
                # Simple signal (just for demo)
                if price > 0:  # Always true for demo
                    self.log(f"Price: {price} - No signal")
                    
                time.sleep(10)  # Wait 10 seconds
                
            except Exception as e:
                self.log(f"Loop error: {str(e)}")
                time.sleep(10)
                
        self.log("Trading loop ended")
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleTradingBot()
    app.run()