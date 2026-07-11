# NSE F&O PCS Telegram Scanner Setup Guide

## Overview
This script runs your PCS (Put Credit Spread) stock scanner and sends results directly to Telegram.

## Prerequisites

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts to create your bot
4. You'll receive a **Bot Token** (example: `6087141234:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGh`)

### 2. Get Your Chat ID

1. Message your newly created bot something like "Hello"
2. Visit this URL in your browser (replace `YOUR_TOKEN` with your bot token):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Look for `"id": NUMBER` - that's your Chat ID

### 3. Set Environment Variables

#### On Linux/Mac:
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

#### On Windows (Command Prompt):
```cmd
set TELEGRAM_BOT_TOKEN=your_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

#### Permanently (recommended):
Add to your shell profile (~/.bashrc, ~/.zshrc, or .env file):
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

## Running the Scanner

### Basic Usage
```bash
python3 telegram_scanner.py
```

### With Custom Filters
Edit the `DEFAULT_FILTERS` dictionary in the script to customize:
- RSI range (default: 30-75)
- ADX minimum (default: 20)
- Moving Average support check
- Volume ratio requirements
- Pattern detection options

### Running as a Scheduled Task

#### Using Cron (Linux/Mac):
```bash
# Run daily at 09:15 AM
15 9 * * * cd /path/to/nsepcs && python3 telegram_scanner.py >> scanner.log 2>&1

# Run every 2 hours
0 */2 * * * cd /path/to/nsepcs && python3 telegram_scanner.py >> scanner.log 2>&1
```

#### Using Task Scheduler (Windows):
1. Create a batch file: `run_scanner.bat`
   ```batch
   @echo off
   cd /d "C:\path\to\nsepcs"
   python telegram_scanner.py >> scanner.log 2>&1
   ```
2. Open Task Scheduler and create a new task pointing to this batch file

## Output

The scanner will:
1. **Print results to console** (always)
2. **Send to Telegram** (if credentials are configured)

Sample output:
```
🎯 NSE F&O PCS Scanner Results
📅 2024-07-11 14:30:25

📊 Summary
✅ Stocks Found: 5
🔥 Average Strength: 78.3%

📈 Top Stocks
1. RELIANCE
   💰 Price: ₹2,845.50
   ⚡ Strength: 85% (HIGH)
   📊 RSI: 62.3 | ADX: 28.5
   📈 Volume: 2.15x
...
```

## Troubleshooting

### "No stocks found"
- Adjust the `pattern_strength_min` lower (default: 65)
- Reduce `rsi_min` or increase `rsi_max`
- Lower the `adx_min` threshold
- Expand the stocks list

### "Telegram message failed"
- Verify Bot Token and Chat ID are correct
- Check internet connection
- Ensure the bot has permission to send messages

### "No data available"
- Yahoo Finance API may be rate limited
- Try running at different times
- Consider using your local machine instead of cloud environment

## Advanced Configuration

### Custom Stock Lists
Edit the `TIER1_STOCKS` variable to add/remove stocks:
```python
TIER1_STOCKS = ['RELIANCE', 'INFY', 'TCS', 'HDFCBANK', 'ICICIBANK']
```

### Filter Presets

**Aggressive (High Risk)**
```python
'rsi_min': 20,      # Very oversold
'rsi_max': 80,      # Allows overbought
'adx_min': 15,      # Weak trend requirement
'pattern_strength_min': 50
```

**Conservative (Low Risk)**
```python
'rsi_min': 40,      # Avoid oversold
'rsi_max': 60,      # Narrow band
'adx_min': 30,      # Strong trend required
'pattern_strength_min': 75
```

## API Reference

### Scanner Methods

```python
scanner = SimplePCSScanner()

# Analyze single stock
result = scanner.analyze_stock('RELIANCE.NS', DEFAULT_FILTERS)

# Scan multiple stocks
results = scanner.scan(['RELIANCE.NS', 'INFY.NS'], DEFAULT_FILTERS)
```

### Result Structure
```python
{
    'symbol': 'RELIANCE.NS',
    'symbol_clean': 'RELIANCE',
    'price': 2845.50,
    'rsi': 62.3,
    'adx': 28.5,
    'volume_ratio': 2.15,
    'patterns': [...],
    'max_strength': 85.0
}
```

## Support

For issues or enhancements:
1. Check the scanner logs
2. Verify Telegram credentials
3. Test data fetch independently
4. Review filter settings

---

**Happy Trading! 📈**
