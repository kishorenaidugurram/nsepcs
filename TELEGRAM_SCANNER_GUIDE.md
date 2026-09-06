# Telegram Stock Scanner Guide

Automated NSE F&O stock analysis with results delivered directly to Telegram.

## Overview

The Telegram Scanner continuously monitors 130+ liquid NSE F&O stocks for HIGH confidence trading patterns and automatically sends results to your Telegram chat.

### Features

✅ **Automated Analysis** - Runs on schedule without user intervention
✅ **Pattern Detection** - Identifies uptrends, oversold bounces, breakouts
✅ **Telegram Integration** - Direct message delivery to your preferred chat
✅ **Flexible Filtering** - Configurable pattern strength and confidence thresholds
✅ **Standalone & Integrated** - Works with or without streamlit_app dependency

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Telegram Credentials

#### a. Create a Bot with BotFather

1. Open Telegram and search for **@BotFather**
2. Send `/start` and follow the prompts
3. Create a new bot with `/newbot`
4. Copy the **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

#### b. Get Your Chat ID

1. Add your bot to your Telegram chat
2. Send a test message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}` and copy the **chat_id**

### 3. Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**For persistent configuration (Linux/Mac):**

Add to `~/.bashrc` or `~/.zshrc`:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then run: `source ~/.bashrc`

## Usage

### Run the Scanner Once

```bash
python3 telegram_scanner_standalone.py
```

### Run via Cron Schedule (Automated)

Run the scanner at specific times daily:

```bash
# Edit crontab
crontab -e

# Add this line to run at 3:30 PM IST (every trading day)
30 15 * * 1-5 cd /home/user/nsepcs && python3 telegram_scanner_standalone.py

# Run at market open (9:15 AM IST)
15 9 * * 1-5 cd /home/user/nsepcs && python3 telegram_scanner_standalone.py
```

### Run on Schedule (Using Systemd)

Create `/etc/systemd/system/telegram-scanner.service`:

```ini
[Unit]
Description=Telegram Stock Scanner
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/home/user/nsepcs
Environment="TELEGRAM_BOT_TOKEN=your_bot_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
ExecStart=/usr/bin/python3 /home/user/nsepcs/telegram_scanner_standalone.py

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/telegram-scanner.timer`:

```ini
[Unit]
Description=Run Telegram Stock Scanner
Requires=telegram-scanner.service

[Timer]
OnCalendar=*-*-* 15:30:00  # 3:30 PM IST
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-scanner.timer
sudo systemctl start telegram-scanner.timer
```

## Two Versions Available

### 1. `telegram_scanner_standalone.py` (Recommended)

**Pros:**
- No external dependencies on streamlit_app
- Simpler, more reliable pattern detection
- Works in any environment
- Faster execution

**Pattern Detection:**
- Uptrend (MA Alignment)
- Oversold Bounce (RSI < 30)
- MACD Bullish Crossover
- Volume Breakout

**Usage:**
```bash
python3 telegram_scanner_standalone.py
```

### 2. `telegram_scanner.py` (Advanced)

**Pros:**
- Uses full ProfessionalPCSScanner from streamlit_app
- Advanced pattern detection (15+ patterns)
- Professional-grade technical analysis
- Matches streamlit UI results

**Requires:**
- All streamlit_app dependencies
- `ta` package or fallback implementation

**Usage:**
```bash
python3 telegram_scanner.py
```

## Configuration

### Filter Settings (in scanner code)

Edit the `_get_default_config()` method in `telegram_scanner.py`:

```python
{
    'rsi_min': 30,              # Minimum RSI
    'rsi_max': 75,              # Maximum RSI
    'adx_min': 20,              # Minimum ADX (trend strength)
    'min_volume_ratio': 1.2,    # Volume threshold
    'pattern_strength_min': 70, # Minimum pattern strength (0-100)
    'lookback_days': 20,        # Historical data period
    # ... more settings
}
```

### Adjust Confidence Level

In `telegram_scanner_standalone.py`, modify the `main()` function:

```python
# Change from HIGH (85+) to MEDIUM (70+)
high_conf_patterns = [p for p in patterns if p['strength'] >= 70]
```

## Understanding Results

Each stock alert shows:

```
🟢 TCS - HIGH
━━━━━━━━━━━━
Pattern: Uptrend (MA Alignment)
Strength: 82%
Success Rate: 75%

Price: ₹3,456.50
RSI: 52.4
ADX: 28.3
Vol Ratio: 1.45x
```

### Emoji Legend

- 🟢 **GREEN** - HIGH Confidence (Strength ≥ 85%)
- 🟡 **YELLOW** - MEDIUM Confidence (Strength 70-84%)
- 🔴 **RED** - LOW Confidence (Strength < 70%)

### Metrics Explained

| Metric | Range | Interpretation |
|--------|-------|-----------------|
| **Strength** | 0-100% | Pattern detection confidence |
| **RSI** | 0-100 | Momentum: <30 Oversold, >70 Overbought |
| **ADX** | 0-100 | Trend strength: >20 Strong trend |
| **Vol Ratio** | 1.0x+ | Volume relative to 20-day average |

## Troubleshooting

### Bot Not Sending Messages

1. **Check credentials:**
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```

2. **Test manually:**
   ```bash
   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
     -d "chat_id=$TELEGRAM_CHAT_ID&text=Test"
   ```

3. **Check bot permissions:**
   - Ensure bot is added to the chat
   - Bot should have message sending permissions

### No Results Found

1. **Market may be closed** - Check if NSE market is open
2. **No HIGH confidence patterns** - Market volatility may reduce signal quality
3. **Check logs** - Run with debug output:
   ```bash
   python3 telegram_scanner_standalone.py 2>&1 | grep -i "ERROR\|pattern"
   ```

### Network/Proxy Issues

If you see "Connection failed" errors:

1. Check internet connectivity
2. Verify proxy settings if behind corporate proxy
3. Yahoo Finance may have rate limiting - wait before retry

### Data Fetch Failures

If stocks can't download data:

1. Ensure ticker symbols are correct (should end with `.NS`)
2. Try with fewer stocks first (modify `stocks_to_scan[:50]`)
3. Wait 5-10 minutes and retry (rate limiting)

## Advanced Usage

### Custom Stock List

Edit the `COMPLETE_NSE_FO_UNIVERSE` list in either scanner file:

```python
MY_STOCKS = [
    'RELIANCE.NS',
    'TCS.NS', 
    'INFY.NS',
    # Add more...
]

# Then modify main():
stocks_to_scan = MY_STOCKS[:20]
```

### Different Analysis Modes

**High-frequency (5-minute bars):**
```python
df = analyzer.get_stock_data(symbol, period='1mo')  # Last 1 month
```

**Swing trading (daily):**
```python
df = analyzer.get_stock_data(symbol, period='3mo')  # Last 3 months (default)
```

**Long-term (weekly):**
```python
df = analyzer.get_stock_data(symbol, period='1y')   # Last 1 year
```

### Modify Pattern Detection

Add custom patterns in `SimpleStockAnalyzer.detect_patterns()`:

```python
# Example: Detect Golden Cross
if latest['SMA_20'] > latest['SMA_50']:
    patterns.append({
        'type': 'Golden Cross',
        'strength': 75,
        'success_rate': 80,
        'pcs_suitability': 85,
        'confidence': 'MEDIUM'
    })
```

## Performance Tips

1. **Reduce stock list:** Change `[:50]` to `[:25]` for faster analysis
2. **Increase minimum strength:** Raise `pattern_strength_min` to 80 for fewer, higher-quality signals
3. **Cache data:** Add local caching to avoid re-downloading same data
4. **Batch by day:** Run once after market close, not multiple times daily

## Integration with Streamlit App

The scanner results complement the streamlit app:

- **Streamlit App** - Interactive exploration, detailed charting, manual analysis
- **Telegram Scanner** - Automated alerts, hands-free monitoring, quick decisions

Use both together:
1. Get automated alerts via Telegram
2. Open Streamlit app for detailed analysis of flagged stocks

## Support & Debugging

To see detailed logs:

```bash
python3 -u telegram_scanner_standalone.py 2>&1 | tee scanner_output.log
```

Check the log file for errors:
```bash
grep -i "error" scanner_output.log
```

## Risk Disclaimer

⚠️ **Important:** This tool provides technical analysis signals only. It is NOT financial advice.

- Always verify signals before trading
- Start with paper trading
- Use proper risk management (position sizing, stop losses)
- Consult qualified financial advisors before investing
- Past performance doesn't guarantee future results

## License

This tool is part of the NSE F&O PCS Scanner project.

---

**Questions?** Check the main [README.md](README.md) or GitHub issues.
