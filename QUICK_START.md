# Quick Start: Telegram PCS Scanner

Get your PCS screening results sent to Telegram in 5 minutes.

## 1️⃣ Create Telegram Bot (2 minutes)

```bash
# Open Telegram and chat with @BotFather
# Send: /newbot
# Follow prompts
# Copy your TOKEN (looks like: 123456:ABC-xyz...)
# Save it
```

## 2️⃣ Get Chat ID (1 minute)

```bash
# Replace TOKEN with your bot token
curl "https://api.telegram.org/botTOKEN/getUpdates"

# Find: "chat":{"id":123456789}
# Copy the number (chat ID)
```

## 3️⃣ Set Environment Variables (1 minute)

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-xyz..."
export TELEGRAM_CHAT_ID="123456789"
```

## 4️⃣ Run Scanner (1 minute)

```bash
cd /home/user/nsepcs
python3 run_scanner_telegram.py
```

✅ **Done!** You'll receive a message with today's PCS opportunities.

---

## Want to Run Daily?

### Linux/Mac (Cron)

```bash
# Add to crontab (run at 9:30 AM daily)
30 9 * * * export TELEGRAM_BOT_TOKEN="your_token"; export TELEGRAM_CHAT_ID="your_chat_id"; /usr/bin/python3 /home/user/nsepcs/run_scanner_telegram.py
```

### Windows (Task Scheduler)

1. Right-click "This PC" → Manage → Task Scheduler
2. Create Basic Task
3. Name: "PCS Scanner"
4. Trigger: Daily at 9:30 AM
5. Action: Run program: `python3.exe`
6. Arguments: `C:\path\to\run_scanner_telegram.py`

---

## Results You'll Get

📊 Telegram message with top stocks + CSV file

```
RELIANCE | ₹3250 | 82% | RSI:58 | Vol:1.8x
TCS      | ₹3750 | 78% | RSI:62 | Vol:2.1x
INFY     | ₹4100 | 71% | RSI:55 | Vol:1.5x
```

Plus a CSV file with full details.

---

## Customize Filters

Edit `run_scanner_telegram.py` line ~330:

```python
filters = {
    'min_volume_ratio': 1.2,        # Volume filter
    'rsi_min': 40, 'rsi_max': 75,  # RSI range
    'adx_min': 15,                  # Trend strength
    'pattern_strength_min': 65,     # Quality threshold
}
```

---

## Need Help?

See `TELEGRAM_SETUP.md` for detailed setup, troubleshooting, and customization.

---

**Note:** Results during market hours (9:15 AM - 3:30 PM IST)
