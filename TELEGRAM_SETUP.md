# NSE F&O PCS Scanner - Telegram Integration Guide

## 🎯 Quick Start

### Step 1: Get Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/start` and then `/newbot`
3. Follow the prompts:
   - Give your bot a name (e.g., "PCS Scanner")
   - Give it a username (e.g., "pcs_scanner_bot")
4. Copy the **API Token** (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Your Chat ID

1. Open Telegram and search for `@userinfobot` (or another chat ID bot)
2. Send `/start` to it
3. It will show your Chat ID (a number like: `123456789`)

Alternatively:
- Send a message to your bot from Step 1
- Run: `curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"`
- Look for `"chat":{"id":<YOUR_CHAT_ID>`

### Step 3: Configure Scanner

**Option A: Environment Variables (Recommended)**
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**Option B: Edit Script Directly**
Open `run_scanner.py` and edit:
```python
TELEGRAM_BOT_TOKEN = 'your_token_here'
TELEGRAM_CHAT_ID = 'your_chat_id_here'
```

### Step 4: Customize Filters

Edit `run_scanner.py` - Find the `SCAN_CONFIG` section:

```python
SCAN_CONFIG = {
    'min_volume_ratio': 0.8,      # 80% of average volume
    'min_momentum': 40,             # Momentum score >= 40
    'max_volatility': 50,           # Volatility <= 50%
    'price_above_sma20': True,      # Must be above 20-day MA
    'min_change_1d': -3,            # Not down more than 3%
    'max_change_1d': 5              # Not up more than 5%
}
```

### Step 5: Install Dependencies

```bash
pip install yfinance pandas numpy plotly pytz requests
```

### Step 6: Run Scanner

```bash
python3 run_scanner.py
```

## 📊 Filter Criteria Explained

### min_volume_ratio
- **Default**: 0.8 (80%)
- **What it does**: Stock must have at least 80% of its average daily volume
- **Higher = Stricter**: Use 1.0+ for only high volume spikes

### min_momentum
- **Default**: 40 (out of 100)
- **What it does**: Momentum score based on up/down days ratio
- **Higher = Stricter**: 50+ for bullish preference

### max_volatility
- **Default**: 50 (50% annualized)
- **What it does**: Limits stock volatility (annualized)
- **Lower = Stricter**: 30% for stable stocks

### price_above_sma20
- **Default**: True
- **What it does**: Price must be above 20-day moving average
- **For Shorts**: Set to False

### min_change_1d / max_change_1d
- **Default**: -3% to +5%
- **What it does**: Filters based on 1-day price change
- **Range**: Prevents extreme movers

## 🔄 Schedule Automated Scanning

### Linux/Mac Cron Job

```bash
crontab -e
```

Add for 9:30 AM every trading day:
```
30 9 * * 1-5 TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_id python3 /path/to/run_scanner.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, 09:30 AM
4. Action: `python3.exe C:\path\to\run_scanner.py`
5. Set environment variables in script or .bat wrapper

## 📱 Example Telegram Output

```
📈 PCS Scan Results - 02 Jul 09:30 IST
🎯 7 Qualified Stocks
========================================

1. 🟢 RELIANCE
   Score: 82 | 1D: +1.5% | Vol: 1.23x
   Price: ₹2,950.00 | Momentum: 65
   • ✓ Volume: 1.23x
   • ✓ Price>SMA20

2. 🟡 INFY
   Score: 65 | 1D: +0.8% | Vol: 0.95x
   Price: ₹1,420.00 | Momentum: 58
   • ✓ Momentum: 58
   • ✓ Vol: 32.5%
```

## 🐛 Troubleshooting

### "Telegram credentials not configured"
- Check environment variables: `echo $TELEGRAM_BOT_TOKEN`
- Or edit the script directly and add credentials

### "Invalid API token"
- Copy-paste token from BotFather again carefully
- Make sure no extra spaces

### "Not getting any results"
- Check filters are not too strict
- Verify yfinance can download data
- Try: `python3 -c "import yfinance as yf; print(yf.download('RELIANCE.NS', period='1d'))"`

### "Network error"
- Check internet connection
- For corporate proxy: Configure pip with proxy settings
- Yahoo Finance API might be blocked - try different DNS

## 📈 Advanced Configuration

### Filter by Market Cap (Tier System)

Modify `STOCKS_TO_SCAN`:

```python
STOCKS_TO_SCAN = {
    'Tier1': [  # Ultra liquid, large caps
        'NIFTY.NS', 'BANKNIFTY.NS', 'RELIANCE.NS', ...
    ],
    'Tier2': [  # High liquidity, mid caps
        'KOTAKBANK.NS', 'WIPRO.NS', ...
    ],
    'Tier3': [  # Medium liquidity, smaller caps
        'COALINDIA.NS', ...
    ]
}
```

Call with specific tiers:
```python
results = scanner.scan(['Tier1'], SCAN_CONFIG)  # Only Tier1
results = scanner.scan(['Tier1', 'Tier2'], SCAN_CONFIG)  # Tier1 & 2
```

### Custom Stock List

Edit `run_scanner.py` and replace `STOCKS_TO_SCAN`:

```python
STOCKS_TO_SCAN = {
    'Custom': ['RELIANCE.NS', 'INFY.NS', 'TCS.NS']
}
```

### Multiple Scans Per Day

Create a schedule like:
- **9:35 AM**: First scan (after market open)
- **12:00 PM**: Mid-day scan
- **3:00 PM**: Near close scan

## 💡 Tips

1. **Conservative**: Higher min_volume_ratio, lower max_volatility
2. **Aggressive**: Lower min_volume_ratio, higher max_volatility
3. **Day Trading**: Set min_change_1d to higher value
4. **Swing Trading**: Use longer lookback, adjust momentum
5. **Testing**: Run with dry filters first, see if you like results

## 📞 Support

If you have issues:
1. Check this guide first
2. Verify Telegram bot token and chat ID
3. Test with: `curl https://api.telegram.org/bot<TOKEN>/getMe`
4. Check internet connectivity

---

**Happy Trading! Remember: Always practice risk management and never risk more than you can afford to lose.**
