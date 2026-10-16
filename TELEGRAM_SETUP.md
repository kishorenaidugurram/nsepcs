# Telegram Integration Setup Guide

## Overview
This guide explains how to set up Telegram notifications for the NSE F&O PCS Scanner so it automatically sends scan results to your Telegram chat.

## Prerequisites
- A Telegram account
- Basic command-line familiarity
- Access to your scheduled task environment

## Step-by-Step Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/start`
3. Send the command `/newbot`
4. Follow the prompts:
   - Enter a display name (e.g., "NSE PCS Scanner")
   - Enter a unique username (e.g., "nse_pcs_scanner_bot")
5. **BotFather will give you a token** - save this! It looks like:
   ```
   123456789:ABCDEfghijklmnopqrstuvwxyz
   ```
   This is your `TELEGRAM_BOT_TOKEN`

### 2. Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Start a chat and send `/start`
3. The bot will show you your User ID as `Your user id is: 123456789`
   This is your `TELEGRAM_CHAT_ID`

Alternatively, to get chat ID:
1. Message your bot once
2. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates` (replace `<TOKEN>` with your bot token)
3. Look for `"chat":{"id":123456789}` - that's your chat ID

### 3. Set Environment Variables

#### For Manual Testing:
```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCDEfghijklmnopqrstuvwxyz"
export TELEGRAM_CHAT_ID="123456789"

# Test the connection:
python3.11 /home/user/nsepcs/telegram_scanner.py test
```

#### For Scheduled Tasks:
Add these to your scheduled task environment before running the scan:

**If using cron:**
```bash
# Add to crontab with environment variables
0 9 * * 1-5 export TELEGRAM_BOT_TOKEN="your_token"; export TELEGRAM_CHAT_ID="your_chat_id"; cd /home/user/nsepcs && python3.11 run_scan.py
```

**If using a systemd timer or other scheduler:**
Add the environment variables to the task configuration:
```ini
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
```

### 4. Verify Setup

```bash
python3.11 /home/user/nsepcs/telegram_scanner.py config
```

Output should show:
```
✅ Configured
   Token: your_token_first_20_chars...
   Chat ID: your_chat_id
```

### 5. Send a Test Message

```bash
python3.11 /home/user/nsepcs/telegram_scanner.py test
```

You should receive a test message in Telegram.

## Usage

### Running Scanner with Telegram Integration

The scan runner will automatically send results to Telegram if configured:

```bash
python3.11 /home/user/nsepcs/run_scan.py
```

### Manual Telegram Sending

From Python:
```python
from telegram_scanner import send_scan_results

stocks = [
    {
        'symbol': 'TCS',
        'pattern': 'Cup with Handle',
        'strength': 85.5,
        'current_price': 4128.75
    }
]

send_scan_results(stocks)
```

## Troubleshooting

### "Telegram not configured" Error
- Verify environment variables are set: `echo $TELEGRAM_BOT_TOKEN`
- Check for typos in token or chat ID
- Ensure bot token format is correct (should contain a colon)

### "API Error" from Telegram
- Verify bot token is correct
- Verify chat ID is correct (must be numeric)
- Ensure bot has permission to send messages
- Check bot isn't rate-limited

### Message Not Received
- Check bot privacy settings (@BotFather → /mybots → select bot → Edit → Privacy)
- Ensure you've messaged the bot at least once
- Check Telegram filters/spam folder

## Configuration for Scheduled Tasks

### Example Cron Job (Daily 9:15 AM IST)

```bash
# Edit crontab: crontab -e
# Add this line:
15 9 * * 1-5 bash -c 'source ~/.bashrc && export TELEGRAM_BOT_TOKEN="your_token" && export TELEGRAM_CHAT_ID="your_chat_id" && cd /home/user/nsepcs && python3.11 run_scan.py' >> /tmp/nse_scan.log 2>&1
```

### Example GitHub Actions Workflow

```yaml
name: Daily NSE Scan
on:
  schedule:
    - cron: '15 9 * * 1-5'  # 9:15 AM IST (4:45 AM UTC)

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run scan
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3.11 run_scan.py
```

## Security Notes

- **Never commit tokens to git**: Use environment variables or secrets management
- **Keep tokens private**: Don't share your bot token or chat ID
- **Use bot privacy mode**: On @BotFather, ensure bot only sees messages it's explicitly sent
- **Rotate tokens if compromised**: Send `/revoke` to @BotFather to invalidate a token

## Support

For issues with:
- **Telegram**: Contact Telegram support or check https://telegram.org
- **Scanner**: Check the repository issues
- **Setup**: Refer back to this guide or create an issue with your error message
