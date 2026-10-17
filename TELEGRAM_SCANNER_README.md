# NSE F&O PCS Scanner with Telegram Integration

## Overview

This script runs the NSE F&O PCS (Put Credit Spread) Scanner and sends results directly to Telegram. It's designed to be run as a scheduled task or manually to scan for stocks meeting your technical analysis filter criteria.

## Features

- **Automated Scanning**: Scans 50 F&O stocks by default (configurable)
- **Advanced Technical Analysis**: Uses multiple chart patterns and indicators
- **Telegram Integration**: Sends results to your Telegram chat
- **Export Formats**: Generates both text and CSV reports
- **Recommended Filters**: Pre-configured with proven technical parameters

## Prerequisites

### 1. Dependencies

```bash
pip install -r requirements.txt
# or manually:
pip install pandas numpy yfinance scikit-learn scipy beautifulsoup4 requests plotly openpyxl streamlit
```

### 2. Telegram Setup

To receive results on Telegram, you need:

1. **Create a Telegram Bot**:
   - Open Telegram and search for `@BotFather`
   - Send `/start` and follow instructions to create a new bot
   - BotFather will give you a `BOT_TOKEN`

2. **Get Your Chat ID**:
   - Start a conversation with your newly created bot
   - Send any message to the bot
   - Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` (replace `<BOT_TOKEN>`)
   - Look for your `chat_id` in the JSON response
   - Or use `@userinfobot` in Telegram to get your user ID

3. **Set Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN='123456789:ABCdefGHIjklmNOpqrsTUVwxyz'
   export TELEGRAM_CHAT_ID='987654321'
   ```

## Usage

### Basic Usage

```bash
python3 nse_pcs_telegram_scanner.py
```

### With Environment Variables

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
python3 nse_pcs_telegram_scanner.py
```

### Scheduled Execution (Cron)

Add to your crontab to run daily at 3:30 PM (after market close):

```bash
# Run daily at 3:30 PM IST
30 15 * * 1-5 cd /home/user/nsepcs && export TELEGRAM_BOT_TOKEN='...' && export TELEGRAM_CHAT_ID='...' && python3 nse_pcs_telegram_scanner.py >> /var/log/pcs_scanner.log 2>&1
```

## Filter Configuration

The scanner uses these recommended technical filters:

### Core Indicators
- **RSI**: 30-75 range (identifying oversold/overbought conditions)
- **ADX**: Minimum 20 (trend strength)
- **Moving Average**: EMA support, 3% tolerance
- **Volume**: Minimum 1.2x average volume
- **Breakout Volume**: 2.0x above average

### Chart Patterns (Detected)
- Current Day Breakout
- Cup and Handle
- Flat Base Breakout
- Bump-and-Run Reversal
- Rectangle Bottom/Top
- Head-and-Shoulders Bottom
- Double Bottom
- Three Rising Valleys
- Rounding Bottom
- Rounding Top (Upside Break)
- Inverted Scallop

### Analysis Mode
- **Daily + Weekly Combined**: Best accuracy with moderate scan time
- Daily data for current day confirmation
- Weekly data for longer-term trend validation

## Output

The scanner generates:

1. **Console Output**: Real-time progress and summary
2. **Text Report**: `pcs_scan_results_YYYYMMDD_HHMMSS.txt`
   - Detailed results for all stocks found
3. **CSV Export**: `pcs_scan_results_YYYYMMDD_HHMMSS.csv`
   - Importable into spreadsheets
4. **Telegram Message**: Formatted results sent to your Telegram chat
   - Top 15 stocks with key metrics
   - Pattern type and strength
   - Volume and RSI/ADX indicators

## Example Output

### Telegram Message
```
🎯 NSE F&O PCS Scan Results
📅 2026-10-17 15:30 IST

📊 Found 12 stocks with confirmed patterns

1. RELIANCE
💰 ₹2580.50 | RSI:55 | ADX:35
📊 Vol:2.3x | Cup and Handle (78%)
```

### CSV Format
```
Symbol,Price,RSI,ADX,Volume,Pattern,Strength,NumPatterns
RELIANCE,2580.50,55.0,35.0,2.30x,Cup and Handle,78%,2
INFY,3450.75,48.0,32.0,1.85x,Flat Base Breakout,72%,1
```

## Troubleshooting

### "No module named 'pandas'"
```bash
python3 -m pip install pandas
```

### Telegram message not received
1. Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correctly set
2. Test with: `curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage -d "chat_id=<ID>&text=Test"`
3. Make sure the bot has permission to message you

### "Failed to get ticker data"
- Market data might be unavailable during non-trading hours
- Yahoo Finance might be blocking requests - check network connectivity
- Try again during market hours (9:15 AM - 3:30 PM IST)

### No stocks found
- Market conditions might not match your filters
- Try adjusting RSI range or ADX minimum
- Check if the stock list is loaded correctly

## Advanced Configuration

To modify filter criteria, edit the `config` dictionary in `run_scanner()`:

```python
config = {
    'rsi_min': 30,        # Increase to be more selective
    'rsi_max': 75,        # Decrease for stronger signals
    'adx_min': 20,        # Increase for stronger trends
    'min_volume_ratio': 1.2,  # Higher = more volume required
    'pattern_strength_min': 65,  # Higher = stronger patterns only
    # ... etc
}
```

## Support

For issues or enhancements, refer to the main project README: `README.md`

## Disclaimer

This is an educational tool. Always conduct your own research before trading. Past performance does not guarantee future results. Use at your own risk.

---

**Last Updated**: 2026-10-17
**Version**: 1.0
**Author**: Claude Code with ProfessionalPCSScanner
