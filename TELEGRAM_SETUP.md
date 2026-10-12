# NSE PCS Scanner - Automated Analysis Setup

## Status: ⚠️ Network Connectivity Issue

### What Was Done
I've created a complete automated stock analysis system with Telegram integration for your NSE PCS scanner. Here's what's been set up:

### Files Created

1. **run_scanner_final.py** - Main analysis script
   - Analyzes 34 top NSE F&O liquid stocks
   - Calculates RSI, volume ratios, and support/resistance levels
   - Detects bullish support zone patterns
   - Filters stocks meeting criteria
   - Sends results to Telegram
   - Saves results to CSV

2. **simple_analysis.py** - Alternate simple version
   - Lightweight analysis engine
   - Same filtering logic
   - Telegram notification support

3. **run_analysis_and_notify.py** - Advanced version with full scanner integration
   - Uses the complete streamlit_app logic
   - Implements all technical indicators
   - Pattern detection (12+ chart patterns)
   - Delivery volume analysis
   - Multi-timeframe analysis (daily + weekly)

### Current Issue: Network Connectivity

**Error:** `CONNECT tunnel failed, response 403`

The remote environment's proxy is blocking HTTPS connections to Yahoo Finance's data servers. This is needed to fetch stock price data.

**Error Details:**
- yfinance cannot establish HTTPS tunnel through proxy
- Cookie/crumb fetch from fc.yahoo.com fails
- Response 403 (Forbidden) from proxy

### How to Fix

**Option 1: Configure Proxy for yfinance**
```bash
export HTTPS_PROXY=http://127.0.0.1:46577
export HTTP_PROXY=http://127.0.0.1:46577
python run_scanner_final.py
```

**Option 2: Use Alternative Data Source**
Modify the script to use:
- NSE API (direct Indian source)
- Yahoo Finance alternative APIs
- Cached/historical data

**Option 3: Run in Different Environment**
Execute on your local machine or cloud environment with open network access.

### Filter Criteria Configured

The scanner uses these default filters (as per your Streamlit UI defaults):

**Technical Indicators:**
- RSI Range: 30-75
- ADX Minimum: 20
- Moving Average: EMA with 3% tolerance
- Volume Ratio: 1.2x minimum
- Lookback Period: 20 days
- Pattern Strength: 65+ (0-100 scale)

**Stocks Scanned (34 NSE F&O Stocks):**
- NIFTY, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK
- SBIN, LT, ITC, KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI
- ASIANPAINT, BHARTIARTL, SUNPHARMA, TATAMOTORS, ADANIENT
- BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN, NESTLEIND
- ULTRACEMCO, POWERGRID, NTPC, ONGC, COALINDIA, JSWSTEEL, TATASTEEL, HINDALCO

**Enhancement Features Enabled:**
- Delivery Volume Analysis
- F&O Consolidation Detection  
- Breakout-Pullback Patterns
- Enhanced Support & Resistance

### Telegram Integration

**What it does:**
- Sends filtered stock list to your Telegram
- Includes: Symbol, Price, RSI, Volume Ratio, Pattern Strength
- Formatted message with top 12 stocks
- HTML formatting for better readability
- Timestamp in IST

**Setup Required:**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then run:
```bash
python run_scanner_final.py
```

### Expected Output

When network is available, the script will:
```
NSE PCS Scanner Results
2026-10-12 04:00 IST

📊 Found X stocks with bullish patterns

1. RELIANCE
   Price: ₹3000.50 | RSI: 45.0
   Pattern: Bullish Support Zone (75/100)
   Support: ₹2950.00 | Resistance: ₹3100.00

2. TCS
   ...

✓ Results saved to: pcs_results.csv
✓ Message sent to Telegram successfully
```

### Next Steps

1. **Resolve Network Issue:**
   - Check proxy configuration
   - Verify HTTPS_PROXY environment variables
   - Test: `curl -v https://query1.finance.yahoo.com/`

2. **Set Telegram Credentials:**
   - Create Telegram bot: @BotFather
   - Get your chat ID
   - Set environment variables

3. **Schedule Automated Runs:**
   - Use cron for daily analysis
   - Example: `0 9 * * 1-5 python /path/to/run_scanner_final.py`

4. **Monitor Results:**
   - Check CSV file: `pcs_results.csv`
   - Verify Telegram messages
   - Adjust filters as needed

### Technical Architecture

**Data Flow:**
```
yfinance → Yahoo Finance API → Stock Data
     ↓
Python Analysis Engine
     ↓
RSI, Volume, Support/Resistance Calculations
     ↓
Pattern Detection & Filtering
     ↓
Results Formatting → Telegram Bot API
                  → CSV Export
```

**Dependencies Installed:**
- yfinance 0.2.18+ (stock data)
- pandas 2.0.0+ (data manipulation)
- numpy 1.24.0+ (numerical computing)
- requests (HTTP calls)
- pytz (timezone handling)

### Backup Solution: Synthetic Data

If network remains unavailable, I can create a fallback version that:
- Uses historical cached data
- Generates synthetic market-realistic data
- Maintains same analysis logic
- Still sends Telegram notifications

### Support

**For questions:**
- Check the script comments
- Review filter criteria in create_professional_sidebar()
- Verify Telegram bot setup

**Script locations:**
- `/tmp/.../scratchpad/run_scanner_final.py` - Primary
- `/tmp/.../scratchpad/simple_analysis.py` - Alternative
- `/tmp/.../scratchpad/run_analysis_and_notify.py` - Advanced

---

**Created:** 2026-10-12 04:00 IST  
**Status:** Ready (pending network fix)  
**Last Action:** Automated scheduled task
