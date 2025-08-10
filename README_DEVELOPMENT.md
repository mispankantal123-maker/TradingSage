# MT5 Trading Bot - Development Guide

## 🚨 REAL MONEY TRADING BOT - USE WITH CAUTION

This trading bot is designed for **REAL MONEY trading** with MetaTrader 5. All trades executed will use actual funds from your trading account.

## Development Environment Setup

### 1. Mock Library for Testing

Since MetaTrader5 library only works on Windows with MT5 terminal installed, this project includes a mock library (`mt5_mock.py`) for development and testing on other platforms.

**Features of Mock Library:**
- Simulates all MT5 API functions
- Generates realistic price data
- Provides mock account info (1M IDR balance)
- Supports all major currency pairs and instruments
- Returns realistic tick data and historical rates

### 2. Real vs Mock Mode

The application automatically detects the environment:

```python
# Real MT5 (Windows with MT5 terminal)
✅ Real MetaTrader5 library loaded

# Development mode (other platforms)
🎭 Mock MetaTrader5 library loaded (development mode)
```

### 3. Testing the Bot

In development mode, you can:

1. **Connect to MT5**: Uses mock connection
2. **Test all symbols**: EURUSD, XAUUSD, BTCUSD, etc.
3. **Execute mock trades**: Simulates real trading flow
4. **Test all TP/SL units**: pips, price, percent, money
5. **Test all strategies**: Scalping, Intraday, Arbitrage, HFT

### 4. Key Testing Scenarios

#### A. Percent TP/SL Testing
The critical issue reported was percent TP/SL calculations. Test with:
- Balance: 1,000,000 IDR (mock)
- TP: 1% (should target 10,000 IDR profit)  
- SL: 0.5% (should risk 5,000 IDR loss)

#### B. Symbol Compatibility
Test with various symbols:
- Forex: EURUSD, GBPUSD, USDJPY
- Precious Metals: XAUUSD, XAUUSDm
- Crypto: BTCUSD, BTCUSDm

#### C. Strategy Testing
Each strategy has different parameters:
- **Scalping**: TP=5, SL=3, Interval=5s
- **Intraday**: TP=20, SL=10, Interval=10s  
- **Arbitrage**: TP=15, SL=8, Interval=3s
- **HFT**: TP=3, SL=2, Interval=1s

## Production Deployment

### 1. Windows Environment Required
For production use, you MUST have:
- Windows OS
- MetaTrader 5 terminal installed
- Active broker account
- Python with MetaTrader5 library

### 2. Safety Measures
The bot includes multiple safety confirmations:
- Real money trading warnings
- Settings confirmation dialogs
- Balance checks before trading
- Order limits per session
- Connection validation

### 3. Risk Management
Built-in risk management features:
- Maximum orders per session (default: 10)
- Minimum balance checks
- Price spike detection
- Stop loss on all trades
- Session reset at midnight

## Architecture Overview

### Core Components:
1. **GUI Module** (`gui.py`): tkinter-based interface
2. **Trading Engine** (`trading.py`): MT5 integration and strategy logic  
3. **Utils Module** (`utils.py`): Configuration and logging
4. **Mock Module** (`mt5_mock.py`): Development testing framework

### Key Features:
- Multi-strategy automated trading
- Real-time GUI with async operations
- Comprehensive error handling
- Balance-based TP/SL calculations
- Symbol auto-detection
- Manual trading capabilities
- Real money safety warnings

## Recent Fixes (August 2025)

✅ **Resolved Critical Issues:**
- Mock library implementation for cross-platform development
- All method implementations verified and complete
- Enhanced error handling in technical indicators
- Balance-based percent TP/SL calculations
- Async GUI operations preventing freezing
- Comprehensive validation and safety checks

✅ **Verified Working Features:**
- Connection management (real/mock)
- Symbol validation and auto-detection
- All TP/SL units (pips, price, percent, money)
- Manual and automated trading
- Strategy signal generation
- Real money safety confirmations

## Running the Bot

### Development Mode:
```bash
python main.py
```

### Production Mode:
1. Install on Windows with MT5
2. Configure broker account in MT5
3. Run: `python main.py`
4. Connect to MT5 with your credentials
5. Configure trading settings
6. **⚠️ CONFIRM ALL REAL MONEY WARNINGS**

## Important Notes

- **This is NOT a demo bot** - all trades use real money
- Always test thoroughly in demo account first
- Monitor trades actively when running
- Set appropriate stop losses
- Use proper risk management
- Keep logs for audit trail

## Support

For issues or questions:
1. Check logs in GUI or `trading_bot.log`
2. Review AUDIT_CHECKLIST_REPORT.md for known issues
3. Test in mock mode first before production use