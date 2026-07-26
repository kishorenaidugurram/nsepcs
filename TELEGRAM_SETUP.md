# Telegram Integration Setup Guide

This guide explains how to set up Telegram integration for the NSE F&O PCS Scanner.

## Prerequisites

You need:
1. A Telegram account
2. A Telegram Bot (created via BotFather)
3. Your Telegram Chat ID

## Step-by-Step Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` to begin
3. Send `/newbot` to create a new bot
4. Follow the prompts:
   - Choose a name for your bot (e.g., "NSE Scanner")
   - Choose a username for your bot (must end with `bot`, e.g., `nse_scanner_bot`)
5. BotFather will give you a token that looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

**Copy this token - you'll need it as `TELEGRAM_BOT_TOKEN`**

### 2. Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start`
3. The bot will show your User ID (this is your Chat ID)

**Copy this ID - you'll need it as `TELEGRAM_CHAT_ID`**

### 3. Set Environment Variables

Add these to your environment or `.env` file:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

For example:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="987654321"
```

### 4. Test the Setup

Run the scanner:
```bash
python3 /home/user/nsepcs/scanner_standalone.py
```

If configured correctly, results will be sent to your Telegram chat.

## Running as a Scheduled Task

To run the scanner on a schedule, use cron or your system's task scheduler:

```bash
0 15 * * * cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 scanner_standalone.py
```

This runs daily at 3 PM IST.

## Troubleshooting

### Bot not sending messages
- Verify `TELEGRAM_BOT_TOKEN` is correct (no spaces, full token)
- Verify `TELEGRAM_CHAT_ID` is correct (should be a number)
- Check that you've started a chat with the bot (search for bot name in Telegram, send `/start`)

### "Chat not found" error
- Make sure Chat ID is a number, not text
- Private chat IDs can be positive or negative numbers

### Bot not responding
- Restart Telegram app
- Verify bot is still active in BotFather
- Check token hasn't been reset

## Security Note

⚠️ **Never commit tokens to Git!**
- Use environment variables or `.env` files (add to `.gitignore`)
- Keep tokens private and rotate if compromised
- Don't share your Chat ID publicly

## Sample Output

When configured, you'll receive messages like:

```
📊 NSE F&O PCS Scanner Results
Time: 2026-07-26 15:30 IST

✅ Found 12 stocks

1. RELIANCE
   Price: ₹2,850.50
   Strength: 88% | Confidence: HIGH
   Volume: 2.1x | RSI: 65.2
   Patterns: Current Day Breakout, Cup with Handle

2. HDFCBANK
   Price: ₹1,520.75
   ...
```

## Support

For issues with:
- **Telegram Bot**: Contact @BotFather on Telegram
- **Scanner Logic**: Check the main streamlit_app.py or create an issue
- **Environment Setup**: Review this guide or consult system documentation
