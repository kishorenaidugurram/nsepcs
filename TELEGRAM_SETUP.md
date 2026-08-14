# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview
The `run_scanner.py` script scans NSE F&O stocks for Put Credit Spread (PCS) trading opportunities and automatically sends results to your Telegram channel/group.

## Features
- **Automated Stock Screening**: Analyzes 30+ liquid NSE F&O stocks
- **Smart Filtering**: 
  - RSI Range: 30-75 (optimal momentum zone)
  - ADX > 20 (confirms trend strength)
  - Price above SMA-20 (supports uptrend)
  - Volume > 1.2x average (confirms interest)
- **Telegram Notifications**: Results sent directly to your Telegram
- **Daily Execution**: Run via cron for scheduled analysis

## Setup Instructions

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "PCS Scanner Bot")
4. BotFather will provide your **Bot Token** - copy it
   - Example: `123456789:ABCDefGHIjklmNOpqrsTUVwxyzABCDEfg`

### Step 2: Get Your Chat ID

1. Create a private group or use a channel for alerts
2. Add your new bot to the group/channel
3. Send any message to the group
4. Visit this URL in your browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with your actual token
5. Look for `"chat"."id"` in the response - this is your **Chat ID**
   - Example: `-1001234567890` (for groups)
   - Example: `1234567890` (for direct messages)

### Step 3: Configure Environment Variables

#### On Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### On Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### Persistent Setup (Linux/Mac):
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then run: `source ~/.bashrc` (or your shell config file)

## Usage

### Manual Run
```bash
python3 run_scanner.py
```

### Scheduled Daily Run (Linux/Mac)

#### Using Cron (Every day at 3 PM IST):
```bash
# Edit crontab
crontab -e

# Add this line:
0 15 * * 1-5 cd /path/to/nsepcs && TELEGRAM_BOT_TOKEN="token" TELEGRAM_CHAT_ID="id" python3 run_scanner.py
```

#### Using Python Schedule:
Create a file `scheduler.py`:
```python
import schedule
import time
import subprocess
import os

def run_scanner():
    env = os.environ.copy()
    env['TELEGRAM_BOT_TOKEN'] = 'your_token'
    env['TELEGRAM_CHAT_ID'] = 'your_id'
    subprocess.run(['python3', 'run_scanner.py'], env=env)

schedule.every().weekday(0).at("15:00").do(run_scanner)  # Monday-Friday at 3 PM

while True:
    schedule.run_pending()
    time.sleep(60)
```

Run with: `python3 scheduler.py &`

### Docker Setup (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt run_scanner.py ./
RUN pip install -r requirements.txt
CMD python3 run_scanner.py
```

Build and run:
```bash
docker build -t pcs-scanner .
docker run -e TELEGRAM_BOT_TOKEN=token -e TELEGRAM_CHAT_ID=id pcs-scanner
```

## Output Example
```
📊 PCS Scanner Results
Found: 5 stocks
──────────────────────
1. RELIANCE
₹2850 | RSI:55 | ADX:25 | Vol:1.8x

2. TCS
₹3420 | RSI:48 | ADX:22 | Vol:1.5x

... +3 more
```

## Troubleshooting

### "Telegram not configured" error
- Check environment variables are set: `echo $TELEGRAM_BOT_TOKEN`
- Verify bot token and chat ID are correct
- Test with: `curl -X POST https://api.telegram.org/botTOKEN/sendMessage -d chat_id=ID -d text=Test`

### No stocks found
- This is normal on low-volume days
- Check market hours: NSE operates 9:15 AM - 3:30 PM IST
- Verify internet connection

### Network connectivity issues
- Ensure Yahoo Finance can be accessed
- Check proxy/firewall settings
- Test with: `curl https://query1.finance.yahoo.com`

## Stock Selection Criteria

The scanner filters for stocks meeting these criteria (default settings):

| Criteria | Value | Reason |
|----------|-------|--------|
| RSI | 30-75 | Optimal momentum without overbought/oversold |
| ADX | > 20 | Confirms strong directional trend |
| Price vs SMA-20 | Above | Validates uptrend |
| Volume | > 1.2x avg | Confirms institutional interest |

## Customization

Edit `run_scanner.py` to modify:
- Stock list (line: `NSE_FO_STOCKS = [...]`)
- RSI range (line: `if 30 <= rsi <= 75`)
- ADX threshold (line: `and adx > 20`)
- Volume multiplier (line: `and vol_ratio > 1.2`)
- Number of results (line: `[:20]`)

## API Reference

### get_stock_data(symbol)
Fetches 3 months of data and calculates technical indicators (RSI, ADX, SMA, EMA)

### scan()
Filters stocks based on criteria, returns list of matching stocks with metrics

### send_telegram(message)
Sends formatted message to Telegram, returns True/False

## Support

For issues:
1. Check logs: Run without Telegram to see scanner output
2. Verify credentials in `getUpdates` API response
3. Ensure Python packages installed: `pip install -r requirements.txt`
4. Check market hours and trading days

## Security Notes

⚠️ **Never commit bot tokens to Git**
- Use environment variables only
- Add to `.gitignore`: `*.env`, `.env.local`
- Consider using `.env` file with python-dotenv

Example `.env` file:
```
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
```

Load with:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

**Last Updated**: 2024-08-14
**Scanner Version**: 1.0
