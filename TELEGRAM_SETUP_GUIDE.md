# NSE F&O PCS Scanner - Telegram Integration Setup Guide

## 📋 Overview

This guide explains how to set up the NSE F&O PCS Scanner to automatically run and send results to Telegram.

## 🔧 Prerequisites

### 1. Telegram Bot Setup

#### Step 1: Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/start` command
3. Send `/newbot` command
4. Follow the prompts to create a new bot
5. **Save the Bot Token** (looks like: `123456789:ABCDefGHijKlmnoPQRStUvwXYZ`)

#### Step 2: Get Your Chat ID
1. Search for `@userinfobot` in Telegram
2. Send `/start` command
3. The bot will reply with your User ID (looks like: `123456789`)

### 2. Environment Configuration

Set the Telegram credentials as environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**For Permanent Setup** (add to `~/.bashrc` or `~/.zshrc`):
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_bot_token_here"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id_here"' >> ~/.bashrc
source ~/.bashrc
```

## 🚀 Running the Scanner

### Option 1: Manual Run (Immediate)

```bash
cd /home/user/nsepcs
python3 run_scan_and_telegram_simple.py
```

### Option 2: Scheduled Run (Cron Job)

#### Set up a cron job to run daily at 9:00 AM IST:

```bash
crontab -e
```

Add this line:
```
0 3 * * * cd /home/user/nsepcs && python3 run_scan_and_telegram_simple.py >> /var/log/nsepcs_scan.log 2>&1
```

**Note**: 3:00 UTC = 8:30 AM IST. Adjust time as needed.

## ⚙️ Filter Configuration

The scanner uses these default filters (customizable in the code):

| Filter | Default | Description |
|--------|---------|-------------|
| RSI Min | 30 | Minimum RSI value (oversold threshold) |
| RSI Max | 75 | Maximum RSI value (overbought threshold) |
| ADX Min | 20 | Minimum ADX (trend strength) |
| Lookback | 20 days | Period for technical analysis |

### Customize Filters

Edit `run_scan_and_telegram_simple.py` and modify the `run_simple_scan()` function call:

```python
results = run_simple_scan(
    stocks_to_scan=NSE_FO_STOCKS[:30],  # Number of stocks to scan
    rsi_min=35,  # Adjust RSI minimum
    rsi_max=70,  # Adjust RSI maximum
    adx_min=25   # Adjust ADX minimum
)
```

## 📊 Available Stock Lists

The scanner can analyze different stock universes:

### Pre-configured in script:
- **NSE_FO_STOCKS**: 30+ highly liquid F&O stocks (default)

### From main app (requires Streamlit):
- **COMPLETE_NSE_FO_UNIVERSE**: 219 NSE F&O stocks
- **NSE Non-F&O Stocks**: 800+ liquid NSE stocks

## 🔍 Understanding Telegram Output

The bot sends results in this format:

```
📊 NSE F&O PCS Scan Results
2026-09-12 14:30 IST

✅ Stocks Found: 5
RSI Range: 30-75
ADX Min: 20
────────────────────────────

1. RELIANCE
   ₹2,850.25 | RSI: 45.2 | ADX: 28.5

2. TCS
   ₹3,420.10 | RSI: 52.8 | ADX: 35.2

...

────────────────────────────
✅ Scan completed at 14:35 IST
Total matches: 5
```

## 🛠️ Troubleshooting

### Issue: "Telegram credentials not configured"

**Solution**: Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python3 run_scan_and_telegram_simple.py
```

### Issue: "No stocks found" (results empty)

**Possible Causes**:
1. Filters are too strict - loosen RSI or ADX ranges
2. Network issue accessing market data
3. Market closed or no matching patterns

**Solution**: 
- Adjust filter values
- Run during market hours
- Check network connectivity

### Issue: Message not arriving on Telegram

**Debugging Steps**:
1. Verify bot token: `python3 -c "import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"`
2. Verify chat ID: `python3 -c "import os; print(os.getenv('TELEGRAM_CHAT_ID'))"`
3. Check bot is not muted in Telegram
4. Verify bot has message permission

### Issue: "Failed building wheel for ta"

**Solution**: Use the simplified scanner:
```bash
python3 run_scan_and_telegram_simple.py  # Uses built-in indicators
```

## 📈 Advanced Features

### Custom Stock List

Edit `run_scan_and_telegram_simple.py`:

```python
CUSTOM_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'ITC.NS'
]

results = run_simple_scan(stocks_to_scan=CUSTOM_STOCKS)
```

### Multiple Telegram Channels

Create separate environment variables and scripts for each channel:

```bash
export TELEGRAM_BOT_TOKEN="token_1"
export TELEGRAM_CHAT_ID="channel_1_id"
python3 run_scan_and_telegram_simple.py

export TELEGRAM_BOT_TOKEN="token_2"
export TELEGRAM_CHAT_ID="channel_2_id"
python3 run_scan_and_telegram_simple.py
```

## 📚 Integration with Streamlit App

For full-featured analysis, use the Streamlit web interface:

```bash
streamlit run streamlit_app.py
```

The web interface provides:
- Advanced chart pattern detection
- Multi-timeframe analysis
- Support/Resistance identification
- Delivery volume analysis
- Enhanced technical indicators

## ⚠️ Important Notes

1. **Paper Trade First**: Always backtest strategies before live trading
2. **Risk Management**: Follow position sizing rules (max 2% per trade)
3. **Data Accuracy**: Verify results before trading decisions
4. **Market Hours**: Scanner works best during NSE trading hours (9:15 AM - 3:30 PM IST)
5. **Backups**: Keep historical scan results for reference

## 🔗 Useful Links

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [NSE F&O Stocks List](https://www.nseindia.com/)
- [Technical Analysis Guide](https://www.investopedia.com/terms/t/technicalanalysis.asp)

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review the scanner logs: `tail -f /var/log/nsepcs_scan.log`
3. Verify Telegram credentials are correctly set
4. Test scanner manually: `python3 run_scan_and_telegram_simple.py`

---

**Last Updated**: 2026-09-12
**Version**: 1.0
