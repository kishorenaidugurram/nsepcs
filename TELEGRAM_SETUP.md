# Telegram Stock Scanner Setup Guide

## Overview

Two scanner scripts have been created to run the NSE F&O stock screening automatically and send results to your Telegram:

1. **`scanner_standalone.py`** - Lightweight, production-ready scanner
2. **`run_scanner_telegram.py`** - Full-featured scanner with streamlit app integration

## Requirements

### 1. Telegram Bot Setup

#### Step 1: Create a Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send command `/start`
3. Send command `/newbot`
4. Follow the prompts:
   - Give your bot a name (e.g., "NSE Stock Scanner")
   - Give it a username (must end with "bot", e.g., "nse_stock_scanner_bot")
5. Copy the **API Token** provided (looks like: `123456789:ABCDefGHIjklmnOPQRstuvwxYZ`)

#### Step 2: Get Your Chat ID
1. Start a conversation with your bot by sending any message
2. Open this URL in your browser (replace YOUR_TOKEN):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Look for `"chat"` in the JSON response and copy the `"id"` value

### 2. Environment Variables Setup

Set these environment variables where you run the script:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**For Scheduled Tasks (GitHub Actions / Cron):**

Add these as secrets in your repository or set them in your execution environment.

### 3. Network Requirements

The scanners require internet access to:
- **Yahoo Finance API** - For stock price and volume data
- **Telegram API** - For sending messages

If running in a restricted network, ensure:
- HTTPS outbound connections are allowed
- Proxy settings are properly configured
- No firewalls are blocking these services

## Usage

### Quick Start - Standalone Scanner

```bash
# Set Telegram credentials
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run the scanner
python3 scanner_standalone.py
```

### With Streamlit App Integration

```bash
python3 run_scanner_telegram.py
```

### Automated Scheduling

#### Option A: Linux Cron Job

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 3:30 PM IST (after market close)
30 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_id python3 scanner_standalone.py >> /var/log/scanner.log 2>&1
```

#### Option B: GitHub Actions

Create `.github/workflows/scanner.yml`:

```yaml
name: Daily Stock Scanner

on:
  schedule:
    - cron: '30 15 * * 1-5'  # 3:30 PM IST (or adjust for your timezone)

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install yfinance pandas numpy requests pytz
      
      - name: Run scanner
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 scanner_standalone.py
```

Then add secrets in GitHub repository settings:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Default Filter Settings

The scanner uses these default technical criteria:

| Setting | Value |
|---------|-------|
| RSI Min | 30 |
| RSI Max | 75 |
| ADX Min | 20 |
| Volume Ratio | 1.2x average |
| Breakout Volume | 2.0x average |
| Lookback Period | 20 days |
| Min Pattern Strength | 65% |
| Analysis Mode | Daily + Weekly Combined |

### Patterns Detected

- **Breakout** - Current day breakout above 20-day high
- **Double Bottom** - Two recent lows at similar levels
- **Cup & Handle** - Classic chart pattern formation
- More patterns available (toggle in configuration)

## Output Format

### Telegram Message Example

```
NSE F&O Scan Results
Generated: 15-Aug-2024 15:35 IST
📊 Stocks Found: 12
────────────────────────────────

1. RELIANCE @ ₹2,850.25
   📈 Breakout + Cup & Handle
   💪 Strength: 78%

2. TCS @ ₹3,650.50
   📈 Double Bottom
   💪 Strength: 72%

... and 10 more stocks
────────────────────────────────
⚠️  For info only. Not financial advice.
```

### JSON Output

Results are also saved to `/tmp/scan_results.json` for further analysis:

```json
{
  "timestamp": "2024-08-15T15:35:00+05:30",
  "total_stocks": 12,
  "stocks": [
    {
      "symbol": "RELIANCE",
      "price": 2850.25,
      "patterns": ["Breakout", "Cup & Handle"],
      "strength": 78.0
    }
  ]
}
```

## Troubleshooting

### Issue: "Telegram credentials not configured"

**Solution:** Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
```

### Issue: "ConnectionError - Failed to download ticker data"

**Possible Causes:**
1. No internet connection
2. Proxy blocking Yahoo Finance
3. API rate limiting

**Solution:**
- Verify internet connectivity
- Check proxy settings
- Reduce number of stocks to scan
- Add retry logic (examples in code comments)

### Issue: "No stocks met the filter criteria"

This can happen when:
- Market is in strong downtrend
- All stocks are overbought (RSI > 75)
- No volume breakouts detected

**Solution:** Adjust filter settings in the script:
```python
config['rsi_min'] = 25  # Lower RSI threshold
config['rsi_max'] = 80  # Higher RSI threshold
config['adx_min'] = 15  # Lower ADX threshold
```

## Customization

### Modify Filter Criteria

Edit the `config` dictionary in the script:

```python
config = {
    'rsi_min': 30,           # Adjust min RSI
    'rsi_max': 75,           # Adjust max RSI
    'adx_min': 20,           # Adjust min ADX
    'min_volume_ratio': 1.2, # Volume threshold
    'pattern_strength_min': 65, # Pattern quality
}
```

### Add Custom Stocks

Modify the `COMPLETE_NSE_FO_UNIVERSE` list or create a custom list:

```python
custom_stocks = [
    'RELIANCE.NS',
    'TCS.NS',
    'INFY.NS',
]
config['stocks_to_scan'] = custom_stocks
```

### Change Scan Frequency

Adjust the cron schedule:
- `30 10 * * 1-5` - 10:30 AM on weekdays
- `30 15 * * 1-5` - 3:30 PM on weekdays (after market close)
- `30 9,14 * * 1-5` - Both 9:30 AM and 2:30 PM

## Performance

- **Scan Time**: ~30-60 seconds for 200 stocks
- **Data Latency**: Real-time (daily close only)
- **Memory Usage**: ~50-100 MB
- **CPU Usage**: Minimal during scan

## Security Notes

⚠️ **Important:**
- Never commit Telegram tokens to public repositories
- Use GitHub Secrets for CI/CD environments
- Rotate bot tokens periodically
- Monitor bot activity for unauthorized access

## Support & Debugging

### Enable Debug Logging

```bash
python3 -u scanner_standalone.py 2>&1 | tee debug_log.txt
```

### Check Telegram Connectivity

```bash
python3 << 'EOF'
import os
import requests

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if token and chat_id:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": "Test message"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print("Telegram credentials not set")
EOF
```

## Disclaimer

⚠️ **Trading Disclaimer**

This scanner is for educational and informational purposes only. It is NOT financial advice.

- Past performance does not guarantee future results
- Options trading involves substantial risk
- You can lose your entire investment
- Always paper trade first
- Consult with a financial advisor before trading
- Never risk money you cannot afford to lose

## Additional Resources

- [NSE F&O Scanner Streamlit App](https://nse-fo-pcs-screener.streamlit.app)
- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [Yahoo Finance Data Guide](https://finance.yahoo.com/)
- [Technical Analysis Basics](https://www.investopedia.com/terms/t/technicalanalysis.asp)

---

**Last Updated**: August 2024  
**Version**: 1.0
