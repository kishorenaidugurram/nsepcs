# NSE Stock Scanner - Complete Setup Guide

## 📦 What You Have

This repository contains a production-ready stock scanner system for finding trading opportunities in NSE F&O stocks. It consists of:

### Scripts
1. **`simple_scanner.py`** - Main scanner (no complex dependencies)
2. **`telegram_scanner.py`** - Advanced scanner with full feature set
3. **`streamlit_app.py`** - Web UI (requires streamlit, optional)
4. **`run_scanner.sh`** - Bash wrapper for easy execution

### Documentation
1. **`SCANNER_INSTRUCTIONS.md`** - Complete usage guide
2. **`TELEGRAM_SETUP.md`** - Telegram integration setup
3. **`README.md`** - Project overview
4. **`SETUP.md`** - This file

---

## ⚡ Quick Start (2 minutes)

### Step 1: Install Dependencies
```bash
cd /home/user/nsepcs
pip install pandas numpy yfinance openpyxl -q
```

### Step 2: Run Scanner (Excel Only)
```bash
python3 simple_scanner.py --stocks 100 --strength 65 --no-telegram
```

### Step 3: Check Results
```bash
# View generated Excel file
ls -lh stock_scan_results_*.xlsx
```

✅ **Done!** Your first scan results are ready in Excel.

---

## 📱 Full Setup with Telegram (5 minutes)

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose name and username
4. **Copy the Bot Token** (looks like: `123456:ABCDEFghij...`)

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Send any message
3. **Copy your User ID** from the reply

### Step 3: Set Environment Variables

```bash
# Temporary (for current session)
export TELEGRAM_BOT_TOKEN='paste_token_here'
export TELEGRAM_CHAT_ID='paste_id_here'

# Permanent (for future sessions - Linux/Mac)
echo "export TELEGRAM_BOT_TOKEN='paste_token_here'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='paste_id_here'" >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Test Connection

```bash
# Verify credentials are set
echo "Bot Token: $TELEGRAM_BOT_TOKEN"
echo "Chat ID: $TELEGRAM_CHAT_ID"

# Run scanner with Telegram
python3 simple_scanner.py --stocks 50 --strength 65
```

✅ **Done!** You should receive Telegram results + Excel file.

---

## 🔄 Automated Daily Scans

### Option 1: Cron Job (Recommended)

**Add this to crontab** (runs 3:30 PM daily, market close):

```bash
crontab -e
```

Then add:
```
30 15 * * 1-5 cd /home/user/nsepcs && python3 simple_scanner.py --stocks 100 --strength 65
```

**For Telegram notifications**, include credentials:
```
30 15 * * 1-5 cd /home/user/nsepcs && export TELEGRAM_BOT_TOKEN='your_token' && export TELEGRAM_CHAT_ID='your_id' && python3 simple_scanner.py --stocks 100 --strength 65
```

### Option 2: Using the Wrapper Script

```bash
# Make script executable
chmod +x run_scanner.sh

# Run it anytime
./run_scanner.sh

# Or add to cron
30 15 * * 1-5 /home/user/nsepcs/run_scanner.sh
```

---

## 🎯 Usage Patterns

### Pattern 1: Daily Market Close Review
```bash
python3 simple_scanner.py --stocks 100 --strength 70
```
- Run: 3:30 PM daily
- Results: 5-15 stocks usually
- Action: Review top candidates for next day

### Pattern 2: Aggressive Opportunity Hunt
```bash
python3 simple_scanner.py --stocks 208 --strength 50
```
- Run: Weekly (Friday EOD)
- Results: 30-50 stocks usually
- Action: Detailed analysis of top 10

### Pattern 3: Conservative High-Confidence Trades
```bash
python3 simple_scanner.py --stocks 150 --strength 80
```
- Run: As needed
- Results: 3-8 stocks usually
- Action: High-probability entry points only

### Pattern 4: Intraday Quick Check
```bash
python3 simple_scanner.py --stocks 50 --strength 65
```
- Run: Multiple times daily
- Results: 2-5 stocks usually
- Action: Quick validation of setups

---

## 📊 File Structure

```
/home/user/nsepcs/
├── simple_scanner.py              # Main scanner (no complex deps)
├── telegram_scanner.py             # Advanced scanner
├── streamlit_app.py                # Web UI (optional)
├── run_scanner.sh                  # Bash wrapper script
│
├── SETUP.md                        # This file
├── SCANNER_INSTRUCTIONS.md         # Complete usage guide
├── TELEGRAM_SETUP.md               # Telegram setup details
├── README.md                       # Project overview
│
├── stock_scan_results_*.xlsx       # Generated Excel files
└── requirements.txt                # Python dependencies
```

---

## 🔧 Customization

### Change Filter Thresholds

Edit `simple_scanner.py`, find `run_scan()` method:

```python
filters = {
    'rsi_min': 25,              # More oversold stocks
    'rsi_max': 80,              # Less overbought
    'min_volume_ratio': 1.0,    # Lower volume threshold
    'min_strength': min_strength
}
```

### Add More Stocks to Universe

The default is first 100 of 208 F&O stocks. Modify:
```python
python3 simple_scanner.py --stocks 208  # Scan all F&O stocks
```

### Change Output Directory

Modify `simple_scanner.py`:
```python
filename = f"/custom/path/stock_scan_results_{timestamp}.xlsx"
```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install pandas numpy yfinance openpyxl`
- [ ] Simple scanner runs: `python3 simple_scanner.py --stocks 10 --strength 50`
- [ ] Excel file generated: `stock_scan_results_*.xlsx`
- [ ] (Optional) Telegram bot created with token
- [ ] (Optional) Telegram chat ID obtained
- [ ] (Optional) Environment variables set: `$TELEGRAM_BOT_TOKEN`, `$TELEGRAM_CHAT_ID`
- [ ] (Optional) Telegram test: `python3 simple_scanner.py --stocks 10 --strength 50`
- [ ] (Optional) Cron job added: `crontab -e`

---

## 🚨 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'pandas'"
```bash
pip install pandas numpy yfinance openpyxl
```

### Issue: "No stocks found"
- Lower the `--strength` value: `--strength 50`
- Increase stocks to scan: `--stocks 150`
- Check if markets are open

### Issue: "Telegram message failed"
1. Verify bot token is correct
2. Verify chat ID is correct
3. Make sure bot is in your Telegram account
4. Check internet connection

### Issue: "Failed to fetch data"
- Check internet connection
- Verify NSE markets are open (9:15 AM - 3:30 PM IST)
- Retry after a few minutes

### Issue: Cron job not running
```bash
# Check cron logs
grep CRON /var/log/syslog

# Verify crontab entry
crontab -l

# Make sure script has execute permissions
chmod +x run_scanner.sh
```

---

## 📚 Learning Resources

### Technical Analysis
- RSI Indicator: https://www.investopedia.com/terms/r/rsi.asp
- Moving Averages: https://www.investopedia.com/terms/m/movingaverage.asp
- Volume Analysis: https://www.investopedia.com/terms/v/volume.asp

### NSE Information
- NSE Official: https://www.nseindia.com
- F&O Resources: https://www.nseindia.com/products/fo_sp_index_nifty.htm
- Trading Hours: 9:15 AM - 3:30 PM IST (Mon-Fri)

### Python Libraries
- yfinance: https://github.com/ranaroussi/yfinance
- pandas: https://pandas.pydata.org/docs/
- openpyxl: https://openpyxl.readthedocs.io/

---

## 📝 Support & Debugging

### Get Detailed Logs
```bash
# Run with verbose output
python3 -u simple_scanner.py --stocks 20 --strength 65 2>&1 | tee scan.log
```

### Test Individual Components
```python
# Test in Python shell
python3
>>> from simple_scanner import SimpleStockScanner
>>> scanner = SimpleStockScanner()
>>> data = scanner.get_stock_data('TCS.NS', period='3mo')
>>> print(data.tail())
```

### Check Network Connectivity
```bash
# Test internet
ping google.com

# Test Yahoo Finance API
curl -s -o /dev/null -w "%{http_code}" https://query2.finance.yahoo.com/
```

---

## 🎓 Next Steps

1. **Read**: `SCANNER_INSTRUCTIONS.md` for detailed usage
2. **Setup**: Follow Telegram setup in `TELEGRAM_SETUP.md`
3. **Run**: First scan with `python3 simple_scanner.py`
4. **Schedule**: Add to crontab for automation
5. **Monitor**: Review Excel results regularly
6. **Optimize**: Adjust filters based on your trading style

---

## 📊 Expected Results

### Scanner Output (Typical)
```
🚀 Starting scan of 100 stocks
Time: 15:30 IST
Pattern Strength: 65%+

✅ Found: RELIANCE - Strength: 78%
✅ Found: TCS - Strength: 72%
✅ Found: ICICIBANK - Strength: 75%
...

✅ SCAN COMPLETE - Found 12 stocks
📊 Results exported to: stock_scan_results_20260929_153045.xlsx
```

### Excel Output (Sample Row)
```
Symbol  | Price  | RSI  | SMA_20 | SMA_50 | Volume | Strength | Date       | Change_5d
--------|--------|------|--------|--------|--------|----------|------------|----------
TCS     | 3850.5 | 52.3 | 3820   | 3750   | 1.8x   | 78%      | 2026-09-29 | +2.1%
```

### Telegram Message (Sample)
```
✅ NSE Stock Scanner Results
Time: 15:30 IST
Stocks Found: 12

Top Candidates:
• TCS: ₹3,850.50 | Str:78% | RSI:52 | Vol:1.8x
• RELIANCE: ₹2,450.00 | Str:77% | RSI:54 | Vol:1.6x
• ICICIBANK: ₹1,080.25 | Str:75% | RSI:51 | Vol:1.9x
...

📊 See Excel file for complete analysis
```

---

## ⚖️ Risk Disclaimer

This tool is **for educational purposes only** and provides **no guarantees**:

- Past performance ≠ Future results
- Technical patterns ≠ Certain outcomes
- Always use stop losses
- Never risk more than you can afford to lose
- Consult qualified financial advisors
- Paper trade first before live trading

---

## 🎉 You're Ready!

Your stock scanner is now set up and ready to use. Start with:

```bash
python3 simple_scanner.py --stocks 50 --strength 65 --no-telegram
```

Check your Excel results and happy trading! 📈

---

**Questions?** See the documentation files:
- `SCANNER_INSTRUCTIONS.md` - Full usage guide
- `TELEGRAM_SETUP.md` - Telegram configuration
- `README.md` - Project overview

**Happy Trading! Trade Smart. Trade Safe. Trade Profitably.** 🚀
