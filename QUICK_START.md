# 🚀 Quick Start - Telegram Bot Setup (5 Minutes)

## The 5-Minute Setup

### 1️⃣ Create Your Bot (2 minutes)
```bash
1. Open Telegram → Search: @BotFather
2. Send: /newbot
3. Choose a bot name: "NSE PCS Screener"
4. Choose bot username: "nse_pcs_screener_bot" 
5. COPY your TOKEN → 123456789:ABCdefGHIjklmnoPQRstuvWXYZ
```

### 2️⃣ Get Your Chat ID (2 minutes)
```bash
1. Find your bot in Telegram and send it a message: "hi"
2. Open this in your browser (paste your TOKEN):
   https://api.telegram.org/bot123456789:ABCdefGHIjklmnoPQRstuvWXYZ/getUpdates
3. FIND your chat ID → Look for "id": 987654321
```

### 3️⃣ Set Environment Variables (1 minute)
```bash
# Linux/Mac - Add to ~/.bashrc or ~/.zshrc:
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvWXYZ"
export TELEGRAM_CHAT_ID="987654321"

# Then reload:
source ~/.bashrc  # or ~/.zshrc

# Windows PowerShell:
$env:TELEGRAM_BOT_TOKEN = "your_token"
$env:TELEGRAM_CHAT_ID = "your_chat_id"
```

### 4️⃣ Run the Screener
```bash
python send_to_telegram.py
```

✅ Done! Results will be sent to your Telegram!

---

## What the Script Does

```
Analyzes 50 NSE F&O stocks → Calculates PCS scores → Sends to Telegram
```

### Filter Criteria Applied:
- **RSI Score**: Looks for RSI 40-75 range (sweet spot 50-65)
- **Volume**: Current volume > average volume
- **Momentum**: Price trending up (5-day comparison)
- **Support**: Close >= 20-day moving average

### Output Format:
```
📊 NSE F&O PCS Screener Results
Generated: 2024-07-14 10:30:45 IST

Found X qualifying stocks:

1. 🟢 STOCK1 | Score: 78/100 | Price: ₹1,234.50
2. 🟡 STOCK2 | Score: 65/100 | Price: ₹5,678.90
```

---

## Customization

Edit `send_to_telegram.py` in the `main()` function:

```python
# Change these values:
min_score = 55      # Lower = more stocks (try 45-60)
max_stocks = 50     # Number of stocks to check (max 200+)
```

---

## Verify Setup Works

```bash
# Test 1: Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Test 2: Check bot token is valid (should return bot info)
curl https://api.telegram.org/botYOUR_TOKEN/getMe

# Test 3: Run the screener
python send_to_telegram.py
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| "Telegram credentials not configured" | Set env vars: `export TELEGRAM_BOT_TOKEN=...` |
| "No stocks meeting criteria" | Lower `min_score` to 45-50 |
| Network errors (curl 403) | Reload terminal or try again later |
| Message not received | Check you sent message to bot first, then got Chat ID |

---

## Schedule It (Optional)

### Run Daily at 9:30 AM:

**Linux/Mac (Crontab):**
```bash
crontab -e
# Add: 30 4 * * * python3 /path/to/send_to_telegram.py
```

**Windows (Task Scheduler):**
1. Search: "Task Scheduler"
2. Create Basic Task → Set time 9:30 AM
3. Action: Run `python.exe` with args `send_to_telegram.py`

---

## Next Steps

✅ Setup complete!

1. **First Run**: `python send_to_telegram.py` to test
2. **Customize**: Edit `min_score` if needed
3. **Schedule**: Set up daily runs (optional)
4. **Monitor**: Check Telegram daily for opportunities

---

**Questions?** See `TELEGRAM_SETUP.md` for detailed guide.

**Ready to trade?** Remember: This is for analysis only. Always do your own research! 📈
