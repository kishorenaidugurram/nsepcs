# Automated NSE F&O PCS Scanner with Telegram Notifications

## Quick Start

This repository now includes automated scanning capabilities that can:
1. ✅ Analyze NSE F&O stocks for PCS opportunities
2. ✅ Send results directly to your Telegram
3. ✅ Run on a schedule (cron jobs)
4. ✅ Save results to CSV files

## What is PCS?

**Put Credit Spread (PCS)** is an options trading strategy. This scanner identifies stocks that meet optimal conditions for this strategy based on:
- Momentum indicators (RSI)
- Trend strength (ADX, MACD)
- Support levels (Moving averages, Bollinger Bands)
- Volume confirmation
- Volatility analysis

## Files in This Project

```
/home/user/nsepcs/
├── streamlit_app.py           # Main Streamlit web application
├── run_pcs_scan.py            # Standalone Python scanner
├── scan_and_notify.sh         # Shell wrapper with Telegram support
├── TELEGRAM_SETUP.md          # Detailed Telegram setup guide
├── AUTOMATED_SCANNING.md      # This file
└── requirements.txt           # Python dependencies
```

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd /home/user/nsepcs
pip install -r requirements.txt

# Or if you encounter build errors with the 'ta' package:
pip install streamlit yfinance pandas numpy plotly pytz beautifulsoup4 openpyxl scikit-learn scipy
```

### Step 2: Configure Telegram (Optional but Recommended)

Follow the detailed guide in `TELEGRAM_SETUP.md`:

```bash
# Quick version:
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'

# Or create a .env file:
cat > /home/user/nsepcs/.env << 'EOF'
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF
chmod 600 .env  # Secure the file
```

### Step 3: Run a Manual Scan

```bash
# Method 1: Using the shell wrapper (recommended)
cd /home/user/nsepcs
./scan_and_notify.sh

# Method 2: Direct Python execution
cd /home/user/nsepcs
python3 run_pcs_scan.py

# Method 3: With environment variables
export TELEGRAM_BOT_TOKEN='your_token'
export TELEGRAM_CHAT_ID='your_chat_id'
python3 run_pcs_scan.py
```

### Step 4: Set Up Automated Scanning (Cron)

```bash
# Edit your crontab
crontab -e

# Add one of these lines:

# Run every weekday at 9:30 AM (market opening)
30 9 * * 1-5 cd /home/user/nsepcs && source .env 2>/dev/null && ./scan_and_notify.sh >> /tmp/pcs_scan_cron.log 2>&1

# Run every weekday at 3:45 PM (market close)
45 15 * * 1-5 cd /home/user/nsepcs && source .env 2>/dev/null && ./scan_and_notify.sh >> /tmp/pcs_scan_cron.log 2>&1

# Run both times
30 9 * * 1-5 cd /home/user/nsepcs && source .env 2>/dev/null && ./scan_and_notify.sh >> /tmp/pcs_scan_cron.log 2>&1
45 15 * * 1-5 cd /home/user/nsepcs && source .env 2>/dev/null && ./scan_and_notify.sh >> /tmp/pcs_scan_cron.log 2>&1
```

**Note**: The script assumes Indian Standard Time (IST/UTC+5:30). Adjust times based on your server's timezone.

## Scanner Output

### Console Output
```
======================================================================
🚀 NSE F&O PCS SCANNER - AUTOMATED BATCH RUN
======================================================================
⏰ Started at: 2024-09-18 14:30:00 IST
📊 Analyzing 60 top liquid stocks

📈 Analyzing stocks (this may take 2-3 minutes)...

🟢 RELIANCE  | Score:  82.3% | RSI:  55.2 | ADX:  28.5
🟢 TCS       | Score:  78.9% | RSI:  52.1 | ADX:  26.3
🟡 INFY      | Score:  68.5% | RSI:  48.9 | ADX:  22.1
...
```

### CSV Output
Generated file: `/tmp/pcs_scan_20240918_143000.csv`

```csv
symbol,price,score,rsi,adx,confidence
RELIANCE,2850.50,82.3,55.2,28.5,HIGH
TCS,3850.25,78.9,52.1,26.3,HIGH
INFY,1500.00,68.5,48.9,22.1,MEDIUM
...
```

### Telegram Notification
```
🎯 NSE F&O PCS SCAN RESULTS
2024-09-18 14:45 IST

🟢 HIGH Confidence (5):
  • RELIANCE: 82.3%
  • TCS: 78.9%
  • HDFCBANK: 76.1%
  ... +2 more

🟡 MEDIUM Confidence (8):
  • INFY: 68.5%
  ... +7 more

Total: 13 stocks
CSV: pcs_scan.csv
```

## Understanding the Score

The PCS score (0-100%) is based on five weighted factors:

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| RSI | 30% | Momentum (ideal: 40-70) |
| Trend | 25% | ADX + MACD (is trend strengthening?) |
| Support | 20% | Distance from key support levels |
| Volume | 15% | Is volume confirming moves? |
| Volatility | 10% | Optimal for options (15-35% range) |

**Scoring:**
- 🟢 **HIGH Confidence**: Score 75+ (Conservative strikes, higher probability)
- 🟡 **MEDIUM Confidence**: Score 60-74 (Moderate strikes, balanced risk)
- 🔴 **LOW Confidence**: Score <60 (Aggressive strikes, higher risk)

## Stocks Analyzed

The scanner analyzes the **top 60 most liquid NSE F&O stocks**:

**Indices**: NIFTY, BANKNIFTY

**Large Caps**: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

**Financials**: KOTAKBANK, AXISBANK, BAJFINANCE, BAJAJFINSV, INDUSINDBK, SBICARD, SBILIFE

**Technology**: WIPRO, HCLTECH, TECHM, HEXAWARE

**Auto/Engineering**: MARUTI, TATAMOTORS, EICHERMOT, HEROMOTOCO, BHARATFORG

**Pharma**: SUNPHARMA, CIPLA, LUPIN, BIOCON, AUROPHARMA

**Consumer**: BRITANNIA, NESTLEIND, COLPAL, DMART, TITAN, DABUR

**Infrastructure/Energy**: POWERGRID, NTPC, ONGC, GAIL, COALINDIA, ULTRACEMCO

**Metals/Materials**: TATASTEEL, JSWSTEEL, HINDALCO, GRASIM, BPCL

**Other**: ASIANPAINT, BHARTIARTL, BOSCHLTD, BLUESTARCO, CONCOR, FEDERALBNK, PAGEIND, SIEMENS, MOTHERSON, MRF, PEL

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'pandas'`

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
# If that fails:
pip install pandas numpy yfinance ta plotly beautifulsoup4
```

### Issue: No message received on Telegram

**Solutions**:
1. Verify Telegram is configured:
   ```bash
   echo "Token: $TELEGRAM_BOT_TOKEN"
   echo "Chat ID: $TELEGRAM_CHAT_ID"
   ```

2. Test Telegram manually:
   ```bash
   python3 -c "
   import requests, os
   url = f\"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage\"
   requests.post(url, json={'chat_id': os.getenv('TELEGRAM_CHAT_ID'), 'text': 'Test message'})
   "
   ```

3. Check internet connectivity:
   ```bash
   curl -I https://api.telegram.org/
   ```

### Issue: Script times out or runs very slow

**Causes & Solutions**:
- Network issues: May take 2-3 minutes to fetch all stock data
- Slow server: Try running during off-peak hours
- Too many stocks: Reduce the list in `run_pcs_scan.py` if needed

### Issue: Cron job doesn't run

**Solutions**:
1. Verify cron service is running:
   ```bash
   systemctl status cron  # or: service cron status
   ```

2. Check cron logs:
   ```bash
   grep CRON /var/log/syslog  # or: journalctl -u cron
   ```

3. Verify .env file is readable:
   ```bash
   ls -la /home/user/nsepcs/.env
   chmod 600 /home/user/nsepcs/.env
   ```

4. Test the cron command manually:
   ```bash
   cd /home/user/nsepcs && source .env && ./scan_and_notify.sh
   ```

## Advanced Usage

### Custom Stock List

Edit `run_pcs_scan.py` and modify the `TOP_NSE_FO_STOCKS` variable:

```python
TOP_NSE_FO_STOCKS = [
    'RELIANCE', 'TCS', 'INFY',  # Your custom list
    # ... add more symbols
]
```

### Adjust Filter Thresholds

Modify the score thresholds in `run_pcs_scan.py`:

```python
def analyze_stock(symbol):
    score = calculate_pcs_score(data)
    if score < 50:  # Change this threshold
        return None
```

### Change Analysis Period

In `run_pcs_scan.py`, modify the `days` parameter:

```python
data = fetch_stock_data(symbol, days=90)  # Change 90 to 30, 180, etc.
```

## API Rate Limits

- **Yahoo Finance**: Generally 2000 requests/hour per IP
- **Telegram**: 30 messages/second
- **This scanner**: Uses ~60 API calls per run, runs safely within limits

## Performance

- **Analysis time**: 2-3 minutes for 60 stocks
- **Data cache**: Results are fetched fresh each run
- **Network**: Requires stable internet connection

## Disclaimer

⚠️ **This scanner is for informational purposes only.**

- **NOT Financial Advice**: This is an educational tool, not investment advice
- **Risk Involved**: Options trading carries substantial risk of loss
- **Paper Trade First**: Test your strategy with virtual money before live trading
- **Verify Results**: Always independently verify signals before trading
- **Risk Management**: Use proper position sizing and stop losses

See the main README.md for complete disclaimers.

## Support & Feedback

If you encounter issues:

1. Check `TELEGRAM_SETUP.md` for Telegram-specific help
2. Review error logs: `tail -100 /tmp/pcs_scan_cron.log`
3. Test manually: `python3 run_pcs_scan.py`
4. Check GitHub issues or create a new one

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Set up Telegram (follow `TELEGRAM_SETUP.md`)
3. ✅ Run a manual scan: `./scan_and_notify.sh`
4. ✅ Set up cron for automation
5. ✅ Monitor results and adjust as needed

---

**Last Updated**: 2024-09-18
**Maintained for**: Python 3.8+
**Compatible with**: NSE F&O stocks (Indian equities)
