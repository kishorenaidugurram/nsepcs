# Telegram Stock Scanner Integration Setup

## Overview

The NSE F&O Stock Scanner can automatically send stock analysis results to Telegram. Two standalone scripts have been created for this purpose.

## Quick Start

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat with BotFather
3. Send the command: `/newbot`
4. Follow the instructions to create your bot:
   - Choose a name (e.g., "NSE Stock Scanner")
   - Choose a username (e.g., "nse_scanner_bot")
5. BotFather will provide a **BOT TOKEN** - save this (e.g., `123456789:ABCDEFGHIJKLMNOPQRSTUVWxyz`)

### Step 2: Get Your Chat ID

1. Start a chat with your newly created bot
2. Send any message to it (e.g., "Hi")
3. Visit this URL in your browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Look for the `"chat"` section and find your **chat ID** (usually a number like `123456789` or `-123456789`)

### Step 3: Configure Environment Variables

Set these environment variables in your system or `.env` file:

```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID_HERE"
```

### Step 4: Test the Integration

Run the standalone scanner:

```bash
python3 telegram_scanner_standalone.py
```

You should receive a message on Telegram with stock scanning results!

## Available Scripts

### 1. `telegram_scanner_standalone.py` (Recommended)

A simplified scanner that works without the `ta` library.

**Features:**
- Basic technical indicators (RSI, SMA, EMA)
- Simple pattern detection
- Lighter dependencies
- Faster execution

**Usage:**
```bash
python3 telegram_scanner_standalone.py
```

**Output:**
- Telegram message with top stocks found
- JSON file saved to `/tmp/stock_scan_*.json`

### 2. `telegram_stock_sender.py`

Full-featured scanner that imports from the main Streamlit app.

**Features:**
- Advanced technical analysis with all patterns
- Weekly validation support
- Full news integration
- Complete pattern detection

**Usage:**
```bash
python3 telegram_stock_sender.py
```

**Note:** Requires the `ta` library to be properly installed.

## Scheduling the Scanner

### Option 1: Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9:00 AM IST (3:30 UTC)
# Note: Adjust time based on your timezone
30 3 * * * cd /home/user/nsepcs && python3 telegram_scanner_standalone.py >> /var/log/nse_scanner.log 2>&1
```

### Option 2: Using at (One-time execution)

```bash
# Schedule for specific time
echo "python3 telegram_scanner_standalone.py" | at 09:00

# Schedule daily
echo "python3 telegram_scanner_standalone.py" | at 09:00 tomorrow
```

### Option 3: Using Systemd Timer

Create `/etc/systemd/system/nse-scanner.service`:

```ini
[Unit]
Description=NSE Stock Scanner with Telegram
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/user/nsepcs
ExecStart=/usr/bin/python3 telegram_scanner_standalone.py
StandardOutput=journal
StandardError=journal
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/nse-scanner.timer`:

```ini
[Unit]
Description=NSE Stock Scanner Timer
Requires=nse-scanner.service

[Timer]
# Run at 9:00 AM IST every day
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nse-scanner.timer
sudo systemctl start nse-scanner.timer
```

## Telegram Message Format

The scanner sends messages with the following information for each stock:

```
📊 NSE F&O Scanner Report
[Timestamp in IST]

✅ Found N stocks meeting criteria:

1. STOCK_SYMBOL
💰 ₹Price | RSI Level | Volume Ratio | 💪 Strength %
🎯 Pattern Type, Pattern Type 2

[More stocks...]

Report generated at [Time]
```

## Filter Criteria

The scanner uses the following default filters:

- **RSI Range:** 30-70 (momentum indicator)
- **Volume Ratio:** >1.0x average (liquidity confirmation)
- **Pattern Strength:** >60% (pattern quality)
- **ADX Threshold:** >20 (trend strength)
- **Technical Indicators:** RSI, SMA, EMA, Volume Analysis

## Patterns Detected

1. **Breakout** - Price breaks above resistance with volume confirmation
2. **Oversold Bounce** - RSI <40 with price above SMA(20)
3. **Bullish Alignment** - Price > SMA(20) > SMA(50)
4. **Current Day Breakout** - Confirmed on current trading day
5. **Cup and Handle** - Classic reversal pattern
6. **Double Bottom** - Support formation pattern

## Customization

### Adjusting Scan Parameters

Edit the `scan_stocks()` call in the script:

```python
# Scan 50 stocks (default: 50)
results = scanner.scan_stocks(limit=50)
```

Or in `telegram_scanner_standalone.py`, modify the `main()` function:

```python
# Change limits and thresholds
results = scanner.scan_stocks(limit=100)  # Scan more stocks
```

### Adding Custom Filters

Modify the `analyze_stock()` method to add custom filters:

```python
# Example: Add custom RSI range filter
if rsi < 35 or rsi > 65:
    return None  # Skip this stock
```

## Troubleshooting

### "Telegram credentials not configured"

**Solution:** Make sure environment variables are set:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

If empty, set them:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
```

### "No stocks found"

**Possible causes:**
- No trading data available (weekend/holiday)
- Filters are too strict
- Network connectivity issues fetching stock data

**Solution:** Check the logs and try lowering the pattern strength threshold.

### Network errors

The scanner requires internet access to fetch stock data from Yahoo Finance.

**Solution:** Ensure your system can reach the internet and that any proxies are properly configured.

## Results Storage

Results are automatically saved to `/tmp/stock_scan_YYYYMMDD_HHMMSS.json` with the following structure:

```json
{
  "timestamp": "2026-09-03T09:30:00",
  "stocks_found": 5,
  "results": [
    {
      "symbol": "RELIANCE.NS",
      "price": 2850.50,
      "rsi": 65.3,
      "volume_ratio": 1.8,
      "trend_strength": 5.2,
      "patterns": [
        {
          "type": "Breakout",
          "strength": 85,
          "confidence": "HIGH"
        }
      ]
    }
  ]
}
```

## Security Notes

1. **Protect Your Bot Token** - Don't share it in public repositories
2. **Protect Your Chat ID** - This identifies where messages are sent
3. **Store Credentials Safely** - Use environment variables, not hardcoded values
4. **Log File Access** - Restrict access to log files that might contain debug info

## Manual Testing

Test without Telegram:

```bash
# Run scanner and see output
python3 -c "
from telegram_scanner_standalone import SimpleStockScanner
scanner = SimpleStockScanner()
results = scanner.scan_stocks(limit=5)
print(f'Found {len(results)} stocks')
for r in results:
    print(f\"{r['symbol']}: {r['max_strength']:.0f}% strength\")
"
```

## Next Steps

1. ✅ Create Telegram bot with BotFather
2. ✅ Get your Chat ID
3. ✅ Set environment variables
4. ✅ Test with `python3 telegram_scanner_standalone.py`
5. ✅ Schedule with cron/systemd
6. ✅ Monitor logs and adjust filters as needed

## Support

For issues:

1. Check environment variables are set correctly
2. Verify Telegram bot token and chat ID are valid
3. Check internet connectivity
4. Review logs in `/var/log/nse_scanner.log` (if using systemd)
5. Ensure Python dependencies are installed: `pip install -r requirements.txt`

## Advanced Configuration

### Change Scan Time

Modify cron/systemd timer to different IST times:

- 9:15 AM IST → 03:45 UTC → `45 3 * * * ...`
- 4:00 PM IST → 10:30 UTC → `30 10 * * * ...`

### Add Multiple Recipients

Modify the sender to send to multiple chat IDs:

```python
CHAT_IDS = [
    os.getenv('TELEGRAM_CHAT_ID'),
    os.getenv('TELEGRAM_CHAT_ID_2'),
    os.getenv('TELEGRAM_CHAT_ID_3'),
]

for chat_id in CHAT_IDS:
    sender.chat_id = chat_id
    sender.send_message(message)
```

---

**Last Updated:** 2026-09-03  
**Maintained by:** Stock Scanner Team
