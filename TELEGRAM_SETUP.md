# NSE Stock Screener - Telegram Integration

## 🎯 Overview

This project includes stock screening with automated Telegram notifications. Stocks are filtered based on technical indicators and results are sent directly to your Telegram account.

## 📦 What You Get

- **screener_final.py** - Production screener using live data
- **demo_screener.py** - Demo version with sample data
- **Technical Filters**:
  - RSI: 30-75 (momentum zone)
  - ADX: ≥ 20 (trend strength)
  - Price: ≥ 20-day EMA (uptrend)

## 🔧 Setup Instructions

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. Follow prompts to name your bot
4. **Copy the Bot Token** (looks like: `123456789:ABCDEFGHijklmnopqrstuvwxyz...`)

### Step 2: Get Your Chat ID

1. Send a message to your newly created bot
2. Open this URL in your browser (replace BOT_TOKEN):
   ```
   https://api.telegram.org/botBOT_TOKEN/getUpdates
   ```
3. Find the `"chat": {"id": XXXXXX}` section
4. **Copy the Chat ID number**

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install yfinance pandas numpy requests
```

### Step 4: Set Environment Variables

**On Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**On Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

**Or add to ~/.bashrc or ~/.zshrc for persistence:**
```bash
echo 'export TELEGRAM_BOT_TOKEN="your_token"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="your_chat_id"' >> ~/.bashrc
source ~/.bashrc
```

## 🚀 Running the Screener

### Demo Mode (Test with sample data)
```bash
python3 demo_screener.py
```

### Live Mode (Real data)
```bash
python3 screener_final.py
```

## 📊 What the Screener Does

1. **Scans** 34 major NSE F&O stocks
2. **Calculates** technical indicators (RSI, ADX, EMA)
3. **Filters** stocks meeting all criteria
4. **Sends** results to your Telegram
5. **Saves** JSON file for further analysis

## 💬 Example Telegram Message

```
🎯 NSE SCREENER - 2026-10-20 10:30
✅ Found: 8 stocks
📊 Filters: RSI 30-75 | ADX≥20 | Price≥EMA20

1. RELIANCE
   Price: ₹2945.50
   RSI: 65.2 | ADX: 28.5
   EMA20: ₹2920.30

[... more stocks ...]
```

## ⏰ Scheduling (Cron Job)

To run daily after market close (3:35 PM IST):

```bash
# Edit crontab
crontab -e

# Add this line (runs at 3:35 PM on weekdays)
35 15 * * 1-5 cd /home/user/nsepcs && python3 screener_final.py
```

## ❓ Troubleshooting

### Message not sending?
- Verify bot token: Send `/getMe` to bot in Telegram
- Check chat ID is correct
- Ensure environment variables are set: `echo $TELEGRAM_BOT_TOKEN`
- Test with demo mode first

### No stocks found?
- This is normal if market doesn't meet filters
- Try demo mode to verify functionality
- Check filter values in the script

### Import errors?
- Install dependencies: `pip install yfinance pandas requests`
- Use Python 3.7+

### Network issues?
- Check internet connection
- Verify firewall allows api.telegram.org

## 📝 Customization

Edit **screener_final.py** to change:

```python
# Line ~11: Change stock list
NSE_FO = ['RELIANCE', 'TCS', ...]

# Line ~182-184: Adjust filters
rsi_min, rsi_max = 30, 75  # Your RSI range
adx_min = 20               # Your ADX minimum
```

## 📈 Filters Explained

- **RSI 30-75**: Optimal momentum zone (not oversold/overbought)
- **ADX ≥ 20**: Strong trend confirmation (>20 indicates strong trend)
- **Price ≥ EMA20**: Above moving average (confirms uptrend)

## 🔐 Security

- ✅ No passwords stored in code
- ✅ Bot token in environment variable only
- ✅ No data sent to external servers (except Telegram API)
- ✅ Local calculations only

## 📊 Output Files

Each run generates:
- `results_YYYYMMDD_HHMM.json` - Stock data in JSON format
- Can be imported to Excel, databases, etc.

## 🎓 Technical Details

**Indicators Used:**
- **RSI**: Relative Strength Index (momentum)
- **ADX**: Average Directional Index (trend strength)
- **EMA**: Exponential Moving Average (trend direction)

**Calculation Period:** 20 days of price history
**Update Frequency:** Run daily after market close

---

**Need Help?** All scripts include error messages and guidance. Run them to see helpful output!

