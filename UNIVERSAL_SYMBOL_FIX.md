# UNIVERSAL SYMBOL SUPPORT - ERROR 10016 FIX

## 🎯 **COMPREHENSIVE ASSET CLASS SUPPORT**

User benar - sistem harus support SEMUA symbols, bukan hanya XAU dan BTC. Berikut implementasi universal:

### **📊 Asset Classes & Minimum Distances**

1. **FOREX PAIRS** (10-20 pips)
   - EURUSD, GBPUSD, AUDUSD: 10 pips
   - USDJPY, EURJPY, GBPJPY: 20 pips 
   - NZDUSD, USDCAD, EURGBP: 10 pips

2. **PRECIOUS METALS** (100+ pips)
   - XAUUSD, XAUUSDm (Gold): 100 pips
   - XAGUSD, XAGUSDm (Silver): 50 pips
   - XPTUSD (Platinum): 75 pips

3. **CRYPTOCURRENCIES** (25-50 pips)
   - BTCUSD, BTCUSDm: 50 pips
   - ETHUSD, ETHUSDm: 30 pips
   - LTCUSD, ADAUSD, DOTUSD: 25 pips

4. **COMMODITIES** (20-30 pips)
   - USOUSD, USOUSDm, WTI: 20 pips
   - UKOUSD (Brent): 20 pips
   - NATGAS: 30 pips

5. **INDICES** (1-5 points)
   - US30, US500, NAS100: 5 points
   - GER30, UK100, FRA40: 3 points
   - AUS200, JPN225: 2 points

6. **STOCKS** (0.01-1.00 based on price)
   - High price (>$100): 1.00
   - Mid price ($10-100): 0.50
   - Low price (<$10): 0.10

## 🔧 **IMPLEMENTATION STRATEGY**

**Smart Symbol Detection:**
```python
def get_symbol_specs(symbol):
    symbol_upper = symbol.upper()
    
    # Forex Detection
    if any(pair in symbol_upper for pair in FOREX_PAIRS):
        return forex_specs
    
    # Metals Detection  
    if any(metal in symbol_upper for metal in METALS):
        return metal_specs
        
    # Crypto Detection
    if any(crypto in symbol_upper for crypto in CRYPTOS):
        return crypto_specs
    
    # Auto fallback with reasonable defaults
    return default_specs
```

**Universal Minimum Distance Calculator:**
```python
def calculate_minimum_distance(symbol, current_price):
    specs = get_symbol_specs(symbol)
    base_distance = specs['min_pips'] * specs['point']
    
    # Dynamic scaling for high-value assets
    if current_price > 1000:
        return base_distance * 2
    elif current_price > 10000:
        return base_distance * 5
    
    return base_distance
```