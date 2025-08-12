import time
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
EXCHANGE_NAME = 'binance'
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT']
TIMEFRAMES = ['15m', '1h', '4h', '1d']
STRATEGY_NAME = 'RSI_MACD_Bollinger'
INITIAL_BALANCE = 1000
TRADE_PERCENTAGE = 0.1 # Percentage of balance to use for each trade
STOP_LOSS_PERCENTAGE = 0.02 # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.05 # 5% take profit

# --- Exchange Initialization ---
def get_exchange():
    exchange_class = getattr(ccxt, EXCHANGE_NAME)
    exchange = exchange_class({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
    })
    return exchange

# --- Data Fetching ---
def fetch_ohlcv(exchange, symbol, timeframe, limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching OHLCV for {symbol} {timeframe}: {e}")
        return None

# --- Technical Analysis ---
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = delta.where(delta < 0, 0).abs()
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df['rsi'] = rsi
    return df

def calculate_macd(df, fastperiod=12, slowperiod=26, signalperiod=9):
    ema_fast = df['close'].ewm(span=fastperiod, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slowperiod, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signalperiod, adjust=False).mean()
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_hist'] = macd - signal
    return df

def calculate_bollinger_bands(df, window=20, std_dev=2):
    df['sma'] = df['close'].rolling(window=window).mean()
    df['std'] = df['close'].rolling(window=window).std()
    df['boll_upper'] = df['sma'] + (df['std'] * std_dev)
    df['boll_lower'] = df['sma'] - (df['std'] * std_dev)
    return df

def analyze_strategy(symbol, timeframe):
    exchange = get_exchange()
    df = fetch_ohlcv(exchange, symbol, timeframe)
    if df is None or df.empty:
        return None

    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)

    # Remove rows with NaN values resulting from calculations
    df.dropna(inplace=True)

    if df.empty:
        return None

    # Get the latest data point
    latest_data = df.iloc[-1]

    # Strategy Logic: RSI crossing up from oversold, MACD bullish crossover, close above lower Bollinger Band
    buy_signal = (latest_data['rsi'] > 30 and latest_data['rsi'].shift(1) <= 30) and \
                 (latest_data['macd'] > latest_data['macd_signal'] and latest_data['macd'].shift(1) <= latest_data['macd_signal'].shift(1)) and \
                 (latest_data['close'] > latest_data['boll_lower'])

    # Strategy Logic: RSI crossing down from overbought, MACD bearish crossover, close below upper Bollinger Band
    sell_signal = (latest_data['rsi'] < 70 and latest_data['rsi'].shift(1) >= 70) and \
                  (latest_data['macd'] < latest_data['macd_signal'] and latest_data['macd'].shift(1) >= latest_data['macd_signal'].shift(1)) and \
                  (latest_data['close'] < latest_data['boll_upper'])

    return {
        'buy': buy_signal,
        'sell': sell_signal,
        'rsi': latest_data['rsi'],
        'macd': latest_data['macd'],
        'macd_signal': latest_data['macd_signal'],
        'close': latest_data['close'],
        'boll_upper': latest_data['boll_upper'],
        'boll_lower': latest_data['boll_lower']
    }

# --- Multi-Timeframe Analysis ---
def should_trade_based_on_mtf(symbol, strategy_config, min_confluence_score=65):
    confluence_score = 0
    mtf_direction = 0 # 1 for bullish, -1 for bearish, 0 for neutral

    for i, timeframe in enumerate(strategy_config['timeframes']):
        analysis = analyze_strategy(symbol, timeframe)
        if analysis:
            if strategy_config['name'] == 'RSI_MACD_Bollinger':
                if analysis['buy']:
                    confluence_score += (100 - analysis['rsi']) # Higher RSI in buy zone = more bullish
                    if timeframe == '15m': confluence_score += 5
                    elif timeframe == '1h': confluence_score += 10
                    elif timeframe == '4h': confluence_score += 15
                    elif timeframe == '1d': confluence_score += 20
                elif analysis['sell']:
                    confluence_score -= (analysis['rsi']) # Lower RSI in sell zone = more bearish
                    if timeframe == '15m': confluence_score -= 5
                    elif timeframe == '1h': confluence_score -= 10
                    elif timeframe == '4h': confluence_score -= 15
                    elif timeframe == '1d': confluence_score -= 20
            else: # Default to simple count if strategy not recognized
                if analysis['buy']: confluence_score += 1
                elif analysis['sell']: confluence_score -= 1

    # Adjust confluence score based on timeframe weighting
    if mtf_direction == 1:
        final_score = confluence_score
    elif mtf_direction == -1:
        final_score = confluence_score
    else:
        final_score = confluence_score # Keep as is for now

    # Determine direction based on the majority of signals
    if final_score > min_confluence_score:
        mtf_direction = 1
    elif final_score < -min_confluence_score:
        mtf_direction = -1
    else:
        mtf_direction = 0

    should_trade = (mtf_direction != 0)

    return should_trade, mtf_direction, mtf_analysis # mtf_analysis is not used but kept for signature consistency

# --- Trading Logic ---
def execute_trade(exchange, symbol, trade_type, amount):
    try:
        if trade_type == 'buy':
            order = exchange.create_market_buy_order(symbol, amount)
        elif trade_type == 'sell':
            order = exchange.create_market_sell_order(symbol, amount)
        else:
            print("Invalid trade type")
            return None
        print(f"Successfully executed {trade_type} order for {amount} {symbol}: {order}")
        return order
    except Exception as e:
        print(f"Error executing trade for {symbol}: {e}")
        return None

def manage_trade(exchange, symbol, order, current_balance):
    if order is None:
        return

    trade_amount = order['filled'] * order['average']
    stop_loss_price = order['average'] * (1 - STOP_LOSS_PERCENTAGE) if order['side'] == 'buy' else order['average'] * (1 + STOP_LOSS_PERCENTAGE)
    take_profit_price = order['average'] * (1 + TAKE_PROFIT_PERCENTAGE) if order['side'] == 'buy' else order['average'] * (1 - TAKE_PROFIT_PERCENTAGE)

    print(f"Managing trade for {symbol}: Stop Loss at {stop_loss_price}, Take Profit at {take_profit_price}")

    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            if order['side'] == 'buy':
                if current_price <= stop_loss_price:
                    print(f"Stop loss triggered for {symbol}! Selling at market.")
                    execute_trade(exchange, symbol, 'sell', order['filled'])
                    break
                elif current_price >= take_profit_price:
                    print(f"Take profit triggered for {symbol}! Selling at market.")
                    execute_trade(exchange, symbol, 'sell', order['filled'])
                    break
            elif order['side'] == 'sell':
                if current_price >= stop_loss_price:
                    print(f"Stop loss triggered for {symbol}! Buying at market.")
                    execute_trade(exchange, symbol, 'buy', order['filled'])
                    break
                elif current_price <= take_profit_price:
                    print(f"Take profit triggered for {symbol}! Buying at market.")
                    execute_trade(exchange, symbol, 'buy', order['filled'])
                    break

            time.sleep(30) # Check every 30 seconds

        except Exception as e:
            print(f"Error managing trade for {symbol}: {e}")
            time.sleep(30)

# --- Main Loop ---
def main():
    exchange = get_exchange()
    balance = exchange.fetch_balance()
    current_balance = balance['total'].get('USDT', 0) # Assuming USDT as base currency
    if current_balance == 0:
        current_balance = INITIAL_BALANCE
        print(f"Initial balance set to {INITIAL_BALANCE} USDT.")

    strategy_config = {
        'name': STRATEGY_NAME,
        'timeframes': TIMEFRAMES
    }

    open_trades = {} # Dictionary to store open trades: {symbol: order_details}

    while True:
        print(f"\n--- Checking for trades at {datetime.now()} ---")
        print(f"Current Balance: {current_balance:.2f} USDT")

        for symbol in SYMBOLS:
            if symbol in open_trades:
                print(f"Already in an open trade for {symbol}. Skipping signal check.")
                # Potentially manage open trade here if not handled in a separate thread/function
                continue

            # Fetch current balance before deciding trade size
            balance = exchange.fetch_balance()
            current_balance = balance['total'].get('USDT', 0)
            if current_balance == 0: current_balance = INITIAL_BALANCE

            trade_amount_usdt = current_balance * TRADE_PERCENTAGE
            symbol_info = exchange.fetch_symbol(symbol)
            tick_size = symbol_info['precision']['amount']
            amount_to_trade = round(trade_amount_usdt / exchange.fetch_ticker(symbol)['last'] / tick_size) * tick_size

            if amount_to_trade <= 0:
                print(f"Skipping {symbol}: Calculated trade amount is zero or negative.")
                continue

            should_trade, mtf_direction, mtf_analysis = should_trade_based_on_mtf(symbol, strategy_config, min_confluence_score=30) # Use ultra-aggressive threshold

            if should_trade:
                if mtf_direction == 1: # Bullish signal
                    print(f"BUY signal detected for {symbol}!")
                    order = execute_trade(exchange, symbol, 'buy', amount_to_trade)
                    if order:
                        open_trades[symbol] = order
                        # Start managing the trade in a separate thread or async task
                        # For simplicity here, we'll just note it and not actively manage in this loop
                        print(f"Trade initiated for {symbol}. Managing...")
                elif mtf_direction == -1: # Bearish signal
                    print(f"SELL signal detected for {symbol}!")
                    # Note: This example primarily focuses on buying.
                    # For a full strategy, you'd also implement sell logic if you hold the asset.
                    # If shorting is allowed, you'd implement short selling here.
                    pass

        # Clean up closed trades (optional, depending on how manage_trade is implemented)
        # For this example, we'll assume trades are managed externally or we're just flagging them.
        # In a real system, you'd check order status and remove from open_trades.

        print("Waiting for next cycle...")
        time.sleep(60) # Check every minute

if __name__ == "__main__":
    main()