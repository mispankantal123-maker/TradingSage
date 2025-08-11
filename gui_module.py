# --- GUI Module ---
"""
Main GUI interface for the trading bot - identical to original but modular
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import datetime
import threading
import traceback
from typing import Optional, Dict, Any

# Import our modular components
from logger_utils import logger
from config import STRATEGIES, DEFAULT_PARAMS, GUI_UPDATE_INTERVAL
from mt5_connection import connect_mt5, get_account_info, get_positions, get_symbol_suggestions
from validation_utils import validate_numeric_input
from risk_management import get_current_risk_metrics
from performance_tracking import generate_performance_report
from telegram_notifications import notify_bot_status, notify_strategy_change, notify_balance_update, test_telegram_connection


class TradingBotGUI:
    """Enhanced Trading Bot GUI with identical functionality to original"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("💹 MT5 ADVANCED AUTO TRADING BOT v4.0 - Premium Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0f0f0f")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        self.current_strategy = "Scalping"
        self._update_counter = 0
        self._last_update_time = datetime.datetime.now()
        
        # Create widgets
        self.create_widgets()
        
        # Initialize GUI states
        self.start_btn.config(state="disabled")
        self.close_btn.config(state="disabled") 
        self.emergency_btn.config(state="normal")
        
        # Auto-connect on startup
        self.root.after(1000, self.auto_connect_mt5)
        
        # Start GUI updates
        self.root.after(2000, self.update_gui_data)
    
    def create_widgets(self):
        """Enhanced GUI creation with better layout"""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f0f0f")
        style.configure("TLabel", background="#0f0f0f", foreground="white")
        style.configure("TButton", background="#2c5aa0", foreground="white")
        style.configure("Treeview", background="#1a1a1a", foreground="white")
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Top frame - Controls
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Connection controls
        connection_frame = ttk.LabelFrame(top_frame, text="🔌 Connection", padding="10")
        connection_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.connect_btn = ttk.Button(connection_frame, text="Connect MT5", command=self.connect_mt5)
        self.connect_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.status_lbl = ttk.Label(connection_frame, text="Status: Disconnected ❌", foreground="red")
        self.status_lbl.grid(row=0, column=1, padx=(0, 10))
        
        # Trading controls
        trading_frame = ttk.LabelFrame(top_frame, text="🎯 Trading Control", padding="10")
        trading_frame.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        self.start_btn = ttk.Button(trading_frame, text="▶️ Start Bot", command=self.start_bot)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.close_btn = ttk.Button(trading_frame, text="🔄 Close Positions", command=self.close_all_positions)
        self.close_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.emergency_btn = ttk.Button(trading_frame, text="🚨 EMERGENCY STOP", 
                                      command=self.emergency_stop, style="Emergency.TButton")
        self.emergency_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Configure emergency button style
        style.configure("Emergency.TButton", background="#d32f2f", foreground="white")
        
        # Strategy and parameters frame - Enhanced layout
        params_frame = ttk.LabelFrame(top_frame, text="⚙️ Strategy & Parameters", padding="8")
        params_frame.grid(row=0, column=2, sticky="ew")
        params_frame.columnconfigure(3, weight=1)
        
        # Row 0: Strategy and Symbol
        ttk.Label(params_frame, text="Strategy:").grid(row=0, column=0, sticky="w", padx=(0,3))
        self.strategy_combo = ttk.Combobox(params_frame, values=STRATEGIES, state="readonly", width=10)
        self.strategy_combo.set("Scalping")
        self.strategy_combo.grid(row=0, column=1, padx=(0, 10), sticky="w")
        self.strategy_combo.bind("<<ComboboxSelected>>", self.on_strategy_change)
        
        ttk.Label(params_frame, text="Symbol:").grid(row=0, column=2, sticky="w", padx=(0,3))
        self.symbol_combo = ttk.Combobox(params_frame, width=12, state="readonly")
        self.symbol_combo.grid(row=0, column=3, padx=(0, 5), sticky="ew")
        
        # Row 1: Lot Size and TP
        ttk.Label(params_frame, text="Lot:").grid(row=1, column=0, sticky="w", padx=(0,3))
        self.lot_entry = ttk.Entry(params_frame, width=8)
        self.lot_entry.insert(0, "0.01")
        self.lot_entry.grid(row=1, column=1, padx=(0, 10), sticky="w")
        
        ttk.Label(params_frame, text="TP:").grid(row=1, column=2, sticky="w", padx=(0,3))
        
        # TP Frame for value and unit
        tp_frame = ttk.Frame(params_frame)
        tp_frame.grid(row=1, column=3, padx=(0, 5), sticky="w")
        
        self.tp_entry = ttk.Entry(tp_frame, width=6)
        self.tp_entry.insert(0, "20")
        self.tp_entry.grid(row=0, column=0, padx=(0, 2))
        
        from config import TP_SL_UNITS
        self.tp_unit_combo = ttk.Combobox(tp_frame, values=TP_SL_UNITS, 
                                         state="readonly", width=8)
        self.tp_unit_combo.set("pips")
        self.tp_unit_combo.grid(row=0, column=1)
        self.tp_unit_combo.bind("<<ComboboxSelected>>", self.on_tp_unit_change)
        
        # Row 2: SL and Scan Interval
        ttk.Label(params_frame, text="SL:").grid(row=2, column=0, sticky="w", padx=(0,3))
        
        # SL Frame for value and unit  
        sl_frame = ttk.Frame(params_frame)
        sl_frame.grid(row=2, column=1, padx=(0, 10), sticky="w")
        
        self.sl_entry = ttk.Entry(sl_frame, width=6)
        self.sl_entry.insert(0, "10")
        self.sl_entry.grid(row=0, column=0, padx=(0, 2))
        
        self.sl_unit_combo = ttk.Combobox(sl_frame, values=TP_SL_UNITS, 
                                         state="readonly", width=8)
        self.sl_unit_combo.set("pips")
        self.sl_unit_combo.grid(row=0, column=1)
        self.sl_unit_combo.bind("<<ComboboxSelected>>", self.on_sl_unit_change)
        
        # Scan Interval
        ttk.Label(params_frame, text="Scan Interval (sec):").grid(row=2, column=2, sticky="w", padx=(0,3))
        self.interval_entry = ttk.Entry(params_frame, width=6)
        self.interval_entry.insert(0, "10")  # Default 10 seconds instead of 30
        self.interval_entry.grid(row=2, column=3, padx=(0, 5), sticky="w")
        
        # Left panel - Account info and positions
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_frame.rowconfigure(1, weight=1)
        
        # Account info
        account_frame = ttk.LabelFrame(left_frame, text="💰 Account Information", padding="10")
        account_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.balance_lbl = ttk.Label(account_frame, text="Balance: $0.00", font=("Arial", 10, "bold"))
        self.balance_lbl.grid(row=0, column=0, sticky="w")
        
        self.equity_lbl = ttk.Label(account_frame, text="Equity: $0.00")
        self.equity_lbl.grid(row=1, column=0, sticky="w")
        
        self.margin_lbl = ttk.Label(account_frame, text="Free Margin: $0.00")
        self.margin_lbl.grid(row=2, column=0, sticky="w")
        
        self.margin_level_lbl = ttk.Label(account_frame, text="Margin Level: 0%")
        self.margin_level_lbl.grid(row=3, column=0, sticky="w")
        
        self.server_lbl = ttk.Label(account_frame, text="Server: Not Connected")
        self.server_lbl.grid(row=4, column=0, sticky="w")
        
        # Bot status
        self.bot_status_lbl = ttk.Label(account_frame, text="Bot: Stopped 🔴", 
                                       font=("Arial", 10, "bold"), foreground="red")
        self.bot_status_lbl.grid(row=5, column=0, sticky="w", pady=(10, 0))
        
        # Positions frame
        positions_frame = ttk.LabelFrame(left_frame, text="📊 Open Positions", padding="10")
        positions_frame.grid(row=1, column=0, sticky="nsew")
        positions_frame.rowconfigure(0, weight=1)
        
        # Positions treeview with TP/SL columns
        columns = ("Symbol", "Type", "Volume", "Price", "TP", "SL", "Current", "Profit")
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            if col in ["TP", "SL"]:
                self.positions_tree.column(col, width=75, anchor="center")
            else:
                self.positions_tree.column(col, width=80, anchor="center")
        
        # Scrollbar for positions
        pos_scrollbar = ttk.Scrollbar(positions_frame, orient="vertical", command=self.positions_tree.yview)
        self.positions_tree.configure(yscroll=pos_scrollbar.set)
        
        self.positions_tree.grid(row=0, column=0, sticky="nsew")
        pos_scrollbar.grid(row=0, column=1, sticky="ns")
        
        positions_frame.columnconfigure(0, weight=1)
        
        # Right panel - Log and controls
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky="nsew")
        right_frame.rowconfigure(0, weight=1)
        
        # Log frame
        log_frame = ttk.LabelFrame(right_frame, text="📝 Trading Log", padding="10")
        log_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # Log text area
        self.log_text = ScrolledText(log_frame, height=25, width=80, 
                                    bg="#1a1a1a", fg="white", 
                                    font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Action buttons frame
        actions_frame = ttk.LabelFrame(right_frame, text="🎮 Actions", padding="10")
        actions_frame.grid(row=1, column=0, sticky="ew")
        
        # Action buttons
        self.refresh_btn = ttk.Button(actions_frame, text="🔄 Refresh", command=self.refresh_data)
        self.refresh_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.report_btn = ttk.Button(actions_frame, text="📊 Report", command=self.show_performance_report)
        self.report_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.clear_log_btn = ttk.Button(actions_frame, text="🗑️ Clear Log", command=self.clear_log)
        self.clear_log_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Configure grid weights for responsive design
        top_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(0, minsize=350)
        main_frame.columnconfigure(1, weight=1)
        
        # Initial log message
        self.log("🚀 Trading Bot GUI initialized successfully")
        self.log("💡 Click 'Connect MT5' to establish connection")
    
    def auto_connect_mt5(self):
        """Enhanced auto-connection on startup with better error handling"""
        try:
            self.log("🔄 Starting auto-connection to MetaTrader 5...")
            self.log("💡 PASTIKAN: MT5 sudah dijalankan dan login ke akun trading")
            self.log("💡 PENTING: MT5 harus dijalankan sebagai Administrator")
            self.status_lbl.config(text="Status: Connecting... 🔄", foreground="orange")
            self.root.update()
            
            # Show system info first
            import platform
            import sys
            self.log(f"🔍 Python: {sys.version.split()[0]} ({platform.architecture()[0]})")
            self.log(f"🔍 Platform: {platform.system()} {platform.release()}")
            
            if connect_mt5():
                self.log("🎉 SUCCESS: Auto-connected to MetaTrader 5!")
                self.status_lbl.config(text="Status: Connected ✅", foreground="green")
                self.update_symbols()
                self.start_btn.config(state="normal")
                self.close_btn.config(state="normal")
                self.connect_btn.config(state="disabled")
                
                # Show detailed connection info
                try:
                    info = get_account_info()
                    if info:
                        self.log(f"👤 Account: {info.get('login', 'N/A')} | Server: {info.get('server', 'N/A')}")
                        self.log(f"💰 Balance: ${info.get('balance', 0):.2f} | Equity: ${info.get('equity', 0):.2f}")
                        self.log(f"🔐 Trade Permission: {'✅' if info.get('balance', 0) > 0 else '⚠️'}")
                        
                        self.log("🚀 GUI-MT5 connection established successfully!")
                        self.log("🚀 Ready to start automated trading!")
                        
                        # Test Telegram notifications
                        self.log("📱 Testing Telegram connection...")
                        if test_telegram_connection():
                            self.log("✅ Telegram notifications active")
                        else:
                            self.log("⚠️ Telegram notifications failed")
                except Exception as info_e:
                    self.log(f"⚠️ Error getting account details: {str(info_e)}")
            else:
                self.log("❌ FAILED: Auto-connection to MT5 failed")
                self.log("🔧 TROUBLESHOOTING WAJIB:")
                self.log("   1. 🔴 TUTUP MT5 SEPENUHNYA")
                self.log("   2. 🔴 KLIK KANAN MT5 → 'Run as Administrator'")
                self.log("   3. 🔴 LOGIN ke akun trading dengan kredensial yang benar")
                self.log("   4. 🔴 PASTIKAN status 'Connected' muncul di MT5")
                self.log("   5. 🔴 BUKA Market Watch dan tambahkan symbols (EURUSD, dll)")
                self.log("   6. 🔴 PASTIKAN Python dan MT5 sama-sama 64-bit")
                self.log("   7. 🔴 DISABLE antivirus sementara jika perlu")
                self.log("   8. 🔴 RESTART komputer jika masalah persisten")
                
                self.status_lbl.config(text="Status: Connection Failed ❌", foreground="red")
                
                # Enable manual connect button
                self.connect_btn.config(state="normal")
                self.start_btn.config(state="disabled")
                self.close_btn.config(state="disabled")
                
                # Show error in account labels
                self.balance_lbl.config(text="Balance: N/A", foreground="gray")
                self.equity_lbl.config(text="Equity: N/A", foreground="gray")
                self.margin_lbl.config(text="Free Margin: N/A", foreground="gray")
                self.margin_level_lbl.config(text="Margin Level: N/A", foreground="gray")
                self.server_lbl.config(text="Server: N/A")
                
        except Exception as e:
            error_msg = f"❌ CRITICAL: Auto-connection error: {str(e)}"
            self.log(error_msg)
            self.status_lbl.config(text="Status: Critical Error ❌", foreground="red")
    
    def connect_mt5(self):
        """Enhanced MT5 connection with comprehensive GUI feedback and proper error handling"""
        try:
            self.log("🔄 Manual MT5 connection initiated...")
            self.status_lbl.config(text="Status: Connecting... 🔄", foreground="orange")
            self.connect_btn.config(state="disabled", text="Connecting...")
            self.root.update()
            
            if connect_mt5():
                self.log("✅ MT5 connection successful!")
                self.status_lbl.config(text="Status: Connected ✅", foreground="green")
                self.connect_btn.config(text="Connected", state="disabled")
                self.start_btn.config(state="normal")
                self.close_btn.config(state="normal")
                
                # Update symbols and account info
                self.update_symbols()
                self.update_account_info()
                self.update_positions()
                
                self.log("🚀 GUI-MT5 connection established successfully!")
                
            else:
                self.log("❌ MT5 connection failed!")
                self.status_lbl.config(text="Status: Connection Failed ❌", foreground="red")
                self.connect_btn.config(text="Retry Connection", state="normal")
                
        except Exception as e:
            error_msg = f"❌ Connection error: {str(e)}"
            self.log(error_msg)
            self.status_lbl.config(text="Status: Error ❌", foreground="red")
            self.connect_btn.config(text="Retry Connection", state="normal")
    
    def update_symbols(self):
        """Update symbol dropdown with comprehensive symbol list"""
        try:
            # Get symbols from MT5 connection
            mt5_symbols = get_symbol_suggestions()
            
            # Combine with default symbols for comprehensive coverage
            from config import DEFAULT_SYMBOLS
            all_symbols = list(set(mt5_symbols + DEFAULT_SYMBOLS))
            
            # Sort symbols logically
            forex_symbols = [s for s in all_symbols if any(pair in s.upper() for pair in ['EUR', 'GBP', 'USD', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']) and len(s) <= 7]
            metal_symbols = [s for s in all_symbols if any(metal in s.upper() for metal in ['XAU', 'XAG', 'GOLD', 'SILVER'])]
            crypto_symbols = [s for s in all_symbols if any(crypto in s.upper() for crypto in ['BTC', 'ETH', 'LTC', 'XRP'])]
            commodity_symbols = [s for s in all_symbols if any(comm in s.upper() for comm in ['OIL', 'NGAS', 'WHEAT'])]
            index_symbols = [s for s in all_symbols if any(idx in s.upper() for idx in ['US30', 'US500', 'NAS100', 'GER30', 'UK100', 'JPN225'])]
            
            # Organize symbols by category
            organized_symbols = []
            if forex_symbols: organized_symbols.extend(sorted(forex_symbols))
            if metal_symbols: organized_symbols.extend(sorted(metal_symbols))
            if crypto_symbols: organized_symbols.extend(sorted(crypto_symbols))
            if commodity_symbols: organized_symbols.extend(sorted(commodity_symbols))
            if index_symbols: organized_symbols.extend(sorted(index_symbols))
            
            # Set symbols in dropdown
            self.symbol_combo['values'] = organized_symbols[:50]  # Limit to 50 most common
            
            # Set default symbol
            if not self.symbol_combo.get() and organized_symbols:
                # Prefer XAUUSD if available, otherwise first symbol
                if 'XAUUSDm' in organized_symbols:
                    self.symbol_combo.set('XAUUSDm')
                elif 'XAUUSD' in organized_symbols:
                    self.symbol_combo.set('XAUUSD')
                elif 'EURUSD' in organized_symbols:
                    self.symbol_combo.set('EURUSD')
                else:
                    self.symbol_combo.set(organized_symbols[0])
            
            self.log(f"📊 Updated symbols: {len(organized_symbols)} available")
            self.log(f"   Forex: {len(forex_symbols)}, Metals: {len(metal_symbols)}, Crypto: {len(crypto_symbols)}")
            self.log(f"   Commodities: {len(commodity_symbols)}, Indices: {len(index_symbols)}")
            
        except Exception as e:
            self.log(f"❌ Error updating symbols: {str(e)}")
            # Fallback to basic symbols
            basic_symbols = ["XAUUSD", "XAUUSDm", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "BTCUSDm", "USOIL", "USOILm"]
            self.symbol_combo['values'] = basic_symbols
            if not self.symbol_combo.get():
                self.symbol_combo.set("XAUUSDm")
    
    def on_strategy_change(self, event=None):
        """Handle strategy change with proper GUI integration"""
        try:
            self.current_strategy = self.strategy_combo.get()
            self.log(f"⚙️ Strategy changed to: {self.current_strategy}")
            
            # Update parameters based on strategy
            params = DEFAULT_PARAMS.get(self.current_strategy, DEFAULT_PARAMS["Scalping"])
            
            # Update GUI fields
            self.lot_entry.delete(0, tk.END)
            self.lot_entry.insert(0, params["lot_size"])
            
            self.tp_entry.delete(0, tk.END)
            self.tp_entry.insert(0, params["tp_pips"])
            
            self.sl_entry.delete(0, tk.END)
            self.sl_entry.insert(0, params["sl_pips"])
            
            self.tp_unit_combo.set(params["tp_unit"])
            self.sl_unit_combo.set(params["sl_unit"])
            
            self.log(f"📊 Parameters updated for {self.current_strategy}")
            self.log(f"   TP: {params['tp_pips']} {params['tp_unit']}")
            self.log(f"   SL: {params['sl_pips']} {params['sl_unit']}")
            self.log(f"   Lot: {params['lot_size']}")
            
            # Send Telegram notification for strategy change
            try:
                old_strategy = getattr(self, '_previous_strategy', 'None')
                tp_text = f"{params['tp_pips']} {params['tp_unit']}"
                sl_text = f"{params['sl_pips']} {params['sl_unit']}"
                notify_strategy_change(old_strategy, self.current_strategy, tp_text, sl_text, params['lot_size'])
                self._previous_strategy = self.current_strategy
            except Exception as e:
                self.log(f"⚠️ Telegram strategy notification failed: {str(e)}")
            
        except Exception as e:
            self.log(f"❌ Error changing strategy: {str(e)}")
    
    def on_tp_unit_change(self, event=None):
        """Handle TP unit change to show percentage info"""
        try:
            unit = self.tp_unit_combo.get()
            if unit in ["balance%", "equity%"]:
                current_value = self.tp_entry.get()
                if not current_value or float(current_value) > 10.0:
                    self.tp_entry.delete(0, tk.END)
                    self.tp_entry.insert(0, "2.0")  # Default 2%
                self.log(f"💡 TP unit changed to {unit} - Value represents percentage")
                self.log(f"💡 Recommended range: 0.1% - 10% of {unit.split('%')[0]}")
            
        except Exception as e:
            self.log(f"❌ Error changing TP unit: {str(e)}")
    
    def on_sl_unit_change(self, event=None):
        """Handle SL unit change to show percentage info"""
        try:
            unit = self.sl_unit_combo.get()
            if unit in ["balance%", "equity%"]:
                current_value = self.sl_entry.get()
                if not current_value or float(current_value) > 10.0:
                    self.sl_entry.delete(0, tk.END)
                    self.sl_entry.insert(0, "1.0")  # Default 1%
                self.log(f"💡 SL unit changed to {unit} - Value represents percentage")
                self.log(f"💡 Recommended range: 0.1% - 10% of {unit.split('%')[0]}")
            
        except Exception as e:
            self.log(f"❌ Error changing SL unit: {str(e)}")
    
    def get_current_lot_size(self) -> float:
        """Get current lot size from GUI with validation"""
        try:
            lot_text = self.lot_entry.get().strip()
            if not lot_text:
                return 0.01
            return validate_numeric_input(lot_text, min_val=0.01, max_val=100.0)
        except:
            self.log("⚠️ Invalid lot size, using 0.01")
            return 0.01
    
    def get_current_tp(self) -> float:
        """Get current TP from GUI with validation"""
        try:
            tp_text = self.tp_entry.get().strip()
            if not tp_text:
                return 20.0
            return validate_numeric_input(tp_text, min_val=0.0, max_val=1000.0)
        except:
            self.log("⚠️ Invalid TP value, using 20")
            return 20.0
    
    def get_current_sl(self) -> float:
        """Get current SL from GUI with validation"""
        try:
            sl_text = self.sl_entry.get().strip()
            if not sl_text:
                return 10.0
            return validate_numeric_input(sl_text, min_val=0.0, max_val=1000.0)
        except:
            self.log("⚠️ Invalid SL value, using 10")
            return 10.0
    
    def get_tp_unit(self) -> str:
        """Get TP unit from GUI"""
        try:
            strategy = self.current_strategy
            if strategy in DEFAULT_PARAMS:
                unit = DEFAULT_PARAMS[strategy].get("tp_unit", "pips")
                logger(f"🔍 GUI: TP unit for {strategy} = {unit}")
                return unit
            else:
                logger(f"⚠️ GUI: Strategy {strategy} not found in params, using default")
                return "pips"
        except Exception as e:
            logger(f"❌ GUI: Error getting TP unit: {str(e)}")
            return "pips"
    
    def get_sl_unit(self) -> str:
        """Get SL unit from GUI"""
        try:
            strategy = self.current_strategy
            if strategy in DEFAULT_PARAMS:
                unit = DEFAULT_PARAMS[strategy].get("sl_unit", "pips")
                logger(f"🔍 GUI: SL unit for {strategy} = {unit}")
                return unit
            else:
                logger(f"⚠️ GUI: Strategy {strategy} not found in params, using default")
                return "pips"
        except Exception as e:
            logger(f"❌ GUI: Error getting SL unit: {str(e)}")
            return "pips"
    
    def start_bot(self):
        """Start the trading bot"""
        try:
            self.log("🚀 Starting automated trading bot...")
            self.bot_status_lbl.config(text="Bot: Starting... 🟡", foreground="orange")
            self.start_btn.config(state="disabled")
            
            # Validate parameters
            lot_size = self.get_current_lot_size()
            tp = self.get_current_tp()
            sl = self.get_current_sl()
            symbol = self.symbol_combo.get()
            
            if not symbol:
                self.log("❌ Please select a symbol")
                self.start_btn.config(state="normal")
                self.bot_status_lbl.config(text="Bot: Stopped 🔴", foreground="red")
                return
            
            self.log(f"⚙️ Bot Configuration:")
            self.log(f"   Strategy: {self.current_strategy}")
            self.log(f"   Symbol: {symbol}")
            self.log(f"   Lot Size: {lot_size}")
            self.log(f"   TP: {tp} {self.get_tp_unit()}")
            self.log(f"   SL: {sl} {self.get_sl_unit()}")
            
            # Start bot thread
            import __main__
            __main__.start_bot_thread()
            
            self.bot_status_lbl.config(text="Bot: Running 🟢", foreground="green")
            self.log("✅ Trading bot started successfully!")
            
            # Send Telegram notification for bot start
            try:
                notify_bot_status("STARTED", f"Trading bot activated - Strategy: {self.current_strategy}, Symbol: {symbol}")
            except Exception as telegram_e:
                self.log(f"⚠️ Telegram start notification failed: {str(telegram_e)}")
            
        except Exception as e:
            self.log(f"❌ Error starting bot: {str(e)}")
            self.start_btn.config(state="normal")
            self.bot_status_lbl.config(text="Bot: Error 🔴", foreground="red")
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        try:
            self.log("🚨 EMERGENCY STOP ACTIVATED!")
            
            # Stop bot
            import __main__
            if hasattr(__main__, 'bot_running'):
                __main__.bot_running = False
            
            # Close all positions
            self.close_all_positions()
            
            self.bot_status_lbl.config(text="Bot: EMERGENCY STOPPED 🔴", foreground="red")
            self.start_btn.config(state="normal")
            
            self.log("🛑 All operations stopped by emergency stop")
            
        except Exception as e:
            self.log(f"❌ Error during emergency stop: {str(e)}")
    
    def close_all_positions(self):
        """Close all open positions"""
        try:
            self.log("🔄 Closing all open positions...")
            
            from trading_operations import close_all_orders
            close_all_orders()
            
            # Update positions display
            self.update_positions()
            
            self.log("✅ All positions closed")
            
        except Exception as e:
            self.log(f"❌ Error closing positions: {str(e)}")
    
    def update_gui_data(self):
        """Ultra-responsive GUI with real-time market analysis and profit optimization"""
        try:
            update_start = datetime.datetime.now()
            self._update_counter += 1
            
            # Track update performance
            if self._update_counter % 10 == 0:
                time_since_last = (update_start - self._last_update_time).total_seconds()
                update_interval = time_since_last / 10
                if update_interval > 2.0:
                    logger(f"⚠️ Slow GUI update detected: {update_interval:.1f}s")
            
            # Update account information
            self.update_account_info()
            
            # Update positions
            self.update_positions()
            
            # Log performance update periodically
            if self._update_counter % 20 == 0:
                try:
                    info = get_account_info()
                    positions = get_positions()
                    position_count = len(positions) if positions else 0
                    
                    if info:
                        logger(f"📊 GUI Update #{self._update_counter}: Balance=${info['balance']:.2f}, Equity=${info['equity']:.2f}, Positions={position_count}")
                    else:
                        logger(f"📊 GUI Update #{self._update_counter}: MT5 disconnected")
                except Exception as perf_e:
                    pass
            
        except Exception as e:
            logger(f"❌ GUI update error: {str(e)}")
            try:
                # Log detailed error info
                logger(f"📝 GUI update traceback: {traceback.format_exc()}")
            except:
                pass
        finally:
            # Schedule next update
            self.root.after(GUI_UPDATE_INTERVAL, self.update_gui_data)
            self._last_update_time = datetime.datetime.now()
    
    def update_account_info(self):
        """Update account information display"""
        try:
            info = get_account_info()
            
            if info:
                self.balance_lbl.config(text=f"Balance: ${info['balance']:.2f}", foreground="white")
                self.equity_lbl.config(text=f"Equity: ${info['equity']:.2f}", foreground="white")
                self.margin_lbl.config(text=f"Free Margin: ${info['free_margin']:.2f}", foreground="white")
                
                if info['margin_level'] > 0:
                    margin_color = "green" if info['margin_level'] > 200 else "orange" if info['margin_level'] > 100 else "red"
                    self.margin_level_lbl.config(text=f"Margin Level: {info['margin_level']:.1f}%", 
                                               foreground=margin_color)
                else:
                    self.margin_level_lbl.config(text="Margin Level: N/A", foreground="gray")
                
                self.server_lbl.config(text=f"Server: {info['server']}", foreground="white")
                
            else:
                # Show disconnected state
                self.balance_lbl.config(text="Balance: Disconnected", foreground="gray")
                self.equity_lbl.config(text="Equity: Disconnected", foreground="gray")
                self.margin_lbl.config(text="Free Margin: Disconnected", foreground="gray")
                self.margin_level_lbl.config(text="Margin Level: Disconnected", foreground="gray")
                self.server_lbl.config(text="Server: Disconnected", foreground="gray")
                
        except Exception as e:
            logger(f"❌ Error updating account info: {str(e)}")
    
    def update_positions(self):
        """Update positions display"""
        try:
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            positions = get_positions()
            
            if positions:
                for pos in positions:
                    pos_type = "BUY" if pos.type == 0 else "SELL"
                    profit_color = "green" if pos.profit >= 0 else "red"
                    
                    item = self.positions_tree.insert("", "end", values=(
                        pos.symbol,
                        pos_type,
                        f"{pos.volume:.2f}",
                        f"{pos.price_open:.5f}",
                        f"{pos.price_current:.5f}",
                        f"${pos.profit:.2f}"
                    ))
                    
                    # Color code profitable/losing positions
                    if pos.profit >= 0:
                        self.positions_tree.set(item, "Profit", f"${pos.profit:.2f}")
                    else:
                        self.positions_tree.set(item, "Profit", f"${pos.profit:.2f}")
            
        except Exception as e:
            logger(f"❌ Error updating positions: {str(e)}")
    
    def refresh_data(self):
        """Manually refresh all data"""
        try:
            self.log("🔄 Refreshing all data...")
            self.update_account_info()
            self.update_positions()
            self.update_symbols()
            self.log("✅ Data refreshed successfully")
        except Exception as e:
            self.log(f"❌ Error refreshing data: {str(e)}")
    
    def show_performance_report(self):
        """Show performance report in popup"""
        try:
            report = generate_performance_report()
            
            # Create popup window
            report_window = tk.Toplevel(self.root)
            report_window.title("📊 Performance Report")
            report_window.geometry("800x600")
            report_window.configure(bg="#0f0f0f")
            
            # Report text
            report_text = ScrolledText(report_window, bg="#1a1a1a", fg="white", 
                                     font=("Consolas", 10))
            report_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            report_text.insert("1.0", report)
            report_text.config(state="disabled")
            
            self.log("📊 Performance report displayed")
            
        except Exception as e:
            self.log(f"❌ Error showing report: {str(e)}")
    
    def clear_log(self):
        """Clear the log display"""
        try:
            self.log_text.delete("1.0", tk.END)
            self.log("🗑️ Log cleared")
        except Exception as e:
            logger(f"❌ Error clearing log: {str(e)}")
    
    def log(self, message: str):
        """Add message to log display"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
            # Limit log size to prevent memory issues
            lines = int(self.log_text.index('end-1c').split('.')[0])
            if lines > 1000:
                self.log_text.delete("1.0", "100.0")
                
        except Exception as e:
            # Fallback to console if GUI log fails
            print(f"GUI Log Error: {str(e)}")
            print(f"Message: {message}")
    
    def on_closing(self):
        """Handle GUI closing event"""
        try:
            self.log("🔄 Shutting down trading bot...")
            
            # Stop bot if running
            import __main__
            if hasattr(__main__, 'bot_running'):
                __main__.bot_running = False
            
            # Give time for cleanup
            import time
            time.sleep(1)
            
            self.root.destroy()
            
        except Exception as e:
            logger(f"❌ Error during shutdown: {str(e)}")
            self.root.destroy()
    
    def get_current_lot_size(self) -> float:
        """Get current lot size for TP/SL percentage calculations""" 
        try:
            return float(self.lot_entry.get())
        except:
            return 0.01
