# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview

The `telegram_scanner.py` script enables automated scanning of NSE F&O stocks for Put Credit Spread (PCS) opportunities and sends results directly to your Telegram chat.

## Components

### 1. `telegram_scanner.py`
Non-interactive scanner that:
- Scans all 208 NSE F&O stocks
- Detects multiple chart patterns (cup & handle, breakouts, rectangles, etc)
- Applies technical filters (RSI, ADX, volume ratios, moving averages)
- Formats results into a readable Telegram message
- Falls back to JSON export if Telegram delivery fails

### 2. `ta.py`
Mock technical analysis module providing:
- RSI (Relative Strength Index)
- SMA/EMA (Simple/Exponential Moving Averages)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- Bollinger Bands
- ATR (Average True Range)
- Stochastic Oscillator
- Williams %R

These are implemented using pandas and numpy when the `ta` package is unavailable.

## Setup Requirements

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt
```

Main libraries needed:
- `yfinance` - For stock data
- `pandas` - For data manipulation
- `numpy` - For calculations
- `requests` - For Telegram API
- `streamlit` - For running the Streamlit app
- `ta-lib` or our mock `ta.py` - For technical indicators

### Telegram Bot Setup

1. **Create a Telegram Bot**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Choose a name for your bot
   - BotFather will provide a token (e.g., `123456789:ABCdef...`)
   - Save this token as `TELEGRAM_BOT_TOKEN`

2. **Get Your Chat ID**
   - Open Telegram and search for `@RawDataBot`
   - Send any message
   - RawDataBot will reply with your user information including `chat_id`
   - Save this as `TELEGRAM_CHAT_ID`

3. **Start the Bot**
   - Open Telegram and search for the bot you created
   - Send `/start` to initialize the bot

### Environment Variables

Set these environment variables before running:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**Security Note:** Never commit these credentials to git. Add them to:
- `.env` file (add to `.gitignore`)
- GitHub Actions secrets (if using CI/CD)
- Environment configuration management system

## Usage

### Manual Execution
```bash
python3 telegram_scanner.py
```

### As a Scheduled Task (Cron)
```bash
# Add to crontab for daily 9:15 AM execution (after market open)
15 9 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python3 telegram_scanner.py
```

### Output

The scanner generates:
1. **Console Output**: Logging information about the scan progress
2. **Telegram Message**: HTML-formatted message with:
   - Top 20 stocks with detected patterns
   - Current price, RSI, ADX values
   - Pattern count and strength
   - Confidence levels (HIGH/MEDIUM/LOW)
3. **JSON Fallback**: If Telegram fails, saves to `/tmp/pcs_scan_results.json`

### Example Telegram Output
```
📊 NSE F&O PCS Scanner Results
2026-09-14 09:15

✅ Found 15 stocks with patterns

1. RELIANCE
Price: ₹2,650.50 | RSI: 55.2 | ADX: 32.1
Patterns: 3 | Strength: 88.0% 🟢 HIGH
Patterns: Current Day Breakout, Cup with Handle

2. TCS
Price: ₹3,850.25 | RSI: 48.3 | ADX: 28.5
Patterns: 2 | Strength: 75.0% 🟡 MEDIUM
Patterns: Double Bottom, Flat Base
...

⚠️ Disclaimer: Educational analysis only.
```

## Filter Criteria (Default)

The scanner uses these default filters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| RSI Min | 30 | Minimum RSI value |
| RSI Max | 75 | Maximum RSI value |
| ADX Min | 20 | Minimum ADX for trend strength |
| MA Support | Enabled | Moving average support requirement |
| Volume Ratio | 1.2x | Volume vs 20-day average |
| Pattern Strength | 65% | Minimum pattern confidence |
| Lookback Days | 20 | Days for analysis window |

## Customization

Edit `telegram_scanner.py` `run_scan()` function to modify:
- Number of stocks to scan
- Filter thresholds (RSI, ADX, volume)
- Pattern detection preferences
- Message formatting

Example:
```python
results = run_scan(
    max_stocks=50,  # Scan only first 50 stocks
    min_volume_ratio=1.5  # Stricter volume filter
)
```

## Troubleshooting

### Issue: "Telegram credentials not configured!"
**Solution:** Set environment variables
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
```

### Issue: "Network connectivity issue" / "CONNECT tunnel failed"
**Solution:** Check network access
- Verify internet connectivity
- Check proxy settings
- Ensure yfinance is accessible
- Check firewall rules

### Issue: "No data for symbol"
**Solution:** Yahoo Finance may be blocking or the symbol may be delisted
- Verify symbol is currently trading
- Check `COMPLETE_NSE_FO_UNIVERSE` list in streamlit_app.py
- Try running with fewer stocks

### Issue: "Module not found: ta"
**Solution:** The mock `ta.py` should handle this
- Ensure `ta.py` is in the same directory as `telegram_scanner.py`
- System should use the mock implementation automatically

## API Reference

### Main Functions

#### `run_scan(max_stocks=None, min_volume_ratio=1.2)`
Executes the PCS scanning algorithm.

**Parameters:**
- `max_stocks` (int, optional): Limit scanning to first N stocks
- `min_volume_ratio` (float): Minimum volume ratio filter

**Returns:**
- List of dicts containing scan results with keys:
  - `symbol`: Stock symbol
  - `current_price`: Current stock price
  - `volume_ratio`: Today's volume vs 20-day average
  - `rsi`: RSI indicator value
  - `adx`: ADX indicator value
  - `patterns`: List of detected pattern dicts
  - `pattern_count`: Number of patterns detected
  - `max_strength`: Highest pattern strength %

#### `send_to_telegram(message, telegram_token=None, telegram_chat_id=None)`
Sends a message to Telegram chat.

**Parameters:**
- `message` (str): Message to send (supports HTML formatting)
- `telegram_token` (str): Bot token (uses env var if not provided)
- `telegram_chat_id` (str): Chat ID (uses env var if not provided)

**Returns:**
- Boolean: True if successful, False otherwise

#### `format_telegram_message(results)`
Formats scan results into a Telegram-ready message.

**Parameters:**
- `results` (list): Results from `run_scan()`

**Returns:**
- String: Formatted message (limited to top 20 stocks)

## Performance

Typical scan performance:
- **Time**: 60-180 seconds for 208 stocks (depends on network)
- **CPU**: Minimal usage (< 30%)
- **Memory**: ~100-200 MB
- **Network**: ~10-20 MB data transfer

## Limitations

1. **Network Dependency**: Requires yfinance access
2. **Data Freshness**: Works with end-of-day data (no real-time)
3. **Message Size**: Telegram limits to ~4000 chars, so limited to top 20 stocks
4. **Rate Limiting**: yfinance may throttle requests if scanning too frequently
5. **Weekends/Holidays**: No data available, script will find no patterns

## Future Enhancements

Potential improvements:
- Database storage of historical scans
- Multiple Telegram channel support
- Configurable pattern weights
- Real-time alert mode
- Web dashboard for results
- Email digest option
- Slack integration

## Support & Issues

For issues or questions:
1. Check `telegram_scanner.py` logs
2. Verify environment variables are set
3. Test Telegram bot connectivity manually
4. Check network/firewall settings
5. Review GitHub issues

## Disclaimer

⚠️ **IMPORTANT**: This tool is for educational purposes only.

- Not financial advice
- Past performance ≠ future results
- Options trading carries substantial risk
- Always consult qualified financial advisors
- Paper trade before live implementation
- Never risk more than you can afford to lose

Trade responsibly!
