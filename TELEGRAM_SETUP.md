# Telegram Integration Setup Guide

## Overview
The stock scanner is configured to run daily and send results to your Telegram account. This guide will help you set up the Telegram notifications.

## Current Status
✅ **Stock Scanner**: Running successfully
📊 **Latest Scan Results**: 19 stocks matched filter criteria (see `/tmp/scan_results.json`)
❌ **Telegram Integration**: Not yet configured

## Setup Steps

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send: `/start`
3. Send: `/newbot`
4. Follow the prompts:
   - Bot name: `NSE Stock Scanner` (or your preferred name)
   - Bot username: `nse_stock_scanner_bot` (must be unique and end with `_bot`)
5. BotFather will send you a **Bot Token** that looks like:
   ```
   123456789:ABCdefGHIjklmNOpqrsTUVwxyzABCDEFGHI
   ```
   **Save this token - you'll need it next**

### Step 2: Get Your Telegram Chat ID

1. Open Telegram and search for `@userinfobot`
2. Send: `/start`
3. It will reply with your **Chat ID** (a number like `123456789`)
4. **Save this Chat ID**

### Step 3: Configure Environment Variables

Add these environment variables to enable Telegram notifications:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

#### For Persistent Configuration:

**Option A: Add to `.bashrc`**
```bash
echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id_here'" >> ~/.bashrc
source ~/.bashrc
```

**Option B: Create `.env` file**
```bash
# Create file: /home/user/nsepcs/.env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then load it in your script or before running:
```bash
source /home/user/nsepcs/.env
```

**Option C: Set in scheduled task/cronjob**
```bash
0 9 * * * export TELEGRAM_BOT_TOKEN='...' TELEGRAM_CHAT_ID='...' && cd /home/user/nsepcs && python stock_scanner_telegram.py
```

### Step 4: Test the Configuration

Run the scanner to test:
```bash
cd /home/user/nsepcs
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_chat_id'
python stock_scanner_telegram.py
```

You should receive a Telegram message with today's scan results.

## Filter Configuration

The scanner uses these default filter criteria:

| Filter | Value |
|--------|-------|
| RSI Range | 30 - 75 |
| ADX Minimum | 20 |
| Min Volume Ratio | 1.2x |
| Pattern Strength | 65% |

### To Modify Filters:
Edit `stock_scanner_telegram.py` and change the `FILTERS` dictionary at the top of the file.

## Running the Scanner

### Manual Execution
```bash
cd /home/user/nsepcs
python stock_scanner_telegram.py
```

### Scheduled Execution (Daily at 9:00 AM IST)
Add to crontab:
```bash
crontab -e

# Add this line:
0 9 * * * source /home/user/nsepcs/.env && cd /home/user/nsepcs && python stock_scanner_telegram.py >> /tmp/scanner.log 2>&1
```

### Scheduled Execution (Using Claude Code scheduled tasks)
The task is configured to run automatically. Once you set the environment variables, results will be sent to Telegram automatically.

## Output Files

The scanner generates several output files:

- **`/tmp/telegram_message.txt`** - The formatted message that was sent to Telegram
- **`/tmp/scan_results.json`** - Full scan results in JSON format

Example JSON structure:
```json
{
  "timestamp": "2026-09-23T09:21:00+05:30",
  "filters": {
    "rsi_min": 30,
    "rsi_max": 75,
    "adx_min": 20,
    "pattern_strength_min": 65,
    "min_volume_ratio": 1.2
  },
  "total_stocks_analyzed": 19,
  "total_matched": 19,
  "results": [
    {
      "symbol": "KOTAKBANK",
      "price": 1240.37,
      "rsi": 69.3,
      "adx": 49.06,
      "volume_ratio": 2.33,
      "pattern_strength": 100.0,
      "change_pct": -2.93
    },
    ...
  ]
}
```

## Troubleshooting

### "Telegram credentials not configured"
- Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Test with: `echo $TELEGRAM_BOT_TOKEN`
- Make sure you've reloaded your shell if you added them to `.bashrc`

### "Telegram API error: 403"
- Check that the Bot Token is correct
- Check that the Chat ID is correct (should be a number)
- Verify the bot has permission to send messages

### "Telegram API error: 404"
- The bot token is invalid
- Get a new token from BotFather

### Network Connection Errors
- Your organization network may block Telegram
- Try from a different network to test
- Contact your IT department if Telegram is blocked

## Support

For issues or to customize the scanner:
1. Check `/tmp/scan_results.json` for detailed results
2. Review the scanner code: `stock_scanner_telegram.py`
3. Check logs for errors

## Next Steps

1. ✅ Create Telegram bot with BotFather
2. ✅ Get your Chat ID from @userinfobot
3. ✅ Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables
4. ✅ Test by running the scanner manually
5. ✅ Scanner will run automatically on schedule

---

**Last Updated**: 2026-09-23
**Scanner Version**: 1.0
**Filter Version**: Default (RSI 30-75, ADX 20+, Vol 1.2x+, Pattern 65+%)
