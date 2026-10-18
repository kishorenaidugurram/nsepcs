# PCS Scanner - Automated Stock Analysis Tool

## What's New

The NSE F&O PCS Screener now includes an **automated scanner** that runs independently and sends results to Telegram.

## Quick Start

### 1. Set Up Telegram (5 minutes)

See [TELEGRAM_SETUP.md](./TELEGRAM_SETUP.md) for detailed instructions.

**Quick version:**
```bash
# Create bot via @BotFather on Telegram, get Chat ID via @getidsbot
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 2. Run the Scanner

```bash
python3 pcs_scanner_standalone.py
```

Or schedule it with cron (Linux/Mac):
```bash
# Run daily at 9:15 AM IST
15 3 * * * cd /path/to/nsepcs && python3 pcs_scanner_standalone.py
```

## Features

### ✅ What the Scanner Does

- **Analyzes 50 stocks** from Nifty 50 index
- **Detects 4+ chart patterns**:
  - Breakout patterns with consolidation
  - Support with bullish indicators
  - MACD bullish crossovers
  - Bounce setups
  
- **Calculates technical indicators**:
  - RSI (Relative Strength Index)
  - Moving Averages (SMA, EMA)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - ADX (Average Directional Index)

- **Grades patterns** on 0-100 scale
  
- **Sends to Telegram** with:
  - Top 10 qualifying stocks
  - Pattern type and strength
  - Current price and RSI
  - ADX trend strength

### Filter Criteria

Stocks are filtered by:
| Criterion | Threshold |
|-----------|-----------|
| Pattern Strength | ≥ 50/100 |
| RSI | 30-80 |
| ADX (Trend) | ≥ 15 |
| Data Quality | ≥ 20 bars |

## Scripts Included

### 1. `pcs_scanner_standalone.py` (Recommended)
**Standalone Python script** - No Streamlit dependency

```bash
python3 pcs_scanner_standalone.py
```

**Pros:**
- Fast and lightweight
- Runs anywhere Python is installed
- Perfect for servers/crons
- Built-in technical indicators
- No external TA library needed

**Output:**
- Console output with progress
- Telegram message with top results
- JSON file with all results

### 2. `run_scanner.py`
**Alternative** - Uses functions from streamlit_app.py

```bash
python3 run_scanner.py
```

**Pros:**
- Uses existing scanner logic
- More sophisticated pattern detection
- Weekly validation support

**Cons:**
- Requires all streamlit_app.py dependencies
- Needs the `ta` library (can be tricky to install)

## Output Example

### Telegram Message
```
✅ PCS Scan Results - 2024-01-15 09:15

📊 Found 8 stocks:

1. HDFCBANK.NS
   Support & Bullish (Strength: 78/100)
   Price: ₹1,823.45 | RSI: 61.2

2. INFY.NS
   MACD Bullish (Strength: 72/100)
   Price: ₹2,456.80 | RSI: 58.7

3. TCS.NS
   Breakout (Strength: 68/100)
   Price: ₹5,234.60 | RSI: 64.1

... +5 more
```

### File Output
If Telegram not configured:
```json
{
  "timestamp": "2024-01-15T09:15:32.123456",
  "total_stocks": 8,
  "stocks": [
    {
      "symbol": "HDFCBANK.NS",
      "pattern": "Support & Bullish",
      "strength": 78,
      "price": 1823.45
    },
    ...
  ]
}
```

## Customization

Edit `pcs_scanner_standalone.py` to:

### Change stocks analyzed
```python
# Modify the stocks list in main()
results = run_scan(stocks=YOUR_STOCK_LIST, max_stocks=50)
```

### Adjust filter thresholds
```python
# In SimpleIndicators and PCSScanner classes
pattern_strength_min = 50  # Change minimum pattern strength
rsi_min, rsi_max = 30, 80  # Adjust RSI range
adx_min = 15  # Change ADX threshold
```

### Modify Telegram message format
```python
# In send_to_telegram() function
# Edit the msg variable to customize output
```

## Scheduling

### Linux/Mac - Crontab

```bash
# Edit crontab
crontab -e

# Add line to run daily at 9:15 AM IST (3:15 AM UTC)
15 3 * * * cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python3 pcs_scanner_standalone.py

# Run every 6 hours
0 */6 * * * cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python3 pcs_scanner_standalone.py
```

### Windows - Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "PCS Scanner"
4. Trigger: Daily, 9:15 AM
5. Action:
   - Program: `C:\Python311\python.exe`
   - Arguments: `C:\path\to\nsepcs\pcs_scanner_standalone.py`
   - Start in: `C:\path\to\nsepcs`
6. Under "Edit" → Advanced, set environment variables

### GitHub Actions (Automated Cloud)

Create `.github/workflows/scanner.yml`:
```yaml
name: PCS Scanner
on:
  schedule:
    - cron: '15 3 * * *'  # 9:15 AM IST daily

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python3 pcs_scanner_standalone.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## Troubleshooting

### Issue: No stocks found
**Cause**: Market hours, high filter thresholds, data quality issues
**Solution**: Check market is open, lower pattern_strength_min, verify data

### Issue: Telegram not sending
**Cause**: Invalid token/chat ID, network blocked
**Solution**: Verify credentials, check internet, see TELEGRAM_SETUP.md

### Issue: "ModuleNotFoundError"
**Cause**: Dependencies not installed
**Solution**: `pip install -r requirements.txt`

### Issue: No data from Yahoo Finance
**Cause**: Network blocked, Yahoo down, regional restrictions
**Solution**: Check internet, use VPN, verify proxy settings

## Dependencies

```
yfinance>=0.2.18      # Stock data
pandas>=2.0.0         # Data processing
numpy>=1.24.0         # Numerical computing
python-telegram-bot   # Telegram integration
```

Optional (for run_scanner.py):
```
ta>=0.10.2            # Technical analysis (can be tricky to install)
streamlit>=1.28.0     # Web UI
plotly>=5.17.0        # Charting
```

## Understanding the Scores

### Pattern Strength (0-100)
- **80-100**: Excellent setup - high probability
- **65-79**: Good setup - moderate probability  
- **50-64**: Fair setup - worth watching
- **<50**: Weak signal - filtered out

### How Strength is Calculated

Each pattern analysis includes:
- **Consolidation quality** (tighter = better)
- **Volume confirmation** (higher = better)
- **Technical indicators alignment** (RSI, MACD, ADX)
- **Distance from support/resistance**
- **Trend strength** (ADX value)

## Important Disclaimers

⚠️ **This is NOT financial advice**
- Use for educational purposes only
- Always verify with your own analysis
- Past performance ≠ Future results
- Options trading involves substantial risk
- Start with paper trading

## Contributing

Want to improve the scanner?
1. Test thoroughly before deployment
2. Add new patterns in `detect_patterns()`
3. Improve indicator calculations
4. Add support for more stocks
5. Enhance Telegram messages

## Files

```
nsepcs/
├── pcs_scanner_standalone.py    # Main scanner (recommended)
├── run_scanner.py               # Alternative using streamlit_app
├── TELEGRAM_SETUP.md            # Telegram configuration guide
├── SCANNER_README.md            # This file
├── streamlit_app.py             # Original Streamlit app
└── requirements.txt             # Python dependencies
```

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set up Telegram**: Follow TELEGRAM_SETUP.md
3. **Test the scanner**: `python3 pcs_scanner_standalone.py`
4. **Schedule automation**: Use cron, Task Scheduler, or GitHub Actions
5. **Monitor results**: Check Telegram messages daily

---

**Questions?** Check TELEGRAM_SETUP.md or review the comments in pcs_scanner_standalone.py

**Last Updated**: October 18, 2024
