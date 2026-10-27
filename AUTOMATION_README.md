# 🚀 NSE F&O PCS - Automated Analysis & Telegram Notifications

This repository now includes automated screening scripts to run PCS analysis and send results directly to your Telegram account.

## 📁 New Files Added

1. **`run_analysis.py`** - Main analysis script
   - Scans NSE F&O stocks for trading opportunities
   - Filters by pattern strength and confidence
   - Sends formatted results to Telegram
   - Saves results to CSV

2. **`telegram_notifier.py`** - Telegram messaging utility
   - Formats analysis results for Telegram
   - Sends messages to your configured account
   - Handles errors gracefully

3. **`run_scan.sh`** - Bash wrapper script
   - Easy-to-use shell wrapper
   - Environment setup helper

4. **`TELEGRAM_SETUP.md`** - Complete setup guide
   - Step-by-step Telegram bot configuration
   - Installation instructions
   - Scheduling examples (cron/systemd)
   - Troubleshooting tips

5. **`AUTOMATION_README.md`** - This file
   - Quick start guide
   - Architecture overview

## ⚡ Quick Start

### 1. Install Dependencies

```bash
cd /home/user/nsepcs
pip3 install -r requirements.txt
```

### 2. Get Telegram Credentials

Create a Telegram bot:
- Message [@BotFather](https://t.me/botfather) on Telegram
- Follow prompts to create bot
- Save your **Bot Token**

Get your chat ID:
- Message [@userinfobot](https://t.me/userinfobot)
- Save your **Chat ID**

### 3. Set Environment Variables

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

### 4. Run Analysis

```bash
python3 run_analysis.py
```

You'll receive results on Telegram automatically!

## 🔧 How It Works

```
┌─────────────────────────────┐
│ run_analysis.py             │
│ ├─ Loads NSE F&O universe   │
│ ├─ Scans each stock         │
│ │  ├─ Gets price data       │
│ │  ├─ Checks volume         │
│ │  ├─ Detects patterns      │
│ │  └─ Calculates confidence │
│ └─ Collects results         │
│    └─ Sends to Telegram     │
│    └─ Saves to CSV          │
└─────────────────────────────┘
```

### Filtering Criteria (Customizable)

- **Pattern Strength**: Minimum 70% (line 180 in run_analysis.py)
- **Pattern Types**: Current day breakout, cup & handle, double bottom, etc.
- **Technical Filters**:
  - RSI: 30-75
  - ADX: Minimum 20
  - Volume: At least 1.2x average

### Output Example

Your Telegram will receive:

```
📊 PCS Analysis Results

Scanned: 219 stocks
Found: 12 stocks

🟢 HIGH Confidence
• RELIANCE   - 92% | ₹2850.50 | RSI: 65
• TCS        - 88% | ₹3450.25 | RSI: 62
  ... and 2 more

🟡 MEDIUM Confidence
• HDFCBANK   - 76%
  ... and 7 more

━━━━━━━━━━━━━━━━━━━━━
View full analysis: [Link]
```

## 📅 Automated Scheduling

### Option 1: Cron (Easiest)

```bash
# Edit crontab
crontab -e

# Add this line for daily 3:30 PM scan
30 15 * * * export TELEGRAM_BOT_TOKEN='token'; export TELEGRAM_CHAT_ID='id'; cd /home/user/nsepcs && python3 run_analysis.py
```

### Option 2: Systemd Timer (More Reliable)

See `TELEGRAM_SETUP.md` for complete systemd setup.

### Option 3: Cloud Scheduler

Use any cloud platform's scheduled tasks:
- GitHub Actions (`.github/workflows/pcs-scan.yml`)
- AWS Lambda
- Google Cloud Scheduler
- Azure Logic Apps

## 🎨 Customization

### Change Filter Criteria

Edit `run_analysis.py` around line 180:

```python
results, total_scanned = run_analysis(
    min_pattern_strength=70,      # Higher = fewer, better quality stocks
    max_stocks=None,               # None = all stocks, or limit (e.g., 50)
    focus_high_confidence=False    # True = only highest confidence
)
```

### Change Analysis Parameters

Edit the `config` dictionary in `run_analysis.py` to adjust:
- RSI ranges
- ADX minimum
- Moving average support
- Pattern types to detect
- And more!

### Change Telegram Message Format

Edit `format_telegram_message()` in `telegram_notifier.py`:
- Add more fields
- Change emoji
- Add charts
- Add links

## 🐛 Troubleshooting

### "ModuleNotFoundError" errors

Install all dependencies:
```bash
pip3 install pandas numpy yfinance ta requests streamlit scipy scikit-learn beautifulsoup4 openpyxl matplotlib plotly pytz python-dateutil
```

### "Telegram connection failed"

1. Verify token is correct
2. Check internet connection
3. Ensure you messaged the bot first
4. Verify chat ID is correct

### Script runs too slow

Reduce stocks scanned:
```python
results, total_scanned = run_analysis(
    max_stocks=50,                    # Only scan first 50
    focus_high_confidence=True        # Only HIGH confidence
)
```

### Missing results

Check:
- Stock data available for that date
- No market holidays
- Minimum pattern strength not too high

## 📊 Result Files

After each run, results are saved to:
```
/tmp/pcs_results/stocks_YYYYMMDD_HHMMSS.csv
```

View latest results:
```bash
ls -ltr /tmp/pcs_results/ | tail -1
cat /tmp/pcs_results/stocks_*.csv | tail -10
```

## 🔒 Security Notes

1. **Never commit bot tokens** to git
2. Use environment variables for credentials
3. Keep systemd service file in `/etc/systemd/system` (not world-readable)
4. Rotate bot tokens periodically
5. Monitor logs for unauthorized access

## 📈 Interpretation Guide

### Confidence Levels

- **🟢 HIGH** (85%+): Strong pattern, high probability
  - Use conservative strike selection
  - Good for aggressive traders

- **🟡 MEDIUM** (70-84%): Decent pattern, moderate probability
  - Use moderate strike selection
  - Good for balanced traders

- **🔴 LOW** (<70%): Weak pattern, lower probability
  - Use aggressive strike selection
  - Skip unless very bullish

### Pattern Strength

- **90%+**: Textbook pattern, very high probability
- **80-89%**: Clear pattern, high probability
- **70-79%**: Visible pattern, moderate probability
- **<70%**: Weak pattern, lower probability

## 🚦 Advanced Features

### Delivery Volume Analysis

Enable in `run_analysis.py` to check:
- Retail vs institutional participation
- Delivery percentage trends
- Volume concentration

### F&O Consolidation Detection

Identify when stocks consolidate near resistance:
- Breakout candidates
- High probability moves
- Optimal entry points

### Support & Resistance Analysis

Multi-timeframe S&R identification:
- Key support levels
- Resistance breakouts
- Support tests

## 📚 Integration Examples

### GitHub Actions

Create `.github/workflows/pcs-scan.yml`:
```yaml
name: PCS Daily Scan
on:
  schedule:
    - cron: '30 10 * * *'  # UTC time (3:30 PM IST)

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python3 run_analysis.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "run_analysis.py"]
```

## 💡 Tips & Tricks

1. **Test first**: Run manually before scheduling
2. **Monitor logs**: Keep logs to debug issues
3. **Adjust timing**: Run before market open (9:30 AM) or after close (3:30 PM)
4. **Weekend runs**: Useful for planning week ahead
5. **Multiple bots**: Create different bots for different strategies

## 📞 Support

For issues or questions:

1. Check logs: `cat /var/log/pcs_scan.log`
2. Run manually for errors: `python3 run_analysis.py`
3. Test Telegram: `python3 telegram_notifier.py`
4. See full setup guide: `cat TELEGRAM_SETUP.md`

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Set up Telegram bot
3. ✅ Run `python3 run_analysis.py` manually
4. ✅ Verify Telegram message received
5. ✅ Schedule with cron/systemd
6. ✅ Monitor logs for a few days
7. ✅ Adjust parameters as needed
8. ✅ Share feedback!

## 📝 License & Attribution

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
