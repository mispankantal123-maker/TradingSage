# Windows MT5 Live Trading Fixes

## Current Error Analysis from Your Screenshot:

### Error Code 10016 - Invalid Stops
- **Problem**: TP/SL levels too close to current price
- **Solution**: Implement minimum stop distance validation
- **Fix**: Use symbol_info.trade_stops_level for proper distances

### Error Code 10015 - Invalid Order  
- **Problem**: Order parameters don't match MT5 requirements
- **Solution**: Validate all order parameters before sending
- **Fix**: Use proper filling modes and precise values

## Implemented Fixes:

### 1. Enhanced TP/SL Validation
✅ Use real bid/ask prices for entry calculations
✅ Implement minimum stop distance requirements  
✅ Auto-adjust TP/SL if too close to price
✅ Validate against symbol specifications

### 2. Improved Order Request Format
✅ Use symbol-specific filling mode detection
✅ Increase price deviation tolerance (20→50 points)
✅ Round all prices to proper digits
✅ Limit comment length to MT5 standard (31 chars)

### 3. Windows MT5 Compatibility
✅ Handle OrderSendResult objects correctly
✅ Extract all response values properly
✅ Enhanced error code mapping
✅ Proper retcode validation

### 4. Symbol-Specific Adjustments
✅ Use symbol_info for accurate point values
✅ Detect proper filling modes per symbol
✅ Apply minimum stop distances per symbol
✅ Handle different asset classes correctly

## Expected Results:
- No more "Invalid stops" errors
- No more "Invalid order" errors
- Successful order execution on Windows MT5
- Proper TP/SL placement within MT5 rules