"""
MT5 Trading Bot - GUI Module
Professional tkinter interface with all trading controls
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime

class TradingBotGUI:
    def __init__(self, root, trading_engine, config, logger):
        self.root = root
        self.trading_engine = trading_engine
        self.config = config
        self.logger = logger
        
        # Variables for GUI controls
        self.setup_variables()
        
        # Create GUI layout
        self.create_widgets()
        
        # Load saved configuration
        self.load_config()
        
        # Start status update thread
        self.start_status_updates()
        
    def setup_variables(self):
        """Initialize tkinter variables"""
        self.strategy_var = tk.StringVar(value="Scalping")
        self.symbol_var = tk.StringVar(value="EURUSD")
        self.manual_symbol_var = tk.StringVar()
        self.lot_var = tk.StringVar(value="0.01")
        self.auto_lot_var = tk.BooleanVar(value=False)
        self.risk_percent_var = tk.StringVar(value="2.0")
        self.tp_value_var = tk.StringVar(value="20")
        self.tp_unit_var = tk.StringVar(value="pips")
        self.sl_value_var = tk.StringVar(value="10")
        self.sl_unit_var = tk.StringVar(value="pips")
        self.interval_var = tk.StringVar(value="10")
        
        # Status variables
        self.connection_status_var = tk.StringVar(value="Disconnected")
        self.trading_status_var = tk.StringVar(value="Stopped")
        self.account_info_var = tk.StringVar(value="No account info")
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with scrollable frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Trading tab
        trading_frame = ttk.Frame(notebook)
        notebook.add(trading_frame, text="Trading")
        self.create_trading_tab(trading_frame)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.create_config_tab(config_frame)
        
        # Logs tab
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Logs")
        self.create_logs_tab(logs_frame)
        
    def create_trading_tab(self, parent):
        """Create main trading interface"""
        # Status section
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Connection status
        conn_frame = ttk.Frame(status_frame)
        conn_frame.pack(fill=tk.X)
        
        ttk.Label(conn_frame, text="MT5 Connection:").pack(side=tk.LEFT)
        self.connection_label = ttk.Label(conn_frame, textvariable=self.connection_status_var, 
                                         foreground="red", font=("Arial", 9, "bold"))
        self.connection_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(conn_frame, text="Trading Status:").pack(side=tk.LEFT)
        self.trading_label = ttk.Label(conn_frame, textvariable=self.trading_status_var,
                                      foreground="red", font=("Arial", 9, "bold"))
        self.trading_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Account info
        ttk.Label(status_frame, textvariable=self.account_info_var).pack(anchor=tk.W, pady=(5, 0))
        
        # Connection controls
        conn_controls = ttk.Frame(status_frame)
        conn_controls.pack(fill=tk.X, pady=(10, 0))
        
        self.connect_btn = ttk.Button(conn_controls, text="Connect MT5", 
                                     command=self.connect_mt5)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(conn_controls, text="Disconnect MT5", 
                                        command=self.disconnect_mt5, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT)
        
        # Strategy and Symbol section
        strategy_frame = ttk.LabelFrame(parent, text="Strategy & Symbol", padding=10)
        strategy_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Strategy selection
        strategy_row = ttk.Frame(strategy_frame)
        strategy_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(strategy_row, text="Strategy:", width=12).pack(side=tk.LEFT)
        strategy_combo = ttk.Combobox(strategy_row, textvariable=self.strategy_var, 
                                     values=["Scalping", "Intraday", "Arbitrage", "High Frequency Trading"],
                                     state="readonly", width=20)
        strategy_combo.pack(side=tk.LEFT, padx=(0, 10))
        strategy_combo.bind('<<ComboboxSelected>>', self.on_strategy_change)
        
        # Symbol selection
        symbol_row = ttk.Frame(strategy_frame)
        symbol_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(symbol_row, text="Symbol:", width=12).pack(side=tk.LEFT)
        self.symbol_combo = ttk.Combobox(symbol_row, textvariable=self.symbol_var, width=15)
        self.symbol_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(symbol_row, text="Manual:").pack(side=tk.LEFT, padx=(10, 5))
        manual_symbol_entry = ttk.Entry(symbol_row, textvariable=self.manual_symbol_var, width=15)
        manual_symbol_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(symbol_row, text="Use Manual", command=self.use_manual_symbol).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(symbol_row, text="Auto-Detect", command=self.auto_detect_symbol).pack(side=tk.LEFT, padx=(5, 0))
        
        # Lot and Risk section
        lot_frame = ttk.LabelFrame(parent, text="Lot Size & Risk", padding=10)
        lot_frame.pack(fill=tk.X, pady=(0, 10))
        
        lot_row = ttk.Frame(lot_frame)
        lot_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(lot_row, text="Lot Size:", width=12).pack(side=tk.LEFT)
        lot_entry = ttk.Entry(lot_row, textvariable=self.lot_var, width=10)
        lot_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        auto_lot_check = ttk.Checkbutton(lot_row, text="Auto Lot", variable=self.auto_lot_var,
                                        command=self.toggle_auto_lot)
        auto_lot_check.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(lot_row, text="Risk %:", width=8).pack(side=tk.LEFT)
        risk_entry = ttk.Entry(lot_row, textvariable=self.risk_percent_var, width=8)
        risk_entry.pack(side=tk.LEFT)
        
        # TP/SL section
        tp_sl_frame = ttk.LabelFrame(parent, text="Take Profit & Stop Loss", padding=10)
        tp_sl_frame.pack(fill=tk.X, pady=(0, 10))
        
        # TP row
        tp_row = ttk.Frame(tp_sl_frame)
        tp_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(tp_row, text="Take Profit:", width=12).pack(side=tk.LEFT)
        tp_entry = ttk.Entry(tp_row, textvariable=self.tp_value_var, width=10)
        tp_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        tp_unit_combo = ttk.Combobox(tp_row, textvariable=self.tp_unit_var,
                                    values=["pips", "price", "percent", "money"],
                                    state="readonly", width=8)
        tp_unit_combo.pack(side=tk.LEFT)
        
        # SL row
        sl_row = ttk.Frame(tp_sl_frame)
        sl_row.pack(fill=tk.X)
        
        ttk.Label(sl_row, text="Stop Loss:", width=12).pack(side=tk.LEFT)
        sl_entry = ttk.Entry(sl_row, textvariable=self.sl_value_var, width=10)
        sl_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        sl_unit_combo = ttk.Combobox(sl_row, textvariable=self.sl_unit_var,
                                    values=["pips", "price", "percent", "money"],
                                    state="readonly", width=8)
        sl_unit_combo.pack(side=tk.LEFT)
        
        # Trading controls
        controls_frame = ttk.LabelFrame(parent, text="Trading Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_row1 = ttk.Frame(controls_frame)
        controls_row1.pack(fill=tk.X, pady=(0, 5))
        
        self.start_btn = ttk.Button(controls_row1, text="Start Bot", command=self.start_trading,
                                   style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(controls_row1, text="Stop Bot", command=self.stop_trading,
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(controls_row1, text="Interval (s):").pack(side=tk.LEFT, padx=(0, 5))
        interval_entry = ttk.Entry(controls_row1, textvariable=self.interval_var, width=8)
        interval_entry.pack(side=tk.LEFT)
        
        # Manual trading controls
        controls_row2 = ttk.Frame(controls_frame)
        controls_row2.pack(fill=tk.X)
        
        ttk.Label(controls_row2, text="Manual Trading:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.buy_btn = ttk.Button(controls_row2, text="Manual BUY", command=self.manual_buy,
                                 style="Accent.TButton")
        self.buy_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.sell_btn = ttk.Button(controls_row2, text="Manual SELL", command=self.manual_sell,
                                  style="Accent.TButton")
        self.sell_btn.pack(side=tk.LEFT)
        
    def create_config_tab(self, parent):
        """Create configuration tab"""
        config_frame = ttk.LabelFrame(parent, text="Bot Configuration", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Strategy-specific settings will be added here
        ttk.Label(config_frame, text="Strategy-specific configurations will be displayed here").pack()
        
        # Save/Load buttons
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Save Configuration", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Load Configuration", command=self.load_config).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_config).pack(side=tk.LEFT, padx=(5, 0))
        
    def create_logs_tab(self, parent):
        """Create logs tab"""
        logs_frame = ttk.Frame(parent)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, width=80, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT)
        
        # Set up log display updates
        self.logger.set_gui_callback(self.update_log_display)
        
    def update_log_display(self, message):
        """Update log display in GUI"""
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"{timestamp} - {message}\n")
            self.log_text.see(tk.END)
            
    def start_status_updates(self):
        """Start thread for updating status information"""
        def update_status():
            while True:
                try:
                    # Update connection status
                    if self.trading_engine.is_connected():
                        self.connection_status_var.set("Connected")
                        self.connection_label.configure(foreground="green")
                        self.connect_btn.configure(state=tk.DISABLED)
                        self.disconnect_btn.configure(state=tk.NORMAL)
                        
                        # Update account info
                        account_info = self.trading_engine.get_account_info()
                        if account_info:
                            self.account_info_var.set(
                                f"Account: {account_info['login']} | Balance: ${account_info['balance']:.2f} | "
                                f"Equity: ${account_info['equity']:.2f}"
                            )
                    else:
                        self.connection_status_var.set("Disconnected")
                        self.connection_label.configure(foreground="red")
                        self.connect_btn.configure(state=tk.NORMAL)
                        self.disconnect_btn.configure(state=tk.DISABLED)
                        self.account_info_var.set("No account info")
                    
                    # Update trading status
                    if self.trading_engine.is_running():
                        self.trading_status_var.set("Running")
                        self.trading_label.configure(foreground="green")
                        self.start_btn.configure(state=tk.DISABLED)
                        self.stop_btn.configure(state=tk.NORMAL)
                    else:
                        self.trading_status_var.set("Stopped")
                        self.trading_label.configure(foreground="red")
                        self.start_btn.configure(state=tk.NORMAL)
                        self.stop_btn.configure(state=tk.DISABLED)
                    
                    # Update symbol list if connected
                    if self.trading_engine.is_connected():
                        symbols = self.trading_engine.get_symbols()
                        if symbols:
                            self.symbol_combo.configure(values=symbols)
                            
                except Exception as e:
                    pass  # Continue silently on errors
                
                time.sleep(1)  # Update every second
        
        status_thread = threading.Thread(target=update_status, daemon=True)
        status_thread.start()
        
    # Event handlers
    def connect_mt5(self):
        """Connect to MT5"""
        success = self.trading_engine.connect_mt5()
        if success:
            self.logger.log("MT5 connected successfully")
        else:
            messagebox.showerror("Connection Error", "Failed to connect to MT5")
            
    def disconnect_mt5(self):
        """Disconnect from MT5"""
        self.trading_engine.disconnect_mt5()
        self.logger.log("MT5 disconnected")
        
    def start_trading(self):
        """Start automated trading"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        # Get current settings
        settings = self.get_current_settings()
        
        # Start trading
        success = self.trading_engine.start_trading(settings)
        if success:
            self.logger.log("Automated trading started")
        else:
            messagebox.showerror("Error", "Failed to start trading")
            
    def stop_trading(self):
        """Stop automated trading"""
        self.trading_engine.stop_trading()
        self.logger.log("Automated trading stopped")
        
    def manual_buy(self):
        """Execute manual BUY order"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        settings = self.get_current_settings()
        success = self.trading_engine.place_manual_order("BUY", settings)
        if success:
            self.logger.log("Manual BUY order executed")
        else:
            messagebox.showerror("Error", "Failed to execute BUY order")
            
    def manual_sell(self):
        """Execute manual SELL order"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        settings = self.get_current_settings()
        success = self.trading_engine.place_manual_order("SELL", settings)
        if success:
            self.logger.log("Manual SELL order executed")
        else:
            messagebox.showerror("Error", "Failed to execute SELL order")
            
    def use_manual_symbol(self):
        """Use manually entered symbol"""
        manual_symbol = self.manual_symbol_var.get().strip()
        if manual_symbol:
            if self.trading_engine.validate_symbol(manual_symbol):
                self.symbol_var.set(manual_symbol)
                self.logger.log(f"Using manual symbol: {manual_symbol}")
            else:
                messagebox.showerror("Error", f"Invalid symbol: {manual_symbol}")
        else:
            messagebox.showwarning("Warning", "Please enter a symbol")
            
    def auto_detect_symbol(self):
        """Auto-detect active symbol"""
        symbol = self.trading_engine.auto_detect_symbol()
        if symbol:
            self.symbol_var.set(symbol)
            self.logger.log(f"Auto-detected symbol: {symbol}")
        else:
            messagebox.showwarning("Warning", "No active symbol detected")
            
    def on_strategy_change(self, event=None):
        """Handle strategy change"""
        strategy = self.strategy_var.get()
        # Load strategy-specific defaults
        defaults = self.trading_engine.get_strategy_defaults(strategy)
        if defaults:
            self.tp_value_var.set(str(defaults.get('tp', 20)))
            self.sl_value_var.set(str(defaults.get('sl', 10)))
            
    def toggle_auto_lot(self):
        """Toggle auto lot calculation"""
        # Implementation for auto lot toggle
        pass
        
    def get_current_settings(self):
        """Get current GUI settings as dictionary"""
        return {
            'strategy': self.strategy_var.get(),
            'symbol': self.symbol_var.get(),
            'lot_size': float(self.lot_var.get()) if self.lot_var.get() else 0.01,
            'auto_lot': self.auto_lot_var.get(),
            'risk_percent': float(self.risk_percent_var.get()) if self.risk_percent_var.get() else 2.0,
            'tp_value': float(self.tp_value_var.get()) if self.tp_value_var.get() else 20,
            'tp_unit': self.tp_unit_var.get(),
            'sl_value': float(self.sl_value_var.get()) if self.sl_value_var.get() else 10,
            'sl_unit': self.sl_unit_var.get(),
            'interval': int(self.interval_var.get()) if self.interval_var.get() else 10
        }
        
    def save_config(self):
        """Save current configuration"""
        settings = self.get_current_settings()
        self.config.update_config(settings)
        self.config.save_config()
        self.logger.log("Configuration saved")
        messagebox.showinfo("Success", "Configuration saved successfully")
        
    def load_config(self):
        """Load saved configuration"""
        config_data = self.config.get_config()
        
        # Update GUI with loaded values
        if 'strategy' in config_data:
            self.strategy_var.set(config_data['strategy'])
        if 'symbol' in config_data:
            self.symbol_var.set(config_data['symbol'])
        if 'lot_size' in config_data:
            self.lot_var.set(str(config_data['lot_size']))
        if 'auto_lot' in config_data:
            self.auto_lot_var.set(config_data['auto_lot'])
        if 'risk_percent' in config_data:
            self.risk_percent_var.set(str(config_data['risk_percent']))
        if 'tp_value' in config_data:
            self.tp_value_var.set(str(config_data['tp_value']))
        if 'tp_unit' in config_data:
            self.tp_unit_var.set(config_data['tp_unit'])
        if 'sl_value' in config_data:
            self.sl_value_var.set(str(config_data['sl_value']))
        if 'sl_unit' in config_data:
            self.sl_unit_var.set(config_data['sl_unit'])
        if 'interval' in config_data:
            self.interval_var.set(str(config_data['interval']))
            
        self.logger.log("Configuration loaded")
        
    def reset_config(self):
        """Reset configuration to defaults"""
        self.config.reset_to_defaults()
        self.load_config()
        self.logger.log("Configuration reset to defaults")
        messagebox.showinfo("Success", "Configuration reset to defaults")
        
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
        
    def save_logs(self):
        """Save logs to file"""
        self.logger.save_logs()
        messagebox.showinfo("Success", "Logs saved to file")
