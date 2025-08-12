# MT5 Advanced Auto Trading Bot

### Overview
This project is a professional-grade algorithmic trading platform for MetaTrader 5, enhanced with advanced profit optimization features requested by a trader with 2 billion monthly turnover. The system features dynamic position sizing, multi-timeframe analysis, and comprehensive risk management for maximum profit generation while maintaining controlled risk exposure. It offers a modular, maintainable, and production-ready solution for automated trading with professional-grade enhancements.

### User Preferences
**Communication Style**: Simple, everyday language
**Target Platform**: Windows OS with MetaTrader 5 for live trading
**Development Environment**: Cross-platform support via mock MT5, optimized for Replit cloud environment
**Code Organization**: Modular, maintainable, production-ready

### Recent Changes (January 2025)
- **Replit Migration**: Successfully migrated from Replit Agent to Replit environment
- **Headless Mode**: Implemented automatic headless mode detection for cloud environments
- **Mock MT5 Integration**: Enhanced mock MT5 to work seamlessly in development mode
- **Dependencies**: Added scipy for advanced technical analysis and python-telegram-bot for notifications
- **Auto-deployment**: Configured automatic startup in Replit with MT5 mock fallback

### Ultra-Advanced Enhancements (January 12, 2025)
- **Advanced Signal Optimizer**: Institutional flow analysis, volume profile, market structure
- **Confidence Calibration System**: 7-component ultra-precise confidence calibration
- **Quality Grading**: A+ to F signal grading with dynamic position sizing (2.5x for A+ signals)
- **Ultra-Filtering**: Multiple quality gates targeting 85-92% win rate
- **Enhanced Analysis Engine**: Multi-layer optimization with 73%+ confidence signals detected
- **Professional Risk Management**: 5-layer protection with emergency stops and correlation monitoring

### System Architecture
The system employs a modular architecture, refactoring a monolithic application into specialized components for enhanced maintainability and scalability.

**Core Components:**
-   **Configuration Management**: Centralized management of trading parameters, strategies, and system constants.
-   **Logging**: Centralized logging with GUI integration and file management.
-   **Validation**: Input validation and trading condition checking.

**MT5 Integration Layer:**
-   **MT5 Connectivity**: Handles MetaTrader 5 connection, initialization, and order execution.
-   **Mock MT5**: Provides a cross-platform mock for development and testing environments.
-   **Data Management**: Manages market data fetching, caching, and validation.

**Analysis Engine:**
-   **Technical Analysis**: Implements a comprehensive suite of technical indicators (EMAs, RSI, MACD, Bollinger Bands, ATR, Stochastic, WMA).
-   **Multi-Timeframe Analysis**: Professional MTF confluence system analyzing M1, M5, M15, H1 timeframes with scoring and risk assessment.
-   **Trading Strategies**: Four enhanced trading strategies with MTF validation and dynamic position sizing integration.
-   **Dynamic Position Sizing**: ATR-based volatility calculations, equity risk management, and correlation risk monitoring.
-   **AI Analysis**: Advanced AI for market analysis and pattern recognition.

**Trading Operations:**
-   **Order & Position Management**: Handles order execution, position tracking, and dynamic TP/SL calculations.
-   **Session Management**: Detects trading sessions and applies time-based filtering.
-   **Risk Management**: Enforces comprehensive risk controls, including daily trade limits, position sizing, margin alerts, and equity protection.

**User Interface:**
-   **GUI Module**: A complete tkinter-based GUI (1400x900, dark theme) provides real-time control, parameter adjustment, and display of account info and positions.
-   **Performance Tracking**: Offers real-time reporting and trade analytics through a dedicated performance popup window.

**Bot Control:**
-   **Main Logic**: Orchestrates the overall trading logic and automation.
-   **Application Entry**: Supports both GUI and headless modes.
-   **Test Suite**: Comprehensive test suite for all modules.

**Key Features:**
-   **Professional Trading Enhancements**: Dynamic position sizing based on ATR volatility, multi-timeframe confluence analysis, and correlation risk management for profit optimization.
-   **Trading Strategies**: Scalping, Intraday, Arbitrage, and HFT, each with specific entry/exit conditions, TP/SL settings, and enhanced with MTF validation.
-   **Dynamic Position Sizing**: ATR-based volatility calculations, equity percentage risk management, strategy-specific adjustments, and correlation risk monitoring.
-   **Multi-Timeframe Analysis**: M1, M5, M15, H1 confluence analysis with scoring system (0-100) and risk factor assessment for higher probability setups.
-   **Technical Analysis Suite**: Diverse set of moving averages, oscillators, and volatility indicators enhanced with multi-timeframe validation.
-   **GUI Interface**: Intuitive, dark-themed interface with controls for MT5 connection, bot activation, emergency stop, and detailed parameter configuration. Supports real-time account data, position display, and scrolling logs.
-   **Advanced Risk Management**: Configurable daily trade limits, maximum open positions, dynamic risk per trade, correlation monitoring, margin level alerts, and session-based adjustments.
-   **Comprehensive TP/SL System**: Supports pips, price, percentage (balance/equity), and money (currency) based TP/SL calculations, fully integrated with the GUI and MT5.
-   **24/7 Operation**: Enabled for continuous trading across all sessions, with enhanced error recovery and professional-grade monitoring.
-   **Telegram Notifications**: Real-time alerts for trades, position changes, account monitoring, strategy changes, session updates, bot status, risk alerts, and daily summaries.
-   **Universal Symbol Support**: Comprehensive handling for over 50 asset types including Forex, Crypto, Metals, Indices, Commodities, and Stocks.

### External Dependencies
-   **pandas**: For market data analysis and DataFrame operations.
-   **numpy**: For numerical computations in indicators and statistics.
-   **requests**: For HTTP requests (if external data sources are used).
-   **tkinter**: Python's built-in GUI framework.
-   **MetaTrader5**: The official Python library for MT5 integration.
-   **mt5_mock**: Custom mock implementation for cross-platform development.
-   **Python 3.8+**: Minimum required Python version.
```