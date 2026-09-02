# NSE Stock Scanner - Telegram Integration Setup

This guide explains how to set up the automated NSE stock scanner to send results to your Telegram.

## Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Click `/start` and then `/newbot`
3. Enter a name for your bot (e.g., "NSE Stock Scanner")
4. Enter a username for your bot (must be unique, e.g., "nse_scanner_bot")
5. Copy the **BOT TOKEN** (looks like: `123456789:ABCDefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Click `/start`
3. You'll see your **User ID** (looks like: `123456789`)
4. This is your **CHAT ID**

Alternative: Create a Telegram group and add the bot to get a group chat ID.

### 3. Set Environment Variables

Set these environment variables on your system:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

For Ubuntu/Linux (add to ~/.bashrc):
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Test the Integration

Run the test script to verify your setup:

```bash
python3 test_scanner.py
```

You should receive test messages in Telegram with sample stock scan results.

## Running the Scanner

### Option 1: Standalone Scanner (Simplified)

The `run_scanner_standalone.py` script runs a simplified analysis on the top 45 liquid stocks:

```bash
python3 run_scanner_standalone.py
```

**Features:**
- Analyzes Nifty 50 + liquid F&O stocks
- Uses RSI, MACD, SMA, Volume filters
- Sends results to Telegram
- Requires: Python 3, pandas, numpy, yfinance, requests

**Filters Applied:**
- RSI: 30-80 (not oversold/overbought)
- Price > SMA20 (above short-term MA)
- MACD Bullish (MACD > Signal line)
- Volume Today > Average Volume
- Recent Uptrend (5-day close > 10-day close)

### Option 2: Full Professional Scanner

The `run_scanner.py` uses the complete analysis from `streamlit_app.py`:

```bash
python3 run_scanner.py
```

**Features:**
- Advanced pattern recognition (20+ patterns)
- Weekly validation support
- News analysis
- Excel export with detailed results
- Requires: All dependencies in requirements.txt

## Scheduling Regular Scans

### Using Cron (Linux/Mac)

Edit your crontab:
```bash
crontab -e
```

Add one of these entries:

**Daily scan at 9:30 AM IST (market open):**
```
30 9 * * 1-5 TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 /path/to/run_scanner_standalone.py >> /tmp/scanner.log 2>&1
```

**Every 30 minutes during market hours (9:30 AM - 3:30 PM IST):**
```
*/30 9-15 * * 1-5 TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_id" python3 /path/to/run_scanner_standalone.py >> /tmp/scanner.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open **Task Scheduler**
2. Create a **New Task**
3. Set trigger to desired time
4. Set action to run Python script with environment variables
5. Add to startup batch file:

```batch
setx TELEGRAM_BOT_TOKEN "your_token"
setx TELEGRAM_CHAT_ID "your_id"
python3 C:\path\to\run_scanner_standalone.py
```

## Configuration

Edit `scanner_config.json` to customize filters:

```json
{
  "scanner": {
    "rsi_min": 30,          // Minimum RSI
    "rsi_max": 80,          // Maximum RSI
    "adx_min": 15,          // Minimum ADX (trend strength)
    "pattern_strength_min": 70,  // Minimum pattern strength %
    "volume_ratio": 1.5,    // Volume must be >1.5x average
    "volume_breakout_ratio": 2.0,  // Breakout needs 2x volume
    "lookback_days": 20,    // Days for pattern detection
    "max_stocks": 50,       // Max stocks to scan
    "ma_support": true,     // Check price above MA
    "ma_type": "SMA",       // SMA or EMA
    "ma_tolerance": 3       // % tolerance for MA check
  }
}
```

## Understanding the Results

### Score Breakdown

The scanner assigns each stock a score based on filter compliance:

- **85%+**: HIGH Confidence - Strong signals
- **70-84%**: MEDIUM Confidence - Moderate signals  
- **<70%**: LOW Confidence - Weak signals

### Telegram Message Format

```
🎯 NSE Stock Scan Results
━━━━━━━━━━━━━━━━━━━━━━
1. RELIANCE
   💰 ₹2850 | RSI: 65 | ✓5/5
   ⭐⭐⭐⭐ Score: 85%

2. TCS
   💰 ₹3650 | RSI: 62 | ✓4/5
   ⭐⭐⭐ Score: 78%
```

## Troubleshooting

### "Failed to send message" Error

1. Check your BOT TOKEN is correct: `python3 -c "print('TOKEN_OK')"` if set
2. Verify CHAT ID is a valid number
3. Test the API: 
   ```bash
   curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
   ```

### No Results Found

This is normal! The scanner is strict with filters. Try:
- Lowering `pattern_strength_min` to 50-60
- Reducing `volume_ratio` to 1.0
- Checking market hours (9:15 AM - 3:30 PM IST)
- Checking if markets traded that day

### Network/Connection Errors

In some environments (corporate proxy, cloud containers):
- Yahoo Finance may be blocked
- Telegram API may be blocked
- Use a VPN or proxy bypass if available

## Risk Disclaimer

⚠️ **IMPORTANT:**
- This scanner is for **educational purposes only**
- It is **NOT financial advice**
- Always do your own research before trading
- Past performance does NOT guarantee future results
- Start with **paper trading** before live trades
- Never risk more than you can afford to lose
- Consult a qualified financial advisor

## Example Workflow

1. **Set up credentials** (BotFather, @userinfobot)
2. **Export environment variables**
3. **Test with** `python3 test_scanner.py`
4. **Run scanner** `python3 run_scanner_standalone.py`
5. **Schedule with cron/Task Scheduler**
6. **Monitor results** in Telegram daily
7. **Use for research** - verify patterns yourself before trading

## Support

For issues with:
- **Telegram Bot**: See [Telegram Bot API docs](https://core.telegram.org/bots/api)
- **Scanner Logic**: Check the detailed comments in `run_scanner_standalone.py`
- **Stock Data**: Verify Yahoo Finance connectivity

---

**Happy Trading! 📈**

Remember: Data-driven analysis + Risk Management = Sustainable returns
