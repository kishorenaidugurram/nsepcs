# NSE F&O Scanner - Quick Start Guide

## 1️⃣ First Time Setup

### A. Install Dependencies
```bash
pip install -r requirements.txt
# Or if that fails, install core packages:
pip install pandas numpy yfinance requests
```

### B. Configure Telegram (Optional but Recommended)

1. **Get Telegram Bot Token**:
   - Open Telegram
   - Search for `@BotFather`
   - Send `/newbot`
   - Save the token (example: `123456789:ABCdefGHIJKLmnoPQRstuvWXYZ`)

2. **Get Your Chat ID**:
   - Search for `@userinfobot`
   - Send `/start`
   - Note your ID (example: `987654321`)

3. **Set Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIJKLmnoPQRstuvWXYZ'
   export TELEGRAM_CHAT_ID='987654321'
   ```

## 2️⃣ Test the Scanner

### Option A: Demo Mode (Recommended First)
Uses sample data, no network required:
```bash
python scanner_demo.py
```
✅ Should show sample stocks and send test message to Telegram

### Option B: Live Scanner (With Real Data)
Fetches current market data:
```bash
python scanner_standalone.py --no-telegram
```
Then enable Telegram:
```bash
python scanner_standalone.py
```

## 3️⃣ Basic Usage

### Run Scanner Without Telegram
```bash
python scanner_standalone.py --no-telegram
```

### Run Scanner With Telegram
```bash
python scanner_standalone.py
```

### Adjust Filter Settings
```bash
# Lower volume threshold (easier criteria)
python scanner_standalone.py --min-volume 1.0

# Higher volume threshold (stricter criteria)
python scanner_standalone.py --min-volume 1.5
```

## 4️⃣ Schedule Automated Scans

### Using Cron (Linux/Mac)

Edit cron schedule:
```bash
crontab -e
```

Add one of these lines:

**Daily at 3:30 PM** (after market close in India):
```bash
30 15 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 scanner_standalone.py >> scanner.log 2>&1
```

**Every 2 hours during market** (9:30 AM - 4 PM):
```bash
0 9-16 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 scanner_standalone.py >> scanner.log 2>&1
```

**Every 4 hours** (morning, afternoon, evening):
```bash
0 9,13,17 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 scanner_standalone.py >> scanner.log 2>&1
```

View scheduled jobs:
```bash
crontab -l
```

Check logs:
```bash
tail -f scanner.log
```

## 5️⃣ Understand the Output

### Console Output
```
🚀 Starting NSE F&O Scanner...
⏰ 2026-08-17 03:44:09 IST
📊 Scanning 50 stocks...
  [50/50] HINDUNILVR...✅ Scan complete! Found 6 stocks

RELIANCE     ₹3087.45 RSI:58.3 ADX:22.8 Vol:1.45x Strength:78.5% HIGH
TCS          ₹3652.10 RSI:52.1 ADX:24.2 Vol:1.32x Strength:72.3% MEDIUM
...
💾 Saved to: scan_results_20260817_034344.json
```

### Telegram Message
Shows:
- ✅ Scan summary (total scanned, qualifying count)
- 🎯 Stock list with prices
- 📊 Technical metrics (RSI, ADX, Volume)
- 💡 Pattern names detected
- 🟢 Confidence indicators

## 6️⃣ Output Files

Each scan creates a JSON file with all results:
```bash
scan_results_20260817_034344.json
```

View latest results:
```bash
tail -f *.json
```

Or use Python:
```python
import json
with open('scan_results_LATEST.json') as f:
    data = json.load(f)
    for stock in data['qualifying_stocks']:
        print(f"{stock['symbol']}: {stock['strength']}%")
```

## 7️⃣ Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'pandas'"
**Solution**:
```bash
pip install pandas numpy yfinance
```

### Problem: "Telegram credentials not found"
**Solution**: Set environment variables
```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'

# Verify it's set:
echo $TELEGRAM_BOT_TOKEN
```

### Problem: "Failed to get ticker" / Network errors
**Solution**: Try demo mode
```bash
python scanner_demo.py  # Uses sample data, no network needed
```

### Problem: "No stocks met the criteria today"
**Possible causes**:
- Market doesn't have qualifying patterns today (normal)
- Filters too strict
- Network issues

**Solutions**:
- Run demo to verify setup
- Lower min-volume: `--min-volume 1.0`
- Check network: `ping google.com`

## 8️⃣ Common Commands Cheatsheet

```bash
# Test demo mode
python scanner_demo.py

# Run without Telegram
python scanner_standalone.py --no-telegram

# Run with Telegram
python scanner_standalone.py

# Lower filters
python scanner_standalone.py --min-volume 1.0

# View help
python scanner_standalone.py --help

# Check cron jobs
crontab -l

# Edit cron jobs
crontab -e

# View logs
tail -f scanner.log

# See all scan results
ls -lh scan_results_*.json
```

## 9️⃣ Important Notes

⚠️ **Disclaimers**:
- This is NOT financial advice
- Stocks identified are technical setups, not buy signals
- Always do your own research (fundamental analysis)
- Never trade without risk management
- Paper trade first before live trading

📊 **Scanner Basics**:
- Looks for bullish technical patterns
- Checks volume above average (institutional interest)
- Calculates trend strength (RSI, ADX)
- Suitable for Put Credit Spread strategies

## 🔟 Getting Help

**For detailed information**:
- `SCANNER_SETUP.md` - Comprehensive setup guide
- `SCANNER_SUMMARY.md` - Full implementation details
- `README.md` - Project overview

**Issues?**:
1. Try demo mode first: `python scanner_demo.py`
2. Check logs: `tail -f scanner.log`
3. Test network: `python scanner_standalone.py --no-telegram`
4. Review SCANNER_SETUP.md troubleshooting section

---

## 🚀 TL;DR - Just Get Started

```bash
# Step 1: Test with demo
python scanner_demo.py

# Step 2: Enable Telegram (optional)
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'

# Step 3: Run scanner
python scanner_standalone.py

# Step 4: Schedule with cron (optional)
crontab -e
# Add: 30 15 * * 1-5 cd /home/user/nsepcs && python scanner_standalone.py
```

**That's it! Scanner is ready to use.** 📈
