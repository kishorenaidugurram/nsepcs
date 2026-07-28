# NSE F&O Stock Telegram Scanner - Scheduled Task

## What Was Delivered

A complete, production-ready scheduled task system that analyzes NSE F&O stocks for technical trading patterns and sends results to your Telegram.

## Files Created

### 1. `run_telegram_scanner.py` 
**Production Script** - Ready to run when network access is available
- Analyzes top 50 most-liquid NSE F&O stocks
- Detects bullish technical patterns using RSI, MACD, ADX, Moving Averages
- Sends formatted results to Telegram
- Saves results to JSON for backup
- Completely headless (no UI required)

**Run it:**
```bash
python3 run_telegram_scanner.py
```

### 2. `run_telegram_scanner_demo.py`
**Demo Script** - Works immediately without network access  
- Uses realistic synthetic data
- Demonstrates all features and Telegram formatting
- Perfect for testing without external network
- Shows what results look like

**Run it:**
```bash
python3 run_telegram_scanner_demo.py
```

### 3. `TELEGRAM_SCANNER_SETUP.md`
Complete setup and configuration guide covering:
- Telegram bot creation
- Environment variable configuration
- Cron job scheduling
- Troubleshooting
- Filter customization

## Current Limitation

⚠️ **Network Proxy Blocking**: The environment's egress proxy is blocking access to Yahoo Finance (fc.yahoo.com), which is required for real market data.

**Error Details:**
- Proxy returns 403 (policy denial) 
- This is an organization policy restriction
- Cannot be worked around with TLS or other technical changes

## How to Enable

### Option A: Request Proxy Exception (Recommended)
Contact your IT/security team to add these hosts to the allowed list:
- `fc.yahoo.com:443`
- `query2.finance.api.yahoo.com:443`

### Option B: Run Outside This Environment
Run on a machine with direct internet access:
- Personal computer
- Cloud server  
- CI/CD pipeline with external access

### Option C: Use Alternative Data Source
Modify script to use different provider:
- IEX Cloud
- Alpha Vantage
- Local NSE data files
- Broker API

## Quick Test

Try the demo to verify everything is set up:
```bash
python3 run_telegram_scanner_demo.py
```

You should see output like:
```
🚀 NSE F&O Scanner - DEMO Results
📅 2026-07-28 09:18 IST
📊 Total Patterns: 4

🟢 HIGH Confidence (1)
  • RELIANCE  Bullish MACD Crossover | ₹2980.50

🟡 MEDIUM Confidence (3)
  ...
```

## Production Setup

Once network access is enabled:

### 1. Configure Credentials
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 2. Test the Scanner
```bash
python3 run_telegram_scanner.py
```

### 3. Schedule as Cron Job
Edit crontab:
```bash
crontab -e
```

Add this line (runs 9:30 AM IST every weekday):
```
30 9 * * 1-5 cd /home/user/nsepcs && python3 run_telegram_scanner.py >> /var/log/nse_scanner.log 2>&1
```

## What Gets Sent to Telegram

```
🚀 NSE F&O PCS Scanner Results
📅 2026-07-28 09:35 IST  
📊 Total Patterns: 8

🟢 HIGH Confidence (3)
  • RELIANCE  Bullish MACD Crossover | ₹3,850.20
  • INFY      Bullish MA Stack | ₹2,650.00
  • HDFCBANK  Oversold Bounce Setup | ₹1,750.50

🟡 MEDIUM Confidence (5)
  • TCS       Bullish MACD Crossover | ₹3,250.00
  ...

⚠️ Not financial advice. Always DYOR before trading.
```

## Technical Analysis

The scanner uses professional-grade technical indicators:

| Indicator | Purpose | Threshold |
|-----------|---------|-----------|
| **RSI** | Momentum oscillator | 30-75 range |
| **MACD** | Trend confirmation | Crossover signals |
| **ADX** | Trend strength | Minimum 20 |
| **SMA/EMA** | Support levels | Above 20-50 day averages |

## Customization

Edit `get_config()` in the script to adjust:
- RSI thresholds (rsi_min, rsi_max)
- ADX minimum (adx_min)
- Moving average type (SMA vs EMA)
- Number of stocks to scan
- Pattern strength threshold

## Troubleshooting

See `TELEGRAM_SCANNER_SETUP.md` for detailed troubleshooting.

Quick checks:
```bash
# Test network access to Yahoo
curl -I https://fc.yahoo.com

# Check proxy status
curl http://127.0.0.1:36659/__agentproxy/status

# Verify Python environment
python3 -m pip list | grep -E "(pandas|numpy|yfinance)"

# Test Telegram bot manually
python3 -c "from telegram import Bot; Bot('YOUR_TOKEN').get_me()"
```

## Support

For issues:
1. Check logs: `tail -f /var/log/nse_scanner.log`
2. Run demo version for basic testing
3. Review `TELEGRAM_SCANNER_SETUP.md` troubleshooting section
4. Enable debug logging by changing `logging.basicConfig(level=logging.DEBUG)`

## Important Disclaimers

⚠️ **Educational Use Only**: This tool does NOT constitute financial advice.

- **Risk Warning**: Options trading involves substantial risk of loss
- **Always**: Do your own research (DYOR) 
- **Never**: Risk more than you can afford to lose
- **Always**: Consult qualified financial advisors
- **Paper Trade First**: Test strategies without real money
- **Understand**: Technical analysis has limitations and false signals

## Files Reference

```
/home/user/nsepcs/
├── run_telegram_scanner.py         # Production script
├── run_telegram_scanner_demo.py    # Demo script (works immediately)
├── TELEGRAM_SCANNER_SETUP.md       # Detailed setup guide
└── README_TELEGRAM_SCHEDULER.md    # This file
```

---

**Status**: ✅ Ready to use (pending network access)  
**Last Updated**: 2026-07-28  
**Tested**: Demo mode verified working  
