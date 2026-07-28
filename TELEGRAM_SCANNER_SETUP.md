# NSE F&O Telegram Scanner Setup Guide

## Overview

The `run_telegram_scanner.py` script analyzes NSE F&O stocks for technical trading patterns and automatically sends results to your Telegram account.

## Current Status

⚠️ **Network Restriction**: The environment's egress proxy is currently blocking access to Yahoo Finance (fc.yahoo.com), which is required for real-time market data. This is an organization policy restriction (403 error).

### Solution Options

#### Option 1: Request Proxy Exception (Recommended)
Contact your organization's administrator to add `fc.yahoo.com` and `query2.finance.api.yahoo.com` to the allowed hosts list for your session/user.

#### Option 2: Run in a Different Environment
Run the script on a machine without proxy restrictions:
- Personal computer/laptop
- Cloud server with direct internet access
- CI/CD pipeline with external access

#### Option 3: Alternative Data Sources
Modify the script to use a different financial data provider:
- IEX Cloud (if allowed)
- Alpha Vantage
- Local NSE data files
- Your broker's API

## Setup Instructions (When Network Access is Available)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install python-telegram-bot
```

### 2. Create Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Type `/newbot` and follow the prompts
3. Note your **BOT_TOKEN** (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 3. Get Your Chat ID
1. Start a conversation with your bot
2. Use this Python snippet to get your Chat ID:
```python
import requests
BOT_TOKEN = "your_bot_token_here"
updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates").json()
chat_id = updates['result'][-1]['message']['chat']['id']
print(f"Your Chat ID: {chat_id}")
```

### 4. Configure Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 5. Test the Scanner
```bash
python3 run_telegram_scanner.py
```

### 6. Schedule as a Cron Job
Add to your crontab (runs at 9:30 AM IST every weekday):
```bash
crontab -e

# Add this line:
30 9 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 run_telegram_scanner.py >> /var/log/nse_scanner.log 2>&1
```

## Troubleshooting

### Telegram Message Not Sending?
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set correctly
- Ensure your bot has permission to send messages
- Check if your bot is blocked

### No Patterns Detected?
- Adjust filters in `get_config()` function
- Check if market conditions match your filter criteria
- Try reducing RSI_min or ADX_min values

### Data Fetch Errors?
- Verify network connectivity
- Check if proxy allows Yahoo Finance access
- Try alternative data sources (see Option 3 above)

## Script Configuration

Edit `get_config()` function in `run_telegram_scanner.py` to customize:

```python
def get_config():
    return {
        'rsi_min': 30,              # Minimum RSI value
        'rsi_max': 75,              # Maximum RSI value
        'adx_min': 20,              # Minimum ADX (trend strength)
        'ma_support': True,         # Check moving average support
        'ma_type': 'EMA',           # EMA or SMA
        'ma_tolerance': 3,          # % below MA before excluding
        # ... other settings
    }
```

## Features

✅ Analyzes 50 most-liquid NSE F&O stocks  
✅ Detects bullish trends using technical indicators  
✅ Filters results by confidence level (HIGH/MEDIUM/LOW)  
✅ Sends formatted results to Telegram  
✅ Saves results to JSON file  
✅ Runs headless (no UI required)  

## Technical Details

The scanner uses these technical indicators:
- **RSI** (Relative Strength Index) - Momentum oscillator
- **MACD** (Moving Average Convergence Divergence) - Trend strength
- **ADX** (Average Directional Index) - Trend confirmation
- **Moving Averages** - Support levels (SMA/EMA 20 & 50)
- **Bollinger Bands** - Volatility assessment

## Example Telegram Output

```
🚀 NSE F&O PCS Scanner Results
📅 2026-07-28 09:35 IST
📊 Total Patterns: 8

🟢 HIGH Confidence (3)
  • RELIANCE  Bullish MACD Crossover | ₹3,850.20
  • INFY      Bullish MA Stack | ₹2,650.00
  • HDFCBANK  Oversold Bounce Setup | ₹1,750.50

🟡 MEDIUM Confidence (5)
  • TCS       Bullish MACD Crossover | ₹3,250.00
  ... and 4 more

⚠️ Not financial advice. Always DYOR before trading.
```

## Disclaimer

⚠️ **Important**: This tool is for educational purposes only. It does NOT constitute financial advice. Always:
- Do your own research (DYOR)
- Consult with a qualified financial advisor
- Paper trade first before using real money
- Never risk more than you can afford to lose
- Understand technical analysis limitations

## Support

For issues or questions:
1. Check the logs: `tail -f /var/log/nse_scanner.log`
2. Enable debug logging by changing `logging.basicConfig(level=logging.DEBUG)`
3. Review proxy status: `curl http://127.0.0.1:36659/__agentproxy/status`
