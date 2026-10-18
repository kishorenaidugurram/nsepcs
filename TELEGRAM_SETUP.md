# PCS Scanner - Telegram Integration Setup

## Overview

The `pcs_scanner_standalone.py` script runs the NSE F&O PCS scanner analysis and sends qualifying stocks to Telegram automatically.

## Prerequisites

1. **Python 3.7+**
2. **Telegram Bot Token** - Create one via BotFather
3. **Telegram Chat ID** - Your personal Telegram chat ID

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat and use `/newbot`
3. Follow the instructions to create a new bot
4. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ-abc123`)

### 3. Get Your Chat ID

1. Search for `@getidsbot` on Telegram
2. Start a chat with the bot
3. It will display your Chat ID (a long number)

Alternatively:
1. Send any message to your new bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `chat.id` in the response

## Configuration

Set environment variables for the bot credentials:

### Linux/Mac
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Windows (Command Prompt)
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

### Windows (PowerShell)
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Docker/CI Environments

Add to your environment configuration or secrets:
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Running the Scanner

### One-time Run
```bash
python3 pcs_scanner_standalone.py
```

### Scheduled Runs (Linux/Mac)

Add to crontab to run daily at 9:15 AM IST:
```bash
crontab -e
```

Add this line:
```cron
15 3 * * * cd /path/to/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 pcs_scanner_standalone.py >> logs/scanner.log 2>&1
```

### Scheduled Runs (Windows)

Use Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily at specific time)
4. Action: `python3 pcs_scanner_standalone.py`
5. Set working directory and environment variables

## How It Works

The scanner:
1. **Fetches Stock Data** - Downloads 3-month price data for 50 Nifty stocks
2. **Calculates Indicators** - RSI, SMA, EMA, MACD, Bollinger Bands, ADX
3. **Detects Patterns** - Identifies bullish patterns and setups
4. **Filters Results** - Keeps stocks with pattern strength >= 50/100
5. **Sends to Telegram** - Posts results to your Telegram chat

### Filter Criteria

- **Minimum Pattern Strength**: 50/100
- **RSI Range**: 30-80
- **ADX Minimum**: 15 (trend strength)
- **Patterns Detected**:
  - Breakout patterns
  - Support & Bullish indicators
  - MACD bullish crossover
  - Bounce setups

## Output

### Telegram Message Format

```
✅ PCS Scan Results - 2024-01-15 09:15

📊 Found 8 stocks:

1. INFY.NS
   Support & Bullish (Strength: 72/100)
   Price: ₹1,234.50 | RSI: 58.3

2. TCS.NS
   MACD Bullish (Strength: 68/100)
   Price: ₹5,678.90 | RSI: 62.1

... +6 more
```

### File Output

If Telegram is not configured, results are saved to:
- `scan_results_YYYYMMDD_HHMMSS.json`

## Troubleshooting

### Bot Token Error
- Check token format (should be 10 digits:long_string)
- Verify token hasn't expired
- Create a new bot if needed

### Chat ID Error
- Ensure you've sent at least one message to your bot
- Use `@getidsbot` to verify your Chat ID
- Chat ID should be a negative number for groups, positive for personal

### Network Errors
- Check internet connection
- Yahoo Finance might be blocked in your region
- Try using a VPN

### No Results Found
- Market might be closed
- Stocks might not meet filter criteria
- Check logs for data fetch errors

## Advanced Configuration

Edit `pcs_scanner_standalone.py` to customize:

- **Stocks to scan**: Modify `NIFTY_50` list
- **Lookback period**: Change from "3mo" to "6mo" etc.
- **Filter thresholds**: Adjust in pattern detection functions
- **Number of results**: Change top 10 in message formatting

## Security Notes

⚠️ **Important**: 
- Never commit bot tokens or chat IDs to version control
- Use environment variables or `.env` files (add to `.gitignore`)
- Rotate bot tokens regularly if exposed
- Restrict bot permissions to "Send Messages" only

## Support

For issues or enhancements:
1. Check the script logs
2. Verify Telegram credentials
3. Test network connectivity
4. Run in debug mode (add print statements)

---

**Created**: 2024
**Last Updated**: 2024-10-18
