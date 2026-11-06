# NSE F&O Stock Scanner - Setup Guide

## Overview

The `simple_scanner.py` script scans 45 major NSE F&O stocks for bullish trading setups and sends results via Telegram.

## Features

- **Automated Scanning**: Scans 45 liquid NSE F&O stocks
- **Technical Analysis**: Calculates RSI, SMA (20/50), MACD, and Bollinger Bands
- **Bullish Detection**: Identifies stocks with:
  - Price above SMA20 and SMA50 (uptrend)
  - RSI in bullish zone (40-80)
  - Above-average trading volume
  - Recent uptrend (last 5 days)
  - Price near support levels
- **Scoring System**: Stocks scored 0-100 based on multiple criteria
- **Telegram Notifications**: Sends results directly to your Telegram

## Prerequisites

1. **Python 3.11+**
2. **Required Packages**:
   ```bash
   pip install yfinance pandas numpy requests pytz
   ```

3. **Telegram Bot Setup** (Optional but recommended):
   - Create a bot via @BotFather on Telegram: https://telegram.me/botfather
   - Get your chat ID (message @userinfobot and note your user ID)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install yfinance pandas numpy requests pytz
```

### 2. Configure Telegram (Optional)

Create a `.env` file or set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
export TELEGRAM_CHAT_ID="your_telegram_user_id"
```

Or create `.env` file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run the Scanner

**One-time run:**
```bash
python3 simple_scanner.py
```

**Scheduled runs (using cron):**
```bash
# Edit crontab
crontab -e

# Add this line to run at 9:30 AM IST daily:
30 9 * * * cd /home/user/nsepcs && python3 simple_scanner.py

# Or run at market open (9:15 AM) for intraday:
15 9 * * 1-5 cd /home/user/nsepcs && python3 simple_scanner.py
```

## Scanner Logic

### Scoring Criteria

Each stock is scored based on:

| Criteria | Points | Condition |
|----------|--------|-----------|
| Uptrend Strength | 25 | Price > SMA20 > SMA50 |
| Weak Uptrend | 15 | Price > SMA20 |
| RSI Bullish | 15 | RSI between 40-80 |
| RSI Overbought | 5 | RSI > 70 |
| High Volume | 15 | Volume > 1.2x average |
| Normal Volume | 5 | Volume > 1.0x average |
| Recent Uptrend | 20 | 3+ up days in last 5 days |
| Support Level | 10 | Price within 15% above 50-day low |

**Minimum Score for Selection: 40+**
**Minimum Signals Required: 3+**

### Technical Indicators

1. **RSI (14 periods)**
   - Bullish: 40-70 (momentum without overbought)
   - Overbought: 70-100

2. **Moving Averages**
   - SMA 20: Short-term trend
   - SMA 50: Medium-term trend
   - Signal: Price above both = strong uptrend

3. **Volume Analysis**
   - Compares current volume vs 20-day average
   - Signals confirmation of price movements

4. **Support Detection**
   - 50-day low as support level
   - 0-15% above low = near support

## Output Format

### Telegram Message
```
📊 NSE F&O Scan Results
⏰ 06-Nov-2026 09:17:51

✅ Found 5 stocks with bullish setups!

📈 Top Picks:

1. RELIANCE
   💰 Price: ₹2,850.50 | Score: 85/100
   📊 RSI: 65.2 | Vol Ratio: 1.35x
   ✅ Price > SMA20 > SMA50 (Strong Uptrend)
   ✅ RSI 65.2 (Bullish Zone)
   ✅ Volume 1.35x (Above Average)
```

### Console Output
- Real-time scanning progress
- Stock score and status for each symbol
- Summary table if Telegram not configured

## Stocks Scanned (45 F&O Instruments)

**Tier 1 - Largest Cap:**
- RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN

**Banking Sector:**
- KOTAKBANK, AXISBANK, CANBK, BANKBARODA

**IT Sector:**
- HCLTECH, WIPRO, COFORGE

**Auto Sector:**
- MARUTI, BAJAJ-AUTO, EICHERMOT

**FMCG & Pharma:**
- ITC, ASIANPAINT, DRREDDY, CIPLA, SUNPHARMA, BRITANNIA, COLPAL

**Metals & Energy:**
- TATASTEEL, HINDALCO, JSWSTEEL, COALINDIA, GAIL, BPCL, IOC

**Infrastructure & Logistics:**
- LT, ADANIPORTS, ADANIGREEN, CONCOR, GMRAIRPORT, IRCTC

**Financial Services:**
- BAJFINANCE, CDSL, HDFCLIFE, ICICIPRULI

**Healthcare:**
- APOLLOHOSP, BIOCON, FORTIS

**Others:**
- HDFC, NTPC, HAL, HUDCO

## Troubleshooting

### Issue: "No stocks meeting criteria found"
**Solution:**
- Market conditions may not support bullish setups
- Adjust scoring thresholds in the code
- Run during/after market open for most accurate data
- Check internet connectivity for yfinance

### Issue: "Failed to get ticker" errors
**Solution:**
- Network/proxy issue blocking Yahoo Finance
- Try again after 5-10 minutes
- Check proxy settings: `/root/.ccr/README.md`

### Issue: Telegram message not sent
**Solution:**
- Verify bot token: `curl -s "https://api.telegram.org/bot<TOKEN>/getMe"`
- Verify chat ID is correct
- Check bot has access to the chat (send it a message first)
- Firewall/proxy may be blocking Telegram API

### Issue: "pandas not found"
**Solution:**
```bash
python3 -m pip install --upgrade pandas yfinance numpy
```

## Future Enhancements

- [ ] NSE direct API integration (better reliability than yfinance)
- [ ] Multiple filter profiles (aggressive, moderate, conservative)
- [ ] Historical performance tracking
- [ ] Delivery volume percentage analysis
- [ ] Options chain analysis
- [ ] Support/Resistance level detection
- [ ] Discord/Slack integration
- [ ] Database storage of results

## Performance Notes

- Scanning 45 stocks typically takes 3-5 minutes
- Uses concurrent processing (3 workers by default)
- Data cached for 5 minutes to reduce API calls
- Best run after market hours (9:15-15:30 IST)

## Legal Disclaimer

This scanner is for educational and informational purposes only. It does not provide financial or investment advice. Always do your own research and consult with a qualified financial advisor before making trading decisions.

## Support

For issues or suggestions:
1. Check the README.md for general project info
2. Review error messages in the console output
3. Ensure all dependencies are properly installed
4. Verify network connectivity and API access

---

**Last Updated:** November 2026
**Version:** 1.0
