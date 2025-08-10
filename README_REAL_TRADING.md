# 🔥 MT5 REAL MONEY TRADING BOT

## ⚠️ PERINGATAN PENTING
**BOT INI MENGGUNAKAN UANG ASLI - BUKAN DEMO!**
- Setiap order yang ditempatkan menggunakan modal nyata
- Anda bisa kehilangan uang jika market bergerak berlawanan 
- WAJIB test dengan demo account terlebih dahulu
- Gunakan dengan hati-hati dan risiko sendiri!

## 🖥️ REQUIREMENTS SISTEM

### Windows Only
- Windows 10/11 (64-bit)
- MT5 Terminal terinstall dan aktif
- Python 3.8+ terinstall
- Akun broker MT5 yang valid

### Broker Requirements
- Broker yang support API trading
- Akun real/live trading (bukan demo)
- Algorithmic trading WAJIB diaktifkan di MT5

## 📦 INSTALASI

### 1. Install Dependencies
```bash
python install_dependencies.py
```

### 2. Setup MT5 Terminal
1. Buka MT5 Terminal
2. Login dengan akun real trading Anda
3. Tools → Options → Expert Advisors
4. ✅ Centang "Allow algorithmic trading"
5. ✅ Centang "Allow WebRequest for listed URL"
6. Restart MT5 Terminal

### 3. Jalankan Bot
```bash
python main.py
```

## 🚀 CARA PENGGUNAAN

### Step 1: Connect ke MT5
1. Klik "Connect MT5"
2. Bot akan menampilkan info akun real
3. Pastikan balance dan equity sesuai

### Step 2: Setup Trading Parameters
- **Strategy**: Pilih Scalping/Intraday/Arbitrage/HFT
- **Symbol**: Pilih pair trading (EURUSD, GBPUSD, dll)
- **Lot Size**: Set ukuran lot (0.01 = micro lot)
- **Auto Lot**: Otomatis hitung lot berdasarkan risk %
- **Take Profit**: Target profit (pips/price/percent/money)
- **Stop Loss**: Batas rugi (pips/price/percent/money)

### Step 3: Test Manual Trading
- Coba "Manual BUY" atau "Manual SELL" dulu
- Pastikan order masuk ke MT5 terminal
- Check spread dan execution time

### Step 4: Start Auto Trading
1. Klik "Start Bot"
2. Konfirmasi peringatan real money
3. Check konfigurasi sekali lagi
4. Bot akan mulai trading otomatis

## 🛡️ SAFETY FEATURES

### Confirmations
- Double confirmation untuk start auto trading
- Manual trade confirmation
- Settings review sebelum eksekusi

### Risk Management
- Maximum orders per session
- Minimum balance checking  
- Price spike detection
- Auto stop pada error berulang

### Logging
- Semua aktivitas tercatat di log
- Real-time monitoring di GUI
- File log tersimpan otomatis

## ⚙️ KONFIGURASI STRATEGI

### Scalping (Cepat)
- TP: 5 pips, SL: 3 pips
- Interval: 5 detik
- Timeframe: M1

### Intraday (Medium)
- TP: 20 pips, SL: 10 pips  
- Interval: 10 detik
- Timeframe: M5

### Arbitrage (Peluang)
- TP: 15 pips, SL: 8 pips
- Interval: 3 detik
- Timeframe: M1

### High Frequency (Ultra Fast)
- TP: 2 pips, SL: 1 pip
- Interval: 1 detik
- Timeframe: M1

## 🚨 TROUBLESHOOTING

### Error: "MT5 not connected"
- Pastikan MT5 Terminal running
- Login ulang ke akun broker
- Check internet connection
- Restart MT5 dan bot

### Error: "Invalid symbol"  
- Pastikan symbol tersedia di market watch
- Coba symbol umum: EURUSD, GBPUSD, USDJPY
- Check jam trading market

### Error: "Order failed"
- Check margin tersedia
- Pastikan lot size valid
- Verifikasi spread tidak terlalu lebar
- Check algorithmic trading enabled

### Bot tidak execute order
- Check sinyal strategi di log
- Pastikan indicator data tersedia
- Verifikasi minimum score setting
- Review TP/SL calculation

## 💡 TIPS TRADING

### Risk Management
- Jangan invest lebih dari yang bisa Anda rugi
- Start dengan lot kecil (0.01)
- Set risk percentage max 2-5%
- Monitor balance secara berkala

### Strategy Selection
- Scalping: Good untuk major pairs, low spread
- Intraday: Balanced risk-reward
- HFT: Butuh VPS, execution cepat
- Arbitrage: Good untuk volatile market

### Monitoring
- Jangan tinggal bot tanpa pengawasan
- Check log error secara berkala
- Monitor drawdown dan profit
- Siapkan emergency stop

## 📞 DISCLAIMER
- Bot ini untuk educational purposes
- Author tidak bertanggung jawab atas kerugian
- Trading forex berisiko tinggi
- Past performance tidak menjamin hasil masa depan
- Gunakan dengan bijak dan risiko sendiri!

## 📚 SUPPORT

Jika ada masalah:
1. Check log error di tab Logs
2. Pastikan setup MT5 sudah benar
3. Verifikasi koneksi internet stable
4. Test dengan akun demo dulu

**GOOD LUCK & TRADE SAFELY!** 🚀💰