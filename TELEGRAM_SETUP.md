# NSE Stock Screener - Telegram Integration Guide

This guide explains how to set up and use the automated stock screener with Telegram notifications.

## 📋 Overview

The NSE Stock Screener analyzes NSE F&O stocks for technical setups and sends qualified results directly to your Telegram chat. The system identifies:

- **🔥 Current Day Breakouts** - Stocks breaking above 20-day resistance with volume confirmation
- **📈 Bullish Setups** - Stocks with strong technical patterns and momentum
- **💪 High Confidence Trades** - Stocks scoring 70%+ based on RSI, ADX, volume, and trend analysis

## 🚀 Quick Start

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/start` and follow the instructions
3. Send `/newbot` and answer the questions:
   - Bot name: e.g., "NSE Stock Screener"
   - Bot username: e.g., "nse_screener_bot" (must end with `_bot`)
4. Copy your **Bot Token** (looks like: `123456789:ABCDefghIJKlmnOPQrstuVwxYZ`)

### Step 2: Get Your Chat ID

1. Start a chat with your newly created bot
2. Search for **@userinfobot** on Telegram
3. Send any message to it
4. It will reply with your **Chat ID** (a number like: `9876543210`)

### Step 3: Configure Environment Variables

Set these environment variables before running the screener:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

Or add them to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# Add to ~/.bashrc or ~/.zshrc
export TELEGRAM_BOT_TOKEN='123456789:ABCDefghIJKlmnOPQrstuVwxYZ'
export TELEGRAM_CHAT_ID='9876543210'
```

### Step 4: Run the Screener

#### Option A: Demo Mode (with sample data)
```bash
python3 analyze_with_demo_data.py
```

#### Option B: Live Analysis (requires network access to Yahoo Finance)
```bash
python3 analyze_simple.py
```

#### Option C: Full Streamlit App (interactive web interface)
```bash
streamlit run streamlit_app.py
```

## 📊 What the Screener Analyzes

### Technical Indicators

The screener uses the following technical analysis:

- **RSI (Relative Strength Index)** - Momentum measurement (0-100)
  - Optimal range: 40-70 for bullish trades
  - < 30: Oversold
  - > 70: Overbought

- **ADX (Average Directional Index)** - Trend strength (0-100)
  - < 20: Weak trend
  - 20-25: Moderate trend
  - > 25: Strong trend

- **Moving Averages** - Trend direction
  - SMA 20: Short-term trend
  - SMA 50: Intermediate trend
  - Price > SMA20 > SMA50: Bullish alignment

- **Volume Analysis** - Participation confirmation
  - Current volume > 1.5x average: Good participation
  - Current volume > 2x average: Strong participation

### Breakout Detection

The screener identifies **Current Day Breakouts** when:

1. **Price Breakout**: Close > 20-day resistance (0.5% above)
2. **High Breakout**: Intraday high > 20-day resistance (1% above)
3. **Volume Confirmation**: Current volume > 2x average
4. **Consolidation**: 20-day range < 15% (tight consolidation)
5. **Strength Calculation**:
   - Breakout % >= 3%: +35 points
   - Breakout % >= 2%: +25 points
   - Breakout % >= 1%: +20 points
   - Volume 4x+: +30 points
   - Volume 3x+: +25 points
   - Volume 2x+: +20 points
   - Tight consolidation: +25 points

### Scoring

Each stock receives a **Strength Score** (0-100) based on:

- **Breakout Pattern** (if detected): Up to 65 points
- **Bullish Momentum**: Up to 40 points
  - RSI 40-70: +15 points
  - Price above SMA20: +30 points
- **Trend Strength**: Up to 30 points
  - ADX 20-25: +10 points
  - ADX >= 25: +15 points
- **Volume Confirmation**: Up to 15 points
- **Support Distance**: Up to 10 points

**Stocks are qualified if Strength Score >= 50**

## 📱 Telegram Message Format

The bot sends messages like this:

```
🎯 NSE Stock Screener Results
2026-08-19 09:13 IST

📊 Summary:
• Total qualified: 10
• 🔥 Current Day Breakouts: 5
• 📈 Other Setups: 5

🔥 CURRENT DAY BREAKOUTS (Highest Priority):
1. RELIANCE ₹3,045.50 | 💪 92% | RSI: 62 | Vol: 2.8x
2. INFY ₹4,278.65 | 💪 88% | RSI: 61 | Vol: 2.5x
3. MARUTI ₹10,845.75 | 💪 86% | RSI: 60 | Vol: 2.4x
4. HDFCBANK ₹2,180.75 | 💪 85% | RSI: 58 | Vol: 2.3x
5. KOTAKBANK ₹1,965.40 | 💪 84% | RSI: 59 | Vol: 2.2x

📈 OTHER QUALIFIED STOCKS:
1. TCS ₹3,685.40 | 💪 81% | RSI: 57 | Vol: 2.1x 📈
2. ASIANPAINT ₹3,245.80 | 💪 79% | RSI: 56 | Vol: 2.0x 📈

📋 Quick Stock List:
RELIANCE, INFY, MARUTI, HDFCBANK, KOTAKBANK, TCS, ...

Scan completed successfully ✓
```

## ⏰ Setting Up Automated Scans

### Option 1: Linux Cron Job

Edit your crontab:
```bash
crontab -e
```

Add a line to run the screener daily at 3:30 PM IST (9:00 AM UTC):
```bash
30 15 * * 1-5 cd /home/user/nsepcs && /usr/bin/python3 analyze_simple.py >> /tmp/screener.log 2>&1
```

### Option 2: GitHub Actions (Cloud)

Create `.github/workflows/daily-scan.yml`:

```yaml
name: Daily NSE Scan

on:
  schedule:
    - cron: '00 9 * * 1-5'  # 2:30 PM IST (9:00 AM UTC) on weekdays

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -q pandas numpy yfinance requests
      
      - name: Run screener
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python3 analyze_simple.py
```

### Option 3: Scheduled Task (This Session)

If running in this cloud environment, the task is already set up to run this script on a schedule.

## 🛠️ Configuration

### Modify Stock List

Edit `analyze_simple.py` or `analyze_with_demo_data.py` to customize which stocks are analyzed:

```python
stocks_to_analyze = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    # Add or remove stock symbols
]
```

### Adjust Sensitivity

Modify these parameters in the scripts:

```python
# Minimum volume requirement
if current_volume < avg_volume * 1.5:  # Change 1.5 to adjust
    return None

# Strength score threshold
if strength < 50:  # Change 50 to adjust (0-100)
    return None

# RSI range filter
if current_rsi < 20 or current_rsi > 90:  # Adjust ranges
    return None

# ADX minimum
if current_adx < 15:  # Change 15 to adjust
    return None
```

## 🔐 Security Notes

1. **Never share your Bot Token or Chat ID** publicly
2. Use environment variables instead of hardcoding credentials
3. In GitHub Actions, store credentials as **Secrets** (Settings → Secrets)
4. For production use, consider rotating your bot token periodically

## 🐛 Troubleshooting

### "Telegram credentials not configured"
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Check: `echo $TELEGRAM_BOT_TOKEN`

### "Telegram send failed: 403"
- Verify your Bot Token is correct
- Make sure @BotFather created the bot
- Confirm you've started a chat with the bot

### "Telegram send failed: 400"
- Chat ID might be incorrect
- Verify Chat ID is a number (no special characters)

### "No stocks found" (demo mode works, live mode doesn't)
- Network might be blocked or Yahoo Finance is down
- Use demo mode to test configuration
- Check internet connection: `curl https://finance.yahoo.com`

## 📚 Stock Universe

The screener analyzes **50+ of the most liquid NSE F&O stocks**, including:

### Large Caps (Nifty 50)
RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, BHARTIARTL, ITC, SBIN, LT, KOTAKBANK, AXISBANK, MARUTI, ASIANPAINT, WIPRO, ONGC, NTPC, POWERGRID, TECHM, ULTRACEMCO, SUNPHARMA, TITAN, COALINDIA, BAJFINANCE, HCLTECH, JSWSTEEL

### Financial Sector
INDUSINDBK, BRITANNIA, CIPLA, DRREDDY, IDFCFIRSTB, AUBANK, CANBK, FEDERALBNK, PNB

### Industrial & Commodities
ADANIENT, GRASIM, HEROMOTOCO, HINDALCO, TATASTEEL, BPCL, M&M, BAJAJ-AUTO, SHRIRAMFIN, ADANIPORTS

## 📝 Example Workflow

1. **Morning Setup** (9:30 AM IST market open)
   ```bash
   export TELEGRAM_BOT_TOKEN='your_token'
   export TELEGRAM_CHAT_ID='your_chat_id'
   python3 analyze_simple.py
   ```

2. **Receive Telegram Notification** with qualifying stocks

3. **Review Results**:
   - Check 🔥 Current Day Breakouts first (highest priority)
   - Look at RSI and Volume for confirmation
   - Note support/resistance levels from ADX

4. **Take Action**:
   - Research the stocks further
   - Set up appropriate put credit spread positions
   - Use the strength score to gauge risk

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section
2. Verify your Telegram bot token is valid
3. Ensure environment variables are set correctly
4. Test demo mode first: `python3 analyze_with_demo_data.py`

## ⚠️ Disclaimer

This tool is for **educational and analytical purposes only**. It does not provide financial advice. Always:

- Do your own research before trading
- Use proper risk management
- Never risk more than you can afford to lose
- Paper trade first to test strategies
- Consult with financial advisors when needed

---

**Happy Trading!** 📈🚀
