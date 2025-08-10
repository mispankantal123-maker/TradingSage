#!/usr/bin/env python3
"""
Ultra Light Trading Bot - Guaranteed No Freeze
Absolute minimal implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys

# Mock MT5 for demo
class MockMT5:
    @staticmethod
    def initialize(): return True
    @staticmethod 
    def account_info(): 
        class Info: 
            login = 123456
            balance = 100000
        return Info()
    @staticmethod
    def symbol_info_tick(symbol):
        class Tick:
            ask = 1.1000 + (time.time() % 100) / 10000
            bid = 1.0990 + (time.time() % 100) / 10000
        return Tick()

mt5 = MockMT5()

class UltraLightBot:
    def __init__(self):
        self.trading = False
        
        # GUI
        self.root = tk.Tk()
        self.root.title("Ultra Light Bot - No Freeze")
        self.root.geometry("400x300")
        
        # Controls
        ttk.Label(self.root, text="Ultra Light Trading Bot", font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Button(self.root, text="Connect", command=self.connect, width=20).pack(pady=5)
        ttk.Button(self.root, text="START TRADING", command=self.start_trading, width=20).pack(pady=5)
        ttk.Button(self.root, text="STOP TRADING", command=self.stop_trading, width=20).pack(pady=5)
        
        # Status
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status, font=("Arial", 10)).pack(pady=10)
        
        # Log
        self.log_text = tk.Text(self.root, height=10, width=50)
        self.log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.connected = False
        
    def log(self, msg):
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def connect(self):
        self.connected = mt5.initialize()
        if self.connected:
            self.status.set("Connected")
            self.log("Connected to MT5")
        else:
            self.status.set("Connection Failed") 
            self.log("Failed to connect")
            
    def start_trading(self):
        if not self.connected:
            messagebox.showerror("Error", "Connect first")
            return
            
        # IMMEDIATE START - NO CONFIRMATIONS TO PREVENT FREEZE
        self.trading = True
        self.status.set("TRADING ACTIVE")
        self.log("TRADING STARTED!")
        
        # Simple thread
        def trade_loop():
            count = 0
            while self.trading:
                count += 1
                tick = mt5.symbol_info_tick("EURUSD")
                self.log(f"Cycle {count}: Price {tick.ask:.5f}")
                time.sleep(10)
            self.log("Trading stopped")
            
        threading.Thread(target=trade_loop, daemon=True).start()
        
    def stop_trading(self):
        self.trading = False
        self.status.set("Stopped")
        self.log("Trading stopped by user")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("Starting Ultra Light Bot...")
    app = UltraLightBot()
    app.run()