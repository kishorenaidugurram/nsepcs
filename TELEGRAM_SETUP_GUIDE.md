# NSE F&O PCS Scanner - Telegram Setup Guide

## Overview
This guide will help you set up the automated stock scanner to send results to your Telegram chat.

## Prerequisites
- Telegram account (free)
- Python 3.7+
- Stock scanner dependencies (already in requirements.txt)

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start the chat** with BotFather
3. **Send command**: `/newbot`
4. **Follow prompts**:
   - Give your bot a name (e.g., "NSE Scanner Bot")
   - Give your bot a username (e.g., "nse_scanner_bot")
5. **Copy the API Token** - This is your `TELEGRAM_BOT_TOKEN`
   - Example: `123456789:ABCdefGHIjklmnoPQRstuvwxyz123456789`

## Step 2: Get Your Chat ID

1. **Open Telegram** and search for `@userinfobot`
2. **Start the chat** with this bot
3. **Send** any message (or just /start)
4. **Copy the ID** - This is your `TELEGRAM_CHAT_ID`
   - Example: `1234567890`

Alternatively, you can:
- Send any message to your bot from Step 1
- Use: `curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
- Look for `"chat":{"id":XXXX}`

## Step 3: Set Environment Variables

### On Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvwxyz123456789"
export TELEGRAM_CHAT_ID="1234567890"
```

### On Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklmnoPQRstuvwxyz123456789"
$env:TELEGRAM_CHAT_ID = "1234567890"
```

### Permanent Setup (Linux/Mac):
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

Then run: `source ~/.bashrc` (or `.zshrc`)

### Permanent Setup (Python - Recommended):
Create a `.env` file in the project root:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
pip install python-telegram-bot requests
```

## Step 5: Run the Scanner

### Quick Scan (50 stocks):
```bash
python3 run_scanner_telegram_complete.py
```

### Full Scan (208 stocks):
Edit the script and change line:
```python
scanner.run(num_stocks=208, send_telegram=True)
```

### With Logging:
```bash
python3 run_scanner_telegram_complete.py 2>&1 | tee scanner.log
```

## Step 6: Schedule Automated Runs

### Using Cron (Linux/Mac):

1. **Edit crontab**:
   ```bash
   crontab -e
   ```

2. **Add a schedule** (example: daily at 9:30 AM):
   ```cron
   30 9 * * 1-5 cd /path/to/nsepcs && python3 run_scanner_telegram_complete.py
   ```

3. **Common schedules**:
   - `30 9 * * 1-5` - Weekdays at 9:30 AM
   - `30 9,15 * * 1-5` - Weekdays at 9:30 AM and 3:30 PM
   - `0 6 * * *` - Daily at 6:00 AM

### Using Windows Task Scheduler:

1. **Open Task Scheduler**
2. **Create Basic Task**
3. **Set trigger** (e.g., Daily at 9:30 AM)
4. **Set action**:
   - Program: `python.exe`
   - Arguments: `/full/path/to/run_scanner_telegram_complete.py`
   - Start in: `/full/path/to/nsepcs/`

### Using Python APScheduler (Cross-platform):

```python
from apscheduler.schedulers.background import BackgroundScheduler
from run_scanner_telegram_complete import StockScannerWithTelegram

def scheduled_scan():
    scanner = StockScannerWithTelegram()
    scanner.run(num_stocks=50)

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_scan, 'cron', hour=9, minute=30, day_of_week='mon-fri')
scheduler.start()

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
```

## Step 7: Customize Scanner Parameters

Edit `run_scanner_telegram_complete.py` and modify `create_default_config()`:

```python
def create_default_config(self) -> Dict:
    return {
        'rsi_min': 30,           # Minimum RSI threshold
        'rsi_max': 80,           # Maximum RSI threshold
        'adx_min': 15,           # Minimum ADX strength
        'min_volume_ratio': 1.2, # Volume threshold multiplier
        'pattern_strength_min': 65,  # Minimum pattern strength %
        # ... more parameters
    }
```

## Telegram Message Features

The scanner will send you:
1. **Summary Report** - Overview of all stocks found
2. **Top 10 Stocks** - Ranked by pattern strength
3. **Detailed Metrics** - Price, RSI, ADX, Volume ratios
4. **Pattern Information** - Type, confidence, success rate
5. **PCS Fit Score** - Suitability for Put Credit Spreads

### Example Message:
```
📊 NSE F&O PCS Scanner Report
⏰ 2026-08-15 09:45 IST

🎯 Summary:
📈 Stocks Found: 12
💪 Avg Strength: 78%

🔝 Top 10 Stocks:
1. 🟢 RELIANCE
   💰 ₹2,345.50 | 💪 92% | HIGH
   📊 Current Day Breakout

2. 🟡 TCS
   💰 ₹3,456.75 | 💪 78% | MEDIUM
   📊 Cup and Handle
   
... and more
```

## Troubleshooting

### Message not sending?
1. **Check token and chat ID**:
   ```bash
   python3 -c "import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"
   python3 -c "import os; print(os.getenv('TELEGRAM_CHAT_ID'))"
   ```

2. **Test bot connectivity**:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
   ```

3. **Verify chat ID**:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage?chat_id=<YOUR_CHAT_ID>&text=Test"
   ```

### Scanner not finding stocks?
- Adjust RSI range to be wider (30-80)
- Lower ADX minimum to 15
- Reduce pattern strength threshold to 60%
- Increase volume ratio tolerance

### Performance issues?
- Reduce `num_stocks` parameter (start with 50)
- Run during market hours
- Check network connection

## Advanced Configuration

### Multiple Chat Recipients:
```python
notifier1 = TelegramNotifier(bot_token="token1", chat_id="chat1")
notifier2 = TelegramNotifier(bot_token="token2", chat_id="chat2")

notifier1.send_stock_results(results, config)
notifier2.send_stock_results(results, config)
```

### Conditional Notifications:
```python
if len(results) > 5:
    notifier.send_stock_results(results, config)
    notifier.send_message("✅ Found 5+ high-confidence patterns!")
else:
    notifier.send_message("⚠️ Less than 5 patterns found. Market may be quiet.")
```

## Files Created

- `run_scanner_telegram_complete.py` - Main scanner with Telegram integration
- `scan_results.json` - Results saved after each run
- `scanner.log` - Log file (if logging enabled)

## Support

For issues with:
- **Telegram Bot**: Visit [Telegram Bot Documentation](https://core.telegram.org/bots)
- **Scanner Logic**: Check the main `streamlit_app.py` file
- **Network Issues**: Ensure HTTPS_PROXY is properly configured

## Security Notes

- ✅ Keep your BOT_TOKEN and CHAT_ID private
- ✅ Don't commit `.env` file to git
- ✅ Use environment variables for credentials
- ✅ Rotate tokens periodically
- ❌ Never share your tokens in public places

## Next Steps

1. ✅ Get Telegram Bot Token from @BotFather
2. ✅ Get Chat ID from @userinfobot
3. ✅ Set environment variables
4. ✅ Test with: `python3 run_scanner_telegram_complete.py`
5. ✅ Schedule with cron or Task Scheduler
6. ✅ Monitor results and adjust parameters

Happy Trading! 📈
