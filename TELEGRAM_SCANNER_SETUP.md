# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview
`run_scanner_telegram.py` is a standalone script that runs the NSE F&O PCS scanner and automatically sends results to your Telegram chat.

## Setup Instructions

### 1. Create a Telegram Bot
- Open Telegram and search for **@BotFather**
- Send `/start` and then `/newbot`
- Follow the prompts to create your bot
- BotFather will provide you with a **Bot Token** (e.g., `123456789:ABCDefGhIjKlMnOpQrStUvWxYz`)

### 2. Get Your Chat ID
- Send a message to your newly created bot (even just `/start`)
- Open this URL in your browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
- Look for the `"chat"` object and find the `"id"` field
- This is your **Chat ID** (e.g., `987654321`)

### 3. Configure Environment Variables
Set these environment variables before running the script:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or add them to your system environment or `.env` file.

### 4. Run the Scanner

**Basic usage:**
```bash
python run_scanner_telegram.py
```

**With custom configuration** (edit the script):
```python
MIN_PCS_SCORE = 55        # Minimum PCS score threshold
MAX_STOCKS = 50           # Maximum stocks to scan (None for all)
```

## Output
The script will:
1. Scan up to 50 stocks from the NSE F&O universe
2. Calculate PCS scores for each stock
3. Filter stocks with score >= 55
4. Send formatted results to your Telegram chat
5. Save results to `/tmp/pcs_scan_YYYYMMDD_HHMMSS.txt`

## Result Format
Results are grouped by confidence level:
- **🟢 HIGH CONFIDENCE** (Score >= 75)
- **🟡 MEDIUM CONFIDENCE** (Score 60-74)
- **🔴 LOW CONFIDENCE** (Score < 60)

For each stock:
- Symbol name
- PCS Score (0-100)
- Current price
- RSI value

## Scheduling with Cron
To run the scanner automatically every day at 9:30 AM:

```bash
crontab -e
```

Add this line:
```
30 9 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_id /usr/bin/python3 run_scanner_telegram.py
```

(Mon-Fri only, 9:30 AM IST)

## Features

### PCS Score Calculation (0-100 scale)
- **Bullish Momentum (30%)**: RSI optimization (sweet spot 45-65)
- **Trend Strength (25%)**: MACD histogram analysis
- **Support Proximity (20%)**: Distance from SMA(20)
- **Volatility Assessment (15%)**: Optimal range 15-35%
- **Volume Confirmation (10%)**: Above-average volume validation

### Filter Criteria
- Minimum PCS Score: 55 (configurable)
- Data Period: 3 months of daily data
- Minimum History: 50 trading days

## Troubleshooting

### Telegram Connection Issues
- Verify your Bot Token and Chat ID are correct
- Make sure the bot has permission to send messages to your chat
- Check that the bot is not rate-limited

### No Data Retrieved
- Yahoo Finance API connectivity issues
- Check your internet connection
- Some stocks may not have sufficient historical data

### Empty Results
- All stocks fell below the minimum PCS score threshold
- Try lowering MIN_PCS_SCORE value
- Check market conditions - low volatility periods may not generate qualifying trades

## Important Disclaimers

⚠️ **DISCLAIMER**: This scanner is for educational purposes only and should NOT be used as financial advice. Always do your own research and consult with a qualified financial advisor before making any trading decisions.

- Options trading involves substantial risk
- You can lose your entire investment
- Past performance does not guarantee future results
- Always paper trade first before live trading

## Support

For issues or questions, refer to the main README.md in this repository.
