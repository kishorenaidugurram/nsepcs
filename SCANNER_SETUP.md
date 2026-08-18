# NSE F&O PCS Scanner - Setup & Usage Guide

## Overview

The standalone scanner (`scanner_standalone.py`) is designed to scan NSE F&O stocks for Put Credit Spread opportunities based on technical criteria and send results to Telegram.

## Prerequisites

### 1. Telegram Configuration

To enable Telegram notifications, set these environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**How to get Telegram credentials:**

1. **Create a Telegram Bot:**
   - Start a chat with [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot` and follow the prompts
   - You'll get a `BOT_TOKEN` in format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

2. **Get your Chat ID:**
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the JSON response

3. **Add credentials to environment:**
   - Add to `~/.bashrc` or `~/.zshrc`:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   ```
   - Then run: `source ~/.bashrc`

### 2. Python Dependencies

Install required packages:

```bash
pip install pytz yfinance pandas numpy requests plotly scikit-learn scipy openpyxl
```

## Filter Configuration

Default filters in `scanner_standalone.py`:

| Filter | Value | Purpose |
|--------|-------|---------|
| **RSI Range** | 30-75 | Identifies stocks not overbought/oversold |
| **ADX Minimum** | 20 | Ensures trend strength |
| **Volume Ratio** | 1.2x | Today's volume > 1.2x of 20-day average |
| **Lookback Period** | 20 days | Resistance level calculated from 20 days |
| **Breakout %** | 1.0% | Price must break 1% above resistance |

**To customize filters**, edit these lines in `scanner_standalone.py`:

```python
filters = {
    'rsi_min': 30,        # Change this
    'rsi_max': 75,        # Change this
    'adx_min': 20,        # Change this
    'min_volume_ratio': 1.2,  # Change this
    'lookback_days': 20,  # Change this
}
```

## Running the Scanner

### Manual Execution

```bash
cd /home/user/nsepcs
python3 scanner_standalone.py
```

**Expected Output:**
- Progress for each stock analyzed
- Summary statistics (found, filtered, errors)
- Top 10 results with RSI, ADX, volume, and strength metrics
- JSON file saved with full results
- Telegram message sent (if configured)

### Scheduled Execution

Add to crontab for daily scans (e.g., 3:30 PM IST):

```bash
crontab -e
```

Add this line (runs at 15:30 IST = 10:00 UTC):

```
0 10 * * 1-5 export TELEGRAM_BOT_TOKEN=your_token && export TELEGRAM_CHAT_ID=your_id && cd /home/user/nsepcs && python3 scanner_standalone.py >> /var/log/nse_scanner.log 2>&1
```

## Understanding Results

### Output Metrics

**Strength %**: Composite score (0-100) based on:
- Breakout percentage (40%)
- RSI positioning (30%)
- ADX trend strength (30%)

**Example Output:**
```
ABB          ₹3,456.50  62.3    28.5  1.45x      85.2%
RELIANCE     ₹2,890.00  51.2    22.1  1.32x      72.5%
```

### JSON Output Format

Results are saved as `/tmp/scanner_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2026-08-18T15:30:00+05:30",
  "total": 5,
  "stocks": [
    {
      "symbol": "RELIANCE",
      "price": 2890.00,
      "rsi": 51.2,
      "adx": 22.1,
      "volume": 1.32,
      "strength": 72.5
    }
  ]
}
```

## Troubleshooting

### "No stocks found matching criteria"

**Possible causes:**
- Market closed
- Filters too strict
- No significant breakouts today

**Solutions:**
- Lower `rsi_min` and `rsi_max` range
- Reduce `min_volume_ratio` to 1.0
- Increase `lookback_days` to 30

### "CONNECT tunnel failed" / 403 errors

**Issue:** Remote environment proxy blocks yfinance

**Solution:** 
- These errors indicate network connectivity issues in the execution environment
- The scanner will show 0 results in restricted environments
- Contact your network administrator to whitelist:
  - `query1.finance.yahoo.com`
  - `fc.yahoo.com`
  - `download.finance.yahoo.com`

### Telegram not receiving messages

**Checklist:**
1. Verify bot token is correct: `curl https://api.telegram.org/bot<TOKEN>/getMe`
2. Verify chat ID is correct (should be a number, possibly negative)
3. Check environment variables are set: `env | grep TELEGRAM`
4. Test message sending:
   ```bash
   curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage \
     -d chat_id=<CHAT_ID> \
     -d text="Test message"
   ```

## Advanced Usage

### Custom Stock List

To scan specific stocks instead of all F&O universe:

1. Edit the `COMPLETE_NSE_FO_UNIVERSE` list at the top of `scanner_standalone.py`
2. Or create a new list:
   ```python
   MY_STOCKS = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']
   ```

### Different Scan Modes

Create variants for different strategies:

- **Aggressive**: RSI 20-85, ADX 15, Vol 1.0x
- **Conservative**: RSI 35-70, ADX 25, Vol 1.5x  
- **Momentum**: RSI 40-70, ADX 20, Vol 2.0x

### Integration with Trading Platforms

Results JSON can be imported into:
- Python/pandas for further analysis
- Trading platforms via API
- Spreadsheets for manual review

## Maintenance

### Weekly Tasks
- Review telegram message content
- Verify bot is still active
- Check for environment variable changes

### Monthly Tasks
- Analyze signal quality (hits vs false alarms)
- Adjust filters based on market conditions
- Archive old results JSON files

## Security Notes

⚠️ **Never commit bot tokens or chat IDs to git!**

- Use environment variables only
- Keep credentials in `~/.bashrc` or `.env` file
- Add `.env` to `.gitignore`
- Use secure credential management for production

## Support

For issues or improvements:
1. Check this guide's troubleshooting section
2. Review the standalone scanner code comments
3. Test manually with different filter values
4. Check market hours (IST 9:15 AM - 3:30 PM, Monday-Friday)

## Changelog

**v1.0** (2026-08-18)
- Initial standalone scanner
- Telegram integration
- Basic technical analysis filters
- JSON result export

---

**Last Updated:** 2026-08-18
**Environment:** Remote Python 3.11
**Status:** Ready for deployment
