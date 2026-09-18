# Quick Start - PCS Scanner with Telegram

## TL;DR - Get Started in 2 Minutes

### 1. Set Up Telegram (Interactive Helper)
```bash
cd /home/user/nsepcs
bash setup_telegram.sh
```
This will guide you through creating a bot and configuring Telegram.

### 2. Run Your First Scan
```bash
cd /home/user/nsepcs
source .env  # Load your Telegram credentials
./scan_and_notify.sh
```

### 3. Set Up Daily Automation (Optional)
```bash
# Edit your crontab
crontab -e

# Add this line (runs at 9:30 AM IST on weekdays):
30 9 * * 1-5 cd /home/user/nsepcs && source .env 2>/dev/null && ./scan_and_notify.sh >> /tmp/pcs_scan_cron.log 2>&1
```

That's it! You'll now receive PCS stock alerts on Telegram automatically.

---

## What You Get

Every time the scanner runs, you'll receive a Telegram message like:

```
🎯 NSE F&O PCS SCAN RESULTS
2024-09-18 09:30 IST

🟢 HIGH Confidence (5):
  • RELIANCE: 82.3%
  • TCS: 78.9%
  • HDFCBANK: 76.1%
  ... +2 more

🟡 MEDIUM Confidence (8):
  • INFY: 68.5%
  ... +7 more

Total: 13 stocks
```

Plus a CSV file with detailed results saved to `/tmp/`.

---

## How It Works

1. **Analyzes** 60 top liquid NSE F&O stocks
2. **Calculates** PCS compatibility score for each (0-100%)
3. **Categorizes** by confidence level:
   - 🟢 HIGH (75%+) - Best opportunities
   - 🟡 MEDIUM (60-74%) - Good opportunities  
   - 🔴 LOW (<60%) - Speculative

4. **Sends results** to your Telegram instantly
5. **Saves CSV** for detailed analysis

---

## Files

| File | Purpose |
|------|---------|
| `run_pcs_scan.py` | Core scanner logic (Python) |
| `scan_and_notify.sh` | Automation wrapper (Shell) |
| `setup_telegram.sh` | Interactive setup helper |
| `QUICKSTART.md` | This file - Get started fast |
| `AUTOMATED_SCANNING.md` | Complete automation guide |
| `TELEGRAM_SETUP.md` | Detailed Telegram setup |
| `.env` | Your credentials (created by setup) |

---

## Troubleshooting

### "requests module not found"
```bash
pip install requests
```

### "No message received"
```bash
# Test Telegram manually
python3 -c "
import requests, os
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
if token and chat_id:
    requests.post(f'https://api.telegram.org/bot{token}/sendMessage', 
                  json={'chat_id': chat_id, 'text': 'Test'})
    print('Message sent!')
"
```

### "Cron job not running"
```bash
# View cron logs
tail -f /tmp/pcs_scan_cron.log

# Test manually
cd /home/user/nsepcs && source .env && ./scan_and_notify.sh
```

---

## Need More Info?

- **Detailed setup**: Read `AUTOMATED_SCANNING.md`
- **Telegram issues**: See `TELEGRAM_SETUP.md`
- **Scanner explanation**: Check main `README.md`

---

## Quick Commands

```bash
# Run a manual scan
./scan_and_notify.sh

# Load credentials
source .env

# View your Telegram config
echo "Token: $TELEGRAM_BOT_TOKEN"
echo "Chat ID: $TELEGRAM_CHAT_ID"

# Check cron jobs
crontab -l

# View last 20 scan results
tail -20 /tmp/pcs_scan_*.csv

# View cron logs
tail -100 /tmp/pcs_scan_cron.log
```

---

**Ready?** Run `bash setup_telegram.sh` and start receiving alerts! 🚀

