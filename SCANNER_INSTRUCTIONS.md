# NSE Stock Scanner - Complete Usage Guide

## 📋 Overview

This is a professional-grade stock scanner for finding NSE F&O stocks meeting specific technical criteria. It analyzes stocks for:
- RSI positioning
- Volume confirmation
- Moving average support
- Pattern strength scoring
- Market sentiment

Results are exported to Excel and optionally sent to your Telegram.

---

## 🚀 Quick Start

### 1. Install Dependencies (First Time Only)

```bash
cd /home/user/nsepcs
pip install pandas numpy yfinance openpyxl -q
```

### 2. Set Telegram Credentials (Optional)

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

See **TELEGRAM_SETUP.md** for detailed Telegram setup instructions.

### 3. Run the Scanner

**Simple usage (Excel export only):**
```bash
python3 simple_scanner.py --stocks 100 --strength 65 --no-telegram
```

**With Telegram:**
```bash
python3 simple_scanner.py --stocks 100 --strength 65
```

**Using the wrapper script:**
```bash
bash run_scanner.sh
```

---

## ⚙️ Command-Line Options

```bash
python3 simple_scanner.py [OPTIONS]

Options:
  --stocks NUM        Number of stocks to scan (default: 100)
  --strength NUM      Minimum pattern strength 0-100 (default: 65)
  --no-telegram       Skip Telegram, save to Excel only
```

### Examples

```bash
# Scan all 208 F&O stocks with high confidence
python3 simple_scanner.py --stocks 208 --strength 75

# Quick scan of first 50 stocks
python3 simple_scanner.py --stocks 50 --strength 60

# Conservative scan (fewer false positives)
python3 simple_scanner.py --stocks 100 --strength 80
```

---

## 📊 Output

The scanner generates:

### 1. Excel File
**Filename:** `stock_scan_results_YYYYMMDD_HHMMSS.xlsx`

**Columns:**
- **Symbol**: Stock ticker (without .NS)
- **Price**: Current closing price (₹)
- **RSI**: Relative Strength Index (0-100)
- **SMA_20**: Simple Moving Average 20-day
- **SMA_50**: Simple Moving Average 50-day
- **Volume**: Volume ratio vs. 20-day average
- **Strength**: Pattern strength score (0-100)
- **Date**: Analysis date
- **Change_5d**: 5-day price change (%)

### 2. Telegram Message (if enabled)
- Summary of stocks found
- Top 10 candidates by strength
- Quick metrics (price, RSI, volume)

### 3. Console Output
- Real-time progress updates
- Summary statistics
- File location

---

## 📈 Filter Criteria Explained

### RSI (Relative Strength Index)
- **Range**: 30-75
- **Interpretation**:
  - RSI < 30: Oversold (potential bounce)
  - RSI 30-70: Normal trading zone
  - RSI > 70: Overbought (potential pullback)
- **Sweet Spot**: 40-60 (adds 15 strength points)

### Volume Ratio
- **Minimum**: 1.2x (20% above 20-day average)
- **Good**: 1.5x+ (adds 10+ strength points)
- **Strong**: 2.0x+ (adds 20 strength points)
- **Excellent**: 3.0x+ (high institutional interest)

### Pattern Strength
- **50-64**: Low confidence (early reversal signals)
- **65-79**: Medium confidence (developing patterns)
- **80-100**: High confidence (confirmed patterns)

### Moving Averages
- Price must be > SMA_20 (short-term support)
- Price must be > SMA_50 (intermediate support)
- Helps filter for uptrending stocks

---

## 🎯 Recommended Scan Strategies

### Strategy 1: High Probability (Conservative)
```bash
python3 simple_scanner.py --stocks 100 --strength 75
```
- Fewer results, but higher quality
- Better for risk-averse traders
- Longer holding periods

### Strategy 2: Active Swing Trading (Moderate)
```bash
python3 simple_scanner.py --stocks 150 --strength 65
```
- Balanced approach
- Good for daily active trading
- Moderate risk-reward

### Strategy 3: Opportunity Hunting (Aggressive)
```bash
python3 simple_scanner.py --stocks 208 --strength 50
```
- More stocks, more variety
- May include early signals
- Requires active monitoring

### Strategy 4: Quick Scan (5 min review)
```bash
python3 simple_scanner.py --stocks 50 --strength 70
```
- Fast results
- Best for end-of-day reviews
- Market-close confirmation

---

## 🔄 Scheduled Execution

### For Daily Scans (Market Close)

**Add to crontab:**
```bash
# 3:30 PM daily (market close) on trading days (Mon-Fri)
30 15 * * 1-5 cd /home/user/nsepcs && TELEGRAM_BOT_TOKEN='token' TELEGRAM_CHAT_ID='id' python3 simple_scanner.py --stocks 100 --strength 65
```

**Edit crontab:**
```bash
crontab -e
```

### For Weekly Scans

```bash
# Every Friday at 3:35 PM
35 15 * * 5 cd /home/user/nsepcs && python3 simple_scanner.py --stocks 208 --strength 70
```

### For Continuous Monitoring (Every 4 hours)

```bash
# Every 4 hours during market hours (9:00 AM - 3:30 PM)
0 9,13 * * 1-5 cd /home/user/nsepcs && python3 simple_scanner.py --stocks 50 --strength 70
```

---

## 🔧 Customization

### Modify Filter Thresholds

Edit `simple_scanner.py`, find the `run_scan()` method:

```python
def run_scan(self, num_stocks=100, min_strength=65):
    filters = {
        'rsi_min': 30,      # Change RSI minimum
        'rsi_max': 75,      # Change RSI maximum
        'min_volume_ratio': 1.2,  # Change volume threshold
        'min_strength': min_strength
    }
```

### Add Custom Indicators

The scanner uses:
1. RSI (14-period)
2. SMA 20/50
3. Volume analysis
4. Price momentum

To add more indicators (MACD, Bollinger Bands, etc.), modify the `scan_stock()` method.

---

## 📱 Telegram Integration

### Benefits
- Real-time notifications
- Quick access to results
- Set-and-forget automation
- Mobile-friendly format

### Setup (5 minutes)

1. **Create Bot** - Chat @BotFather on Telegram
   - Command: `/newbot`
   - Note the Bot Token

2. **Get Chat ID** - Chat @userinfobot on Telegram
   - It replies with your User ID

3. **Set Environment Variables**
   ```bash
   export TELEGRAM_BOT_TOKEN='your_token'
   export TELEGRAM_CHAT_ID='your_id'
   ```

4. **Test Connection**
   ```bash
   python3 simple_scanner.py --stocks 10 --strength 60
   ```

---

## 🐛 Troubleshooting

### "No stocks found"
- **Cause**: Filters too strict
- **Solution**: Lower `--strength` to 60 or 55
- **Alternative**: Increase `--stocks` to 150+

### "ModuleNotFoundError"
- **Cause**: Missing dependencies
- **Solution**: 
  ```bash
  pip install pandas numpy yfinance openpyxl
  ```

### "Failed to fetch data"
- **Cause**: Network issue or market closed
- **Solution**:
  - Check internet connection
  - Run during market hours (9:15 AM - 3:30 PM IST)
  - Check if NSE is open

### "Telegram message failed"
- **Cause**: Invalid token/chat ID
- **Solution**:
  - Verify token and chat ID
  - Test bot with: `python3 -c "import requests; requests.post(f'https://api.telegram.org/bot{TOKEN}/getMe')"`
  - Make sure bot hasn't been blocked

### "Excel file not generated"
- **Cause**: No stocks met criteria
- **Solution**: Reduce `--strength` value
- **Check**: Console output for details

---

## 📊 Interpreting Results

### Example Result Row:

```
RELIANCE: ₹2,450.50 | RSI: 52.3 | SMA: 2440/2380 | Vol: 1.8x | Str: 78% | +2.1%
```

**Analysis:**
- RSI at 52.3 (sweet spot 40-60) ✅
- Price above both SMAs (support) ✅
- Volume 1.8x average (good) ✅
- Strength 78% (high confidence) ✅
- 5-day up 2.1% (positive momentum) ✅

**Trading Implication:** Strong buy signal with good setup

---

## ⚠️ Important Disclaimers

1. **Not Financial Advice**: This tool is for educational purposes only
2. **Past Performance**: Historical patterns don't guarantee future results
3. **Risk Management**: Always use stop losses and position sizing
4. **Paper Trading**: Test strategies before live trading
5. **Verify Data**: Double-check results before trading

---

## 📞 Support

### Common Issues
- See **Troubleshooting** section above
- Check **TELEGRAM_SETUP.md** for Telegram issues
- Review **README.md** for app overview

### For Developers
- Modify `simple_scanner.py` for custom indicators
- Extend `telegram_scanner.py` for advanced features
- Add your own data sources to `get_stock_data()`

### Learning Resources
- Technical Analysis: https://en.wikipedia.org/wiki/Technical_analysis
- RSI Guide: https://www.investopedia.com/terms/r/rsi.asp
- NSE Info: https://www.nseindia.com

---

## 🎓 Next Steps

1. **Set up Telegram** (5 minutes)
2. **Run first scan** (2 minutes)
3. **Review Excel results** (5 minutes)
4. **Schedule automation** (5 minutes)
5. **Monitor and refine** (ongoing)

**Total setup time: ~20 minutes**

---

## 📝 Version History

- **v1.0** (Current): Initial release
  - Stocks: 208 NSE F&O
  - Indicators: RSI, SMA, Volume
  - Export: Excel, Telegram
  - Threading: 5 parallel scans

---

**Happy Trading! 📈**

Remember: Trade Smart. Trade Safe. Trade Profitably.
