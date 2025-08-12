# --- Economic Calendar Module ---
"""
Economic calendar integration untuk avoid trading saat high impact news
Real-time news monitoring untuk protect trading dari volatility spikes
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import logger
import threading
import time


class EconomicCalendar:
    """Economic calendar system untuk news-aware trading"""

    def __init__(self):
        self.news_data = []
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_update = None
        self.update_interval = 300  # 5 minutes
        self.calendar_lock = threading.Lock()

        # News impact levels
        self.impact_levels = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }

        # Ultra-aggressive settings for maximum trading opportunities
        self.settings = {
            "avoid_high_impact": False,  # MORE TRADING OPPORTUNITIES
            "avoid_medium_impact": False,
            "pause_minutes_before": 0,   # NO pause
            "pause_minutes_after": 0,    # NO pause
            "monitored_currencies": ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"],
            "auto_pause_trading": False  # MAXIMIZE TRADING TIME - disable news pause
        }

        # Fallback news schedule (UTC times)
        self.scheduled_news = {
            "Monday": [
                (8, 30, "EUR", "MEDIUM"),  # European session
                (13, 30, "USD", "HIGH"),   # US session
            ],
            "Tuesday": [
                (8, 30, "EUR", "MEDIUM"),
                (13, 30, "USD", "HIGH"),
            ],
            "Wednesday": [
                (8, 30, "EUR", "MEDIUM"),
                (13, 30, "USD", "HIGH"),
                (18, 0, "USD", "HIGH"),    # FOMC potential
            ],
            "Thursday": [
                (8, 30, "EUR", "MEDIUM"),
                (13, 30, "USD", "HIGH"),
            ],
            "Friday": [
                (8, 30, "EUR", "MEDIUM"),
                (13, 30, "USD", "HIGH"),   # NFP potential
            ]
        }

    def start_monitoring(self):
        """Start economic calendar monitoring"""
        try:
            if self.is_monitoring:
                logger("⚠️ Economic calendar already monitoring")
                return

            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()

            logger("✅ Economic calendar monitoring started")

            # Initial update
            self.update_calendar()

        except Exception as e:
            logger(f"❌ Error starting economic calendar: {str(e)}")
            self.is_monitoring = False

    def stop_monitoring(self):
        """Stop economic calendar monitoring"""
        try:
            self.is_monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)

            logger("🛑 Economic calendar monitoring stopped")

        except Exception as e:
            logger(f"❌ Error stopping economic calendar: {str(e)}")

    def update_calendar(self) -> bool:
        """Update economic calendar data"""
        try:
            with self.calendar_lock:
                # Try to fetch from multiple sources
                success = False

                # Method 1: ForexFactory (if available)
                if not success:
                    success = self._fetch_forexfactory_data()

                # Method 2: Economic Calendar API (if available)
                if not success:
                    success = self._fetch_investing_com_data()

                # Method 3: Fallback to scheduled news
                if not success:
                    success = self._use_scheduled_news()

                if success:
                    self.last_update = datetime.now()
                    logger(f"✅ Economic calendar updated: {len(self.news_data)} events")

                return success

        except Exception as e:
            logger(f"❌ Error updating economic calendar: {str(e)}")
            return self._use_scheduled_news()

    def _fetch_forexfactory_data(self) -> bool:
        """Fetch data from ForexFactory (requires parsing)"""
        try:
            # Note: ForexFactory requires web scraping, implemented as fallback
            # For production, use proper economic calendar API
            return False

        except Exception as e:
            logger(f"⚠️ ForexFactory fetch failed: {str(e)}")
            return False

    def _fetch_investing_com_data(self) -> bool:
        """Fetch data from Investing.com calendar API"""
        try:
            # This is a placeholder for proper API integration
            # For production use, implement with proper API key
            return False

        except Exception as e:
            logger(f"⚠️ Investing.com fetch failed: {str(e)}")
            return False

    def _use_scheduled_news(self) -> bool:
        """Use fallback scheduled news times"""
        try:
            self.news_data = []
            now = datetime.now()

            # Generate news events for next 24 hours
            for i in range(2):  # Today and tomorrow
                target_date = now + timedelta(days=i)
                day_name = target_date.strftime("%A")

                if day_name in self.scheduled_news:
                    for hour, minute, currency, impact in self.scheduled_news[day_name]:
                        event_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                        # Only add future events
                        if event_time > now:
                            event = {
                                "time": event_time,
                                "currency": currency,
                                "impact": impact,
                                "title": f"{currency} Economic Data",
                                "source": "scheduled"
                            }
                            self.news_data.append(event)

            # Sort by time
            self.news_data.sort(key=lambda x: x["time"])

            logger(f"📅 Using scheduled news: {len(self.news_data)} events")
            return True

        except Exception as e:
            logger(f"❌ Error creating scheduled news: {str(e)}")
            return False

    def should_pause_trading(self, symbol: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Check if trading should be paused due to news"""
        try:
            now = datetime.now()

            # Check if we have recent calendar data
            if not self.news_data or not self.last_update:
                return False, "No calendar data", {}

            # Check if data is stale
            if (now - self.last_update).total_seconds() > self.update_interval * 2:
                logger("⚠️ Economic calendar data is stale, updating...")
                self.update_calendar()

            # Get relevant currencies for symbol
            relevant_currencies = self._get_symbol_currencies(symbol) if symbol else self.settings["monitored_currencies"]

            # Check upcoming news events
            for event in self.news_data:
                event_time = event["time"]
                currency = event["currency"]
                impact = event["impact"]

                # Skip if not relevant currency
                if currency not in relevant_currencies:
                    continue

                # Calculate time difference
                time_diff = (event_time - now).total_seconds() / 60  # minutes

                # Check if we're in pause window
                pause_before = self.settings["pause_minutes_before"]
                pause_after = self.settings["pause_minutes_after"]

                # Since settings are for ULTRA-AGGRESSIVE, these pause windows are 0
                if -pause_after <= time_diff <= pause_before:
                    # Check impact level
                    should_pause = False

                    if impact == "HIGH" and self.settings["avoid_high_impact"]:
                        should_pause = True
                    elif impact == "MEDIUM" and self.settings["avoid_medium_impact"]:
                        should_pause = True

                    if should_pause:
                        pause_reason = f"{impact} impact {currency} news in {time_diff:.0f} minutes"

                        event_info = {
                            "event_title": event.get("title", "Economic Event"),
                            "event_time": event_time,
                            "currency": currency,
                            "impact": impact,
                            "minutes_until": time_diff
                        }

                        return True, pause_reason, event_info

            return False, "No relevant news", {}

        except Exception as e:
            logger(f"❌ Error checking news pause: {str(e)}")
            return False, f"Error: {str(e)}", {}

    def _get_symbol_currencies(self, symbol: str) -> List[str]:
        """Get relevant currencies for trading symbol"""
        try:
            if not symbol:
                return self.settings["monitored_currencies"]

            symbol_upper = symbol.upper()
            currencies = []

            # Extract currencies from symbol
            for curr in self.settings["monitored_currencies"]:
                if curr in symbol_upper:
                    currencies.append(curr)

            # If no specific currencies found, monitor major ones
            if not currencies:
                currencies = ["USD", "EUR"]

            return currencies

        except Exception as e:
            logger(f"❌ Error getting symbol currencies: {str(e)}")
            return ["USD", "EUR"]

    def get_upcoming_news(self, hours_ahead: int = 4) -> List[Dict[str, Any]]:
        """Get upcoming news events"""
        try:
            now = datetime.now()
            cutoff_time = now + timedelta(hours=hours_ahead)

            upcoming = []
            for event in self.news_data:
                if now <= event["time"] <= cutoff_time:
                    event_copy = event.copy()
                    event_copy["minutes_until"] = (event["time"] - now).total_seconds() / 60
                    upcoming.append(event_copy)

            return upcoming

        except Exception as e:
            logger(f"❌ Error getting upcoming news: {str(e)}")
            return []

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Update calendar periodically
                if (not self.last_update or 
                    (datetime.now() - self.last_update).total_seconds() > self.update_interval):
                    self.update_calendar()

                # Check if trading should be paused
                if self.settings["auto_pause_trading"]:
                    should_pause, reason, event_info = self.should_pause_trading()

                    if should_pause:
                        logger(f"📅 News pause recommended: {reason}")

                        # Notify main system about news pause
                        try:
                            self._notify_news_pause(reason, event_info)
                        except:
                            pass

                # Sleep for next check
                time.sleep(60)  # Check every minute

            except Exception as e:
                logger(f"❌ Error in calendar monitoring loop: {str(e)}")
                time.sleep(60)

    def _notify_news_pause(self, reason: str, event_info: Dict[str, Any]):
        """Notify system about news pause requirement"""
        try:
            # Try to notify bot controller
            import bot_controller
            if hasattr(bot_controller, 'set_news_pause'):
                bot_controller.set_news_pause(True, reason, event_info)

            # Try to notify GUI
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui:
                __main__.gui.update_news_status(reason, event_info)

            # Telegram notification for high impact news
            if event_info.get("impact") == "HIGH":
                try:
                    from telegram_notifications import notify_news_alert
                    notify_news_alert(reason, event_info)
                except:
                    pass

        except Exception as e:
            logger(f"⚠️ Error notifying news pause: {str(e)}")

    def update_settings(self, new_settings: Dict[str, Any]):
        """Update calendar settings"""
        try:
            self.settings.update(new_settings)
            logger("✅ Economic calendar settings updated")

        except Exception as e:
            logger(f"❌ Error updating calendar settings: {str(e)}")

    def get_calendar_status(self) -> Dict[str, Any]:
        """Get calendar status information"""
        try:
            upcoming_news = self.get_upcoming_news(2)  # Next 2 hours
            should_pause, reason, event_info = self.should_pause_trading()

            status = {
                "is_monitoring": self.is_monitoring,
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "total_events": len(self.news_data),
                "upcoming_news_2h": len(upcoming_news),
                "should_pause_trading": should_pause,
                "pause_reason": reason,
                "next_event": event_info if should_pause else None,
                "upcoming_events": upcoming_news[:5]  # Next 5 events
            }

            return status

        except Exception as e:
            logger(f"❌ Error getting calendar status: {str(e)}")
            return {"error": str(e)}


# Global instance
economic_calendar = EconomicCalendar()


def start_economic_calendar():
    """Start economic calendar monitoring"""
    economic_calendar.start_monitoring()


def stop_economic_calendar():
    """Stop economic calendar monitoring"""
    economic_calendar.stop_monitoring()


def should_pause_for_news(symbol: str = None) -> Tuple[bool, str, Dict[str, Any]]:
    """Check if should pause trading for news"""
    return economic_calendar.should_pause_trading(symbol)


def get_upcoming_news_events(hours_ahead: int = 4) -> List[Dict[str, Any]]:
    """Get upcoming news events"""
    return economic_calendar.get_upcoming_news(hours_ahead)


def update_calendar_settings(settings: Dict[str, Any]):
    """Update economic calendar settings"""
    economic_calendar.update_settings(settings)


def get_economic_calendar_status() -> Dict[str, Any]:
    """Get economic calendar status"""
    return economic_calendar.get_calendar_status()