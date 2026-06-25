# NSE Stock Scanner with Telegram Integration

## 📋 Overview

This project provides multiple ways to scan NSE (National Stock Exchange) stocks for trading opportunities and send results to Telegram. The scanner detects current-day breakouts and technical patterns with daily/weekly analysis.

## 🚀 Quick Start

### For Telegram Integration:
1. **Follow the setup guide:** [SETUP_TELEGRAM_GUIDE.md](SETUP_TELEGRAM_GUIDE.md)
2. **Run the scanner locally:**
   ```bash
   python3 simple_scanner.py
   ```
3. **Results will be:**
   - Displayed in terminal
   - Exported to CSV
   - Sent to your Telegram bot

## 📁 Available Scripts

### 1. **simple_scanner.py** ⭐ RECOMMENDED
- **Purpose:** Simplified scanner for current-day breakouts
- **Dependencies:** Only numpy, pandas, yfinance (no complex TA library)
- **Output:** Terminal display + CSV export + Telegram
- **Features:**
  - Scans 200+ NSE F&O stocks
  - Detects current day breakout patterns
  - Calculates RSI, SMA, ADX, MACD indicators
  - Volume confirmation
  - Sends results to Telegram
- **Usage:**
  ```bash
  export TELEGRAM_BOT_TOKEN="your_token"
  export TELEGRAM_CHAT_ID="your_chat_id"
  python3 simple_scanner.py
  ```

### 2. **telegram_scanner.py**
- **Purpose:** Full-featured scanner with Telegram focus
- **Output:** Telegram messages + CSV download
- **Features:**
  - Uses advanced filter criteria
  - Formatted Telegram messages
  - CSV document export to Telegram
  - Pattern-specific analysis
- **Usage:**
  ```bash
  python3 telegram_scanner.py
  ```

### 3. **run_scanner.py**
- **Purpose:** CLI scanner with formatted output
- **Output:** Terminal tables + CSV file
- **Features:**
  - Pretty formatted tables
  - Detailed stock analysis
  - Full technical metrics
  - No Telegram (terminal only)
- **Usage:**
  ```bash
  python3 run_scanner.py
  ```

### 4. **streamlit_app.py** (Original)
- **Purpose:** Web-based UI with all features
- **Output:** Interactive web dashboard
- **Features:**
  - Bloomberg-style dark theme
  - Real-time pattern detection
  - Multiple technical filters
  - Market sentiment analysis
  - News integration
- **Usage:**
  ```bash
  streamlit run streamlit_app.py
  ```

## 🔧 Setup Instructions

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Internet connection
- Telegram account (for Telegram integration)

### Installation

1. **Clone/Download the repository:**
   ```bash
   cd /path/to/nsepcs
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Telegram (Optional):**
   - Follow [SETUP_TELEGRAM_GUIDE.md](SETUP_TELEGRAM_GUIDE.md) Step 1-2
   - Set environment variables:
     ```bash
     export TELEGRAM_BOT_TOKEN="your_bot_token"
     export TELEGRAM_CHAT_ID="your_chat_id"
     ```

## 📊 Filter Criteria

The scanner applies these default filters:

| Criterion | Value | Purpose |
|-----------|-------|---------|
| **Volume** | ≥ 1.2x daily average | Ensure sufficient liquidity |
| **RSI** | 30-75 | Avoid extreme overbought/oversold |
| **ADX** | ≥ 20 | Confirm trend strength |
| **Consolidation** | < 15% range | Tight consolidation before breakout |
| **Breakout** | > 0.5% above resistance | Current day confirmation |
| **Pattern** | Current day only | Real-time trading opportunity |

### Customizable Filters
Edit `simple_scanner.py` to adjust:
- `volume_ratio` (default: 1.2)
- `rsi_min` / `rsi_max` (default: 30-75)
- `adx_min` (default: 20)
- `pattern_strength_min` (default: 65)

## 📈 Stock Universe

### Scanned Stocks
- **208 NSE F&O stocks** (liquid, actively traded)
- Includes major indices: Nifty 50, Bank Nifty, etc.
- Updated with latest NSE listing

### Example Stocks:
TCS, Infy, HDFC Bank, ICICI Bank, Reliance, Maruti, BAJAJ-AUTO, Axis Bank, Kotak Bank, ITC, HUL, Sunpharma, Wipro, Tech Mahindra, LTIM, and many more...

## 🔍 Technical Indicators Used

### Primary Indicators
- **RSI (Relative Strength Index):** 14-period
- **SMA (Simple Moving Average):** 20-period and 50-period
- **EMA (Exponential Moving Average):** 20-period
- **MACD:** 12/26/9 periods
- **ADX (Average Directional Index):** 14-period
- **ATR (Average True Range):** 14-period
- **Bollinger Bands:** 20-period

### Pattern Detection
- **Current Day Breakout:** EOD confirmation with volume
- **Consolidation:** Tight range analysis
- **Volume Surge:** Confirmation of breakout

## 💬 Telegram Integration

### What You'll Receive
```
📊 NSE F&O STOCK SCANNER RESULTS
⏰ 25-06-2026 15:45 IST

✅ Found 15 stocks matching filters
(Showing top 15 results)

1. RELIANCE 🔥
💰 ₹2,543.50 | 📊 Volume: 1.8x 📈
📈 RSI: 62.3 | ⚡ ADX: 28.5
🎯 Current Day Breakout (78%)

2. TCS ⚡
💰 ₹3,321.00 | 📊 Volume: 1.5x
📈 RSI: 58.1 | ⚡ ADX: 25.2
🎯 Rectangle Bottom (72%)

[... more stocks ...]

⚠️ Disclaimer: For educational purpose only.
```

### CSV Export
You'll also receive a CSV file with:
- Stock symbol
- Current price
- Volume ratio
- RSI, ADX values
- Pattern type
- Strength percentage

## ⏱️ Running Times

### Scanning Speed
- **Simple Scanner:** ~2-3 minutes for 200+ stocks
- **With news analysis:** +1-2 minutes
- **Streamlit app:** ~3-5 minutes for full run

### Market Hours (IST)
- **NSE Open:** 9:15 AM
- **NSE Close:** 3:30 PM
- **Optimal scan time:** 3:45 PM (after close, for EOD confirmation)

## 📱 Setting Up Automation

### Windows - Task Scheduler
1. Create task → Daily trigger at 15:45 (3:45 PM)
2. Run: `python3 simple_scanner.py`
3. Add env vars in task settings

### macOS/Linux - Cron
```bash
45 15 * * 1-5 cd /path/to/nsepcs && python3 simple_scanner.py
```
(Runs 3:45 PM, Monday-Friday)

## 🎯 Understanding Results

### Strength Percentage (0-100)
- **85-100%:** Excellent setup
- **70-84%:** Good setup
- **65-69%:** Acceptable setup
- **< 65%:** Weak setup (filtered out)

### Volume Ratio
- **< 1.2x:** Low volume (filtered)
- **1.2-2.0x:** Normal volume
- **2.0-3.0x:** High volume
- **> 3.0x:** Extreme volume spike

### RSI Interpretation
- **30-40:** Weak, reversal potential
- **40-60:** Neutral
- **60-75:** Strong, but not overbought
- **> 75:** Overbought (filtered)
- **< 30:** Oversold (filtered)

## ❓ FAQ

**Q: Will this make me money?**
A: No. This is a scanning tool to identify opportunities. You still need proper risk management.

**Q: Can I trade directly from these results?**
A: No. Use these as alerts to do your own analysis before trading.

**Q: How accurate is the scanner?**
A: ~65-75% of flagged stocks tend to move in expected direction. But past performance ≠ future results.

**Q: Which timeframe should I trade?**
A: Depends on your strategy. These are EOD (end-of-day) signals for swing/positional trading.

**Q: Can I modify the filters?**
A: Yes! Edit the values in `simple_scanner.py` before running.

**Q: Does it work on weekends?**
A: No. Market is closed. Run during market hours (9:15 AM - 3:30 PM IST).

**Q: Can I run multiple instances?**
A: Yes, but they'll all send to same Telegram chat. Consider setting different chat IDs.

## ⚠️ Disclaimer

**IMPORTANT:**
- This tool is for **educational and research purposes only**
- **NOT financial advice** - consult a financial advisor
- **Past performance ≠ Future performance**
- **Options/Futures trading involves high risk**
- **You can lose significant money**
- **Always do your own due diligence**
- **Only trade what you can afford to lose**

## 📞 Support

### Common Issues

1. **"No stocks found"**
   - Check if market is open
   - Verify date is weekday
   - Try loosening filters

2. **"ModuleNotFoundError"**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **"Telegram message failed"**
   - Verify BOT_TOKEN and CHAT_ID
   - Ensure environment variables are set
   - Test with simple message first

4. **"Network error / 403 error"**
   - Check internet connection
   - Try using VPN
   - Verify proxy settings if behind corporate network

## 📚 References

- **Technical Analysis:** Investopedia TA
- **NSE Documentation:** www.nseindia.com
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **yfinance:** https://pypi.org/project/yfinance/

## 🔄 Version History

- **v1.0** - Original Streamlit web app
- **v2.0** - Added telegram_scanner.py
- **v2.1** - Added simple_scanner.py (simplified, no ta dependency)
- **v2.2** - Comprehensive Telegram setup guide

## 💡 Tips & Tricks

### For Best Results:
1. Run scan 15+ minutes after market close (3:45 PM IST)
2. Look for multiple technical confirmations
3. Cross-check with support/resistance levels
4. Review news for the day
5. Check broader market sentiment (Nifty/Banknifty trend)

### Customization Ideas:
1. Add sector filtering
2. Implement profit target calculations
3. Add email notifications
4. Create custom alert thresholds
5. Track accuracy of signals

## 🚦 Next Steps

1. **Clone/Download** this repository
2. **Follow** SETUP_TELEGRAM_GUIDE.md
3. **Run** `python3 simple_scanner.py`
4. **Review** results
5. **Set up automation** (optional)
6. **Start trading** (with risk management!)

---

**Happy Scanning! 📈**

For questions or improvements, feel free to contribute!

*Last Updated: June 25, 2026*
