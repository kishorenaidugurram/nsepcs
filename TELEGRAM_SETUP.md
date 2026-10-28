# Telegram PCS Scanner Setup Guide

This guide explains how to set up the Telegram integration for the NSE F&O PCS Screener.

## Overview

The `run_scanner_telegram.py` script runs the PCS analysis and automatically sends results to your Telegram chat. It can be used as a scheduled task to run daily/weekly and notify you of trading opportunities.

## Prerequisites

1. A Telegram bot token (from BotFather)
2. Your Telegram chat ID
3. Python 3.7+
4. Required packages: `pandas`, `numpy`, `yfinance`, `requests`, `pytz`

## Step-by-Step Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` and follow the instructions
3. Send `/newbot` to create a new bot
4. Follow the prompts:
   - Choose a name for your bot (e.g., "NSE PCS Scanner")
   - Choose a username (must be unique, e.g., "nse_pcs_scanner_bot")
5. BotFather will give you a **Bot Token** that looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
6. Copy and save this token securely

### 2. Get Your Telegram Chat ID

1. Start a chat with your bot by searching for it and clicking `/start`
2. Add the bot to a group chat or keep it as a direct chat
3. Open this URL in your browser (replace TOKEN with your bot token):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
4. Look for `"chat":{"id":YOUR_CHAT_ID}` in the JSON response
5. Copy the **Chat ID** (a number, could be negative for groups)

### 3. Configure Environment Variables

Set these environment variables before running the script:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### For Linux/Mac:
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="123456789"
```

Then reload:
```bash
source ~/.bashrc
```

#### For Windows:
Set environment variables via System Properties or use PowerShell:
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_token"
$env:TELEGRAM_CHAT_ID = "your_chat_id"
```

### 4. Install Requirements

```bash
cd /path/to/nsepcs
pip install -r requirements.txt

# Or minimal install if requirements.txt has issues:
pip install pandas yfinance numpy requests pytz
```

## Running the Scanner

### Manual Run

```bash
python3 run_scanner_telegram.py
```

### Scheduled Run (Linux/Mac)

Use cron to run daily at 9:30 AM IST:

```bash
# Edit crontab
crontab -e

# Add this line:
30 9 * * * /usr/bin/python3 /path/to/nsepcs/run_scanner_telegram.py >> /var/log/pcs_scanner.log 2>&1

# Note: Adjust path and timing as needed
```

### Scheduled Run (Windows)

Use Task Scheduler:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (time)
4. Set action to run: `python3.exe "C:\path\to\nsepcs\run_scanner_telegram.py"`
5. Set environment variables in the action's advanced settings

## Understanding the Output

### Telegram Message

You'll receive a message like:

```
📊 NSE F&O PCS Screener
🕐 2024-10-28 09:45 IST

📈 5 High-Quality Opportunities Found:

1. RELIANCE | 💰₹3250
   🟢 HIGH (82%) | RSI:58 | Vol:1.8x

2. TCS | 💰₹3750
   🟢 HIGH (78%) | RSI:62 | Vol:2.1x

3. INFY | 💰₹4100
   🟡 MED (71%) | RSI:55 | Vol:1.5x

⚙️ Filters: Strength≥65% | Vol≥1.2x | RSI:40-75 | ADX≥15

Not financial advice • Do your own research
```

### CSV Export

You'll also receive a CSV file with:
- Symbol
- Price
- Strength %
- Confidence Level
- RSI
- ADX
- Volume Ratio

## Filter Explanation

| Filter | Default | Meaning |
|--------|---------|---------|
| **Pattern Strength** | ≥65% | Minimum strength score (0-100) |
| **Volume Ratio** | ≥1.2x | Current volume vs 20-day average |
| **RSI Range** | 40-75 | Relative Strength Index sweet spot |
| **ADX Minimum** | ≥15 | Trend strength indicator |

### Adjusting Filters

Edit `run_scanner_telegram.py` line ~330 to change filters:

```python
filters = {
    'min_volume_ratio': 1.2,  # Increase for stricter volume
    'rsi_min': 40,            # Increase to avoid oversold
    'rsi_max': 75,            # Decrease to avoid overbought
    'adx_min': 15,            # Increase for stronger trends
    'pattern_strength_min': 65, # Increase for better setups
}
```

## Stocks Analyzed

The scanner analyzes these **16 NSE stocks** by default:

- **Bank**: ICICIBANK, KOTAKBANK, SBIN, HDFCBANK, AXISBANK
- **IT**: INFY, TCS, HCLTECH, WIPRO
- **Diversified**: RELIANCE, LT, ITC
- **Auto**: MARUTI, TATAMOTORS
- **Consumer**: ASIANPAINT
- **Pharma**: SUNPHARMA

Add more stocks by editing the `stocks_to_scan` list in the script.

## Troubleshooting

### No Telegram message sent

**Check:**
1. Are environment variables set? `echo $TELEGRAM_BOT_TOKEN`
2. Is the token correct? Copy from BotFather
3. Is the chat ID correct? Verify via API
4. Does the bot have permission to send messages to the chat?

### No stocks found

**Reasons:**
- Market is closed
- All stocks failed to meet filter criteria
- Network issue fetching data

Try:
- Run during market hours (9:15-15:30 IST)
- Lower the `pattern_strength_min` value
- Check network connectivity

### Network timeout

The script has a 30-second timeout. If Yahoo Finance is slow:
1. Check your internet connection
2. Try running during off-peak hours
3. Or use a different data source (edit `get_stock_data()`)

## Testing

Before setting up the scheduler, test manually:

```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python3 run_scanner_telegram.py
```

You should receive a message within 2-3 minutes.

## Advanced: Custom Data Source

By default, the script uses **Yahoo Finance**. To use a different source:

1. Edit the `get_stock_data()` function
2. Replace `yf.Ticker()` with your data source
3. Ensure the returned DataFrame has: `Open`, `High`, `Low`, `Close`, `Volume`

## Support

If you encounter issues:

1. Check the error message in console
2. Verify Telegram bot token and chat ID
3. Ensure network connectivity
4. Check Python version: `python3 --version` (needs 3.7+)
5. Verify packages: `pip list | grep -E "pandas|yfinance|requests"`

## Disclaimer

⚠️ **This is for educational purposes only. Not financial advice.**

- Always do your own research
- Test strategies with paper trading first
- Never risk more than you can afford to lose
- Consult a financial advisor before making investment decisions

---

**Happy Trading! 📈**
