# Telegram Scanner Integration Setup Guide

This guide explains how to set up the Telegram integration for the NSE F&O PCS Scanner to automatically send stock filtering results to your Telegram.

## Prerequisites

- Telegram account and app installed
- A Telegram bot token from BotFather
- Your Telegram chat ID

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` command
3. Send `/newbot` command
4. Choose a name for your bot (e.g., "NSE PCS Scanner")
5. Choose a unique username (e.g., "nse_pcs_scanner_bot")
6. BotFather will provide you with a **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
7. **Save this token securely** - you'll need it

## Step 2: Get Your Chat ID

1. Search for your newly created bot in Telegram and click `/start`
2. Go to this URL in your browser, replacing `YOUR_BOT_TOKEN` with the token from Step 1:
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for your chat ID (usually starts with a dash, like: `-123456789`)
4. **Save this chat ID**

## Step 3: Set Environment Variables

For automated scheduled execution, set these environment variables on your system:

### On Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### On a Scheduled Task (Cron):
Add these to your cron job or systemd service:
```bash
#!/bin/bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
cd /home/user/nsepcs
python telegram_scanner.py
```

### Persistent Environment Variables:
Add to `~/.bashrc` or `~/.bash_profile`:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then reload:
```bash
source ~/.bashrc
```

## Step 4: Run the Scanner

Once credentials are set:

```bash
python telegram_scanner.py
```

The scanner will:
1. Scan 30 top NSE F&O stocks
2. Detect bullish patterns and technical setups
3. Send results to your Telegram chat

## Example Output

The Telegram message will look like:

```
🎉 NSE PCS Scanner Results
Total Stocks Found: 5

1. RELIANCE - 🟢 HIGH
   Price: ₹2,500.00 | RSI: 55.2 | Strength: 85%
   Patterns: Bullish Momentum, Range Breakout

2. TCS - 🟡 MEDIUM
   Price: ₹3,200.00 | RSI: 62.1 | Strength: 72%
   Patterns: Oversold Bounce Setup
```

## Customization

### Edit `telegram_scanner.py` to modify:

**Number of stocks to scan:**
```python
stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:50],  # Change from 30 to 50
```

**Pattern strength threshold:**
```python
pattern_strength_min=60,  # Change from 50 (higher = fewer results)
```

**RSI range for filtering:**
```python
rsi_min=25,  # Minimum RSI
rsi_max=85,  # Maximum RSI
```

**Volume threshold:**
```python
min_volume_ratio=1.0,  # Change from 0.8
```

## Troubleshooting

### Bot not receiving messages:
- Verify bot token is correct
- Verify chat ID is correct (including the minus sign if present)
- Check bot privacy settings in BotFather (should allow group messages)
- Send a manual test message to verify connection

### No stocks found:
- Market may be closed
- Adjust pattern_strength_min lower (50 → 40)
- Adjust RSI range wider (25-85 → 20-90)
- Check volume ratio threshold

### Test the bot connection:
```bash
python -c "
import requests
import os

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token or not chat_id:
    print('Error: Environment variables not set')
else:
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': 'Test message from NSE Scanner'}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print('✓ Connection successful!')
    else:
        print(f'✗ Error: {response.status_code}')
"
```

## Scheduled Execution

### Using Cron (Linux/Mac):
```bash
# Edit crontab
crontab -e

# Add this line to run scanner daily at 3 PM IST (9:30 AM UTC)
# When markets close
0 15 * * 1-5 export TELEGRAM_BOT_TOKEN="your_token"; export TELEGRAM_CHAT_ID="your_id"; python /home/user/nsepcs/telegram_scanner.py
```

### Using Systemd Timer (Linux):
Create `/etc/systemd/system/nse-scanner.service`:
```ini
[Unit]
Description=NSE PCS Scanner
After=network.target

[Service]
Type=oneshot
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_id"
ExecStart=/usr/bin/python3 /home/user/nsepcs/telegram_scanner.py
User=root
```

Create `/etc/systemd/system/nse-scanner.timer`:
```ini
[Unit]
Description=Run NSE Scanner Daily

[Timer]
OnCalendar=*-*-* 15:00:00
Unit=nse-scanner.service

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl daemon-reload
systemctl enable nse-scanner.timer
systemctl start nse-scanner.timer
```

## Security Notes

- **Never share your bot token or chat ID publicly**
- Store credentials in environment variables, not in code
- Use restricted access levels if sharing servers
- Consider using a private channel/group instead of personal chat

## Support

For issues or questions, check:
1. Bot token format (should have a colon like `123:ABC`)
2. Chat ID format (should be numeric, often negative)
3. Network connectivity to Telegram API
4. Market trading hours (Monday-Friday, 9:15 AM - 3:30 PM IST)

---

**Version:** 1.0  
**Last Updated:** August 2026
