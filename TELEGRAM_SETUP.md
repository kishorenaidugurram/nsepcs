# Telegram Integration Setup Guide

## Overview
The `scan_and_send_telegram.py` script automatically scans NSE F&O stocks for bullish momentum patterns and sends filtered results to your Telegram channel.

## Prerequisites
- A Telegram account
- A Telegram Bot (created via BotFather)
- Your Telegram Chat ID
- Python 3.11+

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the message: `/start`
3. Send the message: `/newbot`
4. Follow the prompts to create your bot:
   - Choose a name (e.g., "NSE Stock Scanner")
   - Choose a username (e.g., "nse_stock_scanner_bot")
5. BotFather will provide your **Bot Token** (looks like: `123456789:ABCdefGhijKLMnoPqrsTUVwxyz`)

## Step 2: Get Your Chat ID

1. Start a chat with your new bot (search for the username you created)
2. Send `/start` to the bot
3. Go to this URL in your browser (replace TOKEN with your bot token):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
4. Find your user ID in the JSON response (look for `"from":{"id":XXXXXX`)
5. Your **Chat ID** is that number

## Step 3: Set Environment Variables

### For Manual Testing:
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
python3 scan_and_send_telegram.py
```

### For Scheduled Tasks:
Add these to your environment configuration:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Step 4: Run the Script

```bash
# Test the script
python3 scan_and_send_telegram.py

# Expected output:
# 🚀 NSE F&O PCS Scanner - Telegram Reporter
# ============================================================
# 📊 Analyzing stocks for bullish momentum...
# ✅ Found 10 stocks meeting filter criteria
# 
# 📱 Sending to Telegram...
#    Bot Token: 123456789:...
#    Chat ID: 123456789
# ✅ Message sent to Telegram successfully
# ============================================================
# ✅ Process completed successfully!
# ✅ Sent 10 stocks to Telegram
```

## What the Script Does

1. **Analyzes Stocks**: Scans NSE F&O stocks for bullish momentum patterns
2. **Filters Results**: Only shows stocks meeting configured criteria
3. **Sends to Telegram**: Formats results and sends formatted message with:
   - Stock symbols and momentum scores
   - Confidence levels (HIGH/MEDIUM/LOW)
   - Technical indicators (RSI, Price, Moving Averages)
   - Summary statistics

## Message Format

The Telegram message includes:
```
🚀 NSE F&O PCS Scanner - Bullish Momentum Stocks
[Date and Time]

📊 Found X stocks meeting filter criteria:

🟢 STOCK1 [HIGH]
   Score: 85 | RSI: 55.2 | Price: ₹2850.5
   
🟡 STOCK2 [MEDIUM]
   Score: 72 | RSI: 48.5 | Price: ₹2410.8
   
... and more

📈 Summary:
• Total Stocks: X
• 🟢 HIGH Confidence (75+): X
• 🟡 MEDIUM Confidence (60-74): X

ℹ️ Next Steps:
1. Review stocks on NSE F&O PCS Scanner
2. Check technical charts for confirmation
3. Monitor RSI for entry signals
4. Set proper stop losses before trading
```

## Scheduling with Cron

To run automatically each trading day:

```bash
# Add to crontab
0 9 * * 1-5 export TELEGRAM_BOT_TOKEN='...' TELEGRAM_CHAT_ID='...' && cd /home/user/nsepcs && python3 scan_and_send_telegram.py
```

## Troubleshooting

### "ERROR: Telegram credentials not configured"
- Make sure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Check: `echo $TELEGRAM_BOT_TOKEN`

### "❌ Telegram API error"
- Verify your bot token is correct
- Verify your chat ID is correct
- Check if the bot is still active in BotFather

### "Failed to send Telegram message: "
- Check internet connection
- Verify the message format is valid HTML
- Check bot permissions in Telegram

## Security Notes

⚠️ **Never commit sensitive credentials** to version control!

- Store credentials in environment variables only
- Use `.env` files (add to `.gitignore`)
- For production deployments, use secure secret management

## Example .env File (add to .gitignore)

```bash
# .env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhijKLMnoPqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# Load before running:
# source .env
# python3 scan_and_send_telegram.py
```

## Next Steps

1. ✅ Create bot with BotFather
2. ✅ Get your Chat ID
3. ✅ Set environment variables
4. ✅ Test the script manually
5. ✅ Configure scheduled runs
6. ✅ Monitor Telegram messages

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify environment variables are set correctly
3. Test bot connection: `python3 scan_and_send_telegram.py`

---

**Enjoy automated stock monitoring!** 📈
