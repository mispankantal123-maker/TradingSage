"""
MT5 Trading Bot - Dependency Installer
Run this script to install required packages for Windows MT5 trading
"""

import subprocess
import sys
import os

def install_packages():
    """Install required packages for MT5 trading bot"""
    packages = [
        'MetaTrader5>=5.0.45',
        'numpy>=1.21.0', 
        'requests>=2.25.0'
    ]
    
    print("🔥 Installing MT5 Trading Bot Dependencies...")
    print("=" * 50)
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("✅ All dependencies installed successfully!")
    print("\nIMPORTANT NOTES:")
    print("• MetaTrader5 only works on Windows")
    print("• You need MT5 terminal installed and running")
    print("• Make sure your MT5 allows algorithmic trading")
    print("• Test with demo account first before real money!")
    
    return True

if __name__ == "__main__":
    if os.name != 'nt':
        print("⚠️ WARNING: MetaTrader5 only works on Windows!")
        print("This bot is designed for Windows with MT5 terminal")
    
    install_packages()