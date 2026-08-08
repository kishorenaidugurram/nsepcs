# Telegram Setup Guide for NSE PCS Scanner

## Overview
The NSE F&O PCS Scanner can send filtered stock results directly to your Telegram chat. Follow these steps to set it up.

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a conversation with BotFather
3. Send the command: `/newbot`
4. Follow the prompts:
   - Give your bot a name (e.g., "NSE PCS Scanner")
   - Give it a username (e.g., "nse_pcs_scanner_bot")
5. **Save the API Token** that BotFather provides (looks like: `123456789:ABCdefGHIjklmnopQRstuvWXYZ`)

## Step 2: Get Your Chat ID

1. Open Telegram and start a conversation with your newly created bot
2. Send any message to your bot (e.g., "/start")
3. Visit this URL in your browser (replace TOKEN with your bot's API token):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
4. Look for your chat ID in the JSON response (it's a number like `123456789`)
5. **Save your Chat ID**

## Step 3: Configure Environment Variables

Set these environment variables so the scanner can send messages to Telegram:

### Option A: Export in Terminal (One-time)
```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklmnopQRstuvWXYZ'
export TELEGRAM_CHAT_ID='123456789'

# Then run the scanner
python3 run_scanner.py
```

### Option B: Add to ~/.bashrc (Persistent)
```bash
echo "export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklmnopQRstuvWXYZ'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='123456789'" >> ~/.bashrc
source ~/.bashrc
```

### Option C: Create a .env File (Recommended for automation)
Create `/home/user/nsepcs/.env`:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnopQRstuvWXYZ
TELEGRAM_CHAT_ID=123456789
```

Then source it before running:
```bash
source .env
python3 run_scanner.py
```

## Step 4: Test the Setup

1. Ensure variables are exported:
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```

2. Run the scanner:
   ```bash
   python3 run_scanner.py
   ```

3. Check your Telegram chat - you should receive the PCS scanner results!

## Step 5: Schedule Automated Runs (Optional)

To run the scanner automatically, you can set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9:30 AM IST
30 4 * * * cd /home/user/nsepcs && source .env && python3 run_scanner.py
```

## Troubleshooting

### Message not received?
- ✅ Check bot token and chat ID are correct
- ✅ Make sure you sent a message to the bot first (start a conversation)
- ✅ Verify environment variables are set: `printenv | grep TELEGRAM`
- ✅ Check network connectivity

### Bot doesn't respond?
- Visit: `https://api.telegram.org/botTOKEN/getMe` (replace TOKEN)
- If you get JSON with "ok": true, your token is valid

### Wrong chat ID?
- Run: `https://api.telegram.org/botTOKEN/getUpdates`
- Look for `"chat":{"id":YOUR_CHAT_ID}` in the response

## Understanding the Results

When the scanner runs, you'll receive a message like:

```
📊 NSE F&O PCS Scanner Results
⏰ 08-Aug-2026 09:13 IST
📈 Total Stocks Found: 9

🟢 HIGH Confidence (1 stocks)
  • TECHM - 76 pts

🟡 MEDIUM Confidence (5 stocks)
  • NTPC - 72 pts
  • MARUTI - 68 pts
  ... and 3 more

🔴 LOW Confidence (3 stocks)
  • HEROMOTOCO - 58 pts
  ... and 2 more
```

### Confidence Levels:
- **🟢 HIGH (Score 75+)**: Conservative strikes, highest probability of success
- **🟡 MEDIUM (Score 60-74)**: Moderate risk/reward, balanced approach
- **🔴 LOW (Score <60)**: Aggressive strikes, higher risk

## Filter Settings

The scanner uses these default filters (can be modified in `run_scanner.py`):

```python
RSI Range: 30-75 (ideal momentum zone)
ADX Minimum: 20 (trend strength)
PCS Score Minimum: 55 (overall quality)
```

## Recent Scan Results

Latest scan results are saved as JSON files in the results directory:
```
/home/user/nsepcs/pcs_results_YYYYMMDD_HHMMSS.json
```

## Support

- **Questions about Telegram?** Visit: https://telegram.org
- **Issues with the scanner?** Check the README.md in the repository

---

**Note:** These are automated screening results for educational purposes. Always do your own research before placing actual trades!
