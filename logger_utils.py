# --- Logging Utilities Module ---
"""
Enhanced logging functionality with GUI integration
"""

import datetime
import os
import csv


def logger(msg: str) -> None:
    """Enhanced logging function with timestamp and GUI integration"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    
    # Try to log to GUI if available (will be set by main module)
    try:
        import __main__
        if hasattr(__main__, 'gui') and __main__.gui:
            __main__.gui.log(full_msg)
    except Exception as e:
        # Specific exception handling for GUI logging
        pass  # Silently fail if GUI not available


def ensure_log_directory() -> bool:
    """Ensure log directory exists with proper error handling"""
    try:
        log_dir = "logs"
        csv_dir = "csv_logs"
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            logger(f"📁 Created log directory: {log_dir}")
            
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
            logger(f"📁 Created CSV log directory: {csv_dir}")
            
        return True
    except Exception as e:
        logger(f"❌ Error creating log directories: {str(e)}")
        return False


def log_order_csv(filename: str, order: dict) -> None:
    """Log order to CSV file with proper error handling"""
    try:
        ensure_log_directory()
        filepath = os.path.join("csv_logs", filename)
        
        # Check if file exists to determine if header needed
        file_exists = os.path.exists(filepath)
        
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'symbol', 'action', 'volume', 'price', 
                         'tp', 'sl', 'comment', 'ticket', 'profit']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(order)
            
        logger(f"📝 Order logged to {filename}")
        
    except Exception as e:
        logger(f"❌ Error logging to CSV {filename}: {str(e)}")


def cleanup_resources() -> None:
    """Cleanup utility to manage memory usage and resource leaks"""
    try:
        import gc
        gc.collect()
        logger("🧹 Memory cleanup completed")
    except Exception as e:
        logger(f"❌ Error during cleanup: {str(e)}")