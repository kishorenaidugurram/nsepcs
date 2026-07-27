# NSE F&O PCS Screener - Automated Task Status

## 🚨 Issue Report

**Status**: ⚠️ Blocked by Network Policy

### Problem
The automated PCS screener script was configured to run and send results to Telegram, but encountered a network connectivity issue:

- **Blocker**: The proxy environment is blocking connections to Yahoo Finance API (`fc.yahoo.com:443`)
- **Error**: Gateway responded with 403 (policy denial or upstream failure)
- **Impact**: Cannot fetch live stock market data needed for the screening analysis

### Proxy Policy Details
- **Service**: Agent Proxy (HTTPS_PROXY at port 45239)
- **Blocked Host**: fc.yahoo.com:443 (Yahoo Finance)
- **Restriction**: This appears to be a security policy preventing external financial data access

## ✅ What Was Set Up

### 1. **Screener Scripts Created**
   - `/home/user/nsepcs/run_screener.py` - Complex version using the full Streamlit app logic
   - `/home/user/nsepcs/simple_screener.py` - Simplified version for basic scanning

### 2. **Screening Logic**
The screener analyzes NSE F&O stocks using these filter criteria:
   - **Pattern Strength**: Minimum 65% (for breakout/support detection)
   - **RSI**: 30-75 range (momentum indicators)
   - **ADX**: Minimum 20 (trend strength)
   - **Volume**: At least 1.2x average volume
   - **Stocks Analyzed**: 450 F&O universe stocks

### 3. **Output Format**
Results are formatted as:
```
📊 NSE F&O PCS Screener Results
Date: DD-MM-YYYY HH:MM IST
Stocks Found: N

1. SYMBOL - ₹PRICE
   Strength: XX% (Confidence Level)
   RSI: XX | ADX: XX
   Vol Ratio: XX x
```

## 🔧 Scheduled Task Configuration

**Task**: Run screener and send results to Telegram
**Trigger**: `/scheduled_task` (automated)
**Frequency**: Can be set via cron

### Current Telegram Integration Status
⚠️ **Not Configured Yet** - No Telegram bot token or chat ID found
- Would require: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars
- Alternative: Using PushNotification tool to send results to user

## 🛠️ To Enable This Screener

### Option 1: Allow Yahoo Finance Access (Preferred)
Contact your administrator to whitelist:
- Host: `fc.yahoo.com` (Yahoo Finance API)
- Host: `query.yahooapis.com` (Yahoo APIs)
- This is needed for real-time stock data

### Option 2: Use Alternative Data Source
Modify the screener to use:
- NSE official APIs
- Alternative financial data providers
- Local cached data feeds

### Option 3: Set Up Telegram Integration
1. Create a Telegram bot via @BotFather
2. Get your chat ID
3. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
   export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
   ```
4. Modify script to include Telegram sender

## 📝 Manual Testing

To test the screener once network access is restored:

```bash
# Test the simplified screener
python3 simple_screener.py

# Or run with a subset (faster)
python3 simple_screener.py --max-stocks 50
```

Expected output:
- Progress bar showing stock scanning
- Found stocks listed with analysis metrics
- Results saved to `/tmp/screener_results.json`

## 📊 Sample Output (When Running)
```
🚀 Scanning 450 stocks for PCS opportunities...

[  1/450] RELIANCE        ✅ Strength: 78% | HIGH
[  2/450] TCS             ✅ Strength: 72% | MEDIUM
[  3/450] HDFCBANK        ✅ Strength: 85% | HIGH
...

✅ Found 23 stocks meeting PCS filter criteria!

TOP RESULTS:
  RELIANCE      | ₹2,850.50 | Strength:   78% | HIGH   | RSI:  52.3 | ADX:  28.4
  HDFCBANK      | ₹1,620.25 | Strength:   85% | HIGH   | RSI:  48.7 | ADX:  32.1
  ...
```

## 🔄 Next Steps

1. **Resolve Network Blocker**: Contact admin to enable Yahoo Finance access
2. **Test Connection**: Once enabled, run `python3 simple_screener.py` 
3. **Configure Telegram**: Set up Telegram bot if needed (optional)
4. **Schedule Task**: Use cron to run screener on a schedule:
   ```bash
   # Daily at 3:30 PM IST (after market close)
   30 15 * * 1-5 cd /home/user/nsepcs && python3 simple_screener.py
   ```

## 📞 Troubleshooting

**Q: Can I use the Streamlit app instead?**
A: Yes, the Streamlit app works in browser and can also be deployed to the cloud.

**Q: How long does a full scan take?**
A: ~5-10 minutes for 450 stocks with good network connectivity.

**Q: Can I test with a smaller subset?**
A: Yes, modify the script to scan only top 50-100 stocks for faster results.

---

**Created**: 2026-07-27 03:45 IST
**Status**: Ready to run (pending network access)
**Task Type**: Automated stock screening and notification
