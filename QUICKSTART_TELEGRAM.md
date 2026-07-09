# 🚀 Quick Start: Stock Scanner with Telegram

## 30-Second Setup

```bash
# 1. Copy config template
cp telegram_config.example.json telegram_config.json

# 2. Edit with your Telegram bot token & chat ID
# (See "Get Your Credentials" below)

# 3. Test the setup
python test_telegram_config.py

# 4. Run the scanner
python telegram_scanner.py
```

## Get Your Credentials (5 minutes)

### Step 1: Create Telegram Bot
1. Open Telegram, find **@BotFather**
2. Send `/newbot`
3. Follow prompts, choose a name (e.g., "NSE Stock Scanner")
4. Choose a username ending in "bot" (e.g., "nse_stock_bot")
5. **Save the token** BotFather gives you

### Step 2: Get Your Chat ID
1. Open your bot in Telegram
2. Send it any message (e.g., `/start`)
3. Visit this URL in your browser:
   ```
   https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates
   ```
   (Replace `{YOUR_TOKEN}` with your actual token)
4. Find your Chat ID in the JSON response (look for `"id": 123456789`)

### Step 3: Configure Scanner
Edit `telegram_config.json`:
```json
{
  "telegram": {
    "bot_token": "YOUR_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  }
}
```

## Run Now

```bash
# Test your configuration
python test_telegram_config.py

# Run the scanner
python telegram_scanner.py
```

You'll receive a message on Telegram with matching stocks!

## Schedule It (Optional)

### Run Daily After Market Close
**Linux/Mac:**
```bash
crontab -e
# Add this line:
0 16 * * 1-5 cd /path/to/nsepcs && python telegram_scanner.py
```

**Windows:**
- Open Task Scheduler
- Create Basic Task
- Set trigger to daily at desired time
- Set action to run `python telegram_scanner.py`

## Customize Filters

Edit `telegram_config.json` under `"scanner"`:

```json
{
  "scanner": {
    "rsi_min": 30,           # Lower RSI threshold
    "rsi_max": 70,           # Upper RSI threshold
    "adx_min": 20,           # Minimum trend strength
    "pattern_strength_min": 65,  # Higher = better patterns
    "universe": "Nifty 50",  # Which stocks to scan
    "pattern_filters": {
      "current_day_breakout": true,
      "cup_and_handle": true,
      "flat_base": true,
      "double_bottom": true
    }
  }
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Config file not found | Run: `cp telegram_config.example.json telegram_config.json` |
| Invalid token/chat ID | Double-check credentials from @BotFather and getUpdates |
| No stocks matched | Lower `pattern_strength_min` to 55, expand RSI range |
| No message from test | Bot needs permission to send - check Telegram bot settings |

## Documentation

- **Full Setup Guide:** See `TELEGRAM_SETUP.md`
- **Implementation Details:** See `IMPLEMENTATION_SUMMARY.md`
- **For Issues:** Run `python test_telegram_config.py` for diagnostic info

---

**You're all set!** Run `python telegram_scanner.py` to start scanning.

Next: Read `TELEGRAM_SETUP.md` for advanced configuration options.
