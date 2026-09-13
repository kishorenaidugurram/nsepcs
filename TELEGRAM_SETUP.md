# Telegram Stock Scanner Setup Guide

## Overview
The `telegram_scanner.py` script automatically screens NSE F&O stocks for trading opportunities and sends results to Telegram.

## Prerequisites

### 1. Telegram Bot Setup
To use this scanner with Telegram, you need:

1. **Create a Telegram Bot**:
   - Open Telegram and search for `@BotFather`
   - Send `/start` and then `/newbot`
   - Follow the prompts to create your bot
   - Save the **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

2. **Get Your Chat ID**:
   - Send any message to your new bot
   - Go to `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual token
   - Look for the `"id"` field in the response - that's your Chat ID

### 2. Environment Variables
Set these environment variables for the scanner to work:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Optional scanning parameters:
```bash
export SCAN_RSI_MIN=30          # Minimum RSI (default: 30)
export SCAN_RSI_MAX=75          # Maximum RSI (default: 75)
export SCAN_ADX_MIN=20          # Minimum ADX (default: 20)
export SCAN_MIN_VOLUME_RATIO=1.2   # Min volume ratio (default: 1.2x)
export SCAN_PATTERN_STRENGTH_MIN=65  # Min pattern strength % (default: 65%)
export SCAN_MAX_STOCKS=219      # Max stocks to scan (default: 219 - all)
export SCAN_MAX_RESULTS=20      # Max results to report (default: 20)
```

## Running the Scanner

### Direct Execution
```bash
cd /home/user/nsepcs
python3 telegram_scanner.py
```

### With Custom Parameters
```bash
SCAN_RSI_MIN=35 SCAN_RSI_MAX=70 SCAN_PATTERN_STRENGTH_MIN=70 python3 telegram_scanner.py
```

### Scheduled Execution
Add to crontab to run daily at 3:30 PM (after market close):
```bash
30 15 * * 1-5 cd /home/user/nsepcs && python3 telegram_scanner.py
```

## Output

The scanner produces:
1. **Console Output**: Real-time progress of stock analysis
2. **Telegram Message**: HTML-formatted summary of results sent to your Telegram
3. **JSON File**: Detailed results saved to `/tmp/claude-0/-home-user-nsepcs/.../stock_scan_*.json`

Example Telegram output:
```
📊 Stock Screening Results
Time: 13-09-2026 15:30 IST
Found: 5 stocks

1. RELIANCE
   Price: ₹2850.50 | RSI: 52.3 | ADX: 28.5
   Patterns: Current Day Breakout, Cup and Handle
   Strength: 78%

2. TCS
   Price: ₹3520.25 | RSI: 48.7 | ADX: 25.2
   ...
```

## Scanning Parameters Explained

### Technical Filters
- **RSI (Relative Strength Index)**: 30-75 range is ideal for PCS trading
  - Lower values (30-40): Stocks recovering from oversold conditions
  - Higher values (60-75): Strong uptrends before pullbacks
  
- **ADX (Average Directional Index)**: Minimum 20 indicates strong trend
  - Higher ADX = stronger directional movement
  
- **Volume Ratio**: Minimum 1.2x means current volume is 1.2x the average
  - Indicates strong interest and breakout potential

- **Pattern Strength**: Minimum 65% means high-quality pattern detection
  - Patterns are validated against multiple technical parameters

### Recognized Chart Patterns
The scanner detects:
- Current Day Breakout (priority pattern for PCS)
- Cup with Handle (bullish consolidation)
- Flat Base Breakout (strong support formation)
- Bump-and-Run Reversal
- Rectangle Bottom (support test)
- Head-and-Shoulders Bottom (reversal)
- Double Bottom (strength confirmation)
- Three Rising Valleys (progressive support)
- Rounding Bottom (U-shaped recovery)
- Inverted Scallop (O'Neil CAN SLIM pattern)

## Network Requirements

The scanner requires internet access to:
- Yahoo Finance API (stock data) - via proxy
- Telegram Bot API (sending messages)

If you see connection errors:
1. Check your internet connection
2. Verify proxy settings if behind a corporate firewall
3. Ensure Telegram credentials are correct

## Troubleshooting

### "ModuleNotFoundError: No module named 'ta'"
Install missing dependencies:
```bash
pip install -r requirements.txt
```

### "Telegram credentials not found"
The script saves results locally even without Telegram configured. To enable:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python3 telegram_scanner.py
```

### "No stocks found matching criteria"
Try adjusting filters:
- Lower RSI max to 70 or even 65
- Lower ADX minimum to 15
- Reduce Volume Ratio to 1.0x
- Lower Pattern Strength to 55%

### Yahoo Finance Connection Errors
The scanner may be blocked by:
- Firewall/proxy restrictions
- Rate limiting from Yahoo Finance
- Network policy in your environment

Workaround: Run on your local machine or server with unrestricted internet access.

## Code Structure

- `telegram_scanner.py`: Main scanner script
  - `run_scanning()`: Performs stock analysis
  - `send_to_telegram()`: Sends results via Telegram API
  - `format_results_for_telegram()`: Formats output
  - `_scan_single_stock()`: Analyzes individual stocks

- `streamlit_app.py`: Full Streamlit application
  - `ProfessionalPCSScanner`: Core scanner engine
  - `COMPLETE_NSE_FO_UNIVERSE`: List of 219 F&O stocks

## Performance Tips

1. **Reduce stock universe** for faster scans:
   ```bash
   SCAN_MAX_STOCKS=50 python3 telegram_scanner.py
   ```

2. **Increase pattern strength threshold** to get fewer, better-quality results:
   ```bash
   SCAN_PATTERN_STRENGTH_MIN=75 python3 telegram_scanner.py
   ```

3. **Run during market hours** when data is most up-to-date

## Support

For issues or questions about:
- **Telegram setup**: Check Telegram's official docs
- **Stock screening**: Review the chart patterns documentation
- **Script bugs**: Check the error logs and GitHub issues

## Security Notes

- Never commit `.env` files with real Telegram tokens
- Use environment variables or secure vaults for credentials
- Restrict script permissions: `chmod 700 telegram_scanner.py`
- Run from a secure, trusted environment

---

Last Updated: 2026-09-13
