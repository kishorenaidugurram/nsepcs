# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview

The `run_scanner.py` script runs the NSE F&O PCS stock scanner and sends results directly to Telegram. This enables automated stock screening with real-time Telegram notifications.

## Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a conversation with BotFather
3. Send `/newbot`
4. Follow the prompts to create a new bot
5. BotFather will give you a **Bot Token** (looks like: `123456789:ABCDefGHIjklMNOpqrsTUVwxyz`)
6. Copy this token - you'll need it in the next step

### 2. Get Your Chat ID

1. Search for `@userinfobot` in Telegram
2. Start a conversation with it
3. It will display your User ID (Chat ID)
4. Copy this ID - you'll need it in the next step

### 3. Set Environment Variables

Set the following environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 4. Run the Scanner

```bash
python3 run_scanner.py
```

## Scanner Output

The scanner will:
1. Scan all NSE F&O stocks (or custom list)
2. Detect technical chart patterns
3. Filter stocks by strength (default: 65%)
4. Send results to Telegram grouped by confidence level:
   - 🟢 **HIGH**: Confidence >= 85% (most reliable)
   - 🟡 **MEDIUM**: Confidence 70-84% (good signals)
   - 🔴 **LOW**: Confidence < 70% (speculative)

## Fallback Behavior

If Telegram credentials are not set:
- Results are saved to `scanner_results.json`
- Results are also saved to `scanner_results.csv`
- A preview of the message is printed to console

## Configuration

Edit `run_scanner.py` to customize:

```python
config = {
    'rsi_min': 30,              # Minimum RSI value
    'rsi_max': 75,              # Maximum RSI value
    'adx_min': 20,              # Minimum ADX (trend strength)
    'min_volume_ratio': 1.2,    # Volume confirmation ratio
    'pattern_strength_min': 65, # Minimum pattern strength %
    'ma_support': True,         # Check moving average support
    # ... more options
}
```

## Scheduling with Cron

To run the scanner daily at 3:30 PM IST (after market close):

```bash
# Edit crontab
crontab -e

# Add this line (3:30 PM IST = 10:00 AM UTC)
0 10 * * 1-5 cd /home/user/nsepcs && python3 run_scanner.py >> /var/log/scanner.log 2>&1
```

## Troubleshooting

### "Missing Telegram credentials"
- Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables
- Results will still be saved to JSON/CSV files

### "Connection error to Yahoo Finance"
- Check your internet connection
- Verify the proxy settings (if behind corporate proxy)
- Try running from a different network

### "No stocks found"
- Adjust `pattern_strength_min` lower (e.g., 60 instead of 65)
- Check if market data is available
- Verify the scanner filters in the config

## Dependencies

- `yfinance`: Stock data fetching
- `pandas`, `numpy`: Data processing
- `requests`: Telegram API calls
- `ta` (custom): Technical analysis indicators

## Security

- Never commit your TELEGRAM_BOT_TOKEN to git
- Use environment variables for credentials
- Use `.env` files locally (but don't commit to git)

## Error Handling

The scanner handles:
- Network failures gracefully
- Missing or incomplete data
- Invalid stock symbols
- API rate limiting

Results are still sent even if some stocks fail to load.

## Advanced Usage

### Use Different Stock Universe

Modify the stocks list in `run_scanner.py`:
```python
config = {
    'stocks_to_scan': ['INFY.NS', 'TCS.NS', 'RELIANCE.NS'],  # Custom list
    # ... rest of config
}
```

### Filter by Confidence Level

Edit the message formatting in `format_results_for_telegram()` to:
- Only show HIGH confidence stocks
- Limit number of results
- Add custom columns/metrics

## Support

For issues or questions about the NSE F&O PCS Scanner, refer to the main README.md

## Disclaimer

This is an automated trading analysis tool for educational purposes. It is NOT financial advice. Always:
- Conduct your own research
- Consult with a financial advisor
- Paper trade before using real capital
- Understand the risks of options trading
