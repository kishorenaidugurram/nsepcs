# Telegram Bot Setup Guide

## Quick Start

To send stock screener results to your Telegram, follow these steps:

### Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Send** the command: `/newbot`
3. **Follow the prompts:**
   - Give your bot a name (e.g., "Stock Scanner Bot")
   - Give it a username (must be unique, e.g., "my_stock_scanner_bot")
4. **Copy the Bot Token** provided (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

#### Option A: From a Chat/Group
1. **Add your bot** to any Telegram chat or create a group
2. **Send any message** in that chat
3. **Visit this URL** in your browser (replace YOUR_BOT_TOKEN):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. **Look for** the `"chat"."id"` field in the JSON response
5. **Copy your Chat ID** (a number, e.g., `123456789`)

#### Option B: Get Your Personal Chat ID
1. **Message your bot** with `/start`
2. **Visit the getUpdates URL** (same as above)
3. **Find your chat_id** in the response

### Step 3: Run the Scanner

#### Method 1: Command Line (Recommended)
```bash
cd /home/user/nsepcs
python scan_and_send_telegram.py YOUR_BOT_TOKEN YOUR_CHAT_ID
```

#### Method 2: Using Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
python scan_and_send_telegram.py
```

#### Method 3: Run with Custom Filters
```bash
# Adjust minimum score (default: 60)
export MIN_SCORE=70
python scan_and_send_telegram.py YOUR_BOT_TOKEN YOUR_CHAT_ID

# Adjust maximum stocks to scan (default: 50)
export MAX_STOCKS=100
python scan_and_send_telegram.py YOUR_BOT_TOKEN YOUR_CHAT_ID
```

## Example Output

The scanner will send you:
1. **Summary** - Total stocks scanned and matching criteria
2. **Top 20 Stocks** - Ranked by pattern strength with:
   - Pattern strength percentage
   - Current price
   - Volume ratio
   - RSI and ADX indicators
   - Number of patterns detected
3. **Complete List** - All qualifying stocks in table format

## Telegram Bot Security Notes

⚠️ **Important:**
- Keep your Bot Token private - treat it like a password
- Never share your Bot Token publicly
- Never commit it to version control
- Use environment variables for production setups

## Troubleshooting

### "Telegram Error: Unauthorized"
- Check your bot token is correct
- Make sure the bot hasn't been blocked
- Verify the chat ID is correct

### "No qualifying stocks found"
- Try lowering the MIN_SCORE threshold
- Increase MAX_STOCKS to scan more stocks
- Check market hours (scanner works best during trading hours)

### API Rate Limiting
- The scanner may take 2-5 minutes to complete
- Telegram has message limits - very long results are split
- If you get rate limit errors, wait a few seconds and retry

## Automated Scheduling (Optional)

To run the scanner automatically every day:

### Using Cron (Linux/Mac)
```bash
# Add to your crontab
0 9 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 scan_and_send_telegram.py YOUR_BOT_TOKEN YOUR_CHAT_ID >> scan.log 2>&1
```

### Using Windows Task Scheduler
1. Create a batch file with the python command
2. Set it to run at your preferred time
3. Configure it to run even when you're not logged in

## Need Help?

For issues or feature requests:
1. Check the logs in `scan.log`
2. Verify your credentials again
3. Test the bot manually by sending it a message
4. Check your internet connection

---

**Developed for the trading community** ❤️
