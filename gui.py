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
        # WARNING BANNER
        warning_frame = tk.Frame(parent, bg='#FF4444', relief='raised', bd=2)
        warning_frame.pack(fill=tk.X, pady=(0, 10))
        
        warning_label = tk.Label(
            warning_frame, 
            text="⚠️ REAL MONEY TRADING MODE - UANG ASLI AKAN DIGUNAKAN ⚠️",
            bg='#FF4444', 
            fg='white', 
            font=('Arial', 12, 'bold'),
            padx=10, 
            pady=5
        )
        warning_label.pack()
        
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
            error_count = 0
            max_errors = 5
            
            while True:
                try:
                    # Update connection status
                    if self.trading_engine.is_connected():
                        self.root.after(0, self._update_connected_status)
                    else:
                        self.root.after(0, self._update_disconnected_status)
                    
                    # Update trading status
                    if self.trading_engine.is_running():
                        self.root.after(0, self._update_trading_running)
                    else:
                        self.root.after(0, self._update_trading_stopped)
                    
                    # Update symbol list if connected
                    if self.trading_engine.is_connected():
                        try:
                            symbols = self.trading_engine.get_symbols()
                            if symbols:
                                self.root.after(0, lambda: self.symbol_combo.configure(values=symbols))
                        except:
                            pass
                            
                    error_count = 0  # Reset error count on success
                    
                except Exception as e:
                    error_count += 1
                    if error_count >= max_errors:
                        self.logger.log(f"Status update thread stopped after {max_errors} errors")
                        break
                
                time.sleep(2)  # Update every 2 seconds to reduce load
        
        status_thread = threading.Thread(target=update_status, daemon=True)
        status_thread.start()
        
    def _update_connected_status(self):
        """Update GUI for connected status - called from main thread"""
        try:
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
        except Exception as e:
            self.logger.log(f"Error updating connected status: {str(e)}")
            
    def _update_disconnected_status(self):
        """Update GUI for disconnected status - called from main thread"""
        try:
            self.connection_status_var.set("Disconnected")
            self.connection_label.configure(foreground="red")
            self.connect_btn.configure(state=tk.NORMAL)
            self.disconnect_btn.configure(state=tk.DISABLED)
            self.account_info_var.set("No account info")
        except Exception as e:
            self.logger.log(f"Error updating disconnected status: {str(e)}")
            
    def _update_trading_running(self):
        """Update GUI for trading running status - called from main thread"""
        try:
            self.trading_status_var.set("Running")
            self.trading_label.configure(foreground="green")
            self.start_btn.configure(state=tk.DISABLED)
            self.stop_btn.configure(state=tk.NORMAL)
        except Exception as e:
            self.logger.log(f"Error updating trading running status: {str(e)}")
            
    def _update_trading_stopped(self):
        """Update GUI for trading stopped status - called from main thread"""
        try:
            self.trading_status_var.set("Stopped")
            self.trading_label.configure(foreground="red")
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)
        except Exception as e:
            self.logger.log(f"Error updating trading stopped status: {str(e)}")
        
    # Event handlers
    def connect_mt5(self):
        """Connect to MT5 asynchronously"""
        def connect_async():
            try:
                success = self.trading_engine.connect_mt5()
                self.root.after(0, self._handle_connect_result, success)
            except Exception as e:
                self.root.after(0, self._handle_connect_error, str(e))
        
        self.logger.log("⏳ Connecting to MT5...")
        threading.Thread(target=connect_async, daemon=True).start()
        
    def disconnect_mt5(self):
        """Disconnect from MT5 asynchronously"""
        def disconnect_async():
            try:
                self.trading_engine.disconnect_mt5()
                self.root.after(0, self._handle_disconnect_result)
            except Exception as e:
                self.root.after(0, self._handle_disconnect_error, str(e))
        
        self.logger.log("⏳ Disconnecting from MT5...")
        threading.Thread(target=disconnect_async, daemon=True).start()
        
    def _handle_connect_result(self, success):
        """Handle MT5 connection result"""
        if success:
            self.logger.log("✅ MT5 connected successfully")
        else:
            self.logger.log("❌ Failed to connect to MT5")
            messagebox.showerror("Connection Error", "Failed to connect to MT5")
            
    def _handle_connect_error(self, error_msg):
        """Handle MT5 connection error"""
        self.logger.log(f"❌ MT5 connection error: {error_msg}")
        messagebox.showerror("Connection Error", f"MT5 connection error:\n\n{error_msg}")
        
    def _handle_disconnect_result(self):
        """Handle MT5 disconnection result"""
        self.logger.log("✅ MT5 disconnected")
        
    def _handle_disconnect_error(self, error_msg):
        """Handle MT5 disconnection error"""
        self.logger.log(f"❌ MT5 disconnection error: {error_msg}")
        messagebox.showerror("Disconnection Error", f"MT5 disconnection error:\n\n{error_msg}")
        
    def start_trading(self):
        """Start automated trading with safety confirmation"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        # REAL MONEY WARNING
        warning_msg = """⚠️ PERINGATAN REAL MONEY TRADING ⚠️

Anda akan memulai trading otomatis dengan UANG ASLI!

Resiko:
• Bot akan melakukan order BUY/SELL otomatis
• Setiap trade menggunakan modal nyata
• Anda bisa kehilangan uang jika market bergerak berlawanan
• Pastikan sudah test strategi dengan akun demo terlebih dahulu

Apakah Anda yakin ingin melanjutkan?"""
        
        result = messagebox.askyesno(
            "⚠️ KONFIRMASI REAL TRADING", 
            warning_msg,
            icon='warning'
        )
        
        if not result:
            self.logger.log("Trading dibatalkan oleh user")
            return
            
        # Get current settings
        settings = self.get_current_settings()
        
        # Final confirmation with settings
        settings_msg = f"""KONFIRMASI SETTINGS TRADING:

Strategy: {settings['strategy']}
Symbol: {settings['symbol']}
Lot Size: {settings['lot_size']}
Take Profit: {settings['tp_value']} {settings['tp_unit']}
Stop Loss: {settings['sl_value']} {settings['sl_unit']}
Interval: {settings['interval']} detik

Lanjutkan trading dengan settings ini?"""
        
        final_confirm = messagebox.askyesno(
            "Konfirmasi Settings", 
            settings_msg
        )
        
        if not final_confirm:
            self.logger.log("Trading dibatalkan pada konfirmasi settings")
            return
        
        # Start trading asynchronously to prevent GUI freezing
        def start_trading_async():
            try:
                success = self.trading_engine.start_trading(settings)
                # Use root.after to safely update GUI from thread
                self.root.after(0, self._handle_start_result, success)
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, self._handle_start_error, error_msg)
        
        # Show immediate feedback
        self.logger.log("⏳ Starting automated trading...")
        
        # Start in separate thread to prevent GUI freeze
        start_thread = threading.Thread(target=start_trading_async, daemon=True)
        start_thread.start()
        
    def _handle_start_result(self, success):
        """Handle trading start result in main thread"""
        if success:
            self.logger.log("🔥 REAL MONEY TRADING STARTED - BE CAREFUL!")
            messagebox.showinfo("Trading Started", "✅ Automated trading started successfully!\n\n⚠️ REAL MONEY mode active!\nMonitor carefully!")
        else:
            error_msg = """❌ Failed to start automated trading!

Possible issues:
• MT5 not connected properly
• Invalid trading settings
• Market is closed
• Check logs for details

Try:
1. Reconnect to MT5
2. Verify symbol is tradeable
3. Check lot size and TP/SL values"""
            messagebox.showerror("Trading Start Failed", error_msg)
            
    def _handle_start_error(self, error_msg):
        """Handle trading start error in main thread"""
        self.logger.log(f"❌ CRITICAL: Exception in start_trading: {error_msg}")
        messagebox.showerror("Critical Error", f"Unexpected error starting trading:\n\n{error_msg}\n\nCheck logs for details")
        
    def _handle_manual_result(self, order_type, success):
        """Handle manual trading result in main thread"""
        if success:
            self.logger.log(f"💰 Manual {order_type} order executed - REAL MONEY!")
            messagebox.showinfo("Order Success", f"✅ Manual {order_type} order executed successfully!\n\n⚠️ REAL MONEY trade completed!")
        else:
            messagebox.showerror("Order Failed", f"❌ Failed to execute {order_type} order!\n\nCheck logs for details.")
            
    def _handle_manual_error(self, order_type, error_msg):
        """Handle manual trading error in main thread"""
        self.logger.log(f"❌ ERROR executing manual {order_type}: {error_msg}")
        messagebox.showerror("Order Error", f"❌ Error executing {order_type} order:\n\n{error_msg}\n\nCheck logs for details.")
            
    def stop_trading(self):
        """Stop automated trading asynchronously"""
        def stop_trading_async():
            try:
                self.trading_engine.stop_trading()
                self.root.after(0, self._handle_stop_result, True)
            except Exception as e:
                self.root.after(0, self._handle_stop_error, str(e))
        
        self.logger.log("⏳ Stopping automated trading...")
        threading.Thread(target=stop_trading_async, daemon=True).start()
        
    def _handle_stop_result(self, success):
        """Handle stop trading result in main thread"""
        if success:
            self.logger.log("✅ Automated trading stopped successfully")
            messagebox.showinfo("Trading Stopped", "✅ Automated trading stopped successfully!")
        
    def _handle_stop_error(self, error_msg):
        """Handle stop trading error in main thread"""
        self.logger.log(f"❌ Error stopping trading: {error_msg}")
        messagebox.showerror("Stop Error", f"❌ Error stopping trading:\n\n{error_msg}")
        
    def manual_buy(self):
        """Execute manual BUY order with confirmation"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        settings = self.get_current_settings()
        
        # Confirmation for manual trade
        confirm_msg = f"""KONFIRMASI MANUAL BUY ORDER:

Symbol: {settings['symbol']}
Lot: {settings['lot_size']}
TP: {settings['tp_value']} {settings['tp_unit']}
SL: {settings['sl_value']} {settings['sl_unit']}

⚠️ Ini adalah REAL MONEY trade!
Lanjutkan BUY order?"""
        
        if messagebox.askyesno("Konfirmasi BUY Order", confirm_msg):
            # Execute order asynchronously to prevent GUI freeze
            def execute_buy_async():
                try:
                    success = self.trading_engine.place_manual_order("BUY", settings)
                    self.root.after(0, self._handle_manual_result, "BUY", success)
                except Exception as e:
                    self.root.after(0, self._handle_manual_error, "BUY", str(e))
            
            self.logger.log("⏳ Executing manual BUY order...")
            threading.Thread(target=execute_buy_async, daemon=True).start()
        else:
            self.logger.log("Manual BUY order dibatalkan")
            
    def manual_sell(self):
        """Execute manual SELL order with confirmation"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        settings = self.get_current_settings()
        
        # Confirmation for manual trade
        confirm_msg = f"""KONFIRMASI MANUAL SELL ORDER:

Symbol: {settings['symbol']}
Lot: {settings['lot_size']}
TP: {settings['tp_value']} {settings['tp_unit']}
SL: {settings['sl_value']} {settings['sl_unit']}

⚠️ Ini adalah REAL MONEY trade!
Lanjutkan SELL order?"""
        
        if messagebox.askyesno("Konfirmasi SELL Order", confirm_msg):
            # Execute order asynchronously to prevent GUI freeze
            def execute_sell_async():
                try:
                    success = self.trading_engine.place_manual_order("SELL", settings)
                    self.root.after(0, self._handle_manual_result, "SELL", success)
                except Exception as e:
                    self.root.after(0, self._handle_manual_error, "SELL", str(e))
            
            self.logger.log("⏳ Executing manual SELL order...")
            threading.Thread(target=execute_sell_async, daemon=True).start()
        else:
            self.logger.log("Manual SELL order dibatalkan")
            
    def use_manual_symbol(self):
        """Use manually entered symbol with validation"""
        manual_symbol = self.manual_symbol_var.get().strip()
        if not manual_symbol:
            messagebox.showwarning("Warning", "Please enter a symbol")
            return
            
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first to validate symbol")
            return
            
        def validate_async():
            try:
                is_valid = self.trading_engine.validate_symbol(manual_symbol)
                self.root.after(0, self._handle_manual_symbol_result, manual_symbol, is_valid)
            except Exception as e:
                self.root.after(0, self._handle_manual_symbol_error, manual_symbol, str(e))
        
        self.logger.log(f"⏳ Validating manual symbol: {manual_symbol}")
        threading.Thread(target=validate_async, daemon=True).start()
        
    def _handle_manual_symbol_result(self, symbol, is_valid):
        """Handle manual symbol validation result"""
        if is_valid:
            self.symbol_var.set(symbol)
            self.logger.log(f"✅ Using validated manual symbol: {symbol}")
            messagebox.showinfo("Symbol Valid", f"✅ Symbol validated: {symbol}")
        else:
            self.logger.log(f"❌ Invalid symbol: {symbol}")
            messagebox.showerror("Invalid Symbol", f"❌ Invalid symbol: {symbol}\n\nTry:\n• Check symbol spelling\n• Use symbols from MT5 Market Watch\n• Example: EURUSD, GBPUSD, XAUUSD")
            
    def _handle_manual_symbol_error(self, symbol, error_msg):
        """Handle manual symbol validation error"""
        self.logger.log(f"❌ Error validating {symbol}: {error_msg}")
        messagebox.showerror("Validation Error", f"❌ Error validating {symbol}:\n\n{error_msg}")
            
    def auto_detect_symbol(self):
        """Auto-detect active symbol asynchronously"""
        if not self.trading_engine.is_connected():
            messagebox.showerror("Error", "Please connect to MT5 first")
            return
            
        def detect_async():
            try:
                symbol = self.trading_engine.auto_detect_symbol()
                self.root.after(0, self._handle_auto_detect_result, symbol)
            except Exception as e:
                self.root.after(0, self._handle_auto_detect_error, str(e))
        
        self.logger.log("⏳ Auto-detecting symbol...")
        threading.Thread(target=detect_async, daemon=True).start()
        
    def _handle_auto_detect_result(self, symbol):
        """Handle auto detect result in main thread"""
        if symbol:
            self.symbol_var.set(symbol)
            self.logger.log(f"✅ Auto-detected symbol: {symbol}")
            messagebox.showinfo("Symbol Detected", f"✅ Symbol detected: {symbol}")
        else:
            self.logger.log("⚠️ No active symbol detected")
            messagebox.showwarning("No Symbol Found", "⚠️ No active symbol detected\n\nTry:\n• Open a chart in MT5\n• Add symbols to Market Watch\n• Use manual symbol entry")
            
    def _handle_auto_detect_error(self, error_msg):
        """Handle auto detect error in main thread"""
        self.logger.log(f"❌ Auto detect error: {error_msg}")
        messagebox.showerror("Auto Detect Error", f"❌ Error detecting symbol:\n\n{error_msg}")
            
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
        try:
            if self.auto_lot_var.get():
                # Auto lot is enabled - calculate based on risk percentage
                self.calculate_auto_lot()
                self.logger.log("Auto lot calculation enabled")
            else:
                # Manual lot entry enabled
                self.logger.log("Manual lot entry enabled")
                
        except Exception as e:
            self.logger.log(f"ERROR in auto lot toggle: {str(e)}")
            
    def calculate_auto_lot(self):
        """Calculate lot size based on risk percentage and account balance"""
        try:
            if not self.trading_engine.is_connected():
                return
                
            account_info = self.trading_engine.get_account_info()
            if not account_info:
                return
                
            balance = account_info['balance']
            risk_percent = float(self.risk_percent_var.get()) if self.risk_percent_var.get() else 2.0
            sl_pips = float(self.sl_value_var.get()) if self.sl_value_var.get() else 10
            
            # Calculate risk amount in money
            risk_amount = balance * (risk_percent / 100)
            
            # Get symbol info for pip value calculation
            symbol = self.symbol_var.get()
            symbol_info = self.trading_engine.get_symbol_info(symbol)
            
            if symbol_info:
                # Simplified pip value calculation (assumes standard forex pair)
                pip_value = 10  # For standard lots in USD
                
                # Calculate lot size
                calculated_lot = risk_amount / (sl_pips * pip_value)
                
                # Ensure minimum and maximum lot sizes
                calculated_lot = max(0.01, min(calculated_lot, 10.0))
                calculated_lot = round(calculated_lot, 2)
                
                self.lot_var.set(str(calculated_lot))
                self.logger.log(f"Auto-calculated lot size: {calculated_lot} (Risk: {risk_percent}%)")
            
        except Exception as e:
            self.logger.log(f"ERROR calculating auto lot: {str(e)}")
        
    def get_current_settings(self):
        """Get current GUI settings as dictionary with proper validation"""
        try:
            # Validate and convert inputs with fallbacks
            def safe_float(value, default):
                try:
                    return float(value) if value and str(value).strip() else default
                except (ValueError, TypeError):
                    return default
                    
            def safe_int(value, default):
                try:
                    return int(value) if value and str(value).strip() else default
                except (ValueError, TypeError):
                    return default
            
            settings = {
                'strategy': self.strategy_var.get() or 'Scalping',
                'symbol': self.symbol_var.get() or 'EURUSD',
                'lot_size': safe_float(self.lot_var.get(), 0.01),
                'auto_lot': self.auto_lot_var.get(),
                'risk_percent': safe_float(self.risk_percent_var.get(), 2.0),
                'tp_value': safe_float(self.tp_value_var.get(), 20),
                'tp_unit': self.tp_unit_var.get() or 'pips',
                'sl_value': safe_float(self.sl_value_var.get(), 10),
                'sl_unit': self.sl_unit_var.get() or 'pips',
                'interval': safe_int(self.interval_var.get(), 10)
            }
            
            # Additional validation
            settings['lot_size'] = max(0.01, min(settings['lot_size'], 1000))
            settings['risk_percent'] = max(0.1, min(settings['risk_percent'], 20))
            settings['tp_value'] = max(1, settings['tp_value'])
            settings['sl_value'] = max(1, settings['sl_value'])
            settings['interval'] = max(1, min(settings['interval'], 3600))
            
            return settings
            
        except Exception as e:
            self.logger.log(f"ERROR in get_current_settings: {str(e)}")
            # Return safe defaults
            return {
                'strategy': 'Scalping',
                'symbol': 'EURUSD',
                'lot_size': 0.01,
                'auto_lot': False,
                'risk_percent': 2.0,
                'tp_value': 20,
                'tp_unit': 'pips',
                'sl_value': 10,
                'sl_unit': 'pips',
                'interval': 10
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
