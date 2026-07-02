# NSE F&O PCS Scanner - Telegram Integration

A complete solution for scanning NSE F&O stocks for Put Credit Spread opportunities and sending results to Telegram.

## 📦 What's Included

1. **`run_scanner.py`** - Main scanner script with Telegram integration
2. **`setup_telegram.py`** - Interactive setup wizard
3. **`TELEGRAM_SETUP.md`** - Detailed configuration guide
4. **`telegram_scanner.py`** - Simplified scanner (backup)

## 🚀 Quick Start (5 Minutes)

### 1. Run Setup Wizard

```bash
python3 setup_telegram.py
```

The wizard will:
- Ask for your Telegram Bot Token
- Ask for your Chat ID
- Test the connection
- Create configuration files

### 2. First Scan

```bash
python3 run_scanner.py
```

Results will be:
- Printed to console
- Sent to Telegram
- Saved as CSV

That's it! You'll receive qualified stocks in Telegram.

## 🎯 How It Works

### Filter Criteria

The scanner analyzes each stock against these filters:

| Filter | Default | Purpose |
|--------|---------|---------|
| **Volume Ratio** | 0.8x | Stock must have >= 80% of average volume |
| **Momentum** | 40+ | Bullish momentum score (0-100) |
| **Volatility** | ≤50% | Annualized volatility cap |
| **Price > SMA20** | ✓ | Price above 20-day moving average |
| **1D Change** | -3% to +5% | Filter extreme movers |

### Scoring System

Stocks must pass **all mandatory filters** and score ≥50 points:
- ✅ 20 pts: Volume check
- ✅ 25 pts: Momentum score
- ✅ 15 pts: Volatility range
- ✅ 25 pts: Price positioning
- ✅ 15 pts: Price change

### Confidence Levels

```
🟢 Score 75-100  → HIGH confidence (safest trades)
🟡 Score 60-74   → MEDIUM confidence (balanced)
🔴 Score <60     → LOW confidence (higher risk)
```

## 📊 Stocks Analyzed

The scanner analyzes 34 NSE F&O stocks across 3 liquidity tiers:

### Tier 1: Ultra High Liquidity (>1M contracts/day)
- NIFTY, BANKNIFTY, RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, LT, ITC

### Tier 2: High Liquidity (500K-1M contracts/day)
- KOTAKBANK, AXISBANK, HCLTECH, WIPRO, MARUTI, ASIANPAINT, BHARTIARTL, SUNPHARMA

### Tier 3: Medium Liquidity (100K-500K contracts/day)
- BAJFINANCE, BAJAJFINSV, INDUSINDBK, TECHM, TITAN, NESTLEIND, ULTRACEMCO, POWERGRID, NTPC, ONGC, COALINDIA, JSWSTEEL, TATASTEEL, HINDALCO

## ⚙️ Configuration

### Via Setup Wizard (Recommended)
```bash
python3 setup_telegram.py
```

### Manual Configuration

**Option 1: Environment Variables**
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
python3 run_scanner.py
```

**Option 2: Edit Script**
Open `run_scanner.py` and replace:
```python
TELEGRAM_BOT_TOKEN = 'your_token_here'
TELEGRAM_CHAT_ID = 'your_chat_id_here'
```

## 🔧 Customization

### Adjust Filters

Edit `run_scanner.py`:

```python
SCAN_CONFIG = {
    'min_volume_ratio': 0.8,      # Change volume requirement
    'min_momentum': 40,             # Change momentum threshold
    'max_volatility': 50,           # Change volatility limit
    'price_above_sma20': True,      # Require price above MA
    'min_change_1d': -3,            # Min 1D change
    'max_change_1d': 5              # Max 1D change
}
```

**Filter Presets:**

**Conservative** (Fewer, higher-quality signals)
```python
SCAN_CONFIG = {
    'min_volume_ratio': 1.2,
    'min_momentum': 60,
    'max_volatility': 35,
    'price_above_sma20': True,
    'min_change_1d': 0,
    'max_change_1d': 2
}
```

**Aggressive** (More signals, higher risk)
```python
SCAN_CONFIG = {
    'min_volume_ratio': 0.6,
    'min_momentum': 35,
    'max_volatility': 60,
    'price_above_sma20': False,
    'min_change_1d': -5,
    'max_change_1d': 10
}
```

### Custom Stock List

Edit `run_scanner.py`:

```python
STOCKS_TO_SCAN = {
    'MyStocks': ['RELIANCE.NS', 'INFY.NS', 'TCS.NS']
}
```

Then in code: `results = scanner.scan(['MyStocks'], SCAN_CONFIG)`

## 🔄 Automate Scanning

### Linux/Mac (Cron Job)

1. First, ensure your credentials are in `.env`:
```bash
python3 setup_telegram.py
```

2. Create `run_scan.sh` (already created if you used setup wizard):
```bash
#!/bin/bash
export $(cat .env | xargs)
python3 /path/to/run_scanner.py
```

3. Make executable:
```bash
chmod +x run_scan.sh
```

4. Add to crontab:
```bash
crontab -e
```

Add these lines:
```cron
# Run at 9:35 AM (after market opens)
35 9 * * 1-5 cd /path/to/scanner && ./run_scan.sh

# Run at 12:00 PM (mid-day check)
0 12 * * 1-5 cd /path/to/scanner && ./run_scan.sh

# Run at 2:30 PM (before close)
30 14 * * 1-5 cd /path/to/scanner && ./run_scan.sh
```

**Note**: IST is UTC+5:30, adjust times accordingly for your timezone

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task: "PCS Scanner"
3. Trigger: Daily at 9:35 AM
4. Repeat every 1 day
5. Action:
   - Program: `python3.exe`
   - Arguments: `C:\path\to\run_scanner.py`
   - Start in: `C:\path\to\scanner`
6. Advanced: Check "Run whether user is logged in or not"

## 📱 Telegram Output Example

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
```

## 🐛 Troubleshooting

### "Telegram credentials not configured"
- Run setup wizard: `python3 setup_telegram.py`
- Or set environment variables before running

### "Invalid API token"
- Verify token from BotFather
- No spaces or extra characters

### "No results found"
- Filters might be too strict
- Try loosening constraints
- Verify Yahoo Finance can fetch data: `python3 -c "import yfinance as yf; print(yf.download('RELIANCE.NS', period='1d'))"`

### "Network error"
- Check internet connection
- Verify Telegram API is accessible
- Try: `curl https://api.telegram.org/bot<TOKEN>/getMe`

## 📊 Interpreting Results

### Score Components
- **Score 75+**: HIGH confidence - suitable for conservative traders
- **Score 60-74**: MEDIUM confidence - balanced risk/reward
- **Score <60**: LOW confidence - for aggressive traders only

### Key Metrics
- **Volume Ratio**: Current volume / Average volume
  - >1.0 = Above average trading activity
  - <0.8 = Low activity (risky for options)
  
- **Momentum Score**: Based on up/down days
  - >60 = Strong bullish momentum
  - 40-60 = Mixed signals
  - <40 = Bearish bias

- **1D Change**: Single day price change
  - Shows if stock is trending or stable

## ⚠️ Important Disclaimers

1. **NOT Financial Advice**: This tool is for educational purposes only
2. **Past Performance**: Historical patterns don't guarantee future results
3. **Risk Management**: Always use stop losses and position sizing
4. **Paper Trade First**: Test strategies before live trading
5. **Consult Experts**: Speak with financial advisors before trading

## 🎓 Learning Resources

- [NSE F&O Basics](https://www.nseindia.com)
- [Options Trading 101](https://www.investopedia.com/terms/o/option.asp)
- [Technical Analysis](https://en.wikipedia.org/wiki/Technical_analysis)
- [Risk Management](https://www.investopedia.com/terms/r/riskmanagement.asp)

## 📈 Pro Tips

1. **Multiple Scans**: Run at market open (9:35 AM), mid-day (12 PM), and before close (3 PM IST)
2. **Combine with Charts**: Use results as starting point for technical analysis
3. **Back-test**: Paper trade for 2-4 weeks before live trading
4. **Position Sizing**: Never risk more than 2% of capital per trade
5. **Stop Loss**: Always set 3-5% stop losses

## 🔗 Useful Links

- [NSE Website](https://www.nseindia.com)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Yahoo Finance Data](https://finance.yahoo.com)

## 💡 Next Steps

1. Run setup wizard: `python3 setup_telegram.py`
2. Test first scan: `python3 run_scanner.py`
3. Adjust filters to your preference
4. Set up automation with cron/Task Scheduler
5. Start paper trading the results

---

**Happy trading! Remember to always prioritize risk management and continuous learning.**

*Last Updated: July 2026*
