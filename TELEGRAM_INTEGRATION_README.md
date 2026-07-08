# 📱 Stock Scanner with Telegram Integration

A professional NSE stock scanner that analyzes F&O stocks and sends filtered results directly to your Telegram.

## What's New ✨

I've created a complete Telegram integration for your stock scanner that:

✅ **Scans NSE F&O Stocks** - Analyzes 208 stocks from the NSE F&O universe  
✅ **Uses Smart Filters** - Technical indicators: RSI, SMA, EMA, MACD, Volume  
✅ **Sends to Telegram** - Real-time notifications with filtered results  
✅ **No Complex Dependencies** - Lightweight scanner without external TA libraries  
✅ **Customizable** - Adjust filters and thresholds via command-line options  
✅ **Scheduled Scanning** - Easy to set up with cron/Task Scheduler  

## Quick Start (5 minutes)

### 1️⃣ Install Dependencies
```bash
pip install yfinance requests numpy pandas
```

### 2️⃣ Create Telegram Bot
- Chat with `@BotFather` on Telegram
- Create bot → Get Token (e.g., `123456:ABC-DEF...`)
- Send a message to your bot → Get Chat ID from:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
  ```

### 3️⃣ Set Credentials
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 4️⃣ Run Scanner
```bash
python3 simple_scanner.py --telegram --limit 50
```

That's it! Results appear in your Telegram instantly.

## What You Get 📊

### Telegram Message Example
```
📈 Stock Scanner Results
Generated: 2026-07-08 15:30 IST

🎯 Found: 18 stocks matching criteria

1. RELIANCE
   Price: ₹2,845.50
   RSI: 55.2 | Vol: 2.34x
   ✓ Healthy RSI (55.2)
   ✓ Above avg volume (2.34x)
   ✓ Above SMA20 (Uptrend)
```

### CSV Export Example
```
Symbol,Price,RSI,Vol Ratio,Patterns,Max Strength
RELIANCE,2845.50,55.2,2.34,Cup and Handle,78
TCS,3245.75,52.8,1.87,Breakout,75
INFY,1890.25,48.5,2.12,Uptrend,72
```

## Files Included

| File | Purpose |
|------|---------|
| `simple_scanner.py` | Main scanner with Telegram integration |
| `telegram_scanner.py` | Alternative full-featured version |
| `RUN_SCANNER.sh` | Convenient bash wrapper |
| `SETUP_TELEGRAM.md` | Detailed setup instructions |
| `DEMO_RESULTS.txt` | Example output |

## Filter Criteria 🎯

The scanner filters stocks based on:

| Indicator | Min | Max | Meaning |
|-----------|-----|-----|---------|
| **RSI** | 30 | 75 | Healthy momentum (not overbought/oversold) |
| **Volume** | 1.0x | ∞ | Above average trading volume |
| **Trend** | - | - | Price above 20-day moving average |
| **Score** | 40 | 100 | Combined signal strength |

### Signals Detected
- ✓ Healthy RSI (30-75)
- ✓ Above average volume
- ✓ Uptrend (price > SMA20)
- ✓ Breakout potential (near resistance)
- ✓ MACD bullish signal

## Command-Line Options

```bash
python3 simple_scanner.py [OPTIONS]

Options:
  --telegram              Send results to Telegram
  --limit N               Stocks to scan (default: 50)
  --file FILENAME         Export to CSV
  --help                  Show help
```

### Examples
```bash
# Scan 100 stocks and send to Telegram
python3 simple_scanner.py --telegram --limit 100

# Scan and save to file
python3 simple_scanner.py --limit 50 --file results.csv

# Using shell script
bash RUN_SCANNER.sh 100 65
```

## Telegram Integration 📱

### Features
- **Start Notification** - "Scanner started, scanning 100 stocks"
- **Progress Updates** - Every 20 stocks scanned
- **Detailed Results** - Top 15 matches with all metrics
- **Completion Notice** - Final summary statistics
- **File Attachments** - Optional Excel export

### Setup Telegram
See `SETUP_TELEGRAM.md` for complete guide:
1. Create bot with @BotFather
2. Get your Chat ID
3. Set environment variables
4. Run scanner with `--telegram` flag

## Scheduling Automated Scans ⏰

### Linux/Mac (Daily after market close)
```bash
# Edit crontab
crontab -e

# Add line (3:30 PM IST = 9:30 UTC):
30 9 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python3 simple_scanner.py --limit 100 --telegram
```

### Windows
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 3:30 PM
4. Action: Run `python3 simple_scanner.py --limit 100 --telegram`

## How It Works 🔧

### Data Flow
```
1. Fetch stock data (Yahoo Finance via yfinance)
2. Calculate indicators (RSI, SMA, Volume ratio)
3. Apply filters (RSI, Volume, Trend)
4. Score and rank matching stocks
5. Format message with top results
6. Send to Telegram via Bot API
7. (Optional) Export to CSV/Excel
```

### Indicators Used
- **RSI (14-period)** - Momentum oscillator
- **SMA (20-period)** - Trend direction
- **EMA (20-period)** - Weighted trend
- **MACD** - Trend following momentum
- **Volume Ratio** - Activity surge detection
- **ATR** - Volatility measure

### Filtering Logic
```python
score = 0
if 30 <= rsi <= 75:
    score += 20  # Healthy momentum
if volume > avg * 1.5:
    score += 15  # Above average activity
if price > sma20:
    score += 20  # Uptrend
if price near resistance:
    score += 25  # Breakout potential
if macd > signal:
    score += 15  # Bullish momentum

# Stocks with score >= 40 are selected
```

## Customization 🛠️

### Adjust Minimum Score
Edit `simple_scanner.py`:
```python
filters = {'min_score': 50}  # Increase from 40 to 50
```

### Add Custom Indicators
```python
def analyze_stock(self, symbol, data):
    # ... existing code ...
    
    # Add your custom indicator
    custom_signal = calculate_your_indicator(data)
    return analysis
```

### Change Stock List
```python
stock_list = [
    'RELIANCE.NS', 'TCS.NS', ...
][:args.limit]
```

## Troubleshooting 🔍

| Issue | Solution |
|-------|----------|
| "No data" for stocks | Check internet connection / Yahoo Finance access |
| Telegram not working | Verify bot token and chat ID |
| No stocks found | Lower min_score or adjust RSI range |
| Slow scanning | Reduce limit or skip news fetch |

### Debug Commands
```bash
# Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Verify bot token
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Test message
python3 -c "from simple_scanner import SimpleScanner; \
s = SimpleScanner(); \
s.send_telegram_message('Test message')"
```

## Performance 📈

### Scanning Time
- 50 stocks: ~5 minutes
- 100 stocks: ~10 minutes
- 208 stocks: ~20 minutes

### Data Requirements
- ~100MB RAM
- Stable internet connection
- Access to Yahoo Finance

## Limitations ⚠️

- Real-time data lags ~15 minutes (market close)
- NSE symbols only (.NS suffix)
- Historical data: 3 months minimum
- Requires internet connection

## Future Enhancements 🚀

- [ ] Weekly/Monthly timeframe analysis
- [ ] Pattern recognition (cup & handle, head & shoulders)
- [ ] Support/Resistance level detection
- [ ] News sentiment analysis
- [ ] Portfolio tracking
- [ ] Alert on specific patterns
- [ ] Multiple telegram groups support
- [ ] Database storage of results

## Support & Issues 💬

### Common Questions

**Q: How often should I run the scanner?**  
A: Daily after market close (3:30 PM IST) for best results.

**Q: Can I scan specific stocks only?**  
A: Yes, edit the `stock_list` in `simple_scanner.py`

**Q: How do I interpret RSI?**  
A: RSI 30-70 is healthy. Above 70 is overbought, below 30 is oversold.

**Q: Why no stocks found?**  
A: Market conditions may not match filters. Try adjusting min_score.

## License

Open source - feel free to modify and distribute.

## Credits

Built with:
- `yfinance` - Yahoo Finance data
- `pandas` - Data processing
- `numpy` - Numerical computations
- `Telegram Bot API` - Message delivery

---

**Ready to get started? Follow the Quick Start section above!**

For detailed setup instructions, see `SETUP_TELEGRAM.md`

Happy trading! 📈🚀
