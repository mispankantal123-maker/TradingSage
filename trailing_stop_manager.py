# --- Trailing Stop Manager Module ---
"""
Advanced trailing stop system untuk real trading
Protect profits dengan volatility-adjusted trailing stops
"""

import time
import threading
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


class TrailingStopManager:
    """Professional trailing stop system untuk maximize profit retention"""

    def __init__(self):
        self.active_trails = {}  # {position_ticket: trail_config}
        self.trail_thread = None
        self.is_running = False
        self.check_interval = 2  # seconds
        self.trail_lock = threading.Lock()

        # Default trailing parameters
        self.default_config = {
            "trail_distance_pips": 20,
            "trail_step_pips": 5,
            "min_profit_pips": 15,
            "use_atr_based": True,
            "atr_multiplier": 2.0,
            "max_trail_distance": 100,
            "min_trail_distance": 5
        }

    def start_trailing_monitor(self):
        """Start trailing stop monitoring thread"""
        try:
            if self.is_running:
                logger("⚠️ Trailing stop monitor already running")
                return

            self.is_running = True
            self.trail_thread = threading.Thread(target=self._trailing_monitor_loop, daemon=True)
            self.trail_thread.start()

            logger("✅ Trailing stop monitor started")

        except Exception as e:
            logger(f"❌ Error starting trailing monitor: {str(e)}")
            self.is_running = False

    def stop_trailing_monitor(self):
        """Stop trailing stop monitoring"""
        try:
            self.is_running = False
            if self.trail_thread and self.trail_thread.is_alive():
                self.trail_thread.join(timeout=5)

            logger("🛑 Trailing stop monitor stopped")

        except Exception as e:
            logger(f"❌ Error stopping trailing monitor: {str(e)}")

    def add_trailing_stop(self, position_ticket: int, symbol: str, 
                         trail_config: Dict[str, Any] = None) -> bool:
        """Add trailing stop untuk position"""
        try:
            with self.trail_lock:
                # Get position info
                position = None
                positions = mt5.positions_get(ticket=position_ticket)
                if positions and len(positions) > 0:
                    position = positions[0]
                else:
                    logger(f"❌ Position {position_ticket} not found")
                    return False

                # Use default config if not provided
                if not trail_config:
                    trail_config = self.default_config.copy()

                # Ensure all required keys exist
                required_keys = ["trail_distance_pips", "trail_step_pips", "min_profit_pips", 
                               "use_atr_based", "atr_multiplier", "max_trail_distance", "min_trail_distance"]
                for key in required_keys:
                    if key not in trail_config:
                        trail_config[key] = self.default_config.get(key, 0)

                # Calculate ATR-based trailing distance if enabled
                if trail_config.get("use_atr_based", True):
                    atr_distance = self._calculate_atr_trailing_distance(symbol, trail_config)
                    if atr_distance > 0:
                        trail_config["trail_distance_pips"] = atr_distance

                # Initialize trailing configuration
                trail_info = {
                    "ticket": position_ticket,
                    "symbol": symbol,
                    "position_type": position.type,
                    "open_price": position.price_open,
                    "current_sl": position.sl,
                    "current_tp": position.tp,
                    "volume": position.volume,
                    "trail_distance_pips": trail_config["trail_distance_pips"],
                    "trail_step_pips": trail_config["trail_step_pips"],
                    "min_profit_pips": trail_config["min_profit_pips"],
                    "last_trail_price": 0.0,
                    "max_favorable_price": position.price_open,
                    "created_time": datetime.now(),
                    "trail_count": 0
                }

                self.active_trails[position_ticket] = trail_info

                logger(f"✅ Trailing stop added for position {position_ticket}")
                logger(f"   Symbol: {symbol} | Distance: {trail_config['trail_distance_pips']} pips")

                return True

        except Exception as e:
            logger(f"❌ Error adding trailing stop: {str(e)}")
            return False

    def remove_trailing_stop(self, position_ticket: int):
        """Remove trailing stop untuk position"""
        try:
            with self.trail_lock:
                if position_ticket in self.active_trails:
                    del self.active_trails[position_ticket]
                    logger(f"🗑️ Trailing stop removed for position {position_ticket}")

        except Exception as e:
            logger(f"❌ Error removing trailing stop: {str(e)}")

    def _trailing_monitor_loop(self):
        """Main monitoring loop untuk trailing stops"""
        while self.is_running:
            try:
                if not self.active_trails:
                    time.sleep(self.check_interval)
                    continue

                # Process each active trailing stop
                positions_to_remove = []

                with self.trail_lock:
                    for ticket, trail_info in self.active_trails.items():
                        # Check if position still exists
                        positions = mt5.positions_get(ticket=ticket)
                        if not positions or len(positions) == 0:
                            positions_to_remove.append(ticket)
                            continue

                        position = positions[0]

                        # Update trailing stop
                        self._update_trailing_stop(position, trail_info)

                # Remove closed positions
                for ticket in positions_to_remove:
                    self.remove_trailing_stop(ticket)

                time.sleep(self.check_interval)

            except Exception as e:
                logger(f"❌ Error in trailing monitor loop: {str(e)}")
                time.sleep(self.check_interval)

    def _update_trailing_stop(self, position, trail_info: Dict[str, Any]):
        """Update trailing stop untuk individual position"""
        try:
            symbol = position.symbol
            current_price = self._get_current_price(symbol, position.type)

            if current_price <= 0:
                return

            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return

            point = symbol_info.point
            digits = symbol_info.digits

            # Calculate pip value
            pip_value = point * (10 if "JPY" in symbol else 10)

            is_buy_position = position.type == mt5.ORDER_TYPE_BUY

            # Update maximum favorable price
            if is_buy_position:
                if current_price > trail_info["max_favorable_price"]:
                    trail_info["max_favorable_price"] = current_price
            else:
                if current_price < trail_info["max_favorable_price"]:
                    trail_info["max_favorable_price"] = current_price

            # Calculate profit in pips
            if is_buy_position:
                profit_pips = (current_price - position.price_open) / pip_value
            else:
                profit_pips = (position.price_open - current_price) / pip_value

            # Check if minimum profit reached
            if profit_pips < trail_info["min_profit_pips"]:
                return

            # Calculate new trailing stop level
            trail_distance = trail_info["trail_distance_pips"] * pip_value

            if is_buy_position:
                new_sl = trail_info["max_favorable_price"] - trail_distance
            else:
                new_sl = trail_info["max_favorable_price"] + trail_distance

            new_sl = round(new_sl, digits)

            # Check if we should update stop loss
            should_update = False

            if is_buy_position:
                if position.sl == 0 or new_sl > position.sl:
                    # Only trail upward for buy positions
                    trail_step = trail_info["trail_step_pips"] * pip_value
                    if position.sl == 0 or new_sl >= position.sl + trail_step:
                        should_update = True
            else:
                if position.sl == 0 or new_sl < position.sl:
                    # Only trail downward for sell positions
                    trail_step = trail_info["trail_step_pips"] * pip_value
                    if position.sl == 0 or new_sl <= position.sl - trail_step:
                        should_update = True

            if should_update:
                # Validate minimum stop distance
                min_stops_level = getattr(symbol_info, 'trade_stops_level', 0) * point
                if min_stops_level == 0:
                    min_stops_level = 10 * point

                if is_buy_position:
                    min_sl = current_price - min_stops_level
                    if new_sl > min_sl:
                        new_sl = min_sl
                else:
                    max_sl = current_price + min_stops_level
                    if new_sl < max_sl:
                        new_sl = max_sl

                new_sl = round(new_sl, digits)

                # Execute stop loss modification
                if self._modify_position_sl(position.ticket, new_sl):
                    trail_info["current_sl"] = new_sl
                    trail_info["last_trail_price"] = current_price
                    trail_info["trail_count"] += 1

                    profit_distance = abs(new_sl - position.price_open) / pip_value

                    logger(f"📈 Trailing stop updated for {symbol} #{position.ticket}")
                    logger(f"   New SL: {new_sl:.{digits}f} | Profit secured: {profit_distance:.1f} pips")

                    # Telegram notification for significant trails
                    if trail_info["trail_count"] % 3 == 0:  # Every 3rd trail
                        try:
                            from telegram_notifications import notify_trailing_stop_update
                            notify_trailing_stop_update(symbol, position.ticket, new_sl, profit_distance)
                        except:
                            pass

        except Exception as e:
            logger(f"❌ Error updating trailing stop: {str(e)}")

    def _get_current_price(self, symbol: str, position_type: int) -> float:
        """Get current market price untuk position type"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return 0.0

            if position_type == mt5.ORDER_TYPE_BUY:
                return tick.bid  # Exit price for buy position
            else:
                return tick.ask  # Exit price for sell position

        except Exception as e:
            logger(f"❌ Error getting current price: {str(e)}")
            return 0.0

    def _modify_position_sl(self, ticket: int, new_sl: float) -> bool:
        """Modify stop loss untuk position"""
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return False

            position = positions[0]

            # Prepare modification request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "magic": 234000,
                "comment": "TrailingStop"
            }

            # Send modification request
            result = mt5.order_send(request)

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return True
            else:
                error_msg = result.comment if result else "Unknown error"
                logger(f"⚠️ Failed to modify SL: {error_msg}")
                return False

        except Exception as e:
            logger(f"❌ Error modifying position SL: {str(e)}")
            return False

    def _calculate_atr_trailing_distance(self, symbol: str, config: Dict[str, Any]) -> float:
        """Calculate ATR-based trailing distance"""
        try:
            # Get recent price data
            bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
            if bars is None or len(bars) < 14:
                return config["trail_distance_pips"]

            import pandas as pd
            df = pd.DataFrame(bars)

            # Calculate ATR
            from indicators import atr
            df['ATR'] = atr(df, period=14)
            current_atr = df['ATR'].iloc[-1]

            if pd.isna(current_atr) or current_atr <= 0:
                return config["trail_distance_pips"]

            # Convert ATR to pips
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                point = symbol_info.point
                pip_value = point * (10 if "JPY" in symbol else 10)
                atr_pips = (current_atr / pip_value) * config.get("atr_multiplier", 2.0)

                # Apply limits
                max_distance = config.get("max_trail_distance", 100)
                min_distance = config.get("min_trail_distance", 5)

                atr_pips = max(min_distance, min(atr_pips, max_distance))

                logger(f"📊 ATR-based trailing distance for {symbol}: {atr_pips:.1f} pips")

                return atr_pips

            return config["trail_distance_pips"]

        except Exception as e:
            logger(f"❌ Error calculating ATR trailing distance: {str(e)}")
            return config["trail_distance_pips"]

    def get_trailing_status(self) -> Dict[str, Any]:
        """Get current trailing stop status"""
        try:
            with self.trail_lock:
                status = {
                    "is_running": self.is_running,
                    "active_trails_count": len(self.active_trails),
                    "active_trails": []
                }

                for ticket, trail_info in self.active_trails.items():
                    trail_status = {
                        "ticket": ticket,
                        "symbol": trail_info["symbol"],
                        "trail_distance_pips": trail_info["trail_distance_pips"],
                        "trail_count": trail_info["trail_count"],
                        "max_favorable_price": trail_info["max_favorable_price"],
                        "current_sl": trail_info["current_sl"]
                    }
                    status["active_trails"].append(trail_status)

                return status

        except Exception as e:
            logger(f"❌ Error getting trailing status: {str(e)}")
            return {"error": str(e)}

    def update_trailing_config(self, new_config: Dict[str, Any]):
        """Update default trailing configuration"""
        try:
            self.default_config.update(new_config)
            logger(f"✅ Trailing stop configuration updated")

        except Exception as e:
            logger(f"❌ Error updating trailing config: {str(e)}")


# Global instance
trailing_manager = TrailingStopManager()


def start_trailing_stop_system():
    """Start trailing stop system"""
    trailing_manager.start_trailing_monitor()


def stop_trailing_stop_system():
    """Stop trailing stop system"""
    trailing_manager.stop_trailing_monitor()


def add_trailing_stop_to_position(position_ticket: int, symbol: str, config: Dict[str, Any] = None) -> bool:
    """Add trailing stop to position"""
    try:
        # Try multiple methods to find the position
        position = None

        # Method 1: Find by ticket
        positions_by_ticket = mt5.positions_get(ticket=position_ticket)
        if positions_by_ticket:
            position = positions_by_ticket[0]
            logger(f"✅ Found position by ticket: {position_ticket}")
        else:
            # Method 2: Find by symbol (get latest position)
            positions_by_symbol = mt5.positions_get(symbol=symbol)
            if positions_by_symbol:
                # Get the latest position for this symbol
                position = positions_by_symbol[-1]
                logger(f"✅ Found position by symbol: {symbol} (ticket: {position.ticket})")
            else:
                # Method 3: Get all positions and find matching one
                all_positions = mt5.positions_get()
                if all_positions:
                    for pos in all_positions:
                        if pos.symbol == symbol:
                            position = pos
                            logger(f"✅ Found position in all positions: {pos.ticket}")
                            break

        if not position:
            logger(f"❌ Position not found - Ticket: {position_ticket}, Symbol: {symbol}")
            return False
        
        # Ensure the found position's ticket matches the requested ticket if found by ticket
        if positions_by_ticket and position.ticket != position_ticket:
             logger(f"❌ Ticket mismatch: Requested {position_ticket}, found {position.ticket} for symbol {symbol}")
             return False


        # Use default config if not provided
        if not config:
            config = trailing_manager.default_config.copy()

        # Ensure all required keys exist in the provided config
        required_keys = ["trail_distance_pips", "trail_step_pips", "min_profit_pips", 
                       "use_atr_based", "atr_multiplier", "max_trail_distance", "min_trail_distance"]
        for key in required_keys:
            if key not in config:
                config[key] = trailing_manager.default_config.get(key, 0)

        # Calculate ATR-based trailing distance if enabled
        if config.get("use_atr_based", True):
            atr_distance = trailing_manager._calculate_atr_trailing_distance(symbol, config)
            if atr_distance > 0:
                config["trail_distance_pips"] = atr_distance

        # Initialize trailing configuration
        trail_info = {
            "ticket": position.ticket, # Use the ticket of the found position
            "symbol": symbol,
            "position_type": position.type,
            "open_price": position.price_open,
            "current_sl": position.sl,
            "current_tp": position.tp,
            "volume": position.volume,
            "trail_distance_pips": config["trail_distance_pips"],
            "trail_step_pips": config["trail_step_pips"],
            "min_profit_pips": config["min_profit_pips"],
            "last_trail_price": 0.0,
            "max_favorable_price": position.price_open,
            "created_time": datetime.now(),
            "trail_count": 0
        }

        trailing_manager.active_trails[position.ticket] = trail_info

        logger(f"✅ Trailing stop added for position {position.ticket}")
        logger(f"   Symbol: {symbol} | Distance: {config['trail_distance_pips']} pips")

        return True

    except Exception as e:
        logger(f"❌ Error adding trailing stop: {str(e)}")
        return False


def remove_trailing_stop_from_position(ticket: int):
    """Remove trailing stop from position"""
    trailing_manager.remove_trailing_stop(ticket)


def get_trailing_stops_status() -> Dict[str, Any]:
    """Get trailing stops status"""
    return trailing_manager.get_trailing_stops_status()


def configure_trailing_stops(config: Dict[str, Any]):
    """Configure trailing stop parameters"""
    trailing_manager.update_trailing_config(config)