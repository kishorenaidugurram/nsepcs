# Telegram Stock Scanner - User Guide

This directory contains automated stock scanners that analyze NSE F&O stocks and send results to Telegram.

## Overview

There are three scanner versions available:

### 1. **simple_telegram_scanner.py** (RECOMMENDED)
- **Purpose**: Lightweight scanner with essential technical analysis
- **Features**:
  - Real-time price data fetching from Yahoo Finance
  - RSI, ADX, MACD technical indicators
  - Breakout detection
  - Volume analysis
  - Telegram integration
- **Best for**: Automated scheduled runs, lightweight analysis
- **Requirements**: Internet connection

### 2. **telegram_scanner_demo.py** (DEMO/TESTING)
- **Purpose**: Demonstration version using synthetic data
- **Features**:
  - Works offline (no internet required)
  - Same analysis logic as live scanner
  - 15 sample stocks with realistic synthetic data
  - Perfect for testing Telegram integration
- **Best for**: Testing without network access, development
- **Requirements**: None (fully self-contained)

### 3. **telegram_scanner.py** (ADVANCED)
- **Purpose**: Full-featured scanner importing from main Streamlit app
- **Features**:
  - Access to all PCS scoring features
  - Weekly pattern validation
  - News integration
  - Enhanced support/resistance analysis
- **Best for**: Production use with full analysis
- **Requirements**: All dependencies in requirements.txt, network access

## Setup Instructions

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "NSE Stock Scanner")
4. Choose a username for your bot (must end with `bot`, e.g., `nse_stock_scanner_bot`)
5. BotFather will give you a **TOKEN** - save this!

Example token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGH`

### Step 2: Get Your Chat ID

1. Send any message to your new bot
2. Visit this URL in your browser, replacing TOKEN:
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. Look for `"chat":{"id":YOURCHATID` - save this number

### Step 3: Configure Environment Variables

```bash
# Export Telegram credentials
export TELEGRAM_BOT_TOKEN="your-token-here"
export TELEGRAM_CHAT_ID="your-chat-id-here"

# Optional: Configure scanner parameters
export MIN_RSI="35"              # Minimum RSI threshold
export MAX_RSI="75"              # Maximum RSI threshold
export MIN_ADX="20"              # Minimum ADX trend strength
export MIN_VOLUME_RATIO="1.2"    # Minimum volume ratio
export MIN_RESULTS="3"           # Minimum stocks to send results
```

### Step 4: Run the Scanner

**For Testing (Demo Mode - No Internet Required):**
```bash
python3 telegram_scanner_demo.py
```

**For Real Analysis (Requires Internet):**
```bash
python3 simple_telegram_scanner.py
```

**For Advanced Analysis (Full Features):**
```bash
# First install all dependencies
pip install -r requirements.txt

# Then run
python3 telegram_scanner.py
```

## Scanner Comparison

| Feature | Demo | Simple | Advanced |
|---------|------|--------|----------|
| Network Required | ❌ | ✅ | ✅ |
| Setup Time | <1 min | 2 min | 5 min |
| Stocks Analyzed | 15 | 40 | 219 (configurable) |
| Data Type | Synthetic | Real | Real |
| Indicators | Basic | Basic+ | Full |
| Pattern Detection | - | 4 patterns | 15+ patterns |
| Weekly Validation | - | - | ✅ |
| News Analysis | - | - | ✅ |

## Filter Criteria (Configurable)

The scanner uses these filters to identify qualifying stocks:

| Filter | Default | Range |
|--------|---------|-------|
| RSI (Relative Strength Index) | 35-75 | 0-100 |
| ADX (Trend Strength) | ≥20 | 0-100 |
| Volume Ratio | ≥1.2x | 0.5x - 10x |
| Pattern Score | ≥60 | 0-100 |
| Min Results | ≥3 stocks | 1+ |

### What These Filters Mean

- **RSI**: Measures momentum. 35-75 means:
  - < 30: Oversold (might bounce)
  - 30-70: Neutral
  - > 70: Overbought (might pullback)

- **ADX**: Measures trend strength. 20+ means:
  - < 20: Weak trend, lots of chop
  - 20-40: Moderate to strong trend
  - 40+: Very strong trend

- **Volume Ratio**: Today's volume vs 20-day average:
  - 1.2x: 20% above average (good breakout confirmation)
  - 2.0x: 2x average (strong institutional interest)

## Using with Cron/Scheduler

### Run Daily at Market Close (3:30 PM IST)

Add to your crontab:
```bash
# Run scanner at 3:40 PM daily (Monday-Friday)
40 15 * * 1-5 cd /path/to/nsepcs && TELEGRAM_BOT_TOKEN="token" TELEGRAM_CHAT_ID="id" python3 simple_telegram_scanner.py >> /tmp/scanner.log 2>&1
```

### Run Multiple Times Daily

```bash
# Morning (10:30 AM IST) - Mid-day scan
30 10 * * 1-5 cd /path/to/nsepcs && TELEGRAM_BOT_TOKEN="token" TELEGRAM_CHAT_ID="id" python3 simple_telegram_scanner.py >> /tmp/scanner.log 2>&1

# Afternoon (2:00 PM IST) - Pre-close scan
0 14 * * 1-5 cd /path/to/nsepcs && TELEGRAM_BOT_TOKEN="token" TELEGRAM_CHAT_ID="id" python3 simple_telegram_scanner.py >> /tmp/scanner.log 2>&1

# Evening (4:00 PM IST) - Post-close analysis
0 16 * * 1-5 cd /path/to/nsepcs && TELEGRAM_BOT_TOKEN="token" TELEGRAM_CHAT_ID="id" python3 simple_telegram_scanner.py >> /tmp/scanner.log 2>&1
```

## Output Format

### Telegram Message (Example)

```
📊 NSE Stock Scan Results
🕐 2026-09-15 15:40:00

🎯 Stocks Found: 12
📈 Avg Score: 74.5

━━━━━━━━━━━━━━━━━━━━

#1 KOTAKBANK
💰 ₹480.50
📊 RSI: 61.2 | ADX: 28.5
📈 Vol: 1.8x | Score: 85
🟢 MACD: BULLISH 🔥 BREAKOUT

#2 TATAMOTORS
💰 ₹650.25
📊 RSI: 52.8 | ADX: 25.3
📈 Vol: 1.5x | Score: 78
🟢 MACD: BULLISH 📊

... and 10 more stocks
```

### Local Output (Example)

Results are saved to `/tmp/scan_results_*.json`:
```json
[
  {
    "symbol": "KOTAKBANK.NS",
    "price": 480.50,
    "rsi": 61.2,
    "adx": 28.5,
    "volume_ratio": 1.8,
    "score": 85,
    "macd_signal": "BULLISH"
  },
  ...
]
```

## Troubleshooting

### Issue: "Telegram not configured"
**Solution**: Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-id"
```

### Issue: "Only X stocks found, below minimum"
**Solution**: Adjust filters to be less strict:
```bash
export MIN_RSI="30"      # More lenient RSI
export MIN_ADX="15"      # Lower trend requirement
export MIN_VOLUME_RATIO="1.0"  # Any volume
```

### Issue: Network timeout / Connection errors
**Solution**: Use demo version:
```bash
python3 telegram_scanner_demo.py
```

### Issue: No results in Telegram
**Checklist**:
1. ✅ Bot token is correct? Test: Visit `https://api.telegram.org/botTOKEN/getMe`
2. ✅ Chat ID is correct? Send a message to bot and check `/getUpdates`
3. ✅ Chat ID matches exactly (including leading minus for groups)?
4. ✅ Internet connection available?
5. ✅ Firewall allows outbound HTTPS?

## Advanced Usage

### Custom Stock List

Modify scanner files to analyze specific stocks:
```python
# In simple_telegram_scanner.py, modify NSE_FO_STOCKS:
NSE_FO_STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "YOUR_STOCK.NS",  # Add your stocks here
]
```

### Adjust Technical Parameters

```bash
# Stricter filters (fewer results, higher quality)
export MIN_ADX="25"
export MIN_RSI="40"
export MIN_RSI_MAX="70"
export MIN_VOLUME_RATIO="1.5"

# Relaxed filters (more results)
export MIN_ADX="15"
export MIN_RSI="30"
export MIN_RSI_MAX="75"
export MIN_VOLUME_RATIO="1.0"
```

### Get Results via Email (Alternative)

Save results to file and email:
```bash
python3 simple_telegram_scanner.py
# Results saved to /tmp/scan_results_*.json

# Email it
mail -s "Stock Scanner Results" your-email@example.com < /tmp/scan_results_*.json
```

## Performance

### Scan Times (Typical)

| Scanner | Stocks | Time | Notes |
|---------|--------|------|-------|
| Demo | 15 | <1 sec | Synthetic data |
| Simple | 40 | 2-3 min | Network dependent |
| Advanced | 50 | 5-10 min | Full analysis |
| Advanced | 219 | 30-60 sec | All F&O stocks |

### Logs

View scan logs:
```bash
tail -f /tmp/nsepcs_scanner.log
```

## Support & Customization

### Default Stocks Analyzed

**Simple Scanner (40 stocks):**
Top tier liquidity stocks (500K+ daily contracts)

**Advanced Scanner (219 stocks):**
All NSE F&O universe stocks

### Contact & Help

For issues or questions:
1. Check logs: `tail /tmp/nsepcs_scanner.log`
2. Test with demo: `python3 telegram_scanner_demo.py`
3. Verify Telegram setup per "Setup Instructions" above

## Disclaimer

⚠️ **IMPORTANT**: This tool is for educational and informational purposes only. It is NOT financial advice.

- Stock selection is based on technical analysis
- Past performance doesn't guarantee future results
- Use paper trading first
- Always do your own research
- Consult financial advisors before trading
- Risk management is YOUR responsibility

## License

This tool is provided as-is for NSE F&O trading analysis.
