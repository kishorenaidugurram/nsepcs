# 🚀 Quick Start: Telegram PCS Scanner

Get your NSE PCS analysis delivered to Telegram in 5 minutes!

## 5-Minute Setup

### Step 1: Get Telegram Credentials (2 min)

**Create a Bot:**
1. Open Telegram → Search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts, name your bot
4. ✅ Save the **Bot Token** (looks like: `123456:ABC-DEF...`)

**Get Your Chat ID:**
1. Search for **@userinfobot** 
2. Send any message
3. ✅ Save your **User ID/Chat ID** (looks like: `123456789`)

### Step 2: Configure Credentials (1 min)

**Option A: Copy environment template**
```bash
cp .env.example .env
# Edit .env with your credentials
nano .env
```

**Option B: Set environment variables**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Step 3: Run the Scanner (2 min)

```bash
# Install dependencies
pip install -r requirements.txt

# Test the scanner
python3 telegram_pcs_scanner.py RELIANCE.NS INFY.NS

# Use interactive setup
bash setup_telegram.sh
```

## Done! 🎉

Your scanner is ready. Results will be sent to your Telegram.

---

## Common Tasks

### Run Scanner Now
```bash
python3 telegram_pcs_scanner.py
```

### Scan Specific Stocks
```bash
python3 telegram_pcs_scanner.py RELIANCE.NS INFY.NS HDFCBANK.NS
```

### Set Up Daily Automation (Cron)
```bash
# Run the setup helper
bash setup_telegram.sh

# Or manually add to crontab
# Runs at 9:15 AM Monday-Friday
crontab -e
# Add: 15 9 * * 1-5 cd /path/to/nsepcs && python3 telegram_pcs_scanner.py
```

### View Last Results
```bash
cat /tmp/pcs_scan_results.json | python3 -m json.tool
```

### View Logs (if using cron)
```bash
tail -f logs/pcs_scanner.log
```

---

## Need Help?

| Issue | Solution |
|-------|----------|
| "Telegram not installed" | `pip install python-telegram-bot` |
| "Credentials not set" | Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |
| "No stocks found" | Lower filter thresholds or check market hours |
| "Network error" | Check internet and proxy settings |

For detailed help: See **[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)**

---

## What Happens?

1. **Scan Starts** → Analyzes stocks for PCS opportunities
2. **Results Filtered** → Keeps only strong patterns
3. **Telegram Sent** → Formatted message with top stocks
4. **JSON Saved** → Results stored in `/tmp/pcs_scan_results.json`

### Sample Output

```
📊 NSE F&O PCS Scanner Results
⏰ 2026-07-31 09:30:00 IST
📈 Found: 5 stocks

1. RELIANCE.NS
   💪 Strength: 78/100
   🎯 PCS Fit: 85%
   💹 Price: ₹2450.50
   📊 RSI: 58.2, ADX: 28.5

2. INFY.NS
   💪 Strength: 72/100
   🎯 PCS Fit: 82%
   💹 Price: ₹1850.25
   📊 RSI: 52.1, ADX: 24.3

⚠️ Not financial advice. Trade at your own risk.
```

---

## Customization

### Edit Filter Thresholds
```bash
# In telegram_pcs_scanner.py, change:
DEFAULT_FILTERS = {
    'min_pattern_strength': 60,  # Lower = more stocks
    'min_pcs_suitability': 80,   # Lower = more stocks
    'rsi_min': 45,
    'rsi_max': 70,
    # ... more options
}
```

### Add More Stocks
```bash
# In telegram_pcs_scanner.py, edit STOCK_LIST:
STOCK_LIST = [
    'RELIANCE.NS',
    'INFY.NS',
    'TCS.NS',
    # Add more...
]
```

### Run Multiple Times Daily
```bash
# Edit setup in crontab
crontab -e

# Add multiple lines:
15 9 * * 1-5 cd /path && python3 telegram_pcs_scanner.py  # 9:15 AM
0 14 * * 1-5 cd /path && python3 telegram_pcs_scanner.py  # 2:00 PM (pre-close)
```

---

## ⚠️ Important Notes

1. **Not Financial Advice** - Use as a screening tool only
2. **Always Paper Trade First** - Test before live trading
3. **Secure Credentials** - Never commit `.env` to git
4. **Market Hours Only** - NSE: 9:15 AM - 3:30 PM IST
5. **Verify Signals** - Cross-check with your analysis

---

## Next Steps

✅ **Complete Setup**
```bash
bash setup_telegram.sh
```

✅ **Test the Scanner**
```bash
python3 telegram_pcs_scanner.py
```

✅ **Set Up Automation**
```bash
crontab -e  # Add the cron job
```

✅ **Monitor Results**
```bash
tail -f logs/pcs_scanner.log
```

---

Happy Trading! 🚀

For detailed documentation: [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
