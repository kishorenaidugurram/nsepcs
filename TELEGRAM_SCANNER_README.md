# NSE F&O PCS Scanner - Telegram Integration

## Quick Start

### 1. Basic Usage (No Telegram)
```bash
cd /home/user/nsepcs
python3 simple_scanner.py
```
This will scan stocks and save results to `/tmp/pcs_scanner_results.json`

### 2. With Telegram Notifications

**First Time Setup:**
1. Create a Telegram bot:
   - Open Telegram and message [@BotFather](https://t.me/botfather)
   - Type `/newbot` and follow instructions
   - Copy the API token provided

2. Get your Chat ID:
   - Send any message to your newly created bot
   - Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find the `"id"` in the `"chat"` section

3. Set environment variables and run:
```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvWXYZ"
export TELEGRAM_CHAT_ID="987654321"
python3 /home/user/nsepcs/simple_scanner.py
```

### 3. Scheduled Daily Execution

Add to crontab (runs at 3:15 PM IST daily on weekdays):
```bash
crontab -e
```

Add this line:
```
15 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="YOUR_TOKEN" TELEGRAM_CHAT_ID="YOUR_CHAT_ID" python3 simple_scanner.py >> /tmp/pcs_scan.log 2>&1
```

## Default Filter Settings

The scanner uses these default filters (matching Streamlit app):

| Filter | Value |
|--------|-------|
| RSI Min | 30 |
| RSI Max | 75 |
| ADX Minimum | 20 |
| Min Volume Ratio | 1.2x |
| Lookback Days | 20 |
| Pattern Strength Min | 65% |

## What It Scans For

✅ **Current Day Breakouts**
- Stock breaks above 20-day resistance
- Volume surges (2x+ average)
- Strong closing price above resistance

✅ **Technical Validation**
- RSI between 30-75 (not oversold/overbought)
- ADX >= 20 (trend strength)
- Volume confirmation (1.2x+ average)

## Output

### Terminal Output
Shows summary of found stocks with scores

### JSON File (`/tmp/pcs_scanner_results.json`)
```json
{
  "timestamp": "2024-01-15 15:30:00 IST",
  "total_results": 5,
  "top_10_stocks": [
    {
      "rank": 1,
      "symbol": "RELIANCE",
      "score": 85.5,
      "rsi": 55.2,
      "adx": 28.5,
      "price": 2750.50
    }
  ]
}
```

### Telegram Message
- List of top 10 qualifying stocks
- Score, RSI, and ADX values
- Pattern detection summary

## Troubleshooting

### "No qualifying stocks found"
Try adjusting filters:
```python
# In simple_scanner.py, modify config dict:
config = {
    'rsi_min': 25,      # Lower from 30
    'rsi_max': 80,      # Higher from 75
    'adx_min': 15,      # Lower from 20
    'min_volume_ratio': 1.0,  # Lower from 1.2
    'pattern_strength_min': 60  # Lower from 65
}
```

### Telegram not sending
1. Verify credentials are correct
2. Test with curl:
```bash
curl -X POST https://api.telegram.org/botYOUR_TOKEN/sendMessage \
  -d chat_id=YOUR_CHAT_ID \
  -d text="Test message"
```

### Connection errors
The scanner requires internet access to fetch stock data from Yahoo Finance. Ensure:
- No proxy blocking finance.yahoo.com
- Network timeout is adequate
- Try with `timeout=30` in simple_scanner.py

## Files

- `simple_scanner.py` - Main scanner script (recommended)
- `run_scanner.py` - Alternative comprehensive version
- `telegram_scanner.py` - Additional variant
- `TELEGRAM_SCANNER_README.md` - This file

## Support

All three scripts follow the same pattern:
1. Fetch historical stock data (last 3 months)
2. Calculate technical indicators (RSI, ADX)
3. Detect breakout patterns
4. Apply filters
5. Send qualifying stocks to Telegram
6. Save results to JSON file

## Next Steps

1. ✅ Create Telegram bot credentials
2. ✅ Set environment variables
3. ✅ Run the scanner for first time
4. ✅ Verify results in Telegram
5. ✅ Add to crontab for daily automation

Enjoy your automated PCS screening!
