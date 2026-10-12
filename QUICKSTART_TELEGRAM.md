# NSE PCS Scanner - Telegram Setup Guide

## Quick Start

### 1️⃣ Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Choose a name (e.g., "NSE PCS Scanner")
4. Copy the **API Token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvwxyz`)

### 2️⃣ Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Send any message
3. Copy your **Chat ID** (a number like: `987654321`)

### 3️⃣ Configure Environment Variables

```bash
export TELEGRAM_BOT_TOKEN='your_api_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

### 4️⃣ Run the Scanner

```bash
# Option A: Send demo results to Telegram
python send_demo_results.py

# Option B: Run live analysis (requires working market data connection)
python run_analysis.py

# Option C: Use the simple scanner
python scanner_telegram.py
```

## What You'll Get

The Telegram message will contain:

```
🚀 NSE PCS Scanner Results
2026-10-12 09:17 IST

📊 Found 10 stocks with bullish patterns

1. RELIANCE
   Price: ₹3015.5 | RSI: 42.5
   Pattern: Cup with Handle (82/100)

2. TCS
   Price: ₹4250.25 | RSI: 45.2
   Pattern: Flat Base Breakout (78/100)

[... more stocks ...]
```

## Files Included

| File | Purpose |
|------|---------|
| `send_demo_results.py` | Demo - shows sample results format |
| `run_analysis.py` | Full analysis using streamlit logic |
| `scanner_telegram.py` | Simple scanner with pattern detection |
| `TELEGRAM_SETUP.md` | Detailed setup documentation |
| `QUICKSTART_TELEGRAM.md` | This quick reference |

## Filter Criteria Applied

The scanner filters stocks using:

- **RSI Range:** 30-75 (optimal momentum zone)
- **ADX Minimum:** 20 (strong trend requirement)
- **Volume Ratio:** 1.2x average (sufficient liquidity)
- **Pattern Strength:** 65/100 minimum (quality patterns)
- **Lookback Period:** 20 days
- **Stocks Analyzed:** 34-219 NSE F&O stocks

## Pattern Types Detected

The scanner identifies:
- ✓ Current Day Breakout
- ✓ Cup with Handle  
- ✓ Flat Base
- ✓ Bump and Run
- ✓ Rectangle Bottom
- ✓ Head-and-Shoulders Bottom
- ✓ Double Bottom
- ✓ Three Rising Valleys
- ✓ Rounding Bottom
- ✓ Inverted Scallop
- ✓ Multi-timeframe confirmation (Daily + Weekly)

## Scheduling Daily Runs

To run the scanner automatically every trading day at 9:30 AM:

```bash
# Add to crontab
0 9 * * 1-5 cd /home/user/nsepcs && python send_demo_results.py
```

## Troubleshooting

### Message Not Sending?

1. **Check Bot Token:**
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   ```

2. **Check Chat ID:**
   ```bash
   echo $TELEGRAM_CHAT_ID
   ```

3. **Test Connection:**
   ```bash
   python send_demo_results.py
   ```

### Data Not Fetching?

Current status: **Network connectivity issue** with Yahoo Finance

**Temporary Solution:** Use `send_demo_results.py` to see message format

**Permanent Solution:** 
- Configure proxy for yfinance
- Use alternative data source (NSE API)
- Run in environment with open internet

## Support

**For questions or issues:**
- Check the terminal output messages
- Verify environment variables are set
- Review the TELEGRAM_SETUP.md file
- Check /home/user/nsepcs/pcs_results.csv for detailed results

## Next Steps

1. Create Telegram bot (see Step 1 above)
2. Get Chat ID (see Step 2 above)
3. Set environment variables (see Step 3 above)
4. Test: `python send_demo_results.py`
5. Resolve network connectivity for live data
6. Schedule daily automated runs

---

**Created:** 2026-10-12  
**Version:** 1.0  
**Status:** Demo ready, live data requires network fix
