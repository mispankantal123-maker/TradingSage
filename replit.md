# MT5 Trading Bot - REAL MONEY TRADING EDITION

## Overview

This is a comprehensive MetaTrader 5 (MT5) trading bot application built for REAL MONEY trading with Python and tkinter. The bot provides an automated trading system with multiple trading strategies, real-time GUI controls, and advanced risk management features. The application connects directly to MT5 terminals for executing live forex and commodity trades using real money with configurable parameters including take profit, stop loss, lot sizing, and multiple trading strategies like scalping, intraday, arbitrage, and high-frequency trading.

**⚠️ CRITICAL: This is configured for REAL MONEY trading, not demo mode!**

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (August 2025)

**✅ MAJOR SUCCESS - Bot Now Working Perfectly:**
- Fixed GUI freezing issues with async threading implementation
- Automated trading loop now stable and running (tested with Scalping/BTCUSDm)
- All manual trading, connect/disconnect, and start/stop functions working
- Real money safety warnings and confirmations active
- Price spike detection and risk management functioning
- Auto-detect symbol feature restored and improved
- **✅ MAJOR UPGRADE**: Bot3.py integration complete - No freeze issues!
- **✅ SIMPLIFIED TRADING LOOP**: Adopted successful bot3.py approach for reliable execution
- **✅ DIRECT ORDER PLACEMENT**: Streamlined order execution like proven bot3.py
- **✅ SCORING SYSTEM**: Implemented bot3.py's effective 6-point signal scoring
- **✅ FREEZE ISSUE RESOLVED**: Removed excessive logging and complexity causing GUI freeze
- **✅ PERCENT TP/SL WORKING**: Balance-based percent calculations fully functional
- **✅ AUTO ORDER HANDLING**: Bot now places orders automatically like bot3.py
- **✅ REAL MONEY READY**: Simplified but robust approach for live trading
- **✅ START_TRADING SIMPLIFIED**: Replaced complex validation with bot3.py minimal approach
- **✅ NO MORE FREEZE ON START**: Removed all blocking validations that caused GUI freeze

## System Architecture

### GUI Framework
- **Technology**: tkinter with ttk for enhanced styling
- **Architecture**: Single-window desktop application with tabbed or sectioned interface
- **Key Components**: 
  - Real-time trading controls (start/stop, connect/disconnect)
  - Strategy selection dropdown with predefined configurations
  - Symbol selection with both dropdown and manual input
  - Dynamic lot sizing with auto-calculation based on risk percentage
  - Live log display with scrollable text area
  - Status indicators for connection and trading state

### Trading Engine
- **Core Technology**: MetaTrader5 Python API
- **Threading Model**: Separate thread for trading operations to prevent GUI freezing
- **Strategy System**: Modular strategy configuration with predefined parameters for different trading styles
- **Risk Management**: 
  - Maximum orders per session with daily reset
  - Minimum balance checks
  - Price spike detection and filtering
  - Configurable stop loss and take profit in multiple units (pips, price, percent, money)

### Configuration Management
- **Storage**: JSON-based configuration persistence
- **Structure**: Centralized ConfigManager class handling default values and user preferences
- **Auto-save**: Automatic configuration saving when changes are made
- **Validation**: Input validation and sanitization for all user-provided parameters

### Logging System
- **Implementation**: Custom Logger class with multiple output destinations
- **Real-time Display**: GUI log area updates in real-time
- **Persistence**: File-based logging for debugging and audit trails
- **Threading Safety**: Thread-safe logging operations for concurrent access

### Data Flow
- **MT5 Connection**: Direct API connection with auto-reconnection capabilities
- **Price Data**: Real-time price feeds from MT5 for decision making
- **Order Management**: Direct order placement and monitoring through MT5 API
- **State Management**: Centralized state tracking for connection status, trading status, and configuration

## External Dependencies

### Trading Platform Integration
- **MetaTrader5 Python Package**: Primary interface for MT5 terminal communication
- **MT5 Terminal**: Required Windows application for broker connectivity

### Python Libraries
- **tkinter/ttk**: Native GUI framework for desktop interface
- **threading**: Multi-threading support for non-blocking operations
- **numpy**: Mathematical operations and data analysis
- **json**: Configuration file handling and data serialization
- **datetime**: Time-based operations and scheduling

### Optional Integrations
- **Telegram Bot API**: Notifications and remote monitoring capabilities
- **CSV Export**: Trade history and logging data export functionality

### System Requirements
- **Windows OS**: Primary target platform for MT5 compatibility
- **MT5 Terminal**: Must be installed and configured with broker account
- **Python 3.7+**: Core runtime environment with required packages