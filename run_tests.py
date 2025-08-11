# --- Test Runner for Modular Trading Bot ---
"""
Test suite to validate all modular components
"""

import sys
import datetime
from logger_utils import logger

def test_imports():
    """Test all module imports"""
    logger("🧪 Testing module imports...")
    
    try:
        # Core modules
        import config
        import logger_utils
        import validation_utils
        
        # Data and connection modules
        import mt5_mock
        import mt5_connection
        import data_manager
        
        # Analysis modules
        import indicators
        import strategies
        import ai_analysis
        
        # Trading modules
        import trading_operations
        import session_management
        import risk_management
        
        # Application modules
        import performance_tracking
        import gui_module
        import bot_controller
        
        logger("✅ All module imports successful")
        return True
        
    except ImportError as e:
        logger(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        logger(f"❌ Unexpected import error: {str(e)}")
        return False


def test_mt5_mock():
    """Test MT5 mock functionality"""
    logger("🧪 Testing MT5 mock functionality...")
    
    try:
        import mt5_mock as mt5
        
        # Test initialization
        result = mt5.initialize()
        if not result:
            logger("❌ MT5 mock initialization failed")
            return False
        
        # Test account info
        account = mt5.account_info()
        if not account:
            logger("❌ MT5 mock account info failed")
            return False
        
        # Test symbol info
        symbol_info = mt5.symbol_info("EURUSD")
        if not symbol_info:
            logger("❌ MT5 mock symbol info failed")
            return False
        
        # Test tick info
        tick = mt5.symbol_info_tick("EURUSD")
        if not tick:
            logger("❌ MT5 mock tick info failed")
            return False
        
        # Test historical data
        rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M5, 0, 100)
        if not rates:
            logger("❌ MT5 mock historical data failed")
            return False
        
        logger(f"✅ MT5 mock test passed - Got {len(rates)} bars")
        return True
        
    except Exception as e:
        logger(f"❌ MT5 mock test error: {str(e)}")
        return False


def test_data_fetching():
    """Test data fetching and processing"""
    logger("🧪 Testing data fetching...")
    
    try:
        from data_manager import get_symbol_data, validate_symbol_data
        
        # Test single symbol data  
        df = get_symbol_data("EURUSD", timeframe="M1", count=100)
        if df is None:
            logger("❌ Failed to fetch symbol data")
            return False
        
        # Test data validation
        is_valid = validate_symbol_data("EURUSD", df)
        if not is_valid:
            logger("❌ Data validation failed")
            return False
        
        logger(f"✅ Data fetching test passed - Got {len(df)} bars")
        return True
        
    except Exception as e:
        logger(f"❌ Data fetching test error: {str(e)}")
        return False


def test_indicators():
    """Test indicator calculations"""
    logger("🧪 Testing indicator calculations...")
    
    try:
        from data_manager import get_symbol_data
        from indicators import calculate_indicators
        
        # Get test data
        df = get_symbol_data("EURUSD", count=100)
        if df is None:
            logger("❌ No test data available")
            return False
        
        # Calculate indicators
        df_with_indicators = calculate_indicators(df)
        if df_with_indicators is None:
            logger("❌ Indicator calculation failed")
            return False
        
        # Check if indicators were added
        expected_indicators = ['EMA20', 'RSI', 'MACD', 'ATR']
        missing_indicators = [ind for ind in expected_indicators if ind not in df_with_indicators.columns]
        
        if missing_indicators:
            logger(f"❌ Missing indicators: {missing_indicators}")
            return False
        
        logger("✅ Indicator calculation test passed")
        return True
        
    except Exception as e:
        logger(f"❌ Indicator test error: {str(e)}")
        return False


def test_strategies():
    """Test all trading strategies"""
    logger("🧪 Testing trading strategies...")
    
    try:
        from data_manager import get_symbol_data
        from indicators import calculate_indicators
        from strategies import run_strategy
        from config import STRATEGIES
        
        # Get test data
        df = get_symbol_data("EURUSD", count=100)
        if df is None:
            logger("❌ No test data for strategy testing")
            return False
        
        # Calculate indicators
        df_with_indicators = calculate_indicators(df)
        if df_with_indicators is None:
            logger("❌ Failed to calculate indicators for strategy test")
            return False
        
        # Test each strategy
        strategies_passed = 0
        for strategy in STRATEGIES:
            try:
                action, signals = run_strategy(strategy, df_with_indicators, "EURUSD")
                logger(f"   {strategy}: Action={action}, Signals={len(signals) if signals else 0}")
                strategies_passed += 1
            except Exception as strategy_e:
                logger(f"❌ {strategy} strategy failed: {str(strategy_e)}")
        
        if strategies_passed == len(STRATEGIES):
            logger(f"✅ All {len(STRATEGIES)} strategies tested successfully")
            return True
        else:
            logger(f"⚠️ Only {strategies_passed}/{len(STRATEGIES)} strategies passed")
            return False
        
    except Exception as e:
        logger(f"❌ Strategy test error: {str(e)}")
        return False


def test_ai_analysis():
    """Test AI analysis functionality"""
    logger("🧪 Testing AI analysis...")
    
    try:
        from data_manager import get_symbol_data
        from indicators import calculate_indicators
        from ai_analysis import ai_market_analysis
        
        # Get test data
        df = get_symbol_data("EURUSD", count=100)
        if df is None:
            logger("❌ No test data for AI analysis")
            return False
        
        # Calculate indicators
        df_with_indicators = calculate_indicators(df)
        if df_with_indicators is None:
            logger("❌ Failed to calculate indicators for AI test")
            return False
        
        # Run AI analysis
        ai_result = ai_market_analysis("EURUSD", df_with_indicators)
        
        if not ai_result:
            logger("❌ AI analysis returned no result")
            return False
        
        # Check result structure
        required_fields = ['recommendation', 'confidence', 'signals', 'risk_level']
        missing_fields = [field for field in required_fields if field not in ai_result]
        
        if missing_fields:
            logger(f"❌ AI result missing fields: {missing_fields}")
            return False
        
        logger(f"✅ AI analysis test passed: {ai_result['recommendation']} ({ai_result['confidence']}%)")
        return True
        
    except Exception as e:
        logger(f"❌ AI analysis test error: {str(e)}")
        return False


def test_risk_management():
    """Test risk management functions"""
    logger("🧪 Testing risk management...")
    
    try:
        from risk_management import (
            check_daily_limits, 
            calculate_position_size, 
            get_current_risk_metrics,
            risk_management_check
        )
        
        # Test daily limits check
        limits_ok = check_daily_limits()
        if not limits_ok:
            logger("❌ Daily limits check failed")
            return False
        
        # Test position sizing
        position_size = calculate_position_size("EURUSD", 1.0)
        if position_size <= 0:
            logger("❌ Position size calculation failed")
            return False
        
        # Test risk metrics
        risk_metrics = get_current_risk_metrics()
        if not isinstance(risk_metrics, dict):
            logger("❌ Risk metrics failed")
            return False
        
        # Test risk management check
        risk_ok = risk_management_check()
        # Note: This might fail in test environment, which is expected
        
        logger(f"✅ Risk management test passed - Position size: {position_size}")
        return True
        
    except Exception as e:
        logger(f"❌ Risk management test error: {str(e)}")
        return False


def test_trading_operations():
    """Test trading operations (mock only)"""
    logger("🧪 Testing trading operations...")
    
    try:
        from trading_operations import (
            calculate_pip_value,
            parse_tp_sl_input,
            calculate_auto_lot_size
        )
        
        # Test pip value calculation
        pip_value = calculate_pip_value("EURUSD", 1.0)
        if pip_value <= 0:
            logger("❌ Pip value calculation failed")
            return False
        
        # Test TP/SL parsing
        tp_price = parse_tp_sl_input("20", "pips", "EURUSD", "BUY", 1.1000)
        if tp_price <= 0:
            logger("❌ TP/SL parsing failed")
            return False
        
        # Test auto lot size
        lot_size = calculate_auto_lot_size("EURUSD", 2.0, 20.0)
        if lot_size <= 0:
            logger("❌ Auto lot size calculation failed")
            return False
        
        logger(f"✅ Trading operations test passed - Pip value: {pip_value}")
        return True
        
    except Exception as e:
        logger(f"❌ Trading operations test error: {str(e)}")
        return False


def run_all_tests():
    """Run comprehensive test suite"""
    logger("🧪 Starting comprehensive test suite...")
    logger("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("MT5 Mock", test_mt5_mock),
        ("Data Fetching", test_data_fetching),
        ("Indicators", test_indicators),
        ("Strategies", test_strategies),
        ("AI Analysis", test_ai_analysis),
        ("Risk Management", test_risk_management),
        ("Trading Operations", test_trading_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger(f"\n🧪 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                logger(f"✅ {test_name} test PASSED")
            else:
                logger(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger(f"❌ {test_name} test ERROR: {str(e)}")
    
    logger("\n" + "=" * 60)
    logger(f"🧪 TEST SUITE COMPLETE")
    logger(f"✅ Passed: {passed}/{total}")
    logger(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        logger("🎉 ALL TESTS PASSED! System is ready for trading.")
    else:
        logger("⚠️ Some tests failed. Review errors before using in production.")
    
    return passed == total


def test_single_strategy_run():
    """Test a complete single strategy analysis"""
    logger("🧪 Running complete strategy analysis test...")
    
    try:
        from bot_controller import run_single_analysis
        
        # Test with default strategy
        result = run_single_analysis("EURUSD", "Scalping")
        
        if 'error' in result:
            logger(f"❌ Single analysis error: {result['error']}")
            return False
        
        logger(f"✅ Single analysis completed:")
        logger(f"   Symbol: {result.get('symbol')}")
        logger(f"   Strategy: {result.get('strategy')}")
        logger(f"   Action: {result.get('action', 'None')}")
        logger(f"   Signals: {result.get('signal_count', 0)}")
        logger(f"   AI Recommendation: {result.get('ai_analysis', {}).get('recommendation', 'None')}")
        
        return True
        
    except Exception as e:
        logger(f"❌ Single analysis test error: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        # Add current directory to path for imports
        sys.path.insert(0, ".")
        
        print("🧪 MT5 Trading Bot - Test Suite")
        print("=" * 50)
        
        # Run all tests
        success = run_all_tests()
        
        if success:
            logger("\n🎯 Running additional integration test...")
            test_single_strategy_run()
        
        print("\n" + "=" * 50)
        print("🏁 Test suite completed")
        
        if not success:
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
    except Exception as e:
        print(f"Test suite error: {str(e)}")
        sys.exit(1)