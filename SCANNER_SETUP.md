# NSE F&O PCS Scanner - Telegram Integration Setup

## Overview
The `run_nse_scanner.py` script runs the NSE F&O PCS (Put Credit Spread) scanner and automatically sends results to your Telegram channel/chat.

## Requirements

### System Requirements
- Python 3.7+
- Internet connection (for market data and Telegram API)

### Python Dependencies
```bash
pip install yfinance pandas numpy requests
```

### Telegram Setup
1. **Create a Telegram Bot**:
   - Open Telegram and search for `@BotFather`
   - Send `/start` and follow instructions
   - Create a new bot with `/newbot`
   - Copy the **Bot Token** (looks like: `123456789:ABCDefGHIjklMNOpqrSTUVwxyz_1234567890`)

2. **Get Your Chat ID**:
   - Open Telegram and search for `@userinfobot`
   - Send any message, it will reply with your Chat ID (numeric)
   - OR send a message in your bot chat and check: `https://api.telegram.org/bot<TOKEN>/getUpdates`

3. **Set Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   ```

   Or add to `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

## Usage

### Basic Run
```bash
python3 run_nse_scanner.py
```

### With Environment Variables
```bash
TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_chat_id" python3 run_nse_scanner.py
```

### Scheduled Execution (Cron)

**Daily morning scan (before market opens)**:
```bash
# Edit crontab
crontab -e

# Add this line (runs at 8:30 AM IST)
30 08 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_chat_id" python3 run_nse_scanner.py > /var/log/nse_scanner.log 2>&1
```

**During market hours (every 2 hours)**:
```bash
0 */2 09-15 * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_chat_id" python3 run_nse_scanner.py >> /var/log/nse_scanner.log 2>&1
```

## Filter Criteria

The scanner uses these default filters:

| Filter | Default Value | Description |
|--------|---------------|-------------|
| RSI Min | 30 | Minimum RSI level |
| RSI Max | 75 | Maximum RSI level |
| ADX Min | 20 | Minimum ADX strength |
| Volume Ratio | 1.2x | Minimum volume ratio |
| Pattern Strength | 65% | Minimum pattern strength score |

### Patterns Detected
1. **Current Day Breakout** - Price breaks above resistance with volume confirmation
2. **Cup & Handle** - William O'Neil's classic pattern
3. **Flat Base** - Mark Minervini's pattern for breakouts

## Output

### Telegram Message Format
```
📊 NSE F&O PCS Scan Results
2024-08-09 09:30 IST

1. INFY 🟢
   💰 ₹2,150.45 | 📊 85% | RSI: 52.3 | ADX: 28.5
   Current Day Breakout | Cup with Handle

2. TCS 🟡
   💰 ₹3,850.20 | 📊 72% | RSI: 58.1 | ADX: 25.2
   Flat Base Breakout

... and 5 more stocks found

Total: 7 stocks
```

### Confidence Levels
- 🟢 **HIGH**: Strength ≥ 85% - High probability setups
- 🟡 **MEDIUM**: Strength 70-84% - Moderate probability setups
- 🔴 **LOW**: Strength < 70% - Lower probability but watchable

## Troubleshooting

### "Telegram credentials not found"
```bash
# Check if environment variables are set
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# If empty, set them
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### "Failed to send to Telegram"
1. Verify bot token is correct
2. Verify chat ID is correct
3. Check internet connection
4. Ensure bot has permission to send messages in the chat

### "No stocks found"
- Market may be closed (NSE operates 9:15 AM - 3:30 PM IST, Mon-Fri)
- Filter criteria might be too strict
- No valid patterns detected in market conditions

### "No data available"
- Yahoo Finance API might be rate-limited
- Network connectivity issue
- Symbols might not exist or are delisted

## Advanced Configuration

### Modify Filter Thresholds
Edit `run_nse_scanner.py` and change these values:

```python
filters = {
    'rsi_min': 25,      # Lower to include more stocks
    'rsi_max': 80,      # Higher to include more stocks
    'adx_min': 15,      # Lower to include weaker trends
    'pattern_strength_min': 55,  # Lower to catch earlier patterns
}
```

### Modify Stock Universe
Edit the `NSE_FO_STOCKS` list at the top of the file to include/exclude specific stocks.

### Change Number of Stocks to Scan
In the `main()` function, modify:
```python
results = run_scan(max_stocks=50)  # Change 50 to desired number
```

## Important Notes

⚠️ **Disclaimer**: This scanner is for educational and analysis purposes only. Not financial advice.

✅ **Best Practices**:
- Run during NSE market hours (9:15 AM - 3:30 PM IST, Monday-Friday)
- Always verify signals before trading
- Paper trade before live trading
- Use proper position sizing (max 2% per trade)
- Implement stop losses (3% recommended)

## Support

For issues or improvements:
1. Check the logs: `tail -f /var/log/nse_scanner.log`
2. Run with verbose output to debug
3. Verify market data is available
4. Check Telegram bot connectivity

## License

This tool is provided as-is for personal use. Modify as needed for your requirements.
