# NSE F&O PCS Scanner - Telegram Bot Integration

This guide explains how to set up the scanner to send stock screening results to Telegram automatically.

## Overview

The scanner has been enhanced with three runnable scripts:

1. **`run_scanner_demo.py`** - Demo mode with sample data (works without network access)
2. **`run_scanner_simple.py`** - Production mode (fetches real data from Yahoo Finance)
3. **`run_scanner_telegram.py`** - Full-featured scanner with advanced pattern detection

## Quick Setup

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command `/newbot`
3. Follow the prompts:
   - Choose a name for your bot (e.g., "NSE PCS Scanner")
   - Choose a username (e.g., "nse_pcs_bot")
4. Save the **BOT TOKEN** you receive (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`)

### Step 2: Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send any message to it
3. It will reply with your **Chat ID** (a number like: `987654321`)

### Step 3: Configure Environment Variables

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, or your deployment environment):

```bash
export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklmnoPQRstuvWXYZ'
export TELEGRAM_CHAT_ID='987654321'
```

Or set them inline when running:

```bash
TELEGRAM_BOT_TOKEN='your_token' TELEGRAM_CHAT_ID='your_id' python3 run_scanner_simple.py
```

### Step 4: Run the Scanner

```bash
# Demo mode (sample data)
python3 run_scanner_demo.py

# Production mode (real data)
python3 run_scanner_simple.py

# Or with environment variables
TELEGRAM_BOT_TOKEN='...' TELEGRAM_CHAT_ID='...' python3 run_scanner_simple.py
```

## What You'll Receive

The scanner sends two messages to Telegram:

1. **Summary Message**: Lists top qualifying stocks with:
   - Symbol name
   - Current price
   - Technical scores (RSI, ADX, Volume)
   - Pattern status (breakout/qualified)

2. **CSV File**: Complete list of all qualifying stocks for spreadsheet analysis

## Filter Criteria

The scanner uses these default filters:

- **RSI (Relative Strength Index)**: 30-75 (optimal momentum range)
- **ADX (Average Directional Index)**: 20+ (trend strength)
- **Volume Ratio**: 1.2x+ (above-average volume)
- **Lookback Period**: 20 days (consolidation window)

## Scheduling with Cron

To run the scanner automatically after market close:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 3:45 PM IST on weekdays)
45 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN='your_token' TELEGRAM_CHAT_ID='your_id' python3 run_scanner_simple.py >> /tmp/scanner.log 2>&1
```

## System Requirements

### For `run_scanner_demo.py` (No dependencies)
- Python 3.7+
- No additional packages needed

### For `run_scanner_simple.py` (Recommended)
```bash
pip install yfinance pandas numpy scipy requests
```

### For `run_scanner_telegram.py` (Full features)
```bash
pip install -r requirements.txt
```

## Troubleshooting

### "Telegram credentials not configured"
- Ensure environment variables are set correctly
- Check spelling: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Test with: `echo $TELEGRAM_BOT_TOKEN`

### "No data available"
- Check network connectivity to Yahoo Finance
- Some networks/proxies may block stock data APIs
- Use the demo mode (`run_scanner_demo.py`) to test Telegram integration

### "Network timeout"
- Yahoo Finance may be rate limiting
- Try reducing `SCAN_MAX_STOCKS` environment variable
- Increase wait time between requests in the code

## Architecture

### Data Flow

```
┌─────────────────────────────────────────┐
│  Scanner Scripts                         │
│  (run_scanner_*.py)                     │
└──────────────────┬──────────────────────┘
                   │
                   ├─→ Yahoo Finance API (for stock data)
                   │
                   ├─→ Technical Analysis (RSI, ADX, MACD)
                   │
                   └─→ Telegram API (for notifications)
```

### Filter Logic

```
For each stock:
  1. Fetch price/volume data
  2. Calculate technical indicators
  3. Check RSI filter (30-75)
  4. Check ADX filter (20+)
  5. Check Volume filter (1.2x+)
  6. Detect breakout patterns
  7. Calculate strength score (0-100)
  8. Send to Telegram if qualifies
```

## Script Comparison

| Feature | demo | simple | telegram |
|---------|------|--------|----------|
| Demo data | ✅ | ❌ | ❌ |
| Yahoo Finance | ❌ | ✅ | ✅ |
| Telegram integration | ✅ | ✅ | ✅ |
| Advanced patterns | ❌ | ❌ | ✅ |
| Weekly validation | ❌ | ❌ | ✅ |
| News analysis | ❌ | ❌ | ✅ |
| Chart generation | ❌ | ❌ | ✅ |
| Dependencies | None | Minimal | Full |

## Advanced Usage

### Custom Stock Universe

Edit the scanner script to change which stocks are analyzed:

```python
# In any run_scanner_*.py
CUSTOM_STOCKS = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']
stocks_to_scan = CUSTOM_STOCKS[:max_stocks]
```

### Custom Filter Criteria

Modify these values in the scanner:

```python
# RSI filter
rsi_min = 30    # Changed from 30
rsi_max = 75    # Changed from 75

# ADX filter
adx_min = 20    # Changed from 20

# Volume filter
min_volume_ratio = 1.2  # Changed from 1.2
```

### Environment Configuration

```bash
# Set custom scan parameters
export SCAN_MAX_STOCKS=100           # Scan 100 stocks instead of 50
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_CHAT_ID='...'

python3 run_scanner_simple.py
```

## Production Deployment

For production use on a server:

1. Set up bot on a never-restarting service:
```bash
# Using systemd
sudo nano /etc/systemd/system/nse-scanner.service
```

2. Add:
```ini
[Unit]
Description=NSE F&O PCS Scanner
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/nsepcs
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_id"
ExecStart=/usr/bin/python3 /home/your_user/nsepcs/run_scanner_simple.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable nse-scanner
sudo systemctl start nse-scanner
```

## Support & Debugging

### Enable Debug Output

```bash
# Add debug logging
python3 -u run_scanner_simple.py 2>&1 | tee debug.log

# Check logs
tail -f debug.log
```

### Test Telegram Connection

```bash
# Test bot token validity
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Send test message
python3 -c "
import requests
import os
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
msg = 'Test message'
requests.post(f'https://api.telegram.org/bot{token}/sendMessage', 
              json={'chat_id': chat_id, 'text': msg})
"
```

## Safety & Best Practices

⚠️ **Important Security Notes:**

1. **Never share your bot token publicly**
   - Keep it in environment variables, not in code
   - Use `.env` files for local development (add to `.gitignore`)

2. **Limit stock scope**
   - Scanning many stocks takes longer and may hit rate limits
   - Start with 20-50 stocks and increase gradually

3. **Monitor resource usage**
   - Each scan fetches 3 months of data per stock
   - Adjust `period` parameter if needed

4. **Rate limiting**
   - Yahoo Finance may rate limit if too many requests
   - Add delays between requests if experiencing issues

## Next Steps

1. ✅ Set up Telegram bot and chat ID
2. ✅ Configure environment variables
3. ✅ Run demo mode to test: `python3 run_scanner_demo.py`
4. ✅ Run production mode: `python3 run_scanner_simple.py`
5. ✅ Set up scheduling for automated daily runs

## Additional Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Yahoo Finance**: https://finance.yahoo.com
- **NSE F&O Info**: https://www.nseindia.com
- **Technical Analysis**: https://en.wikipedia.org/wiki/Technical_analysis

---

**Last Updated**: 2026-08-11
**Version**: 2.0
