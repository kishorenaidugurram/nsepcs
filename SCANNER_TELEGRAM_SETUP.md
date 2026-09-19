# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview

The standalone scanner (`scanner_telegram.py`) is a Python script that analyzes NSE F&O stocks for Put Credit Spread (PCS) trading opportunities and automatically sends results to Telegram.

## Requirements

- Python 3.8+
- Dependencies: `pandas`, `numpy`, `yfinance`, `requests`, `pytz`
- Telegram Bot (for notifications)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a Telegram Bot:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow the prompts to create a new bot
   - Save the bot token provided (e.g., `123456789:ABCDefGhIjKlMnOpQrStUvWxYz`)

3. **Get your Telegram Chat ID:**
   - Send a message to your new bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual bot token
   - Look for the `"chat":{"id":...}` field in the response
   - Save this ID (e.g., `9876543210`)

## Configuration

### Option 1: Environment Variables (Recommended)

Set these environment variables before running the scanner:

```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID_HERE"
```

### Option 2: Save to .env file

Create a `.env` file in the project root:

```
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
```

Then load it before running:

```bash
source .env
python3 scanner_telegram.py
```

## Usage

### Manual Execution

```bash
python3 scanner_telegram.py
```

### Scheduled Execution (Cron)

To run the scanner daily at 9:15 AM IST:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9:15 AM IST)
15 9 * * * cd /home/user/nsepcs && /usr/bin/python3 scanner_telegram.py >> /var/log/nse_scanner.log 2>&1
```

### Scheduled Execution (System Service)

Create `/etc/systemd/system/nse-scanner.timer`:

```ini
[Unit]
Description=NSE F&O PCS Scanner Timer
Requires=nse-scanner.service

[Timer]
OnCalendar=*-*-* 09:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/nse-scanner.service`:

```ini
[Unit]
Description=NSE F&O PCS Scanner
After=network-online.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/home/user/nsepcs
Environment="TELEGRAM_BOT_TOKEN=YOUR_TOKEN"
Environment="TELEGRAM_CHAT_ID=YOUR_CHAT_ID"
ExecStart=/usr/bin/python3 /home/user/nsepcs/scanner_telegram.py
StandardOutput=append:/var/log/nse_scanner.log
StandardError=append:/var/log/nse_scanner_error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nse-scanner.timer
sudo systemctl start nse-scanner.timer
```

## Filter Criteria

The scanner applies the following filters to identify PCS opportunities:

1. **RSI (Relative Strength Index)**: 30-75
   - Identifies stocks in neutral to slightly overbought territory
   - Sweet spot for PCS trades

2. **ADX (Average Directional Index)**: > 20
   - Ensures trend strength
   - ADX > 20 indicates directional movement

3. **Volume Ratio**: > 1.2x
   - Current volume must be 1.2x average volume
   - Confirms institutional participation

4. **Support Proximity**: Within 3% of SMA(20) or EMA(20)
   - Stock price should be near key support levels
   - Good entry point for PCS trades

## Output

### Console Output

```
🚀 Starting NSE F&O PCS Scanner...
⏰ Time: 2026-09-19 09:15:13 IST

📊 Scanning 25 stocks...

[ 1/25] Analyzing RELIANCE       ... ✅ (87% HIGH)
[ 2/25] Analyzing TCS            ... ✅ (76% MEDIUM)
...

✅ Found 8 stocks with confirmed patterns!

============================ SCAN RESULTS ============================
 1. RELIANCE    | Strength:    87% | Confidence:    HIGH | Price:  ₹2456.75
 2. TCS         | Strength:    76% | Confidence: MEDIUM | Price:  ₹3847.50
...
```

### Telegram Message

The scanner sends results to Telegram with:
- Summary of stocks found
- Confidence levels (HIGH/MEDIUM/LOW)
- Key metrics (Price, RSI, ADX, Volume)
- Top 15 stocks sorted by strength

## Stocks Analyzed

The scanner monitors 25 major NSE F&O stocks across liquidity tiers:

**Tier 1 - Ultra High Liquidity:**
- NIFTY50, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

**Tier 2 - High Liquidity:**
- KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT

**Tier 3 - Medium Liquidity:**
- BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN

## Troubleshooting

### Issue: "Telegram credentials not configured"

**Solution:** Set environment variables
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### Issue: "Failed to send Telegram message"

**Possible causes:**
- Invalid bot token or chat ID
- Network connectivity issues
- Telegram API rate limits

**Solution:**
- Verify credentials at https://api.telegram.org/bot<TOKEN>/getMe
- Check network connectivity
- Wait a few minutes before retrying

### Issue: "No stocks found meeting criteria"

**Possible causes:**
- Market closed or no trading activity
- Technical indicators not calculated yet
- No stocks matching filter criteria

**Solution:**
- Run during market hours (09:15 AM - 3:30 PM IST)
- Ensure adequate data is available
- Adjust filter criteria if needed

### Issue: "No data" for stocks

**Possible causes:**
- Network connectivity issue
- Yahoo Finance API unreachable
- Data unavailable for the stock

**Solution:**
- Check internet connection
- Verify proxy settings if behind corporate proxy
- Try manual test: `curl https://query1.finance.yahoo.com`

## Data Sources

The scanner uses Yahoo Finance for historical data:
- **Period:** 3 months of daily data
- **Update Frequency:** Real-time market data
- **Reliability:** 99%+ uptime with fallback systems

## Performance

- **Scan Time:** ~30-60 seconds for 25 stocks
- **Memory Usage:** ~100-200 MB
- **CPU Usage:** Low (single-threaded, sequential)

## Customization

To modify the scanner, edit these sections in `scanner_telegram.py`:

### Change Stocks Analyzed

```python
DEFAULT_STOCKS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK',
    # Add/remove stocks as needed
]
```

### Modify Filters

```python
# In analyze_stock() function:
if not (30 <= current_rsi <= 75):  # RSI range
if current_adx < 20:                # ADX threshold
if volume_ratio < 1.2:              # Volume ratio
if support_pct > 3:                 # Support distance
```

### Change Message Format

Edit the Telegram message template in `run_scan()` function.

## Security Considerations

- **Never commit credentials** to version control
- **Use environment variables** for bot token and chat ID
- **Restrict script permissions** to prevent unauthorized access
- **Monitor logs** for suspicious activity
- **Use a dedicated bot** for this scanner only

## Support & Documentation

- Scanner Logic: See `scanner_telegram.py` comments
- Technical Indicators: Built-in calculations using pandas/numpy
- Telegram Integration: Uses Telegram Bot API
- Data Source: Yahoo Finance API

## License

This scanner is provided as-is for educational and trading purposes.

## Disclaimer

This scanner is for informational purposes only. It is NOT financial advice. Options trading involves substantial risk and can result in total loss. Always:
- Do your own research
- Consult with qualified financial advisors
- Start with paper trading
- Use proper risk management
- Never risk more than you can afford to lose
