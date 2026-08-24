# Quick Start Guide - NSE Stock Analysis with Telegram

## 5-Minute Setup

### Step 1: Create Telegram Bot (2 minutes)

1. Open Telegram
2. Search for **@BotFather**
3. Send `/newbot`
4. Choose a name (e.g., "NSE Stock Analyzer")
5. Choose a username (must end in "bot", e.g., "nse_stock_bot")
6. **Copy the Bot Token** - looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID (1 minute)

1. Search for **@userinfobot** in Telegram  
2. Send it any message
3. **Copy your Chat ID** - it's a number

### Step 3: Configure (2 minutes)

**Option A: Using Environment Variables**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_from_step_1"
export TELEGRAM_CHAT_ID="your_chat_id_from_step_2"
```

**Option B: Using .env File**
```bash
cp .env.example .env
# Edit .env and fill in your token and chat ID
nano .env
```

### Step 4: Run!

```bash
python3 run_analysis.py
```

That's it! The script will:
- Analyze 200+ NSE F&O stocks
- Find those meeting the criteria
- Send results to your Telegram bot (if credentials are set)
- Save full results to `/tmp/stock_analysis_results.json`

## What You Get

📊 **Results like:**
- Stock symbol
- Current price
- RSI (momentum indicator)
- ADX (trend strength)
- Volume ratio vs average
- Analysis date/time

## Filter Criteria

The script automatically filters for stocks that have:
- ✅ **Healthy momentum** (RSI 30-70)
- ✅ **Strong trend** (ADX 20+)
- ✅ **Good liquidity** (1.5x+ average volume)
- ✅ **Solid support** (price above 20-day moving average)

## Scheduling (Optional)

To run automatically every morning:

### Linux/Mac with Crontab
```bash
# Add this to crontab (crontab -e)
# Run daily at 9:30 AM on weekdays
30 9 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="xxx" TELEGRAM_CHAT_ID="yyy" python3 run_analysis.py
```

### Windows Task Scheduler
```batch
# Create batch file: run_stock_analysis.bat
cd C:\Users\YourUser\nsepcs
set TELEGRAM_BOT_TOKEN=your_bot_token
set TELEGRAM_CHAT_ID=your_chat_id
python run_analysis.py
```

Then schedule it in Task Scheduler.

## Troubleshooting

### ❌ "No module named 'pandas'"
```bash
pip install -r requirements.txt
```

### ❌ "Telegram message not sending"
- Verify bot token is correct
- Verify chat ID is correct  
- Ensure bot is not rate-limited (wait a few minutes)
- Check bot is added to your chat

### ❌ "Network error"
- Ensure internet connection
- Yahoo Finance may be temporarily down
- Wait a few minutes and try again

### ❌ "No stocks found"
- This is normal if markets are closed
- Try on a trading day during market hours
- Adjust filter criteria in code if needed

## Need Help?

See detailed guides:
- **TELEGRAM_SETUP.md** - Detailed Telegram configuration
- **SCHEDULED_TASK_SUMMARY.md** - Technical overview
- **run_analysis.py** - Code comments and implementation details

## Files

- `run_analysis.py` - Main automation script
- `TELEGRAM_SETUP.md` - Complete setup guide
- `QUICKSTART.md` - This file
- `.env.example` - Example configuration
- `requirements.txt` - Python dependencies
- `streamlit_app.py` - Interactive dashboard (run with `streamlit run streamlit_app.py`)

---

**That's it!** You now have automated NSE stock analysis reporting to Telegram. 🎉

For more details, see TELEGRAM_SETUP.md
