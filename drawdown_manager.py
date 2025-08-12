# --- Drawdown Recovery Manager Module ---
"""
Adaptive drawdown recovery system untuk real trading
Smart risk reduction dan recovery strategies saat losing streaks
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class DrawdownManager:
    """Professional drawdown recovery system"""
    
    def __init__(self):
        self.initial_balance = 0.0
        self.peak_equity = 0.0
        self.current_drawdown_pct = 0.0
        self.max_historical_dd = 0.0
        self.recovery_mode = False
        self.recovery_start_time = None
        
        # Drawdown thresholds
        self.dd_thresholds = {
            "warning": 5.0,      # 5% warning level
            "caution": 10.0,     # 10% caution level  
            "danger": 15.0,      # 15% danger level
            "emergency": 20.0    # 20% emergency stop
        }
        
        # Recovery settings
        self.recovery_settings = {
            "reduce_lot_size_pct": 50,        # Reduce lot size by 50%
            "reduce_max_positions": 50,       # Reduce max positions by 50%
            "increase_signal_threshold": 2,   # Require stronger signals
            "pause_low_conf_signals": True,   # Pause low confidence signals
            "enable_conservative_mode": True, # Switch to conservative parameters
            "recovery_target_pct": 5.0,       # Recover 5% before normal mode
            "max_recovery_days": 7            # Max 7 days in recovery mode
        }
        
        # Performance tracking
        self.daily_results = []
        self.trade_results = []
        self.last_analysis = None
        
    def initialize_balance(self):
        """Initialize starting balance and equity tracking"""
        try:
            account = mt5.account_info()
            if account:
                self.initial_balance = account.balance
                self.peak_equity = account.equity
                
                logger(f"💰 Drawdown manager initialized: Balance=${self.initial_balance:.2f}")
                
                return True
            else:
                logger("❌ Cannot get account info for drawdown manager")
                return False
                
        except Exception as e:
            logger(f"❌ Error initializing drawdown manager: {str(e)}")
            return False
    
    def update_drawdown_status(self) -> Dict[str, Any]:
        """Update current drawdown status"""
        try:
            account = mt5.account_info()
            if not account:
                return {"error": "Cannot get account info"}
            
            current_equity = account.equity
            current_balance = account.balance
            
            # Update peak equity
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
                
                # Exit recovery mode if we've recovered sufficiently
                if self.recovery_mode:
                    recovery_pct = ((current_equity - self.recovery_start_equity) / self.recovery_start_equity) * 100
                    if recovery_pct >= self.recovery_settings["recovery_target_pct"]:
                        self._exit_recovery_mode()
            
            # Calculate current drawdown
            if self.peak_equity > 0:
                self.current_drawdown_pct = ((self.peak_equity - current_equity) / self.peak_equity) * 100
            else:
                self.current_drawdown_pct = 0.0
            
            # Update max historical drawdown
            if self.current_drawdown_pct > self.max_historical_dd:
                self.max_historical_dd = self.current_drawdown_pct
            
            # Determine risk level
            risk_level = self._get_risk_level()
            
            # Check if we need to enter recovery mode
            if not self.recovery_mode and self.current_drawdown_pct >= self.dd_thresholds["caution"]:
                self._enter_recovery_mode()
            
            # Emergency stop check
            if self.current_drawdown_pct >= self.dd_thresholds["emergency"]:
                self._trigger_emergency_stop()
            
            # Prepare status
            status = {
                "current_equity": current_equity,
                "current_balance": current_balance,
                "peak_equity": self.peak_equity,
                "current_drawdown_pct": round(self.current_drawdown_pct, 2),
                "max_historical_dd": round(self.max_historical_dd, 2),
                "risk_level": risk_level,
                "recovery_mode": self.recovery_mode,
                "thresholds": self.dd_thresholds
            }
            
            # Add recovery info if in recovery mode
            if self.recovery_mode:
                status["recovery_info"] = self._get_recovery_info()
            
            return status
            
        except Exception as e:
            logger(f"❌ Error updating drawdown status: {str(e)}")
            return {"error": str(e)}
    
    def _get_risk_level(self) -> str:
        """Determine current risk level based on drawdown"""
        if self.current_drawdown_pct >= self.dd_thresholds["emergency"]:
            return "EMERGENCY"
        elif self.current_drawdown_pct >= self.dd_thresholds["danger"]:
            return "DANGER"
        elif self.current_drawdown_pct >= self.dd_thresholds["caution"]:
            return "CAUTION"
        elif self.current_drawdown_pct >= self.dd_thresholds["warning"]:
            return "WARNING"
        else:
            return "NORMAL"
    
    def _enter_recovery_mode(self):
        """Enter drawdown recovery mode"""
        try:
            if self.recovery_mode:
                return
            
            self.recovery_mode = True
            self.recovery_start_time = datetime.now()
            
            account = mt5.account_info()
            if account:
                self.recovery_start_equity = account.equity
            
            logger(f"🚨 ENTERING RECOVERY MODE - Drawdown: {self.current_drawdown_pct:.2f}%")
            logger(f"   Conservative parameters activated")
            logger(f"   Lot sizes reduced by {self.recovery_settings['reduce_lot_size_pct']}%")
            logger(f"   Signal threshold increased")
            
            # Notify trading system
            self._notify_recovery_mode_change(True)
            
            # Telegram notification
            try:
                from telegram_notifications import notify_drawdown_alert
                notify_drawdown_alert(self.current_drawdown_pct, "RECOVERY_MODE_ENTERED")
            except:
                pass
                
        except Exception as e:
            logger(f"❌ Error entering recovery mode: {str(e)}")
    
    def _exit_recovery_mode(self):
        """Exit drawdown recovery mode"""
        try:
            if not self.recovery_mode:
                return
            
            recovery_duration = (datetime.now() - self.recovery_start_time).total_seconds() / 3600  # hours
            
            self.recovery_mode = False
            self.recovery_start_time = None
            
            logger(f"✅ EXITING RECOVERY MODE - Recovery successful!")
            logger(f"   Recovery duration: {recovery_duration:.1f} hours")
            logger(f"   Normal parameters restored")
            
            # Notify trading system
            self._notify_recovery_mode_change(False)
            
            # Telegram notification
            try:
                from telegram_notifications import notify_drawdown_alert
                notify_drawdown_alert(self.current_drawdown_pct, "RECOVERY_MODE_EXITED")
            except:
                pass
                
        except Exception as e:
            logger(f"❌ Error exiting recovery mode: {str(e)}")
    
    def _trigger_emergency_stop(self):
        """Trigger emergency stop for extreme drawdown"""
        try:
            logger(f"🚨 EMERGENCY STOP TRIGGERED - Drawdown: {self.current_drawdown_pct:.2f}%")
            logger(f"   All trading operations halted")
            
            # Stop all trading
            try:
                from bot_controller import emergency_stop_all
                emergency_stop_all()
            except:
                pass
            
            # Close all positions (optional - configurable)
            if self.recovery_settings.get("close_all_on_emergency", False):
                self._close_all_positions()
            
            # Emergency notification
            try:
                from telegram_notifications import notify_emergency_stop
                notify_emergency_stop(self.current_drawdown_pct, "DRAWDOWN_EMERGENCY")
            except:
                pass
                
        except Exception as e:
            logger(f"❌ Error triggering emergency stop: {str(e)}")
    
    def _close_all_positions(self):
        """Close all open positions (emergency measure)"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return
            
            closed_count = 0
            for position in positions:
                try:
                    # Prepare close request
                    if position.type == mt5.ORDER_TYPE_BUY:
                        order_type = mt5.ORDER_TYPE_SELL
                        price = mt5.symbol_info_tick(position.symbol).bid
                    else:
                        order_type = mt5.ORDER_TYPE_BUY
                        price = mt5.symbol_info_tick(position.symbol).ask
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "type": order_type,
                        "position": position.ticket,
                        "price": price,
                        "deviation": 50,
                        "magic": 234000,
                        "comment": "Emergency Close"
                    }
                    
                    result = mt5.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        closed_count += 1
                        logger(f"🔴 Emergency closed position {position.ticket}")
                    
                except Exception as pos_e:
                    logger(f"❌ Error closing position {position.ticket}: {str(pos_e)}")
            
            logger(f"🚨 Emergency close completed: {closed_count} positions closed")
            
        except Exception as e:
            logger(f"❌ Error closing all positions: {str(e)}")
    
    def get_recovery_adjustments(self) -> Dict[str, Any]:
        """Get current recovery mode adjustments"""
        try:
            if not self.recovery_mode:
                return {
                    "lot_size_multiplier": 1.0,
                    "max_positions_multiplier": 1.0,
                    "signal_threshold_adjustment": 0,
                    "conservative_mode": False
                }
            
            # Calculate recovery adjustments
            recovery_days = (datetime.now() - self.recovery_start_time).total_seconds() / (24 * 3600)
            
            # Progressive recovery - more conservative if longer in recovery
            if recovery_days > self.recovery_settings["max_recovery_days"]:
                # Force exit if too long in recovery
                self._exit_recovery_mode()
                return self.get_recovery_adjustments()
            
            # Adjust conservatism based on drawdown severity
            dd_severity = min(self.current_drawdown_pct / self.dd_thresholds["danger"], 1.0)
            
            lot_reduction = self.recovery_settings["reduce_lot_size_pct"] * dd_severity / 100
            position_reduction = self.recovery_settings["reduce_max_positions"] * dd_severity / 100
            
            adjustments = {
                "lot_size_multiplier": 1.0 - lot_reduction,
                "max_positions_multiplier": 1.0 - position_reduction,
                "signal_threshold_adjustment": int(self.recovery_settings["increase_signal_threshold"] * dd_severity),
                "conservative_mode": True,
                "pause_low_confidence": self.recovery_settings["pause_low_conf_signals"],
                "recovery_progress": self._calculate_recovery_progress()
            }
            
            return adjustments
            
        except Exception as e:
            logger(f"❌ Error getting recovery adjustments: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_recovery_progress(self) -> float:
        """Calculate recovery progress percentage"""
        try:
            if not self.recovery_mode or not hasattr(self, 'recovery_start_equity'):
                return 0.0
            
            account = mt5.account_info()
            if not account:
                return 0.0
            
            current_equity = account.equity
            target_equity = self.recovery_start_equity * (1 + self.recovery_settings["recovery_target_pct"] / 100)
            
            if current_equity >= target_equity:
                return 100.0
            
            recovery_needed = target_equity - self.recovery_start_equity
            recovery_achieved = current_equity - self.recovery_start_equity
            
            if recovery_needed <= 0:
                return 100.0
            
            progress = (recovery_achieved / recovery_needed) * 100
            return max(0.0, min(100.0, progress))
            
        except Exception as e:
            logger(f"❌ Error calculating recovery progress: {str(e)}")
            return 0.0
    
    def _get_recovery_info(self) -> Dict[str, Any]:
        """Get detailed recovery mode information"""
        try:
            recovery_duration = (datetime.now() - self.recovery_start_time).total_seconds() / 3600
            
            info = {
                "start_time": self.recovery_start_time.isoformat(),
                "duration_hours": round(recovery_duration, 1),
                "progress_pct": round(self._calculate_recovery_progress(), 1),
                "adjustments": self.get_recovery_adjustments(),
                "target_recovery_pct": self.recovery_settings["recovery_target_pct"],
                "max_duration_days": self.recovery_settings["max_recovery_days"]
            }
            
            return info
            
        except Exception as e:
            logger(f"❌ Error getting recovery info: {str(e)}")
            return {"error": str(e)}
    
    def _notify_recovery_mode_change(self, entering: bool):
        """Notify other systems about recovery mode change"""
        try:
            # Notify bot controller
            try:
                import bot_controller
                if hasattr(bot_controller, 'set_recovery_mode'):
                    bot_controller.set_recovery_mode(entering)
            except:
                pass
            
            # Notify GUI
            try:
                import __main__
                if hasattr(__main__, 'gui') and __main__.gui:
                    __main__.gui.update_recovery_status(entering, self.current_drawdown_pct)
            except:
                pass
                
        except Exception as e:
            logger(f"⚠️ Error notifying recovery mode change: {str(e)}")
    
    def add_trade_result(self, symbol: str, action: str, profit: float, lot_size: float):
        """Add trade result for performance tracking"""
        try:
            trade_result = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "action": action,
                "profit": profit,
                "lot_size": lot_size,
                "recovery_mode": self.recovery_mode
            }
            
            self.trade_results.append(trade_result)
            
            # Keep only last 100 trades
            if len(self.trade_results) > 100:
                self.trade_results = self.trade_results[-100:]
            
            # Update daily results
            self._update_daily_results()
            
        except Exception as e:
            logger(f"❌ Error adding trade result: {str(e)}")
    
    def _update_daily_results(self):
        """Update daily performance results"""
        try:
            today = datetime.now().date()
            
            # Calculate today's results
            today_trades = [t for t in self.trade_results if t["timestamp"].date() == today]
            
            if today_trades:
                daily_profit = sum(t["profit"] for t in today_trades)
                daily_trades_count = len(today_trades)
                winning_trades = len([t for t in today_trades if t["profit"] > 0])
                win_rate = (winning_trades / daily_trades_count) * 100 if daily_trades_count > 0 else 0
                
                daily_result = {
                    "date": today,
                    "profit": daily_profit,
                    "trades_count": daily_trades_count,
                    "win_rate": win_rate,
                    "recovery_mode": self.recovery_mode
                }
                
                # Update or add today's result
                for i, result in enumerate(self.daily_results):
                    if result["date"] == today:
                        self.daily_results[i] = daily_result
                        return
                
                self.daily_results.append(daily_result)
                
                # Keep only last 30 days
                if len(self.daily_results) > 30:
                    self.daily_results = self.daily_results[-30:]
            
        except Exception as e:
            logger(f"❌ Error updating daily results: {str(e)}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and analysis"""
        try:
            account = mt5.account_info()
            if not account:
                return {"error": "Cannot get account info"}
            
            # Recent performance (last 7 days)
            recent_results = [r for r in self.daily_results if 
                            (datetime.now().date() - r["date"]).days <= 7]
            
            # Calculate metrics
            total_profit = sum(r["profit"] for r in recent_results)
            total_trades = sum(r["trades_count"] for r in recent_results)
            avg_win_rate = sum(r["win_rate"] for r in recent_results) / len(recent_results) if recent_results else 0
            
            summary = {
                "current_status": self.update_drawdown_status(),
                "performance_7d": {
                    "total_profit": round(total_profit, 2),
                    "total_trades": total_trades,
                    "avg_win_rate": round(avg_win_rate, 1),
                    "daily_results": recent_results
                },
                "recovery_active": self.recovery_mode,
                "max_historical_dd": round(self.max_historical_dd, 2)
            }
            
            if self.recovery_mode:
                summary["recovery_info"] = self._get_recovery_info()
            
            return summary
            
        except Exception as e:
            logger(f"❌ Error getting performance summary: {str(e)}")
            return {"error": str(e)}
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update drawdown manager settings"""
        try:
            if "thresholds" in new_settings:
                self.dd_thresholds.update(new_settings["thresholds"])
            
            if "recovery_settings" in new_settings:
                self.recovery_settings.update(new_settings["recovery_settings"])
            
            logger("✅ Drawdown manager settings updated")
            
        except Exception as e:
            logger(f"❌ Error updating drawdown settings: {str(e)}")


# Global instance
drawdown_manager = DrawdownManager()


def initialize_drawdown_tracking():
    """Initialize drawdown tracking system"""
    return drawdown_manager.initialize_balance()


def get_current_drawdown_status() -> Dict[str, Any]:
    """Get current drawdown status"""
    return drawdown_manager.update_drawdown_status()


def get_recovery_adjustments() -> Dict[str, Any]:
    """Get recovery mode adjustments for trading"""
    return drawdown_manager.get_recovery_adjustments()


def add_trade_to_tracking(symbol: str, action: str, profit: float, lot_size: float):
    """Add trade result to performance tracking"""
    drawdown_manager.add_trade_result(symbol, action, profit, lot_size)


def get_performance_analysis() -> Dict[str, Any]:
    """Get comprehensive performance analysis"""
    return drawdown_manager.get_performance_summary()


def is_recovery_mode_active() -> bool:
    """Check if recovery mode is currently active"""
    return drawdown_manager.recovery_mode


def configure_drawdown_settings(settings: Dict[str, Any]):
    """Configure drawdown manager settings"""
    drawdown_manager.update_settings(settings)