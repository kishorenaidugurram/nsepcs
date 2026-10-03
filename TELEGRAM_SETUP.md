# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview

The scanner now includes automated Telegram integration to send PCS (Put Credit Spread) scanning results directly to your Telegram chat. The scanner analyzes NSE F&O stocks for high-probability Put Credit Spread opportunities.

## Quick Start

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send: `/newbot`
3. Follow the prompts to create a new bot
4. BotFather will provide you with a **Bot Token** - save this securely
5. Example token format: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`

### 2. Get Your Chat ID

1. Open Telegram and search for `@userinfobot`
2. Send `/start` to get your user ID
3. Save your **Chat ID** (this is your user ID number)

### 3. Configure Environment Variables

Set these environment variables before running the scanner:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or add them to your `.bashrc` or `.zshrc` for permanent setup:

```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id"' >> ~/.bashrc
source ~/.bashrc
```

## Running the Scanner

### Method 1: Simple Demo (Recommended for First Test)

```bash
cd /home/user/nsepcs
python3 run_scanner.py
```

This runs a demo scan with sample data to test the setup without network delays.

### Method 2: Full Live Scanner

```bash
cd /home/user/nsepcs
python3 telegram_scanner.py
```

This runs the complete scanner with live market data from Yahoo Finance.

### Method 3: With Virtual Environment (Recommended)

```bash
source /tmp/nse_scanner_env/bin/activate
cd /home/user/nsepcs
python3 run_scanner.py
deactivate
```

## Output

The scanner generates results in two formats:

### CSV Output
- File: `/tmp/claude-0/-home-user-nsepcs/1afda74d-5275-5193-93af-823cf3d99f2c/scratchpad/scan_results.csv`
- Format: Stock symbol, price, pattern strength, RSI, ADX, volume ratio, pattern type, confidence level, PCS suitability

### JSON Output  
- File: `/tmp/claude-0/-home-user-nsepcs/1afda74d-5275-5193-93af-823cf3d99f2c/scratchpad/scan_results.json`
- Format: Complete detailed data for each stock found

### Telegram Message
When configured, results are sent to Telegram with:
- 🎯 Top 10 qualifying stocks
- 💰 Current price and volume analysis
- 📊 Pattern strength, RSI, ADX metrics
- 🟢/🟡 Confidence level (HIGH/MEDIUM)
- 📈 Detected patterns and PCS suitability

## Scanner Configuration

Edit `run_scanner.py` or `telegram_scanner.py` to customize:

```python
self.config = {
    'stocks_to_scan': 50,              # Number of stocks to analyze
    'min_volume_ratio': 1.5,           # Minimum volume multiplier
    'pattern_strength_min': 65,        # Minimum pattern strength (%)
    'rsi_min': 30,                     # Minimum RSI
    'rsi_max': 85,                     # Maximum RSI
    'adx_min': 15,                     # Minimum ADX (trend strength)
}
```

## Patterns Detected

The scanner identifies these bullish patterns suitable for Put Credit Spreads:

1. **Current Day Breakout** (92% success rate)
   - Price breaks above recent resistance on current day
   - High volume confirmation required
   - Best for aggressive PCS strategies

2. **Cup and Handle** (85% success rate)
   - Classic cup formation with handle pullback
   - Strong support buildup
   - Excellent probability pattern

3. **Flat Base Breakout** (82% success rate)
   - Tight consolidation base
   - Bullish directional breakout
   - Moderate risk/reward

4. **Rectangle Bottom** (75% success rate)
   - Support and resistance boundaries
   - Volume acceleration on breakout
   - Clear entry/exit points

5. **Bump-and-Run Reversal** (78% success rate)
   - Reversal from downtrend
   - Momentum confirmation
   - Trending continuation pattern

## Understanding Confidence Levels

- 🟢 **HIGH** (75-100% strength): Most reliable, use standard PCS strikes
- 🟡 **MEDIUM** (60-74% strength): Good opportunities, slightly wider strikes
- 🔴 **LOW** (<60% strength): Lower probability, use wider defensive spreads

## Scheduling Automated Scans

### Using Cron (Linux/Mac)

Add to your crontab to run daily at market close (3:30 PM IST):

```bash
crontab -e
```

Add this line:

```cron
# Run PCS scanner daily at market close
30 15 * * 1-5 source /tmp/nse_scanner_env/bin/activate && cd /home/user/nsepcs && python3 run_scanner.py >> /var/log/pcs_scanner.log 2>&1
```

### Using at (one-time scheduling)

```bash
at 3:30 PM tomorrow
source /tmp/nse_scanner_env/bin/activate && python3 /home/user/nsepcs/run_scanner.py
Ctrl+D
```

## Troubleshooting

### Bot doesn't receive messages

1. Verify TELEGRAM_BOT_TOKEN is correct
2. Verify TELEGRAM_CHAT_ID is correct
3. Check that your bot has permission to send messages to that chat
4. Try sending a test message to @userinfobot to confirm bot is working

### Network errors in scanner

The scanner includes automatic retry logic:
- Max 5 network errors before stopping
- Errors saved to logs
- Results still saved to CSV/JSON if partial data available

### No patterns found

Try adjusting these settings:
- Lower `pattern_strength_min` from 65 to 50
- Lower `min_volume_ratio` from 1.5 to 1.0
- Expand `rsi_min` to 25 and `rsi_max` to 85
- Check if markets traded that day

### Virtual environment issues

Recreate the environment:

```bash
rm -rf /tmp/nse_scanner_env
python3 -m venv /tmp/nse_scanner_env
source /tmp/nse_scanner_env/bin/activate
pip install -r requirements.txt
```

## Monitoring

Check logs for scan execution:

```bash
# View recent scans
tail -100 /var/log/pcs_scanner.log

# Watch real-time scanning
tail -f /var/log/pcs_scanner.log
```

## Advanced Features

### Email Notifications (Optional)

Modify `run_scanner.py` to also send email:

```python
import smtplib
# Add email sending logic after Telegram
```

### Custom Filters

Create a custom configuration file:

```python
custom_config = {
    'stocks_to_scan': ['RELIANCE.NS', 'INFY.NS', 'HDFCBANK.NS'],
    'analysis_mode': 'Daily + Weekly Combined',
    'enhancements': {
        'delivery_volume': True,
        'fno_consolidation': True,
    }
}
```

### Database Logging

Store results in a database for historical analysis:

```python
# Add SQLite or PostgreSQL support to save results
```

## Support & Resources

- **Original App**: https://nse-fo-pcs-screener.streamlit.app
- **GitHub**: Check repository for latest updates
- **Telegram Community**: Join community for strategy discussions

## Disclaimer

⚠️ **RISK DISCLAIMER**: This scanner is for educational and analysis purposes only. It is NOT financial advice. Options trading involves substantial risk and you can lose your entire investment. Always:

1. Paper trade first before live implementation
2. Use proper position sizing (2% max per trade)
3. Implement strict stop losses (3% protocol)
4. Consult with qualified financial advisors
5. Only use with funds you can afford to lose
6. Understand options Greeks before trading

The scanner is provided as-is without any warranty or guarantee of performance.

## License

This scanner is part of the NSE F&O PCS Screener project. Use responsibly and trade safely.

---

**Last Updated**: October 3, 2026  
**Version**: 1.0 with Telegram Integration
