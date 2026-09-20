# Telegram Integration Setup Guide

This NSE F&O Stock Scanner can send scan results directly to your Telegram account.

## Prerequisites

- A Telegram Bot (created via BotFather)
- Telegram Bot Token
- Telegram Chat ID (your personal chat ID)

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` command
3. Send `/newbot` command
4. Follow the prompts to create your bot
5. **Save the Bot Token** - it looks like: `123456:ABCdefGHIjklmnoPQRstuvWXYZ`

## Step 2: Get Your Telegram Chat ID

### Method 1: Using a simple bot
1. Create another bot (or use the one you just created)
2. Start a chat with your bot and send any message
3. Visit this URL in your browser (replace TOKEN):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
4. Look for your `"chat"` object and note the `"id"` value

### Method 2: Using UpdateNotifier Bot
1. Open Telegram and search for **@userinfobot**
2. Send `/start` to get your Chat ID

## Step 3: Set Environment Variables

### On Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Persistent Setup (recommended):
Add to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
# NSE F&O Scanner Telegram Integration
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### On Windows (PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "your_bot_token_here", "User")
[Environment]::SetEnvironmentVariable("TELEGRAM_CHAT_ID", "your_chat_id_here", "User")
```

### Using .env file (alternative):
1. Create a `.env` file in the nsepcs directory:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

2. Load before running:
   ```bash
   source .env && python send_to_telegram.py
   ```

## Step 4: Run the Scanner

### Option 1: Simple Telegram Send (with existing results)
```bash
python send_to_telegram.py
```

### Option 2: Full Scanner with Telegram
First install dependencies:
```bash
pip install -r requirements.txt
```

Then run:
```bash
python telegram_scanner.py
```

## Verification

To test if your bot is working:

1. **Test with curl:**
   ```bash
   curl -X POST https://api.telegram.org/botTOKEN/sendMessage \
     -d chat_id=YOUR_CHAT_ID \
     -d text="Test message"
   ```

2. **Test with Python:**
   ```bash
   python -c "
   from telegram import Bot
   bot = Bot(token='YOUR_TOKEN')
   bot.send_message(chat_id='YOUR_CHAT_ID', text='Test message')
   "
   ```

## Troubleshooting

### "Unauthorized (401)" error
- Double-check your Bot Token
- Ensure you copied the entire token (often includes colons)

### "Forbidden (403)" error
- Invalid Chat ID
- Re-verify your Chat ID using the methods above

### No message received
- Ensure you've started a conversation with your bot
- Check if the bot has message permissions

### Module not found errors
Install telegram library:
```bash
pip install python-telegram-bot
```

## Example Output

When successful, you'll receive a Telegram message like:

```
📊 NSE F&O Stock Scanner Results
🕐 20-Sep-2026 09:11 IST
━━━━━━━━━━━━━━━━━━━━━━

✅ Found 12 stocks with current day patterns

📈 Statistics:
• Total Patterns: 18
• Avg Strength: 78.5%
• Current Day Breakouts: 5

🏆 Top Stocks (by pattern strength):

1. RELIANCE 🟢 HIGH
   💰 ₹2,345.50 | RSI:65.2 | ADX:32.1
   💪 Strength: 92% | Patterns: 2
   🎯 Current Day Breakout, Cup with Handle

...
```

## Scheduling (Cron)

To run scanner automatically daily at 4:00 PM IST:

```bash
# Edit crontab
crontab -e

# Add this line:
0 16 * * * export TELEGRAM_BOT_TOKEN="your_token" && export TELEGRAM_CHAT_ID="your_id" && cd /home/user/nsepcs && python telegram_scanner.py >> /var/log/scanner.log 2>&1
```

Or use the simpler version:
```bash
0 16 * * * cd /home/user/nsepcs && python send_to_telegram.py >> /var/log/scanner.log 2>&1
```

## API Reference

The scanner uses these libraries:
- `python-telegram-bot` - For sending messages to Telegram
- `yfinance` - For fetching stock data
- `ta` - For technical analysis indicators
- `pandas` - For data manipulation

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file or tokens to git
- Keep your Bot Token secret
- Use environment variables instead of hardcoding tokens
- Consider using a dedicated bot for this purpose

## Support

For issues with Telegram Bot API:
- https://core.telegram.org/bots/api

For technical analysis scanner issues:
- Check the main `streamlit_app.py` for detailed scanner logic
