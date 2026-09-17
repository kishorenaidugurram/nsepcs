# Telegram Setup Guide

This document explains how to set up Telegram notifications for the NSE F&O PCS Scanner.

## Prerequisites

1. **Telegram Account**: You need an active Telegram account
2. **Telegram Bot**: Create a bot through BotFather
3. **Chat ID**: Your personal Telegram chat ID

## Step-by-Step Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/start`
3. Send the command `/newbot`
4. Choose a name for your bot (e.g., "NSE PCS Scanner")
5. Choose a unique username for your bot (e.g., "nse_pcs_scanner_bot")
6. BotFather will give you a **Bot Token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvwxyzABCDEFGH`)
7. Save this token - you'll need it in the next step

### 2. Get Your Chat ID

1. Start a chat with your newly created bot or search for **@userinfobot**
2. Send any message to get your User ID / Chat ID
3. If using your own bot, send `/start` and you'll see your ID
4. The Chat ID is typically your user ID (a number, e.g., `123456789`)

### 3. Set Environment Variables

#### Option A: Linux/Mac (Terminal)
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

#### Option B: Windows (Command Prompt)
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

#### Option C: Create .env file (recommended for persistence)
Create a `.env` file in the repository root:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
MIN_PCS_SCORE=55
MIN_VOLUME_RATIO=1.0
MAX_STOCKS=40
```

Then source it before running:
```bash
source .env
python scanner_telegram.py
```

## Configuration Options

Environment variables you can set:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Required | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Required | Your Telegram chat ID (where to send messages) |
| `MIN_PCS_SCORE` | 55 | Minimum PCS score to include in results |
| `MIN_VOLUME_RATIO` | 1.0 | Minimum volume ratio (current/historical) |
| `MAX_STOCKS` | 40 | Maximum number of stocks to scan |

## Running the Scanner

### Command Line
```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'
python scanner_telegram.py
```

### With Custom Filters
```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_id'
export MIN_PCS_SCORE=65
export MIN_VOLUME_RATIO=1.5
export MAX_STOCKS=25
python scanner_telegram.py
```

## Testing Your Setup

1. First, verify your Telegram bot is working:
   - Send any message to your bot in Telegram
   - The bot should not reply (unless you've added a handler)

2. Run the scanner with debug output:
   ```bash
   python scanner_telegram.py
   ```

3. Check your Telegram for the results message

## Troubleshooting

### "Bot token is invalid"
- Double-check your token is correct
- Ensure no extra spaces or quotes

### "Chat ID not found"
- Make sure you got the right Chat ID (should be a number)
- Try using @userinfobot to confirm your ID
- The Chat ID might be negative for groups (e.g., `-123456789`)

### "Message not sending"
- Verify the bot has not been blocked
- Try sending `/start` to the bot first
- Check that the bot token and chat ID are both set

### No stocks found
- Lower the `MIN_PCS_SCORE` threshold
- Check market hours (scanner works best during trading hours)
- Increase `MAX_STOCKS` to scan more stocks

## Security Notes

- **Never** commit your `.env` file or credentials to version control
- Add `.env` to `.gitignore`:
  ```
  echo ".env" >> .gitignore
  ```
- Use separate bot tokens for different environments (dev, prod)
- Rotate your bot token if you suspect it's been exposed

## Scheduled Execution

To run the scanner automatically on a schedule:

### Linux/Mac (Cron)
```bash
# Edit crontab
crontab -e

# Add a line to run daily at 9:15 AM
15 9 * * * cd /home/user/nsepcs && source .env && python scanner_telegram.py

# Or multiple times a day
15 9 * * * cd /home/user/nsepcs && source .env && python scanner_telegram.py
15 14 * * * cd /home/user/nsepcs && source .env && python scanner_telegram.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (time/frequency)
4. Add action: `python.exe C:\path\to\scanner_telegram.py`
5. Set working directory and environment variables

## Getting Help

For issues with:
- **Telegram Bot Setup**: See Telegram BotFather documentation
- **Scanner**: Check the main README.md
- **Environment Variables**: Verify all variables are set correctly
