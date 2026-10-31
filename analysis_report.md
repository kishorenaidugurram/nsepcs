# NSE F&O PCS Analysis Report
**Generated:** 2026-10-31  
**Status:** ⚠️ Needs Configuration

## System Status

### ✅ What's Working
- Code repository is ready
- All dependencies installed (Python 3.13)
- Analysis framework loaded
- 208 NSE F&O stocks configured for screening
- Technical analysis components available:
  - RSI (Relative Strength Index)
  - Moving Averages (SMA, EMA)
  - MACD indicators
  - ADX (Average Directional Index)
  - Bollinger Bands
  - Volume analysis
  - Pattern detection (11+ chart patterns)

### ❌ What Needs Configuration

#### 1. Network Access
- **Issue:** Cannot reach Yahoo Finance for live stock data
- **Impact:** Cannot fetch current market data
- **Solution:** Configure proxy settings or use alternative data source

#### 2. Telegram Credentials
- **Missing:** TELEGRAM_BOT_TOKEN environment variable
- **Missing:** TELEGRAM_CHAT_ID environment variable
- **Impact:** Cannot send results to Telegram
- **Solution:** Set environment variables:
  ```bash
  export TELEGRAM_BOT_TOKEN='your_bot_token_here'
  export TELEGRAM_CHAT_ID='your_chat_id_here'
  ```

## Configuration Steps

### Step 1: Set Telegram Credentials
Create a Telegram bot and get your chat ID, then set:
```bash
export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
export TELEGRAM_CHAT_ID='YOUR_CHAT_ID'
```

### Step 2: Verify Network Access
The system needs outbound HTTPS access to:
- `api.yfinance.com` (market data)
- `api.telegram.org` (Telegram API)

### Step 3: Run the Analysis
Once configured:
```bash
cd /home/user/nsepcs
python3.13 run_analysis.py
```

## Next Steps

1. **Configure Telegram Bot**
   - Create bot via @BotFather on Telegram
   - Get your chat ID
   - Set environment variables

2. **Verify Network Policy**
   - Check if remote execution environment allows outbound HTTPS
   - Configure proxy if needed (see: /root/.ccr/README.md)

3. **Schedule Automated Analysis**
   - Once working, can be scheduled via cron or task scheduler
   - Results will be sent directly to Telegram

## Analysis Parameters

Default filter criteria:
- **RSI Range:** 30-75 (Bullish momentum zone)
- **ADX Minimum:** 20 (Trend strength)
- **Min Volume Ratio:** 1.2x average
- **Chart Patterns:** 11 advanced patterns detected
- **Time Frame:** Daily analysis

## Stocks to be Scanned

208 NSE F&O stocks including:
- **Tier 1 (Ultra liquid):** NIFTY, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY
- **Tier 2 (High liquid):** KOTAKBANK, AXISBANK, MARUTI, ASIANPAINT
- **Tier 3 (Medium liquid):** BAJFINANCE, TITAN, ULTRACEMCO, NTPC, ONGC, JSWSTEEL

