# NSE PCS Stock Scanner - Automated Telegram Integration

## What Was Set Up

This automated system scans NSE stocks for technical patterns and sends qualifying stocks to your Telegram.

### New Files Created

1. **`scan_and_send_telegram.py`** - Main scanner script
   - Scans 219 NSE F&O stocks daily
   - Applies default technical filters
   - Sends results to Telegram
   - Falls back to CSV export if Telegram not configured

2. **`run_scanner.py`** - Core scanner without Telegram dependency
   - Pure scanning logic
   - Saves results to CSV and text files
   - No external API calls

3. **`simple_scanner.py`** - Lightweight test scanner
   - 30 stocks for quick testing
   - Basic RSI and volume analysis
   - For debugging and development

4. **`requirements.txt`** - Updated dependencies
   - Added `requests` for Telegram API
   - All other dependencies for yfinance and pandas

## How It Works

### Filter Criteria (Default)

The scanner looks for stocks that meet **ALL** of these criteria:

```
✓ RSI: Between 30-75 (healthy zone, not overbought)
✓ ADX: Minimum 20 (trend strength confirmation)
✓ Moving Average: Close to EMA-20 ± 3% (price support)
✓ Volume: 1.2x average (above normal trading)
✓ Pattern Match: 65%+ strength in detected patterns
✓ Analysis: Combined daily + weekly timeframe validation
```

### Detected Patterns

The scanner detects 12 technical patterns:
- Current Day Breakout ⭐
- Cup with Handle
- Flat Base Breakout
- Bump-and-Run Reversal
- Rectangle Bottom
- Head-and-Shoulders Bottom
- Double Bottom (Eve & Eve)
- Three Rising Valleys
- Rounding Bottom
- Rounding Top
- Inverted Scallop
- Rectangle Top

## Setup Instructions

### 1. Get Telegram Credentials

**Create a bot:**
1. Message `@BotFather` on Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy the token: `123456789:ABCDefGhIjKlMnOpQrStUvWxYz...`

**Get your chat ID:**
1. Message `@RawDataBot` on Telegram
2. Send any message
3. Copy the numeric ID shown

### 2. Set Environment Variables

Add to your shell configuration (`~/.bashrc`, `/etc/environment`, or systemd service):

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 3. Test the Scanner

Run manually to test:

```bash
cd /home/user/nsepcs
python scan_and_send_telegram.py
```

You should receive a Telegram message with qualifying stocks.

### 4. Schedule Automated Runs

**Using cron (runs daily at 3:30 PM IST after market close):**

```bash
crontab -e
# Add this line:
30 15 * * 1-5 /usr/local/bin/python /home/user/nsepcs/scan_and_send_telegram.py
```

**Using systemd (Linux):**

Create `/etc/systemd/system/stock-scanner.service`:
```ini
[Unit]
Description=NSE Stock Scanner
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_id"
ExecStart=/usr/local/bin/python /home/user/nsepcs/scan_and_send_telegram.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then create timer `/etc/systemd/system/stock-scanner.timer`:
```ini
[Unit]
Description=Run NSE Stock Scanner daily

[Timer]
OnCalendar=Mon-Fri 15:30
Persistent=true

[Install]
WantedBy=timers.target
```

Enable it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now stock-scanner.timer
```

## Customization

### Change Filter Criteria

Edit `scan_and_send_telegram.py` or `run_scanner.py`:

```python
config = {
    'rsi_min': 30,           # Change to 40 for less volatile stocks
    'rsi_max': 75,           # Change to 70 for more selective filtering
    'adx_min': 20,           # Increase to 25+ for stronger trends
    'min_volume_ratio': 1.2,  # Increase for higher volume requirement
    'pattern_strength_min': 65, # Increase to 70+ for stricter matching
    # ... other settings
}
```

### Change Stock Universe

```python
# F&O stocks (default, 219 stocks):
results = run_scanner(universe_type="NSE F&O Stocks (219)")

# Non-F&O stocks (800+):
results = run_scanner(universe_type="NSE Non-F&O Stocks (800+)")

# Limited scan for speed:
results = run_scanner(universe_type="NSE F&O Stocks (219)", max_stocks=50)
```

### Change Telegram Message Format

The `format_results_for_telegram()` function in `scan_and_send_telegram.py` controls the message layout. Customize as needed.

## Output Files

When Telegram is not configured, results are saved to:

```
/tmp/claude-0/-home-user-nsepcs/0f821919-47d0-5372-aa4d-845b71125a7a/scratchpad/
├── scanner_results_20241119_153000.csv    # Stock list
└── scanner_results_20241119_153000.txt    # Formatted report
```

## Example Output

### CSV Format
```
Symbol,Price,Pattern,Strength,RSI,ADX,Volume_Ratio
RELIANCE,2850.50,Current Day Breakout,87.0,65.3,28.5,2.15
INFY,2250.75,Cup with Handle,78.0,58.9,26.2,1.85
```

### Telegram Message
```
🎯 NSE PCS Stock Scanner Results
Scan Time: 2024-11-19 15:30 IST
Total Stocks Found: 12

1. RELIANCE
   Price: ₹2,850.50
   Pattern: Current Day Breakout (87% strength)
   RSI: 65.3 | ADX: 28.5
   Volume Ratio: 2.15x
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Telegram not configured" | Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars |
| "No stocks found" | Market may be bearish; adjust RSI/ADX minimums lower |
| "Failed to send message" | Verify bot token is correct; ensure internet connectivity |
| "No data fetched" | Network/proxy issues; check yfinance connectivity |
| "Slow scan" | Reduce stock count or increase ADX minimum to skip weak trends |

## Performance Notes

- **Scan Time**: ~30-45 minutes for 219 F&O stocks on first run
- **Data Sources**: Yahoo Finance (yfinance)
- **Memory**: ~500MB-1GB during scan
- **Network**: Requires internet for stock data fetch

## Success Metrics

Track these metrics in your Telegram over time:
- **Stocks Found**: Daily qualifying pattern matches
- **Avg Strength**: Average pattern strength % (target: >70%)
- **Hit Rate**: % of stocks that actually move as predicted
- **Volume**: Avg volume ratio of qualifying stocks

## Support & Customization

The scanner is fully configurable:
1. Edit filter values in config dictionary
2. Add custom patterns in `detect_patterns()` method
3. Modify Telegram message format in `format_results_for_telegram()`
4. Create additional metrics in result processing

## Security Notes

- **Bot Token**: Keep your bot token private
- **Chat ID**: Keep your chat ID private
- **Environment Variables**: Don't commit credentials to git
- **Scheduled Runs**: Use systemd/cron with proper user permissions

---

**Ready to start?** Follow the setup instructions above and you'll receive your first scan results in Telegram! 📈

Need help? Check the TELEGRAM_SETUP_GUIDE.md for detailed step-by-step instructions.
