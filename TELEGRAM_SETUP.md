# Telegram Integration for NSE F&O PCS Screener

This document explains how to set up and use the Telegram alert system for automated stock screening.

## Overview

The NSE F&O PCS Screener now includes two Python scripts for sending stock screening results to Telegram:

1. **`telegram_scanner_simple.py`** - Runs live stock screening with technical analysis
2. **`telegram_scanner_demo.py`** - Demo version with sample data (for testing)

## Prerequisites

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` to begin
3. Send `/newbot` to create a new bot
4. Follow the prompts:
   - Choose a name for your bot (e.g., "NSE Screener Bot")
   - Choose a username for your bot (e.g., "nse_screener_bot")
5. BotFather will provide you with a **Bot Token** that looks like:
   ```
   123456789:ABCDefGhIjklmnoPQRStuvWxyz1234567890
   ```

### 2. Get Your Telegram Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start`
3. The bot will respond with your **User ID** (your Chat ID)

## Setup Instructions

### Option 1: Using Environment Variables (Recommended)

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'

# Run the demo first to test
python3 telegram_scanner_demo.py

# Run the live scanner (requires internet access to Yahoo Finance)
python3 telegram_scanner_simple.py
```

### Option 2: Using a Configuration File

Create a file named `.telegram_config` in the project root:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then source it before running:

```bash
source .telegram_config
python3 telegram_scanner_simple.py
```

## Scripts Overview

### telegram_scanner_demo.py

**Purpose**: Test Telegram integration with sample data

**Usage**:
```bash
python3 telegram_scanner_demo.py
```

**Output**: 
- Displays sample stock screening results
- Shows how the Telegram message would be formatted
- Sends message to Telegram if credentials are configured
- No internet access required

**Sample Output**:
```
📈 NSE F&O PCS Screener Results
2026-10-26 09:18:09 IST

Found 6 stocks with bullish signals

1. RELIANCE 🟢 [82/100]
Price: ₹3245.75 | RSI: 58.3 | ADX: 28.5
Volume: 1.4x
  • Optimal RSI: 58.3
  • Strong uptrend (Price > SMA20 > SMA50)
  • MACD bullish (above signal)
  ...
```

### telegram_scanner_simple.py

**Purpose**: Run automated stock screening and send results to Telegram

**Stocks Analyzed**: 20 major NSE F&O stocks including:
- Large Caps: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC
- Mid Caps: KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT, BAJFINANCE, ULTRACEMCO

**Usage**:
```bash
python3 telegram_scanner_simple.py
```

**Requirements**:
- Internet access to Yahoo Finance API
- pandas, numpy, yfinance, requests libraries

**Output**:
- Analyzes each stock's technical indicators
- Calculates a bullish signal score (0-100)
- Sends top qualifying stocks to Telegram
- Includes RSI, ADX, Volume, and trend analysis

## Technical Indicators Used

### Scoring System

Each stock is scored based on multiple technical indicators:

| Indicator | Weight | Optimal Range |
|-----------|--------|----------------|
| RSI (Relative Strength Index) | 20% | 45-65 (normal 30-80) |
| Trend (SMA 20/50) | 25% | Price > SMA20 > SMA50 |
| MACD | 15% | Above signal line |
| ADX (Trend Strength) | 15% | > 25 for strong trend |
| Volume | 10% | > 1.2x average |
| **Total** | **100%** | **Max Score: 100** |

### Confidence Levels

- 🟢 **HIGH**: Score 70+ (Most bullish)
- 🟡 **MEDIUM**: Score 50-69 (Moderately bullish)
- 🔴 **LOW**: Score < 50 (Least bullish)

## Automating with Cron (Linux/Mac)

To run the screener automatically at a specific time:

```bash
# Edit crontab
crontab -e

# Add this line to run every day at 4 PM IST (8:30 AM UTC)
# Note: Adjust the time according to your timezone
0 16 * * * cd /path/to/nsepcs && export TELEGRAM_BOT_TOKEN='...' && export TELEGRAM_CHAT_ID='...' && python3 telegram_scanner_simple.py >> telegram_alerts.log 2>&1
```

## Automating with GitHub Actions

You can set up automated alerts using GitHub Actions:

1. Add secrets to your GitHub repository:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

2. Create a workflow file `.github/workflows/telegram-alert.yml`:

```yaml
name: NSE PCS Telegram Alert

on:
  schedule:
    # Run at 09:00 IST (03:30 UTC) every weekday
    - cron: '30 3 * * 1-5'
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run scanner
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 telegram_scanner_simple.py
```

## Troubleshooting

### 1. "Telegram credentials not configured"

**Solution**: Make sure environment variables are set:
```bash
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

### 2. "Failed to send message"

**Possible causes**:
- Invalid bot token or chat ID
- Network connectivity issue
- Telegram API is down

**Solution**:
- Verify token and chat ID are correct
- Test with `telegram_scanner_demo.py` first
- Check internet connection

### 3. "Insufficient data" for stocks

**Cause**: Yahoo Finance API is not accessible or stock data is not available

**Solution**:
- Check internet connection
- Try demo version instead: `python3 telegram_scanner_demo.py`
- Verify stock symbols are correct

## Security Considerations

1. **Never commit credentials**: Don't save tokens in version control
2. **Use environment variables**: Load from `.env` file (add to `.gitignore`)
3. **Limit bot permissions**: Use token with minimal required permissions
4. **Monitor activity**: Check your Telegram bot for suspicious activity

## Example .env File

Create a `.env` file in the project root (add to `.gitignore`):

```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Load it before running:
```bash
source .env
python3 telegram_scanner_simple.py
```

## Disclaimer

⚠️ **This is for educational and information purposes only**

- This tool does NOT provide financial advice
- Always do your own research before trading
- Past performance does not guarantee future results
- Only invest what you can afford to lose
- Consult with a qualified financial advisor

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the README.md in the project root
3. Check your Telegram bot token and chat ID
4. Verify network connectivity

## Next Steps

1. Get your Telegram bot token and chat ID
2. Test with: `python3 telegram_scanner_demo.py`
3. Run live scanner: `python3 telegram_scanner_simple.py`
4. Set up automated alerts using cron or GitHub Actions

Happy trading! 🚀
