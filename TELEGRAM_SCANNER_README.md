# NSE F&O PCS Telegram Scanner

## Overview
Automated scanner that runs NSE F&O stock filtering and sends qualifying stocks to Telegram.

## What It Does
- Scans 208+ NSE F&O listed stocks
- Applies filter criteria:
  - **RSI**: 30-75 (healthy momentum)
  - **Moving Average Support**: Close above EMA-20 (3% tolerance)
  - **Volume**: Current volume >= 1.2x 20-day average
  - **Trend Strength**: ADX >= 20 (strong trend confirmation)

## Setup Requirements

### 1. Environment Variables
Set these to enable Telegram notifications:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 2. Get Telegram Credentials
1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Copy the **Bot Token**
3. Send a message to your bot
4. Get your Chat ID from: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`

### 3. Install Dependencies
```bash
pip install yfinance pandas numpy pytz requests
```

## Usage

### Run Scanner Locally
```bash
python3 telegram_scanner.py
```

### Run as Scheduled Task
Add to crontab (runs daily at 3:30 PM IST):
```bash
30 15 * * * cd /home/user/nsepcs && python3 telegram_scanner.py
```

## Features
- ✅ Multi-stock parallel scanning (10 workers)
- ✅ Technical indicator calculations (RSI, SMA, EMA)
- ✅ Real-time Telegram notifications
- ✅ JSON output for integration
- ✅ Graceful error handling

## Output Format
Results are returned as JSON:
```json
[
  {
    "symbol": "RELIANCE.NS",
    "price": 2850.50,
    "rsi": 58.5,
    "volume_ratio": 1.8,
    "timestamp": "2024-10-22 15:30:00 IST"
  }
]
```

## Current Status
- **Network Issue**: Remote environment has proxy restrictions blocking Yahoo Finance API
- **Solution**: Run locally on your machine or configure proxy settings

## Future Enhancements
- [ ] Support for alternative data providers (NSE API, Alpha Vantage)
- [ ] Configurable filter criteria via CLI arguments
- [ ] Email fallback when Telegram unavailable
- [ ] Database storage of historical scans
- [ ] Web dashboard for results visualization

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "CONNECT tunnel failed"
- Running in restricted network environment
- Request local/cloud execution with proper network access

### Telegram not sending
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Test with: `curl -X POST "https://api.telegram.org/botYOUR_TOKEN/sendMessage" -d "chat_id=YOUR_CHAT_ID&text=Test"`

## Files
- `telegram_scanner.py` - Main scanner script
- `streamlit_app.py` - Full Streamlit web application
- `requirements.txt` - Python dependencies

## Support
For issues or feature requests, check the git commit history or contact the maintainer.
