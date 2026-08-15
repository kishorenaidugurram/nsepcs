# NSE F&O PCS Scanner - Telegram Edition

Automated stock scanner that detects technical patterns and sends qualifying stocks directly to Telegram.

## Features

✨ **Core Functionality**
- Scans NSE F&O universe (208 stocks)
- Detects 12+ technical patterns (Cup & Handle, Flat Base, Breakouts, etc.)
- Daily + Weekly timeframe analysis
- Real-time pattern confirmation

📱 **Telegram Integration**
- Sends scan results directly to Telegram
- Beautiful formatted messages with emojis
- Stock rankings by pattern strength
- Detailed metrics and confidence levels

⚙️ **Customizable**
- Adjustable RSI, ADX, volume thresholds
- Pattern filtering by type or success rate
- Weekly validation support
- Multiple analysis modes (Daily/Weekly/Combined)

🚀 **Automation-Ready**
- Cron scheduling support
- Environment variable configuration
- JSON output for integration
- Comprehensive logging

## Quick Start

### 1. Get Telegram Credentials (2 minutes)

**Get Bot Token:**
- Open Telegram → Search "@BotFather"
- Send `/newbot`
- Follow prompts, copy the token

**Get Chat ID:**
- Open Telegram → Search "@userinfobot"  
- Send any message
- Copy the chat ID

### 2. Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install requests
```

### 4. Run Scanner

```bash
python3 run_scanner_telegram_complete.py
```

**That's it!** 🎉 You'll receive results on Telegram immediately.

## Detailed Usage

### Basic Scan (50 stocks)
```bash
python3 run_scanner_telegram_complete.py
```

### Full Scan (all 208 F&O stocks)
Edit `run_scanner_telegram_complete.py`:
```python
scanner.run(num_stocks=208, send_telegram=True)
```

### Scan Without Telegram
```python
scanner.run(num_stocks=50, send_telegram=False)
```

### View Results
Results are saved to: `scan_results.json`

```json
[
  {
    "symbol": "RELIANCE",
    "price": 2345.50,
    "volume_ratio": 2.15,
    "rsi": 65.3,
    "adx": 28.5,
    "pattern_type": "Current Day Breakout",
    "pattern_strength": 92.0,
    "confidence": "HIGH",
    "success_rate": 92.0,
    "pcs_fit": 98.0
  },
  ...
]
```

## Configuration Options

### Default Config
```python
{
    'rsi_min': 30,                 # Min RSI (avoid oversold)
    'rsi_max': 80,                 # Max RSI (avoid overbought)
    'adx_min': 15,                 # Min ADX (trend strength)
    'ma_support': True,            # Check moving average support
    'min_volume_ratio': 1.2,       # Volume above 20-day avg
    'pattern_strength_min': 65,    # Pattern strength threshold %
    'analysis_mode': 'Daily + Weekly Combined (Recommended)'
}
```

### Customize for Aggressive Screening
```python
{
    'rsi_min': 25,           # Wider RSI range
    'adx_min': 10,           # Lower ADX requirement  
    'pattern_strength_min': 50,  # Accept more patterns
    'min_volume_ratio': 1.0  # Lower volume requirement
}
```

### Customize for Conservative Screening
```python
{
    'rsi_min': 40,           # Avoid extreme oversold
    'rsi_max': 70,           # Avoid extreme overbought
    'adx_min': 25,           # Require strong trends
    'pattern_strength_min': 80,  # Only high-quality patterns
    'min_volume_ratio': 2.0  # Require significant volume
}
```

## Available Patterns

The scanner detects these technical patterns:

1. **Current Day Breakout** - Real-time EOD confirmation
2. **Cup and Handle** - William O'Neil pattern
3. **Flat Base** - Mark Minervini pattern
4. **Bump-and-Run Reversal** - Thomas Bulkowski
5. **Rectangle Bottom** - Consolidation breakout
6. **Head-and-Shoulders Bottom** - Classic reversal
7. **Double Bottom** - Support test reversal
8. **Three Rising Valleys** - Progressive support levels
9. **Rounding Bottom** - Saucer accumulation
10. **Rounding Top** - Rare upside breakout
11. **Inverted Scallop** - Gradual decline recovery
12. **Rectangle Top** - Support bounce pattern

Each pattern includes:
- Strength score (0-100%)
- Historical success rate
- PCS (Put Credit Spreads) suitability
- Confidence level (HIGH/MEDIUM/LOW)
- Weekly validation

## Telegram Message Example

```
📊 NSE F&O PCS Scanner Report
⏰ 2026-08-15 09:45 IST

🎯 Summary:
📈 Stocks Found: 12
💪 Avg Strength: 78%

📋 Scanner Settings:
RSI: 30-80
ADX Min: 15
Volume Ratio: 1.2x
Strength Threshold: 65%

🔝 Top 10 Stocks:

1. 🟢 RELIANCE
   💰 ₹2,345.50 | 💪 92% | HIGH
   📊 Current Day Breakout

2. 🟡 TCS
   💰 ₹3,456.75 | 💪 78% | MEDIUM
   📊 Cup and Handle

3. 🟡 HDFC BANK
   💰 ₹1,876.25 | 💪 75% | MEDIUM
   📊 Flat Base Breakout

... and 9 more stocks

📥 Next Steps:
1. Check full results in scan_results.json
2. Export to Excel for detailed analysis
3. Run Streamlit app for interactive charts
```

## Scheduled Automated Scans

### Daily at 9:30 AM (Cron)
```bash
# Edit crontab
crontab -e

# Add this line (market opens at 9:15 AM IST)
30 9 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_telegram_complete.py >> /home/user/nsepcs/scanner.log 2>&1
```

### Multiple Times Daily
```bash
# After market open (9:30 AM)
30 9 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_telegram_complete.py

# Afternoon (3:30 PM)
30 15 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_telegram_complete.py

# After market close (4:00 PM)
0 16 * * 1-5 cd /home/user/nsepcs && python3 run_scanner_telegram_complete.py
```

### Windows Task Scheduler
1. Open "Task Scheduler"
2. "Create Basic Task"
3. Set trigger: Daily 9:30 AM
4. Set action:
   - Program: `C:\Python\python.exe`
   - Arguments: `run_scanner_telegram_complete.py`
   - Start in: `C:\path\to\nsepcs`

## Python Scripting Integration

### Import and Use Directly
```python
from run_scanner_telegram_complete import StockScannerWithTelegram

# Create scanner
scanner = StockScannerWithTelegram()

# Run scan
scanner.run(num_stocks=50, send_telegram=True)

# Access results
results = scanner.scan_stocks(stocks, config)
for stock in results:
    print(f"{stock['symbol']}: {stock['current_price']}")
```

### Send Custom Message
```python
from run_scanner_telegram_complete import TelegramNotifier

notifier = TelegramNotifier()
notifier.send_message("📊 Custom market analysis message")
notifier.send_message("<b>Bold text</b> and <i>italic text</i>", parse_mode='HTML')
```

## Output Files

After running the scanner:

```
nsepcs/
├── scan_results.json           # JSON results
├── scanner.log                 # Execution log (optional)
└── TELEGRAM_SETUP_GUIDE.md     # Setup instructions
```

## Interpreting Results

### Confidence Levels
- 🟢 **HIGH** - Strength ≥ 85%, Multiple confirmations
- 🟡 **MEDIUM** - Strength 70-84%, Good pattern quality
- 🔴 **LOW** - Strength < 70%, Weak or unreliable signals

### Pattern Strength
- **90-100%** - Exceptional (very rare)
- **80-89%** - Excellent (high quality)
- **70-79%** - Good (reliable pattern)
- **60-69%** - Acceptable (worth monitoring)
- **<60%** - Weak (borderline setup)

### Volume Ratio
- **> 3x** - Exceptional volume surge
- **2-3x** - Strong volume confirmation
- **1.5-2x** - Good volume increase
- **1-1.5x** - Moderate volume
- **< 1x** - Low volume (risky)

## Performance Tips

1. **Faster Scans**
   - Reduce to 50 stocks for quick checks
   - Run during market hours (9:15 AM - 3:30 PM IST)

2. **Better Results**
   - Run after market close for EOD confirmation
   - Weekly validation improves accuracy
   - Multiple timeframes catch more patterns

3. **Lower System Load**
   - Use background scheduling
   - Cache data when possible
   - Limit to essential patterns

## Troubleshooting

### "No stocks found"
- Lower `pattern_strength_min` to 60%
- Widen RSI range (20-85)
- Reduce ADX minimum to 10
- Check if market is open/tradable

### Telegram not receiving messages
- Verify token with: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`
- Test connection: `python3 -c "import requests; requests.get('https://api.telegram.org/bot<TOKEN>/getUpdates')"`
- Ensure chat ID is correct

### Scanner running slowly
- Reduce `num_stocks` parameter
- Disable weekly validation for speed
- Run only specific patterns instead of all

### Pattern not detected
- Check if stock has sufficient data (need 30+ days)
- Verify pattern settings are enabled
- Lower pattern strength threshold

## API Reference

### TelegramNotifier
```python
class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None)
    def send_message(message, parse_mode='HTML')
    def send_stock_results(stocks, scan_config)
    def send_detailed_stock(stock)
```

### StockScannerWithTelegram
```python
class StockScannerWithTelegram:
    def run(num_stocks=50, send_telegram=True)
    def scan_stocks(stocks_to_scan, config)
    def create_default_config()
```

## Files Reference

| File | Purpose |
|------|---------|
| `run_scanner_telegram_complete.py` | Main scanner with Telegram integration |
| `streamlit_app.py` | Full Streamlit web app (optional) |
| `TELEGRAM_SETUP_GUIDE.md` | Step-by-step setup instructions |
| `requirements.txt` | Python dependencies |
| `scan_results.json` | Scanner output (generated) |

## Advanced Use Cases

### Email Integration
```python
import smtplib
from email.mime.text import MIMEText

# Send email along with Telegram
# (Implement your email logic here)
```

### Database Integration
```python
import sqlite3

# Save results to database for historical analysis
# Track pattern performance over time
```

### Webhook Integration
```python
import requests

# Send results to external webhook
# Integrate with other tools
```

## Security Considerations

⚠️ **Important**
- Never commit `.env` file to git
- Rotate bot tokens periodically  
- Use environment variables for secrets
- Don't share tokens in public channels
- Run on trusted machines only

## License

This scanner uses data from Yahoo Finance and yfinance library.

## Support & Contributing

For issues or suggestions:
1. Check TELEGRAM_SETUP_GUIDE.md
2. Review scanner.log for errors
3. Test network connectivity
4. Verify credentials are correct

## Disclaimer

This tool is for educational and analysis purposes only. Past performance does not guarantee future results. Always do your own research and consult with a financial advisor before trading.

---

**Happy Scanning! 📈**

Made with ❤️ for Indian Options Traders
