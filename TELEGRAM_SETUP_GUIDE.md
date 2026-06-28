# Stock Scanner with Telegram Integration - Setup Guide

## Overview
This guide will help you set up and run the NSE F&O stock scanner with Telegram notifications.

## Prerequisites

1. **Python 3.8+** installed
2. **Telegram Bot** (created via BotFather)
3. **Internet Connection** (for downloading stock data)

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts:
   - Give your bot a name (e.g., "Stock Scanner")
   - Give it a username (e.g., "stock_scanner_bot")
4. **Save the Token** you receive (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

## Step 2: Get Your Telegram Chat ID

1. Search for your bot in Telegram and send it any message
2. Visit this URL in your browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with your actual token

3. Look for your message in the response. Find the `"chat":{"id":` field
4. **Save your Chat ID** (a numeric value like: `123456789`)

## Step 3: Install Dependencies

```bash
# Navigate to the project directory
cd /path/to/nsepcs

# Install required packages
pip install -r requirements.txt

# If you have issues with 'ta' package, try:
pip install --upgrade setuptools wheel
pip install -r requirements.txt
```

## Step 4: Set Environment Variables

### On Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### On Windows (PowerShell):
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:TELEGRAM_CHAT_ID = "your_chat_id_here"
```

### Or create a `.env` file:
Create a file named `.env` in the project directory:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then load it:
```bash
set -a
source .env
set +a
```

## Step 5: Run the Scanner

### Using the Simple Scanner (Recommended):
```bash
# Quick scan of 50 stocks with Telegram notifications
python3 run_scanner_simple.py --max-stocks 50

# Scan all F&O stocks
python3 run_scanner_simple.py

# Scan with custom filters
python3 run_scanner_simple.py --max-stocks 100 --rsi-min 25 --rsi-max 80 --adx-min 15
```

### Options:
```
--max-stocks NUMBER        Maximum stocks to scan (default: 50)
--rsi-min VALUE           Minimum RSI value (default: 30)
--rsi-max VALUE           Maximum RSI value (default: 75)
--adx-min VALUE           Minimum ADX value (default: 20)
--volume-ratio VALUE      Minimum volume ratio (default: 1.2)
--strength-min VALUE      Minimum pattern strength (default: 65)
--telegram-token TOKEN    Telegram bot token
--telegram-chat-id ID     Telegram chat ID
```

## Example Usage

### Basic Scan:
```bash
python3 run_scanner_simple.py --max-stocks 50
```

### Aggressive Scanning (Lower filters):
```bash
python3 run_scanner_simple.py --max-stocks 100 \
  --rsi-min 20 --rsi-max 80 \
  --adx-min 15 \
  --volume-ratio 1.0 \
  --strength-min 60
```

### Conservative Scanning (Higher filters):
```bash
python3 run_scanner_simple.py --max-stocks 50 \
  --rsi-min 40 --rsi-max 70 \
  --adx-min 25 \
  --volume-ratio 1.5 \
  --strength-min 75
```

## Understanding the Filters

- **RSI (Relative Strength Index)**: Momentum oscillator
  - 30-40: Oversold (potential buying opportunity)
  - 40-70: Healthy range
  - 70+: Overbought (potential caution)
  - Default: 30-75 (all but extreme oversold)

- **ADX (Average Directional Index)**: Trend strength
  - < 20: Weak trend
  - 20-25: Moderate trend
  - > 25: Strong trend
  - Default: > 20 (requires moderate strength)

- **Volume Ratio**: Current volume vs average
  - < 1.0: Lower than average
  - 1.0-1.5: Normal
  - > 1.5: Above average (increased interest)
  - Default: > 1.2 (above normal activity)

- **Pattern Strength**: Confidence in detected pattern
  - 60-70%: Low confidence
  - 70-85%: Medium confidence
  - > 85%: High confidence
  - Default: > 65% (medium+)

## Troubleshooting

### "Failed to build wheel for ta"
Solution:
```bash
pip install --upgrade setuptools wheel
pip install ta==0.10.2
```

### "Telegram not configured"
Make sure your environment variables are set:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### "No stocks matched the criteria"
Try lowering the filters:
- Decrease `--rsi-min` (e.g., 25)
- Decrease `--adx-min` (e.g., 15)
- Decrease `--volume-ratio` (e.g., 1.0)
- Decrease `--strength-min` (e.g., 60)

### Proxy Issues (in remote environments)
The remote environment may block external data sources. Run on your local machine instead.

## Understanding the Output

When the scan completes, you'll see:
1. **Progress bar** showing scan progress
2. **Summary statistics**:
   - Number of stocks found
   - Average pattern strength
   - High confidence stocks
3. **Top 10 stocks** with details:
   - Stock symbol and price
   - Volume ratio
   - RSI and ADX values
   - Detected patterns
4. **Telegram message** sent to your bot

## Pattern Types Detected

1. **Current Day Breakout**: Stock breaking above resistance with high volume
2. **Cup and Handle**: William O'Neil classic pattern
3. **Flat Base Breakout**: Mark Minervini consolidation pattern
4. **Double Bottom**: Support level tested twice
5. **And more technical patterns**

## Scheduling Regular Scans

### Using cron (Linux/Mac):
```bash
# Run scanner daily at 3:30 PM IST
30 15 * * * cd /path/to/nsepcs && python3 run_scanner_simple.py >> /var/log/stock_scanner.log 2>&1
```

### Using Task Scheduler (Windows):
Create a batch file `run_scanner.bat`:
```batch
@echo off
set TELEGRAM_BOT_TOKEN=your_token
set TELEGRAM_CHAT_ID=your_chat_id
cd C:\path\to\nsepcs
python run_scanner_simple.py --max-stocks 100
```

Then schedule it using Windows Task Scheduler.

## Support & Documentation

For issues or questions:
1. Check the error messages for clues
2. Verify your Telegram token and chat ID
3. Ensure you have internet connectivity
4. Try with lower filter values to debug

## Disclaimer

This is a technical analysis tool for educational purposes. Past performance does not guarantee future results. Always do your own research before trading.

---

Happy scanning! 🚀
