# 📱 NSE F&O PCS Screener - Telegram Integration Guide

## Overview
The `send_to_telegram.py` script analyzes NSE F&O stocks for Put Credit Spread opportunities and sends results directly to your Telegram account.

## Setup Instructions

### Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Send `/start`** to begin
3. **Send `/newbot`** to create a new bot
4. **Follow the prompts:**
   - Choose a name for your bot (e.g., "NSE PCS Screener")
   - Choose a username (must end with `bot`, e.g., `nse_pcs_screener_bot`)
5. **Copy the API Token** that BotFather sends you
   - Format: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`

### Step 2: Get Your Chat ID

1. **Send a message** to your newly created bot (search for it in Telegram and send any message)
2. **Get your Chat ID** using this URL in your browser (replace TOKEN with your actual token):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. **Find your Chat ID** in the response (it's in the `"id"` field under `"chat"`)
   - Example: `"id": 123456789`

### Step 3: Set Environment Variables

#### On Linux/Mac:
```bash
# Add these to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Or set them in the current session:
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvWXYZ"
export TELEGRAM_CHAT_ID="123456789"
```

#### On Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_token_here"
$env:TELEGRAM_CHAT_ID = "your_chat_id_here"
```

#### Using .env file (alternative):
Create a `.env` file in the project directory:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ
TELEGRAM_CHAT_ID=123456789
```

Then load it before running:
```bash
source .env
python send_to_telegram.py
```

### Step 4: Run the Screener

```bash
# Basic run (analyzes first 50 stocks)
python send_to_telegram.py

# Customize the analysis:
# Edit send_to_telegram.py and modify these parameters:
# - min_score=55  # Minimum score threshold (0-100)
# - max_stocks=50  # Number of stocks to analyze
```

## Script Configuration

### Parameters to Customize

Edit `send_to_telegram.py` in the `main()` function:

```python
# Configuration
min_score = 55      # Minimum PCS score threshold
max_stocks = 50     # Number of stocks to screen
```

### Score Interpretation

- **🟢 75+**: HIGH Confidence - Very bullish setup
- **🟡 60-74**: MEDIUM Confidence - Moderate bullish setup  
- **🔴 <60**: LOW Confidence - Weak or uncertain setup

## Features

✅ **Real-time Stock Analysis**
- Analyzes 200+ NSE F&O stocks
- Calculates technical indicators:
  - RSI (Relative Strength Index)
  - Momentum (5-day vs current)
  - Volume confirmation
  - SMA20 proximity

✅ **Automated Telegram Delivery**
- Sends formatted results directly to Telegram
- Includes stock symbols, scores, and current prices
- Confidence level indicators (🟢🟡🔴)

✅ **Parallel Processing**
- Analyzes multiple stocks concurrently
- Typical runtime: 30-60 seconds for 50 stocks

## Troubleshooting

### Issue: "No stocks meeting filter criteria found"
- **Cause**: Market conditions don't align with PCS setup criteria
- **Solution**: Lower the `min_score` parameter (try 45-50)

### Issue: "Telegram credentials not configured"
- **Cause**: Environment variables not set
- **Solution**: 
  ```bash
  echo $TELEGRAM_BOT_TOKEN  # Should print your token
  echo $TELEGRAM_CHAT_ID     # Should print your chat ID
  ```

### Issue: Network errors/API failures
- **Cause**: Yahoo Finance API unavailable or network issue
- **Solution**: Try again later or use a different data source

### Issue: "Failed building wheel for ta"
- **Cause**: Python package dependency issue
- **Solution**: The script now uses pure numpy/pandas calculations (already fixed)

## Running on a Schedule

### Using Cron (Linux/Mac):
```bash
# Edit crontab:
crontab -e

# Add this line (runs daily at 9:30 AM IST):
30 4 * * * /usr/bin/python3 /path/to/send_to_telegram.py > /tmp/pcs_screener.log 2>&1
```

### Using Task Scheduler (Windows):
1. Open **Task Scheduler**
2. Create **Basic Task**
3. Set trigger: Daily at 9:30 AM
4. Set action: Start program `python.exe` with arguments `send_to_telegram.py`

## Sample Output

When results are found, Telegram message will look like:

```
📊 NSE F&O PCS Screener Results
Generated: 2024-07-14 10:30:45 IST

Found 5 qualifying stocks:

1. 🟢 RELIANCE | Score: 78/100 | Price: ₹3,245.50
2. 🟢 HDFCBANK | Score: 76/100 | Price: ₹1,789.30
3. 🟡 INFY | Score: 68/100 | Price: ₹2,567.80
4. 🟡 TCS | Score: 65/100 | Price: ₹4,123.60
5. 🔴 WIPRO | Score: 58/100 | Price: ₹456.20

Green (🟢): High Confidence (75+)
Yellow (🟡): Medium Confidence (60-74)
Red (🔴): Low Confidence (<60)
```

## API References

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Yahoo Finance (yfinance)](https://github.com/ranaroussi/yfinance)
- [NSE F&O Stocks List](https://www.nseindia.com)

## Support

If you encounter issues:
1. Check environment variables are set: `env | grep TELEGRAM`
2. Verify bot token is valid via: `curl https://api.telegram.org/botTOKEN/getMe`
3. Test Chat ID by sending message to bot first
4. Check network connectivity

## Disclaimer

⚠️ **This is for educational purposes only**
- Always validate analysis before making trades
- Never risk more than you can afford to lose
- Implement proper risk management strategies
- Paper trade before live trading

---

**Happy Trading! 📈**
