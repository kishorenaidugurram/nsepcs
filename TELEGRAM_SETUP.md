# NSE F&O PCS Scanner - Telegram Automation Setup

This guide explains how to set up automated stock scanning with Telegram notifications.

## 🚀 Quick Start

The scanner has two modes:

### 1. **Online Mode** (with live market data)
- Requires: Network access to Yahoo Finance
- Script: `telegram_scanner.py`
- Status: Currently blocked by environment proxy policy
- Feature: Real-time technical analysis with actual market data

### 2. **Offline Mode** (with demonstration data)
- Requires: No external network access
- Script: `offline_scanner.py`
- Status: ✅ Fully functional
- Feature: Pattern matching and stock analysis ready for extension

## 📱 Setting Up Telegram Notifications

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a conversation and send `/newbot`
3. Follow the prompts to create a new bot
4. **Save your Bot Token** (e.g., `123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefg`)

### Step 2: Get Your Chat ID

1. Search for `@getmyid_bot` on Telegram
2. Start the bot and it will show your Chat ID (e.g., `987654321`)
3. **Save your Chat ID**

### Step 3: Configure Environment Variables

#### Option A: Set Permanently (Recommended for Cron Jobs)

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

Then reload:
```bash
source ~/.bashrc
```

#### Option B: Set for Current Session Only

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
python3 offline_scanner.py
```

#### Option C: Create a .env File

Create `.telegram.env` in the project root:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then run with:
```bash
source .telegram.env && python3 offline_scanner.py
```

## 🔄 Running the Scanner

### Manual Execution

```bash
# Run offline scanner (works without network access)
python3 offline_scanner.py

# Run online scanner (requires Yahoo Finance access)
python3 telegram_scanner.py
```

### Automated Execution (Cron)

#### Option 1: Daily at 4 PM IST

```bash
0 16 * * * cd /home/user/nsepcs && python3 offline_scanner.py >> /var/log/pcs_scanner.log 2>&1
```

#### Option 2: Every 4 hours

```bash
0 */4 * * * cd /home/user/nsepcs && python3 offline_scanner.py >> /var/log/pcs_scanner.log 2>&1
```

#### Option 3: Weekdays at Market Close (3:30 PM IST)

```bash
30 15 * * 1-5 cd /home/user/nsepcs && python3 offline_scanner.py >> /var/log/pcs_scanner.log 2>&1
```

To edit crontab:
```bash
crontab -e
```

## 📊 Output Files

The scanner generates:

1. **Telegram Message** - Sent to your Telegram chat with:
   - Top 10 stocks with highest pattern strength
   - Price, RSI, ADX indicators
   - Pattern types and confidence levels
   - Link to full analysis

2. **CSV File** - Saved with timestamp:
   - Location: `/tmp/claude-0/-home-user-nsepcs/scratchpad/pcs_scan_YYYYMMDD_HHMMSS.csv`
   - Contains all stocks found with pattern data
   - Ready for import to Excel/Google Sheets

## 🔧 Extending the Scanner

### Adding Live Data Integration

When network access becomes available:

1. Run `python3 telegram_scanner.py` instead
2. The script will fetch real market data from Yahoo Finance
3. Results will be based on actual technical indicators

### Customizing Filter Criteria

Edit the `get_default_config()` method in `offline_scanner.py`:

```python
def get_default_config(self):
    return {
        'rsi_min': 30,        # Minimum RSI (default: 30)
        'rsi_max': 75,        # Maximum RSI (default: 75)
        'adx_min': 20,        # Minimum ADX (default: 20)
        'pattern_strength_min': 65,  # Minimum pattern strength (default: 65%)
        ...
    }
```

### Adding Custom Patterns

Add new patterns to `PATTERNS` list in `offline_scanner.py`:

```python
PATTERNS = [
    'Current Day EOD Breakout',
    'Your Custom Pattern',
    ...
]
```

## 📈 Understanding Results

### Confidence Levels

- **HIGH** (🎯): Strength 85%+ - High probability pattern
- **MEDIUM** (🟡): Strength 70-84% - Moderate probability
- **LOW** (🔴): Strength <70% - Use with caution

### Technical Indicators

- **RSI (Relative Strength Index)**
  - 30-50: Weak momentum
  - 50-70: Moderate strength
  - 70-75: Strong momentum

- **ADX (Average Directional Index)**
  - <20: Weak trend
  - 20-40: Medium trend strength
  - >40: Strong trend

## ⚠️ Important Notes

1. **Demo Data**: The offline scanner uses demonstration data
   - Perfect for testing and setup
   - Not suitable for live trading decisions
   - Upgrade to online mode with real data when network access is available

2. **Risk Management**: Always
   - Verify signals with additional analysis
   - Use proper position sizing (max 2% per trade)
   - Implement stop losses
   - Never trade on scanner signals alone

3. **Testing**: 
   - Always paper trade first
   - Validate patterns on live charts
   - Use scanner as a screening tool only

## 🐛 Troubleshooting

### Telegram Message Not Sent

```bash
# Check if credentials are set
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Test with a simple message
python3 -c "
import requests
token = 'YOUR_BOT_TOKEN'
chat_id = 'YOUR_CHAT_ID'
url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {'chat_id': chat_id, 'text': 'Test message'}
r = requests.post(url, data=data)
print(r.status_code, r.text)
"
```

### Scanner Not Running in Cron

```bash
# Check cron logs
grep CRON /var/log/syslog

# Run with explicit paths
0 16 * * * /usr/bin/python3 /home/user/nsepcs/offline_scanner.py
```

### Missing Dependencies

```bash
# Reinstall required packages
pip install -r requirements.txt requests pandas numpy pytz
```

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the main README.md for more details
3. Check script output for specific error messages
4. Verify Telegram bot configuration

## 🎯 Next Steps

1. ✅ Get Telegram credentials
2. ✅ Set environment variables
3. ✅ Test the scanner manually
4. ✅ Set up cron job for automation
5. ✅ Monitor results in Telegram

Happy trading! 📈
