# --- Main Application Entry Point ---
"""
MT5 Advanced Auto Trading Bot v4.0 - Modular Edition
Main entry point for the trading bot application
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import datetime
import threading

# Import our modular components
from logger_utils import logger, ensure_log_directory
from config import STRATEGIES
from gui_module import TradingBotGUI
from bot_controller import start_bot_thread, stop_bot, start_auto_recovery_monitor, get_bot_status, emergency_stop_all

# Global variables
gui = None
bot_running = False


def initialize_application():
    """Initialize the application and all required components"""
    try:
        logger("🚀 Initializing MT5 Advanced Trading Bot v4.0")
        logger("=" * 60)
        logger("📋 System Information:")
        logger(f"   Python Version: {sys.version.split()[0]}")
        logger(f"   Platform: {sys.platform}")
        logger(f"   Working Directory: {os.getcwd()}")
        logger("")
        
        # Ensure required directories exist
        if not ensure_log_directory():
            logger("⚠️ Warning: Could not create log directories")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger("❌ Error: Python 3.8 or higher required")
            return False
        
        logger("✅ Application initialized successfully")
        return True
        
    except Exception as e:
        logger(f"❌ Fatal initialization error: {str(e)}")
        return False


def create_main_window():
    """Create and configure the main application window"""
    try:
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide initially
        
        # Configure window properties
        root.protocol("WM_DELETE_WINDOW", on_application_closing)
        
        # Center window on screen
        root.update_idletasks()
        width = 1400
        height = 900
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create GUI instance
        global gui
        gui = TradingBotGUI(root)
        
        # Set global GUI reference for other modules
        # Note: In Replit environment, we handle global state through module imports
        global bot_running
        bot_running = False  # Will be updated by bot_controller
        
        # Show window
        root.deiconify()
        
        logger("🎨 GUI created successfully")
        return root
        
    except Exception as e:
        logger(f"❌ Error creating main window: {str(e)}")
        return None


def on_application_closing():
    """Handle application closing event"""
    try:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔄 Application shutdown initiated...")
        
        # Ask user confirmation if bot is running
        global bot_running
        if bot_running:
            try:
                response = messagebox.askyesno(
                    "Confirm Exit",
                    "Trading bot is running. Stop bot and exit?",
                    icon="warning"
                )
                if not response:
                    return
            except:
                # GUI might be destroyed, force stop
                pass
        
        # Stop bot and cleanup
        stop_bot()
        
        # Mark GUI as shutting down
        if gui:
            gui._shutdown_in_progress = True
        
        # Close GUI
        if gui and hasattr(gui, 'root') and gui.root:
            try:
                gui.root.quit()
            except:
                pass
            try:
                gui.root.destroy()
            except:
                pass
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Application shutdown completed")
        
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error during application shutdown: {str(e)}")
        # Force exit if normal shutdown fails
        try:
            if gui and hasattr(gui, 'root') and gui.root:
                gui.root.destroy()
        except:
            pass
        sys.exit(0)


def run_application():
    """Main application entry point"""
    try:
        # Print startup banner
        print("=" * 70)
        print("🚀 MT5 ADVANCED AUTO TRADING BOT v4.0 - MODULAR EDITION")
        print("=" * 70)
        print("📊 Professional Algorithmic Trading Platform")
        print("🎯 Multi-Strategy Support: Scalping | Intraday | Arbitrage | HFT")
        print("🔧 Modular Architecture with Advanced Risk Management")
        print("=" * 70)
        print()
        
        # Initialize application
        if not initialize_application():
            logger("❌ Application initialization failed")
            input("Press Enter to exit...")
            return
        
        # Create main window
        root = create_main_window()
        if not root:
            logger("❌ Failed to create main window")
            input("Press Enter to exit...")
            return
        
        # Start auto-recovery monitor
        start_auto_recovery_monitor()
        
        # Log successful startup
        logger("✅ Application startup completed successfully")
        logger("💡 Ready for trading operations")
        logger("")
        logger("📋 Quick Start Guide:")
        logger("   1. Ensure MT5 is running and logged in")
        logger("   2. Click 'Connect MT5' button")
        logger("   3. Configure strategy and parameters")
        logger("   4. Click 'Start Bot' to begin trading")
        logger("   5. Monitor log and positions in real-time")
        logger("")
        
        # Start GUI main loop
        try:
            root.mainloop()
        except KeyboardInterrupt:
            logger("⚠️ Application interrupted by user")
        except Exception as main_loop_e:
            logger(f"❌ GUI main loop error: {str(main_loop_e)}")
        
        # Final cleanup
        logger("🔄 Final cleanup...")
        stop_bot()
        
    except Exception as e:
        logger(f"❌ Critical application error: {str(e)}")
        import traceback
        logger(f"📝 Critical traceback: {traceback.format_exc()}")
        
        # Show error to user
        try:
            messagebox.showerror(
                "Critical Error",
                f"Application encountered a critical error:\n\n{str(e)}\n\nCheck logs for details."
            )
        except:
            print(f"CRITICAL ERROR: {str(e)}")
        
    finally:
        logger("🏁 Application terminated")
        print("\n" + "=" * 70)
        print("🏁 MT5 Advanced Trading Bot - Session Ended")
        print("=" * 70)


def run_headless_mode():
    """Run bot in headless mode (no GUI) for server deployments"""
    try:
        logger("🖥️ Starting in headless mode...")
        
        if not initialize_application():
            logger("❌ Headless initialization failed")
            return
        
        # Set default configuration
        from bot_controller import current_strategy
        current_strategy = "Scalping"  # Default strategy
        
        # Auto-connect to MT5 (mock) in headless mode
        from mt5_connection import connect_mt5
        if connect_mt5():
            logger("✅ MT5 (mock) connected for headless mode")
        else:
            logger("⚠️ Using mock MT5 for development - proceeding anyway")
        
        # Start bot
        if start_bot_thread():
            logger("🚀 Headless bot started successfully")
            
            # Keep running until interrupted
            try:
                while True:
                    import time
                    time.sleep(60)  # Check every minute
                    
                    # Print status periodically
                    status = get_bot_status()
                    if status.get('running'):
                        logger(f"📊 Headless Status: Running | Trades: {status.get('daily_trades', 0)} | Positions: {status.get('open_positions', 0)}")
                    
            except KeyboardInterrupt:
                logger("⚠️ Headless mode interrupted by user")
            
        else:
            logger("❌ Failed to start headless bot")
        
        # Cleanup
        stop_bot()
        logger("🏁 Headless mode terminated")
        
    except Exception as e:
        logger(f"❌ Headless mode error: {str(e)}")


if __name__ == "__main__":
    try:
        # For Replit environment, check if GUI is available
        # Default to headless mode in cloud environments
        if os.environ.get('REPLIT_ENVIRONMENT') or os.environ.get('REPL_ID'):
            print("🌐 Detected Replit environment - running in headless mode")
            run_headless_mode()
        elif len(sys.argv) > 1 and sys.argv[1] == "--headless":
            run_headless_mode()
        else:
            # Try GUI mode, fallback to headless if display not available
            try:
                import tkinter as tk
                # Test if display is available
                test_root = tk.Tk()
                test_root.withdraw()
                test_root.destroy()
                run_application()
            except Exception as gui_e:
                print(f"🖥️ GUI not available ({str(gui_e)}), falling back to headless mode")
                run_headless_mode()
            
    except Exception as startup_e:
        print(f"STARTUP ERROR: {str(startup_e)}")
        # Don't wait for input in cloud environments
        if not (os.environ.get('REPLIT_ENVIRONMENT') or os.environ.get('REPL_ID')):
            input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    finally:
        # Ensure clean exit
        try:
            sys.exit(0)
        except:
            os._exit(0)