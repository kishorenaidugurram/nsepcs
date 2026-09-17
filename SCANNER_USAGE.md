# NSE F&O PCS Scanner - Telegram Notifications

Complete guide to set up and run the stock scanner with Telegram notifications.

## Quick Start

### 1. Three Scanner Options

**Option A: Live Scanner with Telegram** (Recommended)
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
python scanner_telegram.py
```

**Option B: Demo Scanner with Synthetic Data** (For testing)
```bash
python scanner_demo_data.py
```

**Option C: Standalone Scanner** (No external dependencies)
```bash
python scanner_demo.py
```

### 2. Get Telegram Credentials

Follow the detailed steps in `TELEGRAM_SETUP.md`:
1. Open Telegram and chat with @BotFather
2. Create a new bot to get your `TELEGRAM_BOT_TOKEN`
3. Chat with @userinfobot to get your `TELEGRAM_CHAT_ID`

### 3. Set Environment Variables

```bash
# Terminal/Linux/Mac
export TELEGRAM_BOT_TOKEN='123456:ABCdefGHIjklmno...'
export TELEGRAM_CHAT_ID='987654321'

# Or create .env file
echo "TELEGRAM_BOT_TOKEN=123456:ABCdefGHIjklmno..." >> .env
echo "TELEGRAM_CHAT_ID=987654321" >> .env
source .env
```

### 4. Run the Scanner

```bash
python scanner_telegram.py
```

You'll receive Telegram messages with:
- Stocks meeting your PCS score criteria
- Price, RSI, Volume ratios
- Technical analysis details

## Configuration Options

Customize scanner behavior with environment variables:

```bash
# Minimum PCS score threshold (default: 50)
export MIN_PCS_SCORE=55

# Minimum volume ratio (default: 0.7)
export MIN_VOLUME_RATIO=0.8

# Number of stocks to scan (default: 40)
export MAX_STOCKS=30

# Then run
python scanner_telegram.py
```

## Filter Explanation

| Filter | Meaning | Range | Recommendation |
|--------|---------|-------|-----------------|
| **PCS Score** | Overall trading opportunity score | 0-100 | 50-70 for balanced trading |
| **Volume Ratio** | Recent vol / Historical vol | 0.5-1.5 | ≥0.7 for good liquidity |
| **RSI** | Momentum indicator | 0-100 | 40-70 optimal range |
| **ADX** | Trend strength | 0-100 | >20 indicates strong trend |
| **MACD** | Trend direction | - | Positive = bullish momentum |

## Understanding Results

### PCS Score Components (100 points total)

- **Momentum (30%)**: RSI in optimal range
- **Trend (25%)**: Strong directional movement (ADX)
- **Support (20%)**: Price near support levels
- **Volatility (15%)**: Suitable for option writing
- **Volume (10%)**: Good liquidity for entry/exit

### Example Output

```
Symbol      Price  PCS Score  RSI  Vol Ratio
RELIANCE   2850.50   85       52.3   0.92
TCS        3620.00   78       48.7   0.88
HDFCBANK   1820.25   92       61.5   1.05
```

## Scheduled Execution

### Run Daily (Linux/Mac - Crontab)

```bash
# Edit crontab
crontab -e

# Add this line to run at 9:15 AM daily
15 9 * * * cd /home/user/nsepcs && source .env && python scanner_telegram.py

# Run twice daily (9:15 AM and 2:15 PM)
15 9 * * * cd /home/user/nsepcs && source .env && python scanner_telegram.py
15 14 * * * cd /home/user/nsepcs && source .env && python scanner_telegram.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set Name: "NSE PCS Scanner"
4. Set Trigger: Daily at 9:15 AM
5. Set Action:
   - Program: `C:\Python\python.exe`
   - Arguments: `C:\path\to\scanner_telegram.py`
   - Start in: `C:\path\to\nsepcs`
6. Add environment variables in Action settings

## Troubleshooting

### "No stocks found"

**Solutions:**
1. Lower `MIN_PCS_SCORE` (try 45 instead of 55)
2. Increase `MAX_STOCKS` to scan more stocks
3. Lower `MIN_VOLUME_RATIO` (try 0.6 instead of 0.7)
4. Check if market is open (scanner works best during trading hours)

**Example:**
```bash
MIN_PCS_SCORE=45 MIN_VOLUME_RATIO=0.6 python scanner_telegram.py
```

### "Telegram: invalid bot token"

1. Copy token again from @BotFather (avoid spaces)
2. Verify: `export TELEGRAM_BOT_TOKEN='...'`
3. Check: `echo $TELEGRAM_BOT_TOKEN` (should show your token)

### "Telegram: Chat ID not found"

1. Make sure Chat ID is a number (no spaces)
2. Try @userinfobot for confirmation
3. For groups, ID might be negative (e.g., `-123456789`)

### Network Connection Errors

If getting proxy errors:
1. Check internet connection
2. Verify firewall allows outbound HTTPS
3. For corporate networks, configure proxy in environment

## Scanner Files

### Main Files

- **scanner_telegram.py** (365 lines)
  - Live data from Yahoo Finance
  - Telegram notifications
  - Technical analysis engine

- **scanner_demo_data.py** (200 lines)
  - Synthetic sample data
  - No external dependencies
  - Great for testing setup

- **scanner_demo.py** (250 lines)
  - Offline mode
  - Pure Python indicators
  - No Telegram required

### Setup & Documentation

- **TELEGRAM_SETUP.md** (150 lines)
  - Detailed Telegram bot creation
  - Environment variable configuration
  - Scheduling instructions

- **SCANNER_USAGE.md** (This file)
  - Quick start guide
  - Configuration reference
  - Troubleshooting

## Results Handling

### Automatic CSV Export

Every scan creates `pcs_results_YYYYMMDD_HHMMSS.csv` with:
```
Symbol,Price,PCS Score,RSI,Vol Ratio,Details
RELIANCE,2850.50,85,52.3,0.92,RSI optimal | Strong trend | Above SMA20 | MACD positive | Good Volume
```

### Telegram Message Format

```
📊 NSE F&O PCS Scanner
2026-09-17 09:45 IST

Found 12 stocks

Results:
RELIANCE     85  52.3
TCS          78  48.7
HDFCBANK     92  61.5
```

## Best Practices

1. **Start Conservative**
   - Begin with default settings
   - Observe results for 1 week
   - Adjust based on patterns

2. **Morning Scans**
   - Run between 9:15-10:00 AM IST
   - Avoids early market noise
   - Gives time for position planning

3. **Combine with Your Analysis**
   - Scanner identifies candidates
   - Use your own technical analysis to confirm
   - Always verify price levels

4. **Monitor Both Screens**
   - Keep 2 stocks minimum score threshold
   - Track both best and marginal opportunities
   - Compare weekly trends

5. **Review Results**
   - Save weekly results for backtesting
   - Track which stocks actually moved
   - Refine filters based on results

## FAQ

**Q: Can I run multiple scanners simultaneously?**
A: Yes, use different MAX_STOCKS values or separate stock lists.

**Q: How often should I run the scanner?**
A: Once or twice daily during trading hours is optimal.

**Q: Can I modify the stock list?**
A: Yes, edit the DEMO_STOCKS list in scanner files.

**Q: What if I only want certain sectors?**
A: Filter the stock list to include only your preferred sectors.

**Q: Can I send to multiple Telegram accounts?**
A: Create separate bots and run multiple instances with different tokens.

## Support

For issues with:
- **Telegram Setup**: See TELEGRAM_SETUP.md
- **Scanner Logic**: Check the README.md
- **Configuration**: Review this file's Configuration section
- **Network Issues**: Contact your system administrator

## Security Notes

⚠️ **Never:**
- Commit `.env` file to version control
- Share bot tokens or chat IDs
- Store credentials in source code

✅ **Always:**
- Use `.gitignore` for `.env` and `.env.local`
- Rotate tokens if exposed
- Use separate credentials for dev/prod environments

---

**Last Updated**: 2026-09-17  
**Scanner Version**: 1.0  
**Status**: Production Ready
