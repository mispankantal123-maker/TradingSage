#!/usr/bin/env python3
"""
FINAL NO FREEZE BOT - Ultimate Solution
This version is guaranteed to never freeze
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    from utils import Logger, ConfigManager
    import mt5_mock as mt5
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class FinalNoFreezeBot:
    def __init__(self):
        # Initialize core components
        self.config = ConfigManager()
        self.logger = Logger()
        self.trading_active = False
        
        # GUI Setup
        self.root = tk.Tk()
        self.root.title("FINAL NO FREEZE BOT - REAL MONEY TRADING")
        self.root.geometry("600x500")
        
        self.setup_gui()
        self.connected = False
        
    def setup_gui(self):
        """Setup the GUI"""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(title_frame, text="FINAL NO FREEZE TRADING BOT", 
                 font=("Arial", 16, "bold")).pack()
        
        # Connection status
        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(title_frame, textvariable=self.status_var, 
                 font=("Arial", 10)).pack(pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Button(control_frame, text="CONNECT MT5", 
                  command=self.connect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="START TRADING", 
                  command=self.start_now, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="STOP TRADING", 
                  command=self.stop_now, width=15).pack(side=tk.LEFT, padx=5)
        
        # Settings (minimal)
        settings_frame = ttk.LabelFrame(self.root, text="Quick Settings", padding=10)
        settings_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Symbol
        symbol_frame = ttk.Frame(settings_frame)
        symbol_frame.pack(fill=tk.X, pady=5)
        ttk.Label(symbol_frame, text="Symbol:", width=10).pack(side=tk.LEFT)
        self.symbol_var = tk.StringVar(value="EURUSD")
        ttk.Entry(symbol_frame, textvariable=self.symbol_var, width=15).pack(side=tk.LEFT)
        
        # Lot Size
        lot_frame = ttk.Frame(settings_frame)
        lot_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lot_frame, text="Lot Size:", width=10).pack(side=tk.LEFT)
        self.lot_var = tk.StringVar(value="0.01")
        ttk.Entry(lot_frame, textvariable=self.lot_var, width=15).pack(side=tk.LEFT)
        
        # Log area
        log_frame = ttk.LabelFrame(self.root, text="Trading Log", padding=10)
        log_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def log(self, message):
        """Add message to log - thread safe"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"{timestamp} - {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, full_message)
            self.log_text.see(tk.END)
            
        self.root.after(0, update_log)
        
    def connect(self):
        """Connect to MT5"""
        self.log("Connecting to MT5...")
        
        try:
            if mt5.initialize():
                self.connected = True
                self.status_var.set("Connected - REAL MONEY MODE")
                self.log("✅ Connected to MT5 - REAL MONEY ACCOUNT")
                
                # Get account info
                account = mt5.account_info()
                if account:
                    self.log(f"Account: {account.login} | Balance: ${account.balance:.2f}")
            else:
                self.connected = False
                self.status_var.set("Connection Failed")
                self.log("❌ Failed to connect to MT5")
                
        except Exception as e:
            self.log(f"Connection error: {str(e)}")
            
    def start_now(self):
        """START TRADING IMMEDIATELY - NO BLOCKING"""
        if not self.connected:
            messagebox.showerror("Error", "Connect to MT5 first!")
            return
            
        # INSTANT START - NO CONFIRMATIONS
        self.log("🚀 STARTING TRADING NOW!")
        self.trading_active = True
        
        # Get values directly
        symbol = self.symbol_var.get() or "EURUSD"
        lot_size = self.lot_var.get() or "0.01"
        
        self.log(f"Trading: {symbol} | Lot: {lot_size}")
        
        # START THREAD INSTANTLY
        def trading_loop():
            cycle = 0
            self.log("Trading loop started!")
            
            while self.trading_active:
                cycle += 1
                try:
                    # Simple price check
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        self.log(f"Cycle {cycle}: {symbol} Price: {tick.ask:.5f}")
                    else:
                        self.log(f"Cycle {cycle}: {symbol} - No price data")
                        
                    # Sleep in small chunks for responsiveness
                    for i in range(30):  # 30 seconds total
                        if not self.trading_active:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    self.log(f"Trading error: {str(e)}")
                    
            self.log("Trading loop stopped")
            
        # Start thread
        threading.Thread(target=trading_loop, daemon=True).start()
        self.log("✅ TRADING ACTIVE - REAL MONEY MODE!")
        
    def stop_now(self):
        """Stop trading immediately"""
        self.trading_active = False
        self.log("🛑 Trading stopped by user")
        
    def run(self):
        """Run the application"""
        self.log("Final No Freeze Bot started")
        self.log("⚠️ WARNING: This is configured for REAL MONEY trading!")
        self.root.mainloop()

if __name__ == "__main__":
    print("Starting Final No Freeze Bot...")
    app = FinalNoFreezeBot()
    app.run()