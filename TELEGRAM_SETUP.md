# NSE F&O PCS Telegram Scanner Setup Guide

## Overview

This guide explains how to set up automated stock scanning with Telegram notifications. The scanner analyzes NSE F&O stocks based on technical indicators (RSI, ADX, Volume) and sends results to your Telegram chat.

## Two Scanner Options

### 1. **Simple Telegram Scanner** (Recommended for Automation)
- **File**: `simple_telegram_scanner.py`
- **Pros**: Lightweight, minimal dependencies, fast execution (5-10 minutes for 35 stocks)
- **Cons**: Simplified technical analysis (no complex pattern detection)
- **Best for**: Scheduled automation, daily routine scans
- **Dependencies**: yfinance, pandas, numpy, requests (all basic)

### 2. **Full Telegram Scanner** (Feature-rich)
- **File**: `telegram_scanner.py`
- **Pros**: Advanced pattern detection, multiple timeframe analysis, comprehensive indicators
- **Cons**: Higher resource usage, requires additional dependencies
- **Best for**: Detailed analysis, manual execution when needed
- **Note**: Requires fixing the `ta` package dependency issue

## Quick Start - Simple Scanner

### Step 1: Get Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create a new bot
4. Copy the **Bot Token** provided (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

**Option A: Using Web (Easiest)**
1. Create/open a private Telegram chat with your bot
2. Send any message to your bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Replace `<YOUR_BOT_TOKEN>` with your actual token
5. Look for `"chat":{"id":123456789}` - that's your Chat ID

**Option B: Using a Test Command**
```bash
# Run this script to find your chat ID
TELEGRAM_BOT_TOKEN="your_bot_token" python3 -c "
import requests
import json
response = requests.get(f'https://api.telegram.org/botTELEGRAM_BOT_TOKEN/getUpdates')
data = response.json()
if data['ok'] and data['result']:
    for msg in data['result']:
        print(f\"Chat ID: {msg['message']['chat']['id']}\")
"
```

### Step 3: Set Environment Variables

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Verify they're set
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

Or pass them inline when running:

```bash
TELEGRAM_BOT_TOKEN="token" TELEGRAM_CHAT_ID="id" python3 simple_telegram_scanner.py
```

### Step 4: Test the Scanner

```bash
python3 simple_telegram_scanner.py
```

You should see:
```
INFO:__main__:============================================================
INFO:__main__:NSE F&O Simple Telegram Scanner
INFO:__main__:============================================================
INFO:__main__:Testing Telegram connection...
INFO:__main__:✓ Telegram connection OK
INFO:__main__:Running stock analysis...
[Progress messages...]
INFO:__main__:✓ Scan completed successfully
```

And receive a Telegram message with the results!

## Scheduling Automated Scans

### Option 1: Linux Cron Job

1. Open crontab editor:
```bash
crontab -e
```

2. Add this line to run at 3:30 PM IST daily (after market close):
```bash
30 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 simple_telegram_scanner.py >> /var/log/nse_scanner.log 2>&1
```

3. Or run at specific time for weekly scan (Friday 4 PM):
```bash
0 16 * * 5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 simple_telegram_scanner.py >> /var/log/nse_scanner.log 2>&1
```

### Option 2: Systemd Timer (Advanced)

Create `/etc/systemd/system/nse-scanner.service`:
```ini
[Unit]
Description=NSE F&O PCS Telegram Scanner
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/home/user/nsepcs
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_id"
ExecStart=/usr/bin/python3 /home/user/nsepcs/simple_telegram_scanner.py
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/nse-scanner.timer`:
```ini
[Unit]
Description=NSE F&O Scanner Timer
Requires=nse-scanner.service

[Timer]
OnCalendar=Mon-Fri 15:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nse-scanner.timer
sudo systemctl start nse-scanner.timer
```

### Option 3: GitHub Actions (Cloud Scheduler)

Create `.github/workflows/nse-scan.yml`:
```yaml
name: NSE F&O Scan

on:
  schedule:
    - cron: '30 10 * * 1-5'  # 10:30 UTC = 15:30 IST

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -q -r requirements.txt
      - run: python3 simple_telegram_scanner.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

Then add your secrets to GitHub:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Filter Criteria - Simple Scanner

The simple scanner uses these default filters:

| Indicator | Min | Max | Description |
|-----------|-----|-----|-------------|
| **RSI** | 40 | 70 | Momentum strength (not overbought/oversold) |
| **ADX** | 20+ | - | Trend strength confirmation |
| **Volume** | 1.2x | - | Above average volume |
| **Price Position** | Above SMA20 | - | Price above 20-day moving average |

All criteria must be met for a stock to qualify.

## Customizing the Scanner

### Modify Filter Thresholds

Edit `simple_telegram_scanner.py` and change values in the `analyze_stock()` method:

```python
# Current thresholds
rsi_ok = 40 <= current_rsi <= 70
adx_ok = current_adx >= 20
volume_ok = volume_ratio >= 1.2  # Change from 1.2
```

### Add/Remove Stocks

Edit the `COMPLETE_NSE_FO_UNIVERSE` list at the top:

```python
COMPLETE_NSE_FO_UNIVERSE = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    # Add or remove as needed
]
```

### Change Telegram Message Format

Modify the `format_telegram_message()` method to customize the output.

## Troubleshooting

### "Missing environment variables" Error

```bash
# Fix: Set environment variables first
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
python3 simple_telegram_scanner.py
```

### "Telegram connection failed" Error

1. Verify your bot token is correct
2. Check internet connectivity
3. Ensure bot is not restricted by Telegram firewall
4. Test with: `curl https://api.telegram.org/bot<token>/getMe`

### "No stocks met the filter criteria" Message

This is normal! It means:
- Market conditions don't meet current filter requirements
- All stocks are either oversold/overbought
- Trading volume is low
- No strong trends detected

### "No module named..." Error

Install missing dependencies:
```bash
pip install -r requirements.txt
```

Or just the essentials:
```bash
pip install yfinance pandas numpy requests
```

## What Results Look Like

**Telegram Message Example:**

```
📊 NSE F&O PCS Scan Results
🕐 2024-01-15 15:30:00

🎯 Found 8 Qualifying Stocks

Summary Metrics:
• Average Strength: 72.3%
• Highest Strength: 89.2%
• Average Volume Ratio: 1.85x

Top Stocks:
1. RELIANCE 🟢
   Price: ₹2,847.50 | SMA20: ₹2,825.00
   RSI: 56.3 | ADX: 28.5
   Strength: 89.2% | Volume: 2.1x

2. HDFCBANK 🟡
   Price: ₹1,652.35 | SMA20: ₹1,628.50
   RSI: 48.2 | ADX: 24.1
   Strength: 65.4% | Volume: 1.6x

... and 6 more stocks

⚠️ Disclaimer: For educational purposes only. Not financial advice.
```

### Legend
- 🟢 Green = High Strength (80%+)
- 🟡 Yellow = Medium Strength (60-79%)
- 🔴 Red = Lower Strength (<60%)

## Performance Tips

1. **Reduce Stock Universe**: Start with top 20 liquid stocks
2. **Use Cron Off-Hours**: Schedule for 4-5 PM IST (after market close)
3. **Cache Results**: Modify scanner to skip stocks with no recent volume
4. **Cloud Provider**: Use GitHub Actions to avoid local resource usage

## Advanced: Full Scanner with Patterns

If you want the advanced scanner (`telegram_scanner.py`):

```bash
# First fix the ta package issue:
pip install --upgrade setuptools wheel
pip install ta==0.10.2

# Then run:
python3 telegram_scanner.py
```

## Support & Issues

- **Telegram issues**: Check @BotFather or official Telegram docs
- **Python issues**: Ensure Python 3.8+ installed
- **Data issues**: yfinance sometimes has delays, try re-running in 5 minutes
- **Scanner issues**: Check logs with: `tail -f /var/log/nse_scanner.log`

## Security Notes

⚠️ **Important**: 
- Never commit bot tokens to git
- Use environment variables or `.env` files (add to `.gitignore`)
- Rotate tokens regularly in @BotFather
- Don't share Chat ID with untrusted parties

## Disclaimer

This scanner is for **educational and informational purposes only**. It is NOT financial advice. Options trading carries substantial risk. Always:
- Verify signals independently
- Use paper trading first
- Consult qualified financial advisors
- Never risk more than you can afford to lose
- Follow proper risk management

---

**Happy Trading! 📈**
