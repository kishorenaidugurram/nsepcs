# NSE PCS Scanner - Telegram Integration Setup

## Overview

I've created a standalone NSE PCS Scanner that runs without the Streamlit UI and sends results directly to your Telegram account. This allows you to get daily stock screening results delivered to your phone automatically.

## Files Created

1. **run_scanner.py** - Main standalone scanner script
2. **telegram_config.py** - Telegram credentials configuration
3. **telegram_sender.py** - Module for sending results to Telegram
4. **ta_compat.py** - Compatibility layer for technical analysis (uses pandas-ta as fallback)

## Prerequisites

The following packages need to be installed:
- yfinance (stock data)
- pandas (data processing)
- numpy (numerical operations)
- pandas-ta (technical indicators)
- requests (Telegram API calls)
- pytz (timezone handling)
- scikit-learn, scipy (advanced analysis)
- beautifulsoup4 (web scraping)
- openpyxl (Excel export)
- matplotlib, plotly (charting)

Install with:
```bash
pip3.13 install -r requirements.txt
```

**Note**: Python 3.13 is required due to build compatibility issues with some packages on this system.

## Configuration

### 1. Set Telegram Credentials

Before running the scanner, you need to set up your Telegram bot token and chat ID as environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### How to Get Telegram Credentials

#### Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/start` to begin
3. Send `/newbot` to create a new bot
4. Follow the prompts to name your bot
5. BotFather will give you a token that looks like: `123456789:ABCDefGHIJKlmNoPQRstUVwxyZ`
6. Copy this token and use as `TELEGRAM_BOT_TOKEN`

#### Get Your Chat ID
1. Send a message to your bot or any bot you have created
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Replace `<YOUR_BOT_TOKEN>` with your actual bot token
4. Find your `chat.id` in the response (usually a negative number for groups or positive for personal)
5. Use this as `TELEGRAM_CHAT_ID`

Alternatively, use a bot like `@userinfobot` to get your personal chat ID.

### 2. Store Credentials Permanently

For scheduled tasks, add to your shell profile (~/.bashrc or ~/.bash_profile):

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then reload:
```bash
source ~/.bashrc
```

## Running the Scanner

### Quick Test
```bash
cd /home/user/nsepcs
python3.13 run_scanner.py
```

### Scanner Output

The scanner will:
1. 🚀 Scan configured stocks (default: 208 NSE F&O stocks)
2. 🔍 Apply technical filters:
   - RSI: 30-75
   - ADX: Minimum 20
   - Volume: 1.2x average
   - Chart patterns: Current day breakouts, cup & handle, flat bases, etc.
3. 📊 Generate a results file: `scan_results_YYYYMMDD_HHMMSS.json`
4. 📱 Send results to Telegram (if configured)

### Sample Output

**Console Output:**
```
============================================================
🎯 NSE PCS Scanner - Standalone Mode
============================================================

✅ Telegram is configured and ready
🚀 Starting NSE PCS Scanner at 2026-11-27 03:47:07
📊 Scanning 208 stocks...
   [20/208] Processing...
   [40/208] Processing...
   ...

✅ Scan Complete!
   📈 Stocks Found: 15
   ⚠️  Failed/Skipped: 193
   
💾 Results saved to scan_results_20261127_034707.json
📱 Sending results to Telegram...
✅ Results sent to Telegram
```

**Telegram Message:**
```
🎯 NSE PCS Scanner Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Timestamp: 2026-11-27 03:47:15
📊 Stocks Found: 15

Top Qualifying Stocks:

1. 🟢 RELIANCE
   💰 ₹2,845.50 | 📊 Vol: 2.1x | RSI: 65 | ADX: 28
   💪 Strength: 88% | HIGH

2. 🟢 TCS
   💰 ₹3,520.25 | 📊 Vol: 1.8x | RSI: 58 | ADX: 25
   💪 Strength: 82% | HIGH
...
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Total Patterns Found: 18
✨ High Confidence Stocks: 8
📱 Sent from NSE PCS Scanner
```

## Schedule with Cron

To run the scanner daily at 4:00 PM IST (after market close):

```bash
# Edit your crontab
crontab -e

# Add this line (4:00 PM IST = 10:30 AM UTC)
30 10 * * 1-5 cd /home/user/nsepcs && python3.13 run_scanner.py >> /tmp/scanner.log 2>&1
```

For 3:30 PM IST instead:
```bash
0 10 * * 1-5 cd /home/user/nsepcs && python3.13 run_scanner.py >> /tmp/scanner.log 2>&1
```

## Customization

### Filter Criteria

Edit the default configuration in `run_scanner.py`:

```python
def _get_default_config(self):
    return {
        'rsi_min': 30,           # Minimum RSI
        'rsi_max': 75,           # Maximum RSI
        'adx_min': 20,           # Minimum ADX
        'ma_support': True,      # Use moving average support
        'min_volume_ratio': 1.2, # Minimum volume multiplier
        'lookback_days': 20,     # Lookback period for breakout detection
        'pattern_strength_min': 65,  # Minimum pattern strength
        # ... more options
    }
```

### Stock Universe

Change from F&O stocks to Non-F&O stocks:

```python
# In run_scanner.py's _get_default_config():
# Change from:
'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,

# To:
'stocks_to_scan': get_nse_non_fno_stocks(),  # ~800+ stocks
```

## Troubleshooting

### "Telegram not configured"
- Ensure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set
- Check with: `echo $TELEGRAM_BOT_TOKEN`

### "No stocks found"
- Adjust filter criteria (lower ADX, RSI ranges)
- Run during market hours for better data
- Check if stock data is available

### "Network connection errors"
- This is a known issue in this environment with Yahoo Finance
- May need network policy adjustments

### "Module not found" errors
- Ensure all packages are installed: `pip3.13 install -r requirements.txt`
- Use Python 3.13: `python3.13 run_scanner.py`

## Results File Format

Each scan creates a JSON file with this structure:

```json
[
  {
    "symbol": "RELIANCE.NS",
    "current_price": 2845.50,
    "volume_ratio": 2.1,
    "rsi": 65.2,
    "adx": 28.5,
    "patterns": [
      {
        "type": "Current Day Breakout",
        "strength": 88.0,
        "confidence": "HIGH",
        "success_rate": 72.5,
        "pcs_suitability": 85.3
      }
    ]
  }
]
```

## API Limits

- Telegram API: ~30 messages per second (no issue for daily scans)
- Yahoo Finance: Requests are throttled, scanner handles this automatically

## Support & Issues

If you encounter issues:
1. Check the log file: `tail -f /tmp/scanner.log`
2. Run manually to see error messages: `python3.13 run_scanner.py`
3. Verify network connectivity and credentials

## Next Steps

1. ✅ Create a Telegram bot and get credentials
2. ✅ Set environment variables
3. ✅ Run: `python3.13 run_scanner.py`
4. ✅ Check Telegram for results
5. ✅ Set up cron job for daily automated scans

---

**Scanner Version**: 1.0  
**Created**: 2026-11-27  
**Compatible with**: NSE F&O and Non-F&O stocks
