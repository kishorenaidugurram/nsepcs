# Telegram Integration Setup Guide

This guide explains how to set up Telegram integration for sending PCS Screener results to your Telegram account.

## Prerequisites

- A Telegram account
- Python 3.8+
- `python-telegram-bot` library (already installed)

## Step-by-Step Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` to BotFather
3. Send `/newbot` to create a new bot
4. Follow the prompts:
   - Choose a name for your bot (e.g., "PCS Screener")
   - Choose a username for your bot (e.g., "pcs_screener_bot")
5. **Save the API Token** (you'll need this in step 3)

### 2. Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start` to the bot
3. The bot will show your User ID (e.g., 123456789)
4. **Save your User ID** (this is your Chat ID)

### 3. Configure Environment Variables

Set these environment variables on your system:

```bash
export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN_HERE'
export TELEGRAM_CHAT_ID='YOUR_CHAT_ID_HERE'
```

**On Linux/Mac**, add to `~/.bashrc` or `~/.zshrc`:
```bash
echo "export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN_HERE'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='YOUR_CHAT_ID_HERE'" >> ~/.bashrc
source ~/.bashrc
```

**On Windows**, set via System Properties:
- Press `Win + X` → System
- Advanced system settings → Environment Variables
- Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as new User or System variables

### 4. Test the Integration

Run the test script:

```bash
python send_stocks_telegram.py --demo
```

You should see a preview of the message format. If credentials are set, the message will be sent to your Telegram chat.

## Usage

### Manual Execution

```bash
# Send demo message
python send_stocks_telegram.py --demo

# Send with live analysis results
python send_stocks_telegram.py

# Custom options
python send_stocks_telegram.py \
    --bot-token 'YOUR_TOKEN' \
    --chat-id 'YOUR_CHAT_ID' \
    --min-score 60 \
    --stocks-count 15
```

### Scheduled Execution (Cron Job)

Add to your crontab to run daily at 3:30 PM IST:

```bash
crontab -e

# Add this line (runs at 10:00 AM UTC which is 3:30 PM IST):
0 10 * * * cd /home/user/nsepcs && python send_stocks_telegram.py >> /var/log/pcs_screener.log 2>&1
```

Or for running after market hours (4:00 PM IST = 10:30 AM UTC):

```bash
30 10 * * 1-5 cd /home/user/nsepcs && python send_stocks_telegram.py >> /var/log/pcs_screener.log 2>&1
```

## Troubleshooting

### "Telegram credentials not configured"
- Ensure environment variables are set correctly
- Run: `echo $TELEGRAM_BOT_TOKEN` to verify
- Or pass credentials as command-line arguments

### "Failed to send message"
- Verify the bot token is correct
- Verify the chat ID is correct
- Ensure the bot is not restricted
- Check internet connection

### "No module named telegram"
Install the library:
```bash
pip install python-telegram-bot
```

## Message Format

The message sent to Telegram includes:

1. **Header**: Shows timestamp in IST
2. **Stock List**: Shows top qualifying stocks with:
   - Symbol
   - PCS Score
   - Confidence Level (HIGH/MEDIUM/LOW)
   - Current Price
   - RSI Indicator
3. **Summary**: Shows analysis date/time
4. **Disclaimer**: Risk warning

Example output:

```
🚀 NSE F&O PCS SCREENER RESULTS
2026-10-06 15:30:00 IST

📊 Stocks Meeting Criteria: 8
Minimum PCS Score: 55

1. RELIANCE.NS 🟢
   Score: 78.5 | Confidence: HIGH
   Price: ₹2850.5 | RSI: 58.2

[...more stocks...]

⚠️ Disclaimer:
This is educational analysis only. Always verify independently before trading.
Never risk more than you can afford to lose. Trade safely!
```

## Features

✅ Real-time PCS analysis results
✅ Formatted Telegram messages with emojis
✅ Multiple confidence levels (HIGH/MEDIUM/LOW)
✅ IST timezone support
✅ Risk disclaimers included
✅ Customizable filters (min score, stock count)
✅ Error handling and logging

## Next Steps

1. Complete the setup steps above
2. Test with `--demo` flag
3. Configure cron job for automated daily runs
4. Monitor the log file for any issues

---

**Questions or Issues?** Check the logs or refer to the Python code comments for more details.
