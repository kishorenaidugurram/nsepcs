# NSE F&O PCS Scanner - Telegram Integration Setup Guide

## Overview
The `telegram_pcs_scanner.py` is a standalone Python script that runs the PCS (Put Credit Spread) analysis and sends qualifying stocks directly to your Telegram.

## Prerequisites

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a Telegram Bot

#### Step 1: Create Bot via BotFather
1. Open Telegram and search for **@BotFather**
2. Send `/start`
3. Send `/newbot`
4. Follow the prompts to name your bot
5. BotFather will provide a **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
6. Save this token securely

#### Step 2: Get Your Chat ID
1. Search for **@userinfobot** in Telegram
2. Send any message to it
3. It will reply with your **User ID** (or Chat ID)
4. This is a number like: `123456789`

## Configuration

### Option 1: Environment Variables (Recommended for Cron/Scheduled Tasks)

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Add to your `.bashrc` or `.zshrc` for persistent configuration:
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Create a `.env` File

Create a file named `.env` in the project directory:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then run the scanner:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); exec(open('telegram_pcs_scanner.py').read())"
```

## Usage

### Basic Usage (Default Stock List)
```bash
python telegram_pcs_scanner.py
```

### Scan Specific Stocks
```bash
python telegram_pcs_scanner.py RELIANCE.NS INFY.NS HDFCBANK.NS
```

### Expected Output
The script will:
1. Scan specified stocks for PCS opportunities
2. Filter by technical criteria (RSI, ADX, Volume, Support levels)
3. Display results in console
4. Save results to `/tmp/pcs_scan_results.json`
5. Send formatted message to your Telegram bot

### Example Telegram Message
```
📊 NSE F&O PCS Scanner Results
⏰ 2026-07-31 03:42:11 IST
📈 Found: 5 stocks

1. RELIANCE.NS
   💪 Strength: 78/100
   🎯 PCS Fit: 85%
   💹 Price: ₹2450.50
   📊 RSI: 58.2, ADX: 28.5

2. INFY.NS
   💪 Strength: 72/100
   🎯 PCS Fit: 82%
   💹 Price: ₹1850.25
   📊 RSI: 52.1, ADX: 24.3

... and 3 more stocks

⚠️ Not financial advice. Trade at your own risk.
```

## Automation with Cron

### Run Daily at 9:15 AM (After Market Open)
```bash
# Edit crontab
crontab -e

# Add this line (runs Monday-Friday at 9:15 AM):
15 9 * * 1-5 /usr/bin/python3 /path/to/nsepcs/telegram_pcs_scanner.py >> /path/to/nsepcs/logs/pcs_scanner.log 2>&1
```

### Run Multiple Times Daily
```bash
# Run at 9:15 AM and 2:00 PM (pre-close)
15 9 * * 1-5 export TELEGRAM_BOT_TOKEN="..."; export TELEGRAM_CHAT_ID="..."; python3 /path/to/telegram_pcs_scanner.py
0 14 * * 1-5 export TELEGRAM_BOT_TOKEN="..."; export TELEGRAM_CHAT_ID="..."; python3 /path/to/telegram_pcs_scanner.py
```

## Configuration Options

Edit `telegram_pcs_scanner.py` to modify filter criteria:

```python
DEFAULT_FILTERS = {
    'min_pattern_strength': 60,      # Minimum strength score (0-100)
    'min_pcs_suitability': 80,       # Minimum PCS fit score (0-100)
    'rsi_min': 45,                   # Minimum RSI value
    'rsi_max': 70,                   # Maximum RSI value
    'adx_min': 20,                   # Minimum ADX (trend strength)
    'ma_support': True,              # Check moving average support
    'ma_tolerance': 2,               # % tolerance from MA
    'lookback_days': 20,             # Days for resistance/support
    'volume_breakout_ratio': 2.0,    # Volume increase ratio
    'pattern_strength_min': 60,      # Min strength to qualify
}
```

## Modifying Stock List

Edit the `STOCK_LIST` in `telegram_pcs_scanner.py`:

```python
STOCK_LIST = [
    'RELIANCE.NS',
    'TCS.NS',
    'HDFCBANK.NS',
    # Add more stocks with .NS suffix
]
```

Or use the command-line to scan specific stocks:
```bash
python telegram_pcs_scanner.py RELIANCE.NS INFY.NS HDFCBANK.NS
```

## Troubleshooting

### Error: "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"
**Solution:** Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
```

### Error: "python-telegram-bot not installed"
**Solution:** Install the package:
```bash
pip install python-telegram-bot
```

### No stocks found
**Solutions:**
1. Check market hours (NSE: 9:15 AM - 3:30 PM IST)
2. Adjust filter criteria (lower `min_pattern_strength` or `min_pcs_suitability`)
3. Check data availability for stocks
4. Review logs for specific errors

### Network errors
**Solution:** Check internet connection and proxy settings:
```bash
python -c "import yfinance as yf; yf.Ticker('RELIANCE.NS').history(period='1d')"
```

## Testing Without Telegram

To test the scanner without Telegram credentials:
```bash
python telegram_pcs_scanner.py
# Results will print to console and save to /tmp/pcs_scan_results.json
```

View results:
```bash
cat /tmp/pcs_scan_results.json
```

## Advanced Usage

### Running in Background
```bash
python telegram_pcs_scanner.py &
```

### Running with Logging
```bash
python telegram_pcs_scanner.py > logs/scan_$(date +%Y%m%d_%H%M%S).log 2>&1
```

### Sending to Multiple Telegram Chats
Modify the script to send to multiple chat IDs:
```python
chat_ids = [os.getenv('TELEGRAM_CHAT_ID_1'), os.getenv('TELEGRAM_CHAT_ID_2')]
for chat_id in chat_ids:
    asyncio.run(scanner.send_telegram_message(message, telegram_token, chat_id))
```

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file with credentials to git
- Add `.env` to `.gitignore`
- Use environment variables for sensitive data
- Rotate bot tokens periodically
- Keep dependencies updated

## Support

For issues or questions:
1. Check the logs in `/tmp/pcs_scan_results.json`
2. Review filter settings in the script
3. Test with a single stock first
4. Check Telegram bot connectivity

## License

This tool is provided as-is for educational purposes. Always verify trading signals independently and consult with qualified advisors before trading.
