# 💹 MT5 Advanced Auto Trading Bot v4.0 - Modular Edition

## 🚀 Overview

This is a **completely refactored and modularized version** of the original bobot2.py trading bot. The bot maintains **100% identical functionality** while providing clean, maintainable, and professional code architecture.

### ✨ Key Improvements
- **Modular Architecture**: 15+ specialized modules replacing 12,465 lines of duplicated code
- **Zero Duplication**: Eliminated massive code duplication (2 identical GUI classes, repeated functions)
- **Clean Structure**: Professional separation of concerns with clear interfaces
- **Cross-Platform**: Works on Windows (production) and Linux/Mac (development) via mock MT5
- **Maintainable**: Easy to modify, extend, and debug individual components
- **Production Ready**: Ready for live trading on Windows with real MT5

## 📂 Project Structure

```
modular-mt5-bot/
├── 🎯 Core Configuration
│   ├── config.py                 # Trading parameters & constants
│   ├── logger_utils.py           # Logging system
│   └── validation_utils.py       # Input validation
│
├── 🔌 MT5 Integration  
│   ├── mt5_connection.py         # MT5 connectivity
│   ├── mt5_mock.py              # Cross-platform mock
│   └── data_manager.py          # Market data management
│
├── 📊 Analysis Engine
│   ├── indicators.py            # Technical indicators
│   ├── strategies.py            # Trading strategies (4 types)
│   └── ai_analysis.py           # AI market analysis
│
├── ⚡ Trading Operations
│   ├── trading_operations.py    # Order execution
│   ├── session_management.py    # Trading sessions
│   └── risk_management.py       # Risk controls
│
├── 🖥️ User Interface
│   ├── gui_module.py            # Complete GUI (identical)
│   └── performance_tracking.py  # Reports & analytics
│
├── 🤖 Bot Controller
│   ├── bot_controller.py        # Main bot logic
│   ├── main.py                  # Application entry
│   └── run_tests.py             # Test suite
│
└── 📋 Documentation
    ├── README.md                # This file
    ├── SIMILARITY_CHECKLIST.md  # Functionality comparison
    └── replit.md                # Project documentation
```

## 🎯 Identical Features Maintained

### Trading Strategies (4 Complete Strategies)
- ✅ **Scalping**: Fast EMA crossovers, quick scalping signals
- ✅ **Intraday**: Trend following with EMA alignment  
- ✅ **Arbitrage**: Mean reversion on Bollinger Band extremes
- ✅ **HFT**: High-frequency micro-movement detection

### GUI Interface (100% Identical)
- ✅ Same layout, colors, and styling (`#0f0f0f` theme)
- ✅ All buttons: Connect, Start Bot, Emergency Stop, Close Positions
- ✅ Parameter controls: Strategy, Symbol, Lot, TP/SL with units
- ✅ Real-time account info: Balance, Equity, Margin, Server
- ✅ Positions tree view with Symbol, Type, Volume, Price, Profit
- ✅ Scrolling log with timestamp formatting
- ✅ Performance report popup window

### Technical Analysis (Complete Set)
- ✅ **EMAs**: 8, 12, 20, 26, 50, 100, 200 periods
- ✅ **RSI**: Standard (14), Fast (7), Slow (21) periods  
- ✅ **MACD**: Enhanced with histogram and signals
- ✅ **Bollinger Bands**: 20-period with width calculation
- ✅ **Stochastic**: %K and %D oscillators
- ✅ **ATR**: Volatility measurement (7 & 14 periods)
- ✅ **WMA**: Weighted moving averages (8, 14, 21)

### Order Management (Complete System)
- ✅ Market order execution (BUY/SELL)
- ✅ TP/SL in pips, points, or absolute price
- ✅ Position sizing and lot calculation
- ✅ Order validation and error handling
- ✅ Emergency position closing
- ✅ CSV logging of all trades

### Risk Management (Full Implementation)
- ✅ Daily trade limits and profit targets
- ✅ Maximum open positions control
- ✅ Margin level monitoring
- ✅ Drawdown protection
- ✅ Auto-recovery system
- ✅ Session balance tracking

### Session Management (Complete)
- ✅ Asian, European, US, Pacific sessions
- ✅ High-impact news time detection
- ✅ Session-specific symbol recommendations
- ✅ Volatility-based strategy adjustments

### AI Analysis Engine (Advanced)
- ✅ Pattern recognition and trend analysis
- ✅ Momentum and volatility scoring
- ✅ Support/resistance level detection
- ✅ Market regime classification
- ✅ Confidence scoring system

## 🚀 Quick Start Guide

### 1. Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd modular-mt5-bot

# Install dependencies (Python 3.8+)
pip install pandas numpy requests

# On Windows (for production)
pip install MetaTrader5

# Run tests to verify setup
python run_tests.py
```

### 2. Running the Bot

```bash
# GUI Mode (Recommended)
python main.py

# Headless Mode (Server deployment)  
python main.py --headless

# Test Mode (Development)
python run_tests.py
```

### 3. MT5 Connection Setup

1. **Windows (Production)**:
   - Install and run MetaTrader 5
   - Login to your trading account
   - Run MT5 as Administrator
   - Add symbols to Market Watch (EURUSD, GBPUSD, etc.)

2. **Linux/Mac (Development)**:
   - Uses built-in mock MT5 for testing
   - All functionality works for development
   - Deploy to Windows for live trading

### 4. Bot Configuration

1. **Connect to MT5**: Click "Connect MT5" button
2. **Select Strategy**: Choose from Scalping, Intraday, Arbitrage, HFT
3. **Set Parameters**: Configure symbol, lot size, TP/SL
4. **Start Trading**: Click "Start Bot" to begin automated trading
5. **Monitor**: Watch real-time log and positions

## 🔧 Advanced Configuration

### Strategy Parameters

Each strategy has optimized default parameters:

```python
# Scalping (Default)
{
    "tp_pips": "20",
    "sl_pips": "10", 
    "lot_size": "0.01"
}

# Intraday  
{
    "tp_pips": "50",
    "sl_pips": "25",
    "lot_size": "0.02"  
}

# Arbitrage
{
    "tp_pips": "10", 
    "sl_pips": "5",
    "lot_size": "0.05"
}

# HFT
{
    "tp_pips": "5",
    "sl_pips": "3", 
    "lot_size": "0.01"
}
```

### Risk Management Settings

```python
# In config.py - Modify as needed
MAX_RISK_PERCENTAGE = 2.0    # Max 2% risk per trade
MAX_DAILY_TRADES = 50        # Daily trade limit  
MAX_OPEN_POSITIONS = 10      # Max concurrent positions
```

### Symbol Configuration

```python
# Default trading symbols
DEFAULT_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", 
    "AUDUSD", "USDCAD", "XAUUSD"
]
```

## 📊 Performance Monitoring

### Built-in Reports
- **Account Summary**: Balance, equity, margin, positions
- **Performance Metrics**: Win rate, daily P&L, trade statistics  
- **Risk Assessment**: Drawdown analysis, margin status
- **Trade History**: Complete CSV logging with timestamps

### Log Analysis
- Real-time trading log with detailed signal analysis
- Color-coded profit/loss position tracking
- Session-based performance breakdown
- Error tracking and recovery logging

## 🛡️ Safety Features

### Emergency Controls
- **Emergency Stop**: Instant bot shutdown + position closure
- **Auto-Recovery**: Automatic MT5 reconnection and error handling
- **Risk Limits**: Hard stops on losses, margin, and trade count
- **Session Filters**: Avoid trading during high-impact news

### Testing & Validation
- Comprehensive test suite (`run_tests.py`)
- Mock MT5 environment for safe development
- Input validation on all parameters
- Connection status monitoring

## 🔄 Migration from Original Bot

This modular version is a **drop-in replacement** for the original bobot2.py:

### ✅ What's Identical
- All GUI elements and layout
- Complete trading logic and strategies  
- Technical indicator calculations
- Order execution and management
- Risk management rules
- Performance tracking

### 🚀 What's Improved  
- **Clean Code**: Professional modular architecture
- **No Duplication**: Removed 12,000+ lines of duplicate code
- **Maintainable**: Easy to modify individual components
- **Testable**: Comprehensive test suite included
- **Cross-Platform**: Development on any OS
- **Production Ready**: Optimized for live trading

## 📋 Testing & Validation

Run the complete test suite to verify all functionality:

```bash
python run_tests.py
```

**Test Coverage**:
- ✅ Module imports and dependencies
- ✅ MT5 mock functionality  
- ✅ Data fetching and validation
- ✅ Technical indicator calculations
- ✅ All 4 trading strategies
- ✅ AI analysis engine
- ✅ Risk management systems
- ✅ Trading operations

## 🎯 Production Deployment

### Windows MT5 Setup
1. Install MetaTrader 5 from MetaQuotes
2. Open trading account with broker
3. Run MT5 as Administrator
4. Configure symbols in Market Watch
5. Run bot: `python main.py`

### Risk Management
- Start with small lot sizes (0.01)
- Monitor performance for first week
- Gradually increase position sizes
- Keep emergency stop button accessible
- Regular performance review

### Monitoring Checklist
- [ ] MT5 connection stable
- [ ] Account balance adequate  
- [ ] Daily trade limits reasonable
- [ ] Risk percentage appropriate
- [ ] Bot log shows healthy signals
- [ ] Position management working

## 🤝 Support & Maintenance

### Common Issues
1. **Connection Failed**: Ensure MT5 running as Administrator
2. **No Signals**: Check symbol availability and market hours
3. **Trade Errors**: Verify account permissions and margin
4. **Performance Issues**: Monitor log for error patterns

### Code Maintenance
- Each module is independent and replaceable
- Configuration centralized in `config.py`
- Logging system provides detailed debugging
- Test suite ensures stability after changes

## 📈 Future Enhancements

This modular architecture supports easy extensions:
- Additional trading strategies
- New technical indicators  
- Enhanced AI analysis
- Integration with external data sources
- Advanced risk management rules
- Multi-broker support

## ⚠️ Disclaimer

**Trading involves significant risk of loss. This bot is for educational and research purposes. Always:**
- Test thoroughly with demo accounts
- Never risk more than you can afford to lose  
- Understand all strategies before live trading
- Monitor bot performance regularly
- Keep emergency stops accessible

---

## 📞 Contact & Support

For technical support, bug reports, or feature requests, please refer to the project documentation or contact the development team.

**Happy Trading! 💹**