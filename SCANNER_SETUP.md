# NSE PCS Scanner - Setup Guide

## Current Status
✗ **Scanner not fully configured** - Telegram credentials missing

## What's Ready
- ✓ Stock scanner code (streamlit_app.py)
- ✓ Standalone scanner script (run_scanner.py)
- ✓ Telegram integration (ready to use)
- ✓ Pattern detection system
- ✓ 208 NSE F&O stocks database

## What's Needed

### 1. Telegram Bot Setup
To send results to Telegram, you need:

#### Step 1: Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Start the chat and send `/newbot`
3. Follow the instructions to create a new bot
4. Copy the **Bot Token** (looks like: `123456789:ABCDefGHijKLmnoPQRstUVwxyz`)

#### Step 2: Get Your Chat ID
1. Send a message to your newly created bot
2. Visit this URL (replace TOKEN with your bot token):
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` and copy the number

### 2. Set Environment Variables

Choose one of the following methods:

#### Method A: Export in Terminal (Temporary)
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### Method B: Create .env file (Recommended)
Create a file named `.env` in `/home/user/nsepcs/`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

#### Method C: GitHub Actions Secrets (For Scheduled Runs)
If using GitHub Actions:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `TELEGRAM_BOT_TOKEN` with your token
4. Add `TELEGRAM_CHAT_ID` with your chat ID

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or manually:
pip install streamlit yfinance pandas numpy ta plotly pytz scikit-learn scipy beautifulsoup4 openpyxl requests
```

If you get permission errors, try:
```bash
pip install --user -r requirements.txt
```

## Running the Scanner

### Option 1: Standalone Scanner (Recommended)
```bash
python run_scanner.py
```

This will:
- Scan first 100 NSE F&O stocks
- Detect bullish patterns
- Send results to Telegram
- Run ~5-10 minutes depending on internet

### Option 2: Streamlit Web App
```bash
streamlit run streamlit_app.py
```

This opens an interactive dashboard where you can:
- Customize scan parameters
- View charts and detailed analysis
- Export results to Excel
- Adjust pattern thresholds

## Scanner Features

### Detected Patterns
1. **Current Day Breakout** - High probability breakouts on current trading day
2. **Cup and Handle** - Classic trend continuation pattern
3. **Flat Base Breakout** - Tight consolidation followed by breakout
4. **Bump-and-Run Reversal** - Bounce reversal from bottom
5. **Rectangle Bottom** - Support/resistance rectangle breakout
6. **Head-and-Shoulders Bottom** - Classic reversal pattern
7. **Double Bottom** - Two-point support reversal
8. **Three Rising Valleys** - Multiple progressive support tests
9. **Rounding Bottom** - Gradual accumulation pattern
10. **Inverted/Descending Scallop** - Step-down consolidation
11. **Rounding Top (Upside Break)** - Counter-trend breakout
12. **Rectangle Top** - Optional bearish pattern

### Default Scan Parameters
- **RSI Range:** 30-75 (momentum filtering)
- **ADX Minimum:** 20 (trend strength)
- **Volume Ratio:** 1.0x+ (volume confirmation)
- **Pattern Strength:** 70%+ (quality filtering)
- **Lookback Period:** 20 days (pattern formation)
- **Weekly Validation:** Enabled (timeframe alignment)

### Stocks Scanned
- 208 NSE F&O stocks
- Organized by sector
- Includes Nifty 50, Bank Nifty, IT, Pharma, Auto, Metals, Energy

## Configuration Examples

### Aggressive Scan (More Results)
```python
results = run_scanner(
    stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:150],
    rsi_min=25,
    rsi_max=80,
    adx_min=15,
    min_volume_ratio=0.8,
    pattern_strength_min=60
)
```

### Conservative Scan (Higher Probability)
```python
results = run_scanner(
    stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:50],
    rsi_min=35,
    rsi_max=70,
    adx_min=25,
    min_volume_ratio=1.5,
    pattern_strength_min=80
)
```

## Automation Setup

### GitHub Actions Scheduled Task
Create `.github/workflows/daily-scan.yml`:
```yaml
name: Daily Stock Scan

on:
  schedule:
    - cron: '0 15 * * 1-5'  # 3:30 PM IST on weekdays

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run scanner
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python run_scanner.py
```

### Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add (runs daily at 3:30 PM IST)
30 15 * * 1-5 cd /home/user/nsepcs && python run_scanner.py
```

## Output Format

### Telegram Message Example
```
🔍 Stock Scanner Results
📅 2026-09-22 15:30:00 IST

✅ Found 12 stocks with patterns
==================================================

1. RELIANCE
  💰 Price: ₹2,450.50
  📊 Volume: 2.5x
  📈 RSI: 55.3
  🎯 Pattern: Current Day Breakout
  💪 Strength: 88% (HIGH)

2. INFY
  💰 Price: ₹1,850.25
  📊 Volume: 2.1x
  📈 RSI: 62.1
  🎯 Pattern: Cup and Handle
  💪 Strength: 82% (HIGH)

... and 10 more stocks
==================================================
📊 Summary:
  • Total: 12
  • Current Day Breakouts: 5
  • Avg Strength: 78%
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'yfinance'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Telegram credentials not found"
**Solution:** Set environment variables
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Issue: "No stocks found matching criteria"
**Solution:** Adjust scan parameters
- Lower `pattern_strength_min` from 70 to 50
- Reduce `adx_min` from 20 to 15
- Lower `min_volume_ratio` from 1.0 to 0.8

### Issue: "Network timeout"
**Solution:** Retry or check internet connection
- Scanner uses yfinance API
- May timeout during market hours
- Run after market closes for best results

## Performance

- **Typical Scan Time:** 5-10 minutes
- **Stocks Processed:** 100+ per run
- **API Calls:** ~200-300 total
- **Telegram Message Size:** <4096 characters

## Next Steps

1. **Create Telegram Bot** - Follow steps above
2. **Set Environment Variables** - Save credentials
3. **Test Scanner** - Run `python run_scanner.py`
4. **Setup Automation** - Configure scheduled runs
5. **Monitor Results** - Check Telegram for daily updates

## Support

For questions or issues:
- Check the README.md file
- Review scanner code comments
- Verify Telegram credentials
- Check environment variables
- Test network connectivity

---

**Last Updated:** 2026-09-22
**Scanner Version:** 1.0
**Python:** 3.11+
