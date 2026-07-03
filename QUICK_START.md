# Quick Start: Send NSE Scanner Results to Telegram

## 🎯 What You Need

1. **Telegram Bot Token** - Get from @BotFather
2. **Telegram Chat ID** - Get from @userinfobot  
3. **Python 3.8+** - Already have it

## ⚡ 3-Step Setup

### Step 1: Get Your Telegram Credentials
```
1. Chat @BotFather → /newbot → Follow prompts → Save TOKEN
2. Chat @userinfobot → /start → Note CHAT_ID (number)
```

### Step 2: Install & Run
```bash
# Navigate to project
cd /home/user/nsepcs

# Install dependencies
pip install -r requirements.txt

# Run scanner (replace TOKEN and CHAT_ID)
python run_scanner.py \
  --stocks 50 \
  --telegram "YOUR_BOT_TOKEN" "YOUR_CHAT_ID"
```

### Step 3: Get Results
✅ Results appear in Telegram instantly!

## 📊 What You Get

The scanner runs through NSE F&O stocks and sends you:

```
✅ NSE PCS Scan Results
⏰ 2026-07-03 15:30 IST
📊 Found 23 stocks

Top Stocks:
 1. RELIANCE  ₹2,645.20 Vol:2.3x Str: 78%
 2. INFOSYS   ₹1,890.50 Vol:1.8x Str: 72%
 3. TCS       ₹3,450.00 Vol:2.1x Str: 71%
 ...

All Stocks:
RELIANCE | INFOSYS | TCS | ICICIBANK | HDFCBANK | ...
```

## 🎛️ Customize Your Scan

```bash
# All 219 F&O stocks (slower, more comprehensive)
python run_scanner.py --stocks 219 --telegram "TOKEN" "CHAT_ID"

# Lower quality threshold (more results)
python run_scanner.py --min-strength 50 --telegram "TOKEN" "CHAT_ID"

# Higher volume requirement
python run_scanner.py --min-volume 2.0 --telegram "TOKEN" "CHAT_ID"

# Combine options
python run_scanner.py --stocks 100 --min-strength 60 --min-volume 1.5 --telegram "TOKEN" "CHAT_ID"
```

## 📁 Output Files

Results are also saved to CSV:
```
/tmp/scan_results_20260703_153000.csv
```

Contains: Symbol, Price, Volume, RSI, ADX, Pattern Type, Strength

## 🚀 Run Every Day

### Linux/Mac (Add to crontab)
```bash
# Every weekday at 3:30 PM IST
30 15 * * 1-5 python /home/user/nsepcs/run_scanner.py --stocks 219 --telegram "TOKEN" "CHAT_ID"
```

### Windows (Task Scheduler)
Schedule command:
```
python C:\Users\YourName\nsepcs\run_scanner.py --stocks 219 --telegram "TOKEN" "CHAT_ID"
```

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to get ticker" | Running in restricted environment (use local machine) |
| No Telegram messages | Check token & chat ID are correct |
| No stocks found | Lower --min-strength to 50 |
| Slow scanning | Reduce --stocks or run --stocks 50 |

## 📚 Full Documentation

See `TELEGRAM_SETUP.md` for complete guide including:
- Advanced filters
- Scheduling
- Custom pattern detection
- Troubleshooting

---

**Status**: ✅ Ready to use on your local machine with network access

**Next**: Provide your Telegram credentials and enjoy daily stock scans! 🚀
