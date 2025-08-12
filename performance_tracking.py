# --- Performance Tracking Module ---
"""
Trading performance analysis, reporting, and statistics
"""

import datetime
import os
from typing import Dict, Any, List
from logger_utils import logger, ensure_log_directory
from risk_management import get_current_risk_metrics

try:
    import MetaTrader5 as mt5
except ImportError:
    import mt5_mock as mt5


def generate_performance_report() -> str:
    """Generate comprehensive performance report"""
    try:
        ensure_log_directory()

        # Get account info
        account_info = mt5.account_info()
        if not account_info:
            return "❌ Cannot generate report - MT5 not connected"

        # Get positions and history
        positions = mt5.positions_get()
        current_positions = len(positions) if positions else 0

        # Get risk metrics
        risk_metrics = get_current_risk_metrics()

        # Generate report
        report = []
        report.append("=" * 60)
        report.append("📊 TRADING PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append(f"📅 Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Account Summary
        report.append("💰 ACCOUNT SUMMARY")
        report.append("-" * 30)
        report.append(f"Account: {account_info.login}")
        report.append(f"Server: {account_info.server}")
        report.append(f"Balance: ${account_info.balance:.2f}")
        report.append(f"Equity: ${account_info.equity:.2f}")
        report.append(f"Margin: ${account_info.margin:.2f}")
        report.append(f"Free Margin: ${account_info.margin_free:.2f}")
        if account_info.margin > 0:
            report.append(f"Margin Level: {account_info.margin_level:.1f}%")
        report.append(f"Leverage: 1:{account_info.leverage}")
        report.append("")

        # Current Positions
        report.append("📈 CURRENT POSITIONS")
        report.append("-" * 30)
        if positions:
            total_profit = 0
            for pos in positions:
                report.append(f"#{pos.ticket}: {pos.symbol} {pos.volume} lots")
                report.append(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
                report.append(f"  Open: {pos.price_open:.5f}")
                report.append(f"  Current: {pos.price_current:.5f}")
                report.append(f"  Profit: ${pos.profit:.2f}")
                total_profit += pos.profit
                report.append("")
            report.append(f"Total Open P&L: ${total_profit:.2f}")
        else:
            report.append("No open positions")
        report.append("")

        # Performance Metrics
        if risk_metrics:
            report.append("📊 PERFORMANCE METRICS")
            report.append("-" * 30)
            report.append(f"Daily Profit: ${risk_metrics.get('daily_profit', 0):.2f}")
            report.append(f"Daily Profit %: {risk_metrics.get('daily_profit_pct', 0):.2f}%")
            report.append(f"Equity Ratio: {risk_metrics.get('equity_ratio', 100):.1f}%")
            report.append(f"Daily Trades: {risk_metrics.get('daily_trades', 0)}")
            report.append("")

        # Risk Assessment
        report.append("🛡️ RISK ASSESSMENT")
        report.append("-" * 30)
        equity_ratio = (account_info.equity / account_info.balance) * 100
        if equity_ratio >= 95:
            risk_status = "LOW ✅"
        elif equity_ratio >= 85:
            risk_status = "MEDIUM ⚠️"
        else:
            risk_status = "HIGH ❌"

        report.append(f"Risk Level: {risk_status}")
        report.append(f"Equity/Balance: {equity_ratio:.1f}%")

        if account_info.margin_level > 0:
            if account_info.margin_level >= 500:
                margin_status = "SAFE ✅"
            elif account_info.margin_level >= 200:
                margin_status = "MODERATE ⚠️"
            else:
                margin_status = "RISKY ❌"
            report.append(f"Margin Status: {margin_status}")

        report.append("")
        report.append("=" * 60)

        report_text = "\n".join(report)

        # Save report to file
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"logs/performance_report_{timestamp}.txt"

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger(f"📊 Performance report saved: {report_filename}")
        except Exception as save_e:
            logger(f"⚠️ Could not save report: {str(save_e)}")

        return report_text

    except Exception as e:
        logger(f"❌ Error generating performance report: {str(e)}")
        return f"❌ Report generation failed: {str(e)}"


def send_hourly_report() -> None:
    """Send hourly performance update"""
    try:
        current_hour = datetime.datetime.now().hour

        # Send detailed report every 4 hours, or summary every hour
        if current_hour % 4 == 0:
            report = generate_performance_report()
            logger("📊 Hourly Performance Report:")
            for line in report.split('\n')[:20]:  # First 20 lines only
                logger(line)
        else:
            # Quick summary
            risk_metrics = get_current_risk_metrics()
            if risk_metrics:
                logger("📊 Quick Performance Update:")
                logger(f"   Balance: ${risk_metrics.get('balance', 0):.2f}")
                logger(f"   Equity: ${risk_metrics.get('equity', 0):.2f}")
                logger(f"   Daily P&L: ${risk_metrics.get('daily_profit', 0):.2f}")
                logger(f"   Open Positions: {risk_metrics.get('open_positions', 0)}")
                logger(f"   Daily Trades: {risk_metrics.get('daily_trades', 0)}")

    except Exception as e:
        logger(f"❌ Error sending hourly report: {str(e)}")


def track_trade_performance(symbol: str, action: str, entry_price: float, 
                          exit_price: float = None, profit: float = None) -> None:
    """Track individual trade performance"""
    try:
        ensure_log_directory()

        trade_data = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,
            'exit_price': exit_price or 0,
            'profit': profit or 0,
            'status': 'CLOSED' if exit_price else 'OPEN'
        }

        # Log to performance CSV
        performance_file = "csv_logs/trade_performance.csv"
        file_exists = os.path.exists(performance_file)

        with open(performance_file, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write("timestamp,symbol,action,entry_price,exit_price,profit,status\n")

            f.write(f"{trade_data['timestamp']},{trade_data['symbol']},{trade_data['action']},"
                   f"{trade_data['entry_price']},{trade_data['exit_price']},{trade_data['profit']},"
                   f"{trade_data['status']}\n")

        logger(f"📈 Trade tracked: {symbol} {action} @ {entry_price}")

    except Exception as e:
        logger(f"❌ Error tracking trade performance: {str(e)}")


def calculate_win_rate() -> Dict[str, float]:
    """Calculate win rate from trade history"""
    try:
        performance_file = "csv_logs/trade_performance.csv"

        if not os.path.exists(performance_file):
            return {'win_rate': 0, 'total_trades': 0, 'winning_trades': 0}

        with open(performance_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # Skip header

        total_trades = 0
        winning_trades = 0
        total_profit = 0

        for line in lines:
            try:
                parts = line.strip().split(',')
                if len(parts) >= 6 and parts[6] == 'CLOSED':
                    profit = float(parts[5])
                    total_trades += 1
                    total_profit += profit

                    if profit > 0:
                        winning_trades += 1
            except (ValueError, IndexError):
                continue

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'total_profit': total_profit,
            'avg_profit_per_trade': total_profit / total_trades if total_trades > 0 else 0
        }

    except Exception as e:
        logger(f"❌ Error calculating win rate: {str(e)}")
        return {'win_rate': 0, 'total_trades': 0, 'winning_trades': 0}


def add_trade_to_tracking(symbol: str, action: str, profit: float, lot_size: float):
    """Add trade result to performance tracking and drawdown management - FIXED VERSION"""
    try:
        # FIXED: Ensure all parameters are properly typed
        if isinstance(profit, str):
            try:
                profit = float(profit)
            except ValueError:
                profit = 0.0
        elif not isinstance(profit, (int, float)):
            profit = 0.0
            
        if isinstance(lot_size, str):
            try:
                lot_size = float(lot_size)
            except ValueError:
                lot_size = 0.01
        elif not isinstance(lot_size, (int, float)):
            lot_size = 0.01

        # Track in performance system
        track_trade_performance(symbol, action, 0.0, profit=profit)

        # Also add to drawdown tracking if available
        try:
            from drawdown_manager import add_trade_result
            add_trade_result(symbol, action, profit, lot_size)
        except ImportError:
            logger("⚠️ Drawdown manager not available for trade tracking")
        except Exception as dm_e:
            logger(f"⚠️ Drawdown tracking error: {str(dm_e)}")

        # FIXED: Safe string formatting
        logger(f"📊 Trade tracked: {symbol} {action} P&L: ${float(profit):.2f}")

    except Exception as e:
        logger(f"❌ Error adding trade to tracking: {str(e)}")
        import traceback
        logger(f"📝 Traceback: {traceback.format_exc()}")


def get_daily_summary() -> Dict[str, Any]:
    """Get comprehensive daily trading summary"""
    try:
        today = datetime.date.today()

        # Get account info
        account_info = mt5.account_info()
        risk_metrics = get_current_risk_metrics()
        win_rate_data = calculate_win_rate()

        summary = {
            'date': today.strftime('%Y-%m-%d'),
            'account_balance': account_info.balance if account_info else 0,
            'account_equity': account_info.equity if account_info else 0,
            'daily_profit': risk_metrics.get('daily_profit', 0),
            'daily_profit_pct': risk_metrics.get('daily_profit_pct', 0),
            'daily_trades': risk_metrics.get('daily_trades', 0),
            'open_positions': risk_metrics.get('open_positions', 0),
            'win_rate': win_rate_data.get('win_rate', 0),
            'equity_ratio': risk_metrics.get('equity_ratio', 100),
            'margin_level': account_info.margin_level if account_info and account_info.margin > 0 else 0
        }

        return summary

    except Exception as e:
        logger(f"❌ Error getting daily summary: {str(e)}")
        return {}


def export_performance_data(days: int = 7) -> str:
    """Export performance data for specified number of days"""
    try:
        ensure_log_directory()

        # Get data from various sources
        account_info = mt5.account_info()
        risk_metrics = get_current_risk_metrics()
        win_rate_data = calculate_win_rate()

        # Create export data
        export_data = []
        export_data.append("# Trading Bot Performance Export")
        export_data.append(f"# Generated: {datetime.datetime.now()}")
        export_data.append(f"# Period: Last {days} days")
        export_data.append("")

        # Account summary
        if account_info:
            export_data.append("## Account Information")
            export_data.append(f"Account: {account_info.login}")
            export_data.append(f"Server: {account_info.server}")
            export_data.append(f"Balance: {account_info.balance:.2f}")
            export_data.append(f"Equity: {account_info.equity:.2f}")
            export_data.append(f"Leverage: 1:{account_info.leverage}")
            export_data.append("")

        # Performance metrics
        export_data.append("## Performance Metrics")
        if win_rate_data:
            export_data.append(f"Win Rate: {win_rate_data.get('win_rate', 0):.1f}%")
            export_data.append(f"Total Trades: {win_rate_data.get('total_trades', 0)}")
            export_data.append(f"Winning Trades: {win_rate_data.get('winning_trades', 0)}")
            export_data.append(f"Total Profit: ${win_rate_data.get('total_profit', 0):.2f}")

        if risk_metrics:
            export_data.append(f"Daily Profit: ${risk_metrics.get('daily_profit', 0):.2f}")
            export_data.append(f"Daily Trades: {risk_metrics.get('daily_trades', 0)}")
            export_data.append(f"Current Positions: {risk_metrics.get('open_positions', 0)}")

        # Save export
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f"logs/performance_export_{timestamp}.md"

        with open(export_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(export_data))

        logger(f"📤 Performance data exported: {export_filename}")
        return export_filename

    except Exception as e:
        logger(f"❌ Error exporting performance data: {str(e)}")
        return ""