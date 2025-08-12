# --- Professional Trading Systems Initializer ---
"""
Initialize all professional trading enhancement systems
Centralized startup untuk trailing stops, economic calendar, drawdown manager
"""

from logger_utils import logger
import threading
import time

# Global status tracking
systems_status = {
    "trailing_stops": False,
    "economic_calendar": False,
    "drawdown_manager": False,
    "all_systems_ready": False
}

def initialize_all_professional_systems():
    """Initialize all professional trading enhancement systems"""
    logger("🚀 Initializing Professional Trading Enhancement Systems...")
    
    success_count = 0
    total_systems = 3
    
    # 1. Initialize Trailing Stop System
    try:
        from trailing_stop_manager import start_trailing_stop_system
        start_trailing_stop_system()
        systems_status["trailing_stops"] = True
        success_count += 1
        logger("✅ Trailing Stop System initialized")
    except Exception as e:
        logger(f"❌ Trailing Stop System failed: {str(e)}")
        systems_status["trailing_stops"] = False
    
    # 2. Initialize Economic Calendar
    try:
        from economic_calendar import start_economic_calendar
        start_economic_calendar()
        systems_status["economic_calendar"] = True
        success_count += 1
        logger("✅ Economic Calendar System initialized")
    except Exception as e:
        logger(f"❌ Economic Calendar System failed: {str(e)}")
        systems_status["economic_calendar"] = False
    
    # 3. Initialize Drawdown Manager
    try:
        from drawdown_manager import initialize_drawdown_tracking
        if initialize_drawdown_tracking():
            systems_status["drawdown_manager"] = True
            success_count += 1
            logger("✅ Drawdown Manager System initialized")
        else:
            logger("❌ Drawdown Manager initialization failed")
            systems_status["drawdown_manager"] = False
    except Exception as e:
        logger(f"❌ Drawdown Manager System failed: {str(e)}")
        systems_status["drawdown_manager"] = False
    
    # Overall status
    systems_status["all_systems_ready"] = (success_count == total_systems)
    
    if systems_status["all_systems_ready"]:
        logger("🎯 ALL PROFESSIONAL SYSTEMS READY FOR REAL TRADING")
        logger(f"   ✅ Trailing Stops: Active")
        logger(f"   ✅ Economic Calendar: Monitoring")
        logger(f"   ✅ Drawdown Manager: Tracking")
    else:
        logger(f"⚠️ Professional Systems Status: {success_count}/{total_systems} ready")
        
        if not systems_status["trailing_stops"]:
            logger("   ❌ Trailing Stops: DISABLED")
        if not systems_status["economic_calendar"]:
            logger("   ❌ Economic Calendar: DISABLED")
        if not systems_status["drawdown_manager"]:
            logger("   ❌ Drawdown Manager: DISABLED")
    
    return systems_status["all_systems_ready"]

def shutdown_all_professional_systems():
    """Shutdown all professional trading systems"""
    logger("🛑 Shutting down Professional Trading Systems...")
    
    # 1. Stop Trailing Stops
    try:
        from trailing_stop_manager import stop_trailing_stop_system
        stop_trailing_stop_system()
        logger("✅ Trailing Stop System stopped")
    except Exception as e:
        logger(f"❌ Error stopping Trailing Stops: {str(e)}")
    
    # 2. Stop Economic Calendar
    try:
        from economic_calendar import stop_economic_calendar
        stop_economic_calendar()
        logger("✅ Economic Calendar stopped")
    except Exception as e:
        logger(f"❌ Error stopping Economic Calendar: {str(e)}")
    
    # Update status
    systems_status.update({
        "trailing_stops": False,
        "economic_calendar": False,
        "drawdown_manager": False,
        "all_systems_ready": False
    })
    
    logger("🔒 All Professional Systems shutdown complete")

def get_systems_status():
    """Get current status of all professional systems"""
    return systems_status.copy()

def is_ready_for_real_trading():
    """Check if all critical systems are ready for real trading"""
    critical_systems = ["trailing_stops", "economic_calendar", "drawdown_manager"]
    
    for system in critical_systems:
        if not systems_status.get(system, False):
            return False, f"Critical system not ready: {system}"
    
    return True, "All critical systems ready for real trading"

def start_professional_monitoring():
    """Start background monitoring of professional systems"""
    def monitoring_loop():
        while systems_status.get("all_systems_ready", False):
            try:
                # Check system health every 30 seconds
                time.sleep(30)
                
                # Quick health check
                current_status = get_systems_status()
                if not current_status["all_systems_ready"]:
                    logger("⚠️ Professional system health check failed")
                    break
                    
            except Exception as e:
                logger(f"❌ Monitoring loop error: {str(e)}")
                break
    
    if systems_status.get("all_systems_ready", False):
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        logger("🔍 Professional systems monitoring started")

# Auto-initialize when imported (if needed)
def auto_initialize_if_trading():
    """Auto-initialize systems if trading bot is active"""
    try:
        import __main__
        if hasattr(__main__, 'gui') and __main__.gui:
            # Check if bot is running or about to run
            if hasattr(__main__.gui, 'bot_running') and __main__.gui.bot_running:
                logger("🤖 Bot is running, auto-initializing professional systems...")
                initialize_all_professional_systems()
                start_professional_monitoring()
    except:
        pass  # Silent fail if not in main bot context