# Telegram Integration for NSE F&O PCS Scanner

## Overview

The NSE F&O PCS Scanner now supports Telegram notifications. This allows you to receive stock screening results automatically on your Telegram account.

## Setup Instructions

### 1. Get Your Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/start` and follow the instructions
3. Send `/newbot` to create a new bot
4. BotFather will give you a **BOT_TOKEN** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvwxyzABCDEfghij`)

### 2. Get Your Chat ID

1. Open your created bot and send it any message
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find the `chat.id` in the response (looks like: `123456789`)

### 3. Configure Environment Variables

Set these environment variables before running the scanner:

```bash
export TELEGRAM_BOT_TOKEN='your-bot-token-here'
export TELEGRAM_CHAT_ID='your-chat-id-here'
```

For persistent configuration, add to `.bashrc` or `.bash_profile`:

```bash
echo "export TELEGRAM_BOT_TOKEN='your-bot-token-here'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your-chat-id-here'" >> ~/.bashrc
source ~/.bashrc
```

## Usage

### Run the Simplified Scanner (Recommended)

```bash
python simple_scanner.py
```

This scanner:
- ✅ Works without complex dependencies
- ✅ Uses basic technical indicators (RSI, Volume, Breakouts)
- ✅ Detects bullish patterns automatically
- ✅ Sends results directly to Telegram (if credentials configured)
- ✅ Shows top 15 results in Telegram message

### Run the Full Scanner

```bash
python run_scanner_telegram.py
```

This scanner:
- ✅ Uses the complete technical analysis from streamlit_app.py
- ✅ Detects multiple pattern types
- ✅ Provides detailed analysis
- ⚠️ Requires additional dependencies

## Features

### Scanner Detects

**Simple Scanner (simple_scanner.py)**
- Consolidation Breakout patterns
- Higher Lows trends
- RSI Oversold bounces
- Volume Surges

**Full Scanner (run_scanner_telegram.py)**
- Current Day Breakouts
- Cup and Handle patterns
- Flat Base Breakouts
- Double Bottoms
- Rectangle formations
- Head-and-Shoulders
- Bump-and-Run reversals
- And 5+ more advanced patterns

### Telegram Message Format

```
📊 NSE F&O PCS Scanner Results
Generated: 2024-07-10 15:30:45 IST
Stocks found: 12 out of 50 scanned

1. RELIANCE - ₹2,856.50
   📈 Patterns: Consolidation Br, Volume Surge
   📊 Score: 78/100 (2 patterns)

2. TCS - ₹3,456.75
   📈 Patterns: Higher Lows, RSI Bounce
   📊 Score: 72/100 (2 patterns)

[... more results ...]

Run the full scan for detailed analysis
```

## Troubleshooting

### Message Says "Telegram credentials not configured"

1. **Verify credentials are set:**
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```

2. **If empty, set them:**
   ```bash
   export TELEGRAM_BOT_TOKEN='your-token'
   export TELEGRAM_CHAT_ID='your-id'
   ```

3. **Test the bot:**
   ```bash
   curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage \
     -d chat_id=<CHAT_ID> \
     -d text="Test message"
   ```

### "Failed to get ticker" Errors

The scanner requires internet access to Yahoo Finance. This may be blocked by:
- Network proxy restrictions
- Firewall rules
- ISP blocking

**Workaround:** Run on a system with unrestricted internet access.

### No Stocks Found

This can happen if:
- All stocks failed to fetch data (network issue)
- No patterns matched your filters
- Market conditions don't match pattern criteria

**Check logs:** Run with `2>&1 | tee scan.log` to save output for analysis

## Running Periodically

### Using Cron (Linux/Mac)

```bash
# Run scanner daily at 3:30 PM IST
30 15 * * * source ~/.bashrc && cd /home/user/nsepcs && python simple_scanner.py >> /tmp/scanner.log 2>&1
```

### Using Task Scheduler (Windows)

1. Create a batch file `run_scanner.bat`:
   ```batch
   @echo off
   cd C:\path\to\nsepcs
   set TELEGRAM_BOT_TOKEN=your-token
   set TELEGRAM_CHAT_ID=your-id
   python simple_scanner.py
   ```

2. Schedule in Task Scheduler with daily trigger

### Using GitHub Actions

1. Add repository secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

2. Create `.github/workflows/scanner.yml`:
   ```yaml
   name: Daily Scanner
   on:
     schedule:
       - cron: '30 15 * * *'
   jobs:
     scan:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - uses: actions/setup-python@v2
           with:
             python-version: '3.11'
         - run: pip install -r requirements.txt
         - run: python simple_scanner.py
           env:
             TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
             TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
   ```

## Filter Customization

Edit `simple_scanner.py` or `run_scanner_telegram.py` to customize:

- `max_stocks`: Number of stocks to scan (default: 50)
- RSI thresholds (default: 35-65)
- Pattern strength minimum (default: 50)
- ADX minimum (default: 20)
- Volume ratio threshold

Example:
```python
scan_data = run_scanner(
    max_stocks=100,  # Scan more stocks
    pattern_strength_min=60  # Higher threshold
)
```

## File Reference

| File | Purpose | Complexity |
|------|---------|-----------|
| `simple_scanner.py` | Lightweight scanner with Telegram | Low |
| `run_scanner_telegram.py` | Full-featured scanner | High |
| `streamlit_app.py` | Web UI (Streamlit) | High |
| `requirements.txt` | Python dependencies | - |

## Performance

| Metric | Value |
|--------|-------|
| Stocks per minute | 2-3 |
| 50 stocks | ~20 minutes |
| 100 stocks | ~40 minutes |
| Telegram message delay | <2 seconds |

## Security Notes

⚠️ **Protect your credentials:**
- Never commit tokens to git
- Use environment variables, not hardcoding
- Rotate bot tokens periodically
- Keep chat IDs private

✅ **Best practices:**
- Use separate bots for dev and production
- Limit bot permissions to "Send messages only"
- Review bot command access (set to admin only)

## Example Output

```
======================================================================
               NSE F&O PCS Scanner - Telegram Integration
======================================================================

🔍 Starting Simplified PCS Scanner...
   Analyzing: 50 stocks

[ 1/50] RELIANCE   ✅ 2 patterns | Score: 78
[ 2/50] TCS        ✅ 1 pattern  | Score: 65
[ 3/50] HDFCBANK   ✗
...
[50/50] TRENT      ✅ 3 patterns | Score: 82

✅ Scan complete: Found 12 stocks with bullish patterns

📤 Sending results to Telegram...
✅ Message sent to Telegram successfully

📋 Top Stocks Found:
   1. TRENT      - Score: 82 - ₹3,456.50
   2. RELIANCE   - Score: 78 - ₹2,856.50
   3. HCLTECH    - Score: 75 - ₹1,234.75
   4. WIPRO      - Score: 72 - ₹456.25
   5. INFY       - Score: 70 - ₹2,345.60

✅ Scanner completed successfully!
```

## Support

For issues:
1. Check that bot token and chat ID are correct
2. Verify network connectivity to Telegram API
3. Review the scan.log for detailed error messages
4. Test credentials independently using curl

## Future Enhancements

- [ ] Support for multiple Telegram groups
- [ ] Custom alert thresholds per pattern
- [ ] Historical performance tracking
- [ ] Integration with trading APIs
- [ ] Web dashboard with historical charts
- [ ] Email fallback notifications
