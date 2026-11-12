# Quick Start Guide - NSE PCS Scanner

## 30-Second Setup

### 1. Get Telegram Bot Token
- Open Telegram
- Search for **@BotFather** and start chat
- Send `/newbot` and follow instructions
- Copy the **token** you receive

### 2. Get Your Chat ID
- Search for **@userinfobot** in Telegram
- It shows you your **User ID**
- Start a chat with your new bot
- Send any message to it

### 3. Set Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="123456789"
```

### 4. Run Scanner
```bash
cd /home/user/nsepcs
python3 run_scanner_simple.py
```

Done! Results will appear in Telegram.

---

## Daily Automated Scans

### Setup Cron Job
```bash
crontab -e
```

Add this line (runs at 3:30 PM weekdays):
```
30 15 * * 1-5 export TELEGRAM_BOT_TOKEN=your_token && export TELEGRAM_CHAT_ID=your_id && python3 /home/user/nsepcs/run_scanner_simple.py >> /tmp/scanner.log 2>&1
```

Save and exit. Done!

---

## What the Scanner Does

✅ **Analyzes** 50 NSE F&O stocks  
✅ **Detects** bullish technical patterns  
✅ **Filters** based on:
   - Volume surge (>1.5x average)
   - Price breakout
   - RSI levels
   - Trend strength (ADX)

✅ **Sends** top results to Telegram

**Output:** Telegram message + JSON file

---

## Telegram Message Example

```
NSE F&O PCS Scanner Results
2026-11-12 15:30 IST

Found: 8 stocks

1. RELIANCE
   Price: ₹3250.50
   RSI: 65 | ADX: 28
   Volume: 2.15x | Strength: 82%

2. INFY
   Price: ₹2850.25
   RSI: 62 | ADX: 26
   Volume: 1.85x | Strength: 76%

... (up to 15 stocks)
```

---

## Troubleshooting

**Q: No stocks found**
- Run during market hours (9:15 AM - 3:30 PM IST)
- Market may be closed
- All stocks may not meet criteria

**Q: Telegram not receiving messages**
```bash
# Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Should show your token and ID (not blank)
```

**Q: Error accessing data**
- Market may be closed
- Network connectivity issue
- Try again in 5 minutes

---

## Commands

```bash
# Run manually
python3 /home/user/nsepcs/run_scanner_simple.py

# View latest results
cat /tmp/pcs_results_*.json | python3 -m json.tool

# Check scheduled runs
crontab -l

# View scanner logs
tail /tmp/scanner.log

# Test Telegram connection
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe
```

---

## Advanced Settings

Edit `run_scanner_simple.py` to change:

```python
# Line 150 - Number of stocks to scan
stocks = [...].  # Change to scan more/fewer stocks

# Line 200 - Minimum strength filter
min_strength=65  # Lower = more stocks, Higher = better quality

# Line 235+ - Change technical parameters
```

---

## Important Disclaimers

⚠️ **This is NOT investment advice**
- Use for educational/research purposes only
- Past patterns ≠ future results
- Always verify before trading
- Use stop-losses
- Start with paper trading
- Risk only what you can afford to lose

---

## Need Help?

1. Read `TELEGRAM_SETUP.md` for detailed setup
2. Read `SCANNER_IMPLEMENTATION_SUMMARY.md` for technical details
3. Check logs: `/tmp/scanner.log`
4. Verify credentials: `echo $TELEGRAM_BOT_TOKEN`

---

**That's it! Happy trading!** 📈
