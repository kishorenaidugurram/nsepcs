# Scheduled Scanner Status - 2026-08-04

## ❌ Issue: Network Policy Blocks Data Access

**Status**: Scanner created but **BLOCKED** by network policy

### Problem
The automated NSE F&O PCS scanner attempted to run but failed due to network restrictions:

- **Blocked Host**: `fc.yahoo.com:443` (Yahoo Finance API)
- **Reason**: Organization egress policy denies access
- **Impact**: Cannot fetch stock price data needed for scanning

### Scanner Status
✅ **Script Created**: `scanner_telegram.py`
- Standalone scanner without Streamlit UI
- Integrated Telegram notification support  
- Configured with default filter criteria for PCS trading
- Ready to run once network access is restored

### How to Fix

#### Option 1: Allowlist Yahoo Finance (Recommended)
Contact your network/proxy administrator to allowlist these Yahoo Finance endpoints:

```
fc.yahoo.com:443
query1.finance.yahoo.com:443
query2.finance.yahoo.com:443
```

Then run:
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
python3 scanner_telegram.py
```

#### Option 2: Use Alternative Data Source
Replace yfinance with a local data provider:
- NSE website direct download
- Alternative APIs (Finnhub, Alpha Vantage, etc.)
- Local CSV data files

#### Option 3: Run Streamlit App Directly
Use the Streamlit UI which may have different network handling:
```bash
streamlit run streamlit_app.py
```

### Setup Telegram Integration

To enable automated Telegram notifications:

1. **Create a Telegram Bot**:
   - Chat with [@BotFather](https://t.me/botfather) on Telegram
   - Create new bot, get the API token

2. **Get Your Chat ID**:
   - Chat with [@userinfobot](https://t.me/userinfobot)
   - Get your chat ID

3. **Configure Environment**:
   ```bash
   export TELEGRAM_BOT_TOKEN='123456:ABC-DEF...'
   export TELEGRAM_CHAT_ID='987654321'
   ```

4. **Add to Cron/Scheduled Task**:
   ```cron
   # Run daily at 9 AM IST
   0 3 * * * cd /home/user/nsepcs && python3 scanner_telegram.py
   ```

### Scanner Configuration

Default filter settings (in `scanner_telegram.py`):
- **Stocks to Scan**: 50 (first 50 F&O stocks)
- **RSI Range**: 30-70
- **ADX Minimum**: 15 (trend strength)
- **Pattern Strength**: 65+ (out of 100)
- **Volume Ratio**: 1.0x minimum
- **Analysis Mode**: Daily + Weekly Combined
- **Enhanced Analysis**: All features enabled

### Next Steps
1. ⏳ Wait for network policy update (allowlist Yahoo Finance)
2. 🤖 Configure Telegram credentials
3. 🚀 Re-run the scanner script
4. 📊 Stocks meeting criteria will be sent to Telegram automatically

### Logs
- **Run Time**: 2026-08-04 09:11:20 IST
- **Stocks Attempted**: 50
- **Stocks Successfully Scanned**: 0 (all failed due to network)
- **Telegram Status**: Not configured

---
*Last Updated: 2026-08-04 09:11 IST*
