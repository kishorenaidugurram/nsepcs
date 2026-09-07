# NSE F&O PCS Screener - Telegram Integration Setup

## Overview

The NSE F&O PCS Screener can automatically scan stocks and send results to Telegram. This document explains how to set it up.

## Prerequisites

### 1. Python Dependencies

Install all required packages:

```bash
pip install -r requirements.txt requests
```

Or install individually:

```bash
pip install streamlit pandas numpy yfinance requests pytz ta plotly scikit-learn scipy beautifulsoup4 openpyxl
```

### 2. Telegram Setup

You need:
- A Telegram bot token
- Your Telegram chat ID

#### Getting a Telegram Bot Token

1. Open Telegram and search for "@BotFather"
2. Start the chat and send: `/newbot`
3. Follow the prompts to create a bot
4. BotFather will give you a token like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
5. Save this token

#### Getting Your Chat ID

1. Start a chat with your bot (message it first)
2. Go to: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Look for `"chat":{"id":123456789...}` in the response
5. The number is your Chat ID

## Configuration

### Option 1: Environment Variables (Recommended)

Set these environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

To make these persistent, add them to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Via Script

The scripts automatically detect the environment variables. No additional configuration needed.

## Running the Scanner

### Standalone Scan (Fast)

Run a quick scan of 15 Nifty 50 stocks:

```bash
python3 run_scanner_simple.py
```

### Full Scan

Run a comprehensive scan of 50+ stocks:

```bash
python3 run_scanner.py
```

### Expected Output

When Telegram is configured, you'll see results like:

```
📊 NSE F&O PCS Screener Results
📅 2026-09-07 10:30:45 IST

✅ Found 5 qualifying stocks

1. INFY
   💰 Price: ₹2500.00
   📊 Volume: 2.5x
   📈 RSI: 65.3
   🎯 Patterns: 1

[Results continue...]
```

## Scheduled Execution

### Using Cron (Linux/Mac)

Add to your crontab to run daily at 3:30 PM (after market close):

```bash
crontab -e
```

Add this line:

```cron
# Run screener daily at 3:30 PM IST
30 15 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_simple.py >> /var/log/pcs_scanner.log 2>&1
```

(Adjust the time as needed. The above runs Monday-Friday at 3:30 PM UTC)

### Using GitHub Actions

Create `.github/workflows/pcs_screener.yml`:

```yaml
name: PCS Screener

on:
  schedule:
    - cron: '30 10 * * 1-5'  # Daily at 10:30 AM UTC (3:30 PM IST, Mon-Fri)

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt requests
      - name: Run scanner
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 run_scanner_simple.py
```

Then add secrets to your GitHub repository:
1. Go to Settings → Secrets and variables → Actions
2. Add `TELEGRAM_BOT_TOKEN`
3. Add `TELEGRAM_CHAT_ID`

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt requests

COPY . .

CMD ["python3", "run_scanner_simple.py"]
```

Run with Docker:

```bash
docker build -t pcs-screener .
docker run -e TELEGRAM_BOT_TOKEN="..." -e TELEGRAM_CHAT_ID="..." pcs-screener
```

## Troubleshooting

### "Telegram not configured"

- Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Verify they're correct (no quotes in export)
- Test with: `echo $TELEGRAM_BOT_TOKEN`

### "ModuleNotFoundError"

Install missing packages:

```bash
pip install ta yfinance plotly scikit-learn scipy
```

### No stocks found

- The market might be closed
- Try running during market hours (9:15 AM - 3:30 PM IST, Mon-Fri)
- Check that your stocks list is updated

### Telegram message failed

- Verify bot token is correct
- Verify chat ID is correct
- Make sure you've messaged the bot first
- Check your internet connection

## Customization

### Adjusting Scanner Settings

Edit `run_scanner.py` or `run_scanner_simple.py`:

```python
DEFAULT_CONFIG = {
    'min_score': 55,  # Minimum pattern strength
    'max_stocks': 50,  # Max stocks to scan
    'rsi_min': 30,   # RSI range
    'rsi_max': 80,
    # ... other settings
}
```

### Changing Stocks to Scan

Modify the `get_stocks_to_scan()` function:

```python
def get_stocks_to_scan():
    return [
        'INFY.NS', 'TCS.NS', 'HDFCBANK.NS',  # Your stocks
        # ... add more
    ]
```

## Support

For issues:
1. Check the output logs
2. Verify Telegram token and chat ID
3. Test the Telegram bot manually
4. Check if dependencies are installed with `pip list`

## Tips

- **Best time to run**: After market close (3:30 PM IST) for same-day patterns
- **Avoid market hours**: Running during market hours may give incomplete data
- **Sample size**: Scanning 50 stocks takes ~2-3 minutes
- **Caching**: Yahoo Finance may rate-limit requests. Space out scans by at least 5 minutes

## Files

- `run_scanner_simple.py` - Basic screener (fast, 15 stocks)
- `run_scanner.py` - Full screener (comprehensive, 50 stocks)
- `telegram_notifier.py` - Telegram integration library
- `streamlit_app.py` - Main PCS scanner logic
- `SETUP_TELEGRAM.md` - This file

---

For more information about the PCS scanner, see [README.md](README.md)
