# --- Telegram Notifications Module ---
"""
Telegram notification system for MT5 trading bot
Sends real-time notifications for trades, profits, balance, and strategy updates
"""

import os
import requests
import datetime
from typing import Optional, Dict, Any
from logger_utils import logger

# Telegram Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8365734234:AAH2uTaZPDD47Lnm3y_Tcr6aj3xGL-bVsgk")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5061106648")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Notification settings
NOTIFICATIONS_ENABLED = True
MAX_RETRIES = 3


def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Send message to Telegram with retry logic"""
    if not NOTIFICATIONS_ENABLED or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger("📱 Telegram notifications disabled or not configured")
        return False
        
    try:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
                
                if response.status_code == 200:
                    logger("📱 Telegram notification sent successfully")
                    return True
                else:
                    logger(f"📱 Telegram API error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger(f"📱 Telegram request failed (attempt {attempt+1}): {str(e)}")
                
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(2)  # Wait 2 seconds before retry
                
        return False
        
    except Exception as e:
        logger(f"📱 Error sending Telegram message: {str(e)}")
        return False


def notify_trade_executed(symbol: str, action: str, volume: float, price: float, 
                         tp: float, sl: float, strategy: str) -> None:
    """Notify about executed trade"""
    try:
        action_emoji = "🟢" if action.upper() == "BUY" else "🔴"
        
        message = f"""
{action_emoji} <b>TRADE EXECUTED</b>
━━━━━━━━━━━━━━━━
📊 <b>Symbol:</b> {symbol}
🎯 <b>Action:</b> {action.upper()}
📈 <b>Volume:</b> {volume} lots
💰 <b>Price:</b> ${price:.2f}
🎯 <b>Take Profit:</b> ${tp:.2f}
🛡️ <b>Stop Loss:</b> ${sl:.2f}
🔧 <b>Strategy:</b> {strategy}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in trade notification: {str(e)}")


def notify_position_closed(symbol: str, action: str, volume: float, open_price: float,
                          close_price: float, profit: float, reason: str = "Manual") -> None:
    """Notify about closed position"""
    try:
        profit_emoji = "💚" if profit > 0 else "❤️" if profit < 0 else "💛"
        action_emoji = "🟢" if action.upper() == "BUY" else "🔴"
        
        message = f"""
{profit_emoji} <b>POSITION CLOSED</b>
━━━━━━━━━━━━━━━━
📊 <b>Symbol:</b> {symbol}
{action_emoji} <b>Action:</b> {action.upper()}
📈 <b>Volume:</b> {volume} lots
🔓 <b>Open:</b> ${open_price:.2f}
🔒 <b>Close:</b> ${close_price:.2f}
💰 <b>Profit/Loss:</b> ${profit:.2f}
📝 <b>Reason:</b> {reason}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in position closed notification: {str(e)}")


def notify_balance_update(balance: float, equity: float, free_margin: float, 
                         margin_level: float, positions_count: int) -> None:
    """Notify about account balance update"""
    try:
        message = f"""
💰 <b>ACCOUNT UPDATE</b>
━━━━━━━━━━━━━━━━
💵 <b>Balance:</b> ${balance:,.2f}
📊 <b>Equity:</b> ${equity:,.2f}
🆓 <b>Free Margin:</b> ${free_margin:,.2f}
📈 <b>Margin Level:</b> {margin_level:.1f}%
📊 <b>Open Positions:</b> {positions_count}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in balance notification: {str(e)}")


def notify_strategy_change(old_strategy: str, new_strategy: str, 
                          tp: str, sl: str, lot_size: str) -> None:
    """Notify about strategy change"""
    try:
        message = f"""
🔄 <b>STRATEGY CHANGED</b>
━━━━━━━━━━━━━━━━
📊 <b>From:</b> {old_strategy}
🎯 <b>To:</b> {new_strategy}
🎯 <b>Take Profit:</b> {tp}
🛡️ <b>Stop Loss:</b> {sl}
📈 <b>Lot Size:</b> {lot_size}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in strategy notification: {str(e)}")


def notify_session_change(session_name: str, volatility: str, risk_modifier: float,
                         recommended_pairs: list) -> None:
    """Notify about trading session change"""
    try:
        volatility_emoji = {
            'VERY_HIGH': '🔥',
            'HIGH': '📈', 
            'MEDIUM': '📊',
            'LOW': '📉',
            'NONE': '😴'
        }.get(volatility, '📊')
        
        pairs_text = ", ".join(recommended_pairs[:4]) if recommended_pairs else "All pairs"
        
        message = f"""
🌍 <b>TRADING SESSION</b>
━━━━━━━━━━━━━━━━
🕐 <b>Session:</b> {session_name}
{volatility_emoji} <b>Volatility:</b> {volatility}
⚖️ <b>Risk Modifier:</b> {risk_modifier:.1f}x
💎 <b>Recommended:</b> {pairs_text}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in session notification: {str(e)}")


def notify_bot_status(status: str, message: str = "") -> None:
    """Notify about bot status changes"""
    try:
        status_emoji = {
            'STARTED': '🚀',
            'STOPPED': '🛑', 
            'PAUSED': '⏸️',
            'ERROR': '❌',
            'CONNECTED': '✅',
            'DISCONNECTED': '🔌'
        }.get(status.upper(), '📱')
        
        notification = f"""
{status_emoji} <b>BOT STATUS</b>
━━━━━━━━━━━━━━━━
🤖 <b>Status:</b> {status.upper()}
📝 <b>Message:</b> {message or 'No additional info'}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(notification)
        
    except Exception as e:
        logger(f"📱 Error in bot status notification: {str(e)}")


def notify_risk_alert(alert_type: str, current_value: float, threshold: float, 
                     action_taken: str = "") -> None:
    """Notify about risk management alerts"""
    try:
        alert_emoji = {
            'DRAWDOWN': '⚠️',
            'MARGIN': '🚨',
            'DAILY_LOSS': '📉',
            'MAX_POSITIONS': '📊'
        }.get(alert_type.upper(), '⚠️')
        
        message = f"""
{alert_emoji} <b>RISK ALERT</b>
━━━━━━━━━━━━━━━━
🚨 <b>Type:</b> {alert_type.upper()}
📊 <b>Current:</b> {current_value:.2f}
⚖️ <b>Threshold:</b> {threshold:.2f}
🛡️ <b>Action:</b> {action_taken or 'Manual intervention required'}
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in risk alert notification: {str(e)}")


def notify_daily_summary(trades_count: int, profit_loss: float, win_rate: float,
                        balance_start: float, balance_end: float) -> None:
    """Send daily trading summary"""
    try:
        profit_emoji = "💚" if profit_loss > 0 else "❤️" if profit_loss < 0 else "💛"
        
        message = f"""
📊 <b>DAILY SUMMARY</b>
━━━━━━━━━━━━━━━━
📈 <b>Total Trades:</b> {trades_count}
{profit_emoji} <b>P&L:</b> ${profit_loss:.2f}
🎯 <b>Win Rate:</b> {win_rate:.1f}%
🌅 <b>Start Balance:</b> ${balance_start:,.2f}
🌇 <b>End Balance:</b> ${balance_end:,.2f}
📊 <b>Return:</b> {((balance_end - balance_start) / balance_start * 100):.2f}%
⏰ <b>Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d')}
"""
        
        send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error in daily summary notification: {str(e)}")


def test_telegram_connection() -> bool:
    """Test Telegram connection and send test message"""
    try:
        message = f"""
🧪 <b>TELEGRAM TEST</b>
━━━━━━━━━━━━━━━━
✅ <b>Connection:</b> OK
🤖 <b>Bot:</b> MT5 Trading Bot v4.0
⏰ <b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Telegram notifications are working properly! 📱
"""
        
        return send_telegram_message(message)
        
    except Exception as e:
        logger(f"📱 Error testing Telegram connection: {str(e)}")
        return False


def toggle_notifications(enabled: bool) -> None:
    """Enable or disable Telegram notifications"""
    global NOTIFICATIONS_ENABLED
    NOTIFICATIONS_ENABLED = enabled
    
    status = "enabled" if enabled else "disabled"
    logger(f"📱 Telegram notifications {status}")
    
    if enabled:
        notify_bot_status("NOTIFICATIONS_ENABLED", "Telegram notifications activated")