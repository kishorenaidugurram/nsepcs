# NSE PCS Scanner - Telegram Integration Guide

## Overview
This guide explains how to set up automated stock screening results delivery to your Telegram chat.

## Prerequisites

### 1. Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/start` and then `/newbot`
3. Follow the prompts to create a new bot
4. Copy the **BOT TOKEN** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvwxyzABC123`)

### 2. Get Your Chat ID
1. Open Telegram and search for `@userinfobot`
2. Send `/start`
3. Copy your **CHAT ID** (a long number)

Alternatively, if you want to send to a group:
- Add the bot to your group
- Send `/start` to the bot in the group
- Use `@userinfobot` to get the group chat ID

## Setup Instructions

### Step 1: Set Environment Variables
Save these in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

Or set them for the current session:
```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklmnoPQRstuvwxyzABC123'
export TELEGRAM_CHAT_ID='987654321'
```

### Step 2: Run the Scanner
```bash
# Using the Streamlit app
python3 -m streamlit run streamlit_app.py

# Or set up a scheduled task
# Add to crontab for automated daily scans (6:00 AM IST)
0 0 * * * cd /home/user/nsepcs && python3 send_to_telegram.py >> /tmp/telegram_scan.log 2>&1
```

### Step 3: Send Results to Telegram
After running the scanner and generating results:

```bash
python3 send_to_telegram.py
```

## Automated Scheduling

### Using Cron (Linux/Mac)

1. Open crontab editor:
```bash
crontab -e
```

2. Add entry for daily scan at 6:00 AM IST (0:30 UTC):
```bash
30 0 * * * cd /home/user/nsepcs && /usr/bin/python3 send_to_telegram.py
```

### Using GitHub Actions

Create `.github/workflows/scanner.yml`:

```yaml
name: Daily PCS Scanner

on:
  schedule:
    - cron: '30 0 * * *'  # 6:00 AM IST (0:30 UTC)
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run scanner and send to Telegram
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 send_to_telegram.py
```

Then add secrets in GitHub repo settings:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Message Format

The Telegram message includes:
- **Scan Time**: When the scan was performed
- **Stocks Found**: Total number of stocks meeting criteria
- **Top 20 Results**: Ranked by PCS Score
  - Stock symbol
  - Current price in INR
  - RSI (momentum indicator)
  - PCS Score (0-100 scale)

## Troubleshooting

### Bot not responding
- Check that bot token is correct
- Verify bot was added to the chat
- Ensure chat ID is correct

### No stocks found in scan
- May indicate current market conditions don't meet filter criteria
- Adjust scanner filters in `streamlit_app.py`
- Check market hours (9:15 AM - 3:30 PM IST)

### Network errors
- Verify internet connection
- Check proxy settings if behind corporate firewall
- Ensure Python requests library can reach Telegram API

## API Reference

### send_telegram_message()
```python
from send_to_telegram import send_telegram_message

# Send a message
send_telegram_message("<b>Hello!</b> This is a <b>bold</b> message.", parse_mode='HTML')
```

### Message Formatting
- **Bold**: `<b>text</b>`
- **Italic**: `<i>text</i>`
- **Code**: `<code>text</code>`
- **Links**: `<a href="url">text</a>`

## Advanced Usage

### Custom Filter Configuration
Edit `streamlit_app.py` to adjust:
- RSI thresholds
- Volume ratios
- Pattern recognition
- Support level distances

### Multiple Recipients
To send to multiple chats:
```bash
for CHAT_ID in "chat1" "chat2" "chat3"; do
    export TELEGRAM_CHAT_ID="$CHAT_ID"
    python3 send_to_telegram.py
done
```

## Support
For issues or enhancements, check the repository or create an issue.
