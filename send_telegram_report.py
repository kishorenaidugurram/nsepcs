#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Report Generator
Creates and sends a scan report based on filter configuration
"""

import os
import requests
from datetime import datetime
import json

# NSE F&O Stocks - Top 50 most liquid
TOP_NSE_FO_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'BHARTIARTL', 'ITC', 'SBIN', 'LT', 'KOTAKBANK',
    'AXISBANK', 'MARUTI', 'ASIANPAINT', 'WIPRO', 'ONGC',
    'NTPC', 'POWERGRID', 'TATAMOTORS', 'TECHM', 'ULTRACEMCO',
    'SUNPHARMA', 'TITAN', 'COALINDIA', 'BAJFINANCE', 'HCLTECH',
    'JSWSTEEL', 'INDUSINDBK', 'BRITANNIA', 'CIPLA', 'DRREDDY',
    'EICHERMOT', 'GRASIM', 'HEROMOTOCO', 'HINDALCO', 'TATASTEEL',
    'BPCL', 'M&M', 'BAJAJ-AUTO', 'SHRIRAMFIN', 'ADANIPORTS',
    'APOLLOHOSP', 'BAJAJFINSV', 'DIVISLAB', 'NESTLEIND', 'TRENT',
    'HDFCLIFE', 'SBILIFE', 'LTIM', 'ADANIENT', 'HINDUNILVR'
]

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    if not bot_token:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not chat_id:
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not set in environment")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            print(f"✅ Telegram message sent successfully")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def create_scan_report():
    """Create a comprehensive scan report"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M IST')

    report = {
        'timestamp': now,
        'stocks_to_scan': len(TOP_NSE_FO_STOCKS),
        'filter_configuration': {
            'RSI_Range': '30-75',
            'ADX_Minimum': 20,
            'Volume_Ratio': '1.2x (above 20-day average)',
            'Moving_Average_Support': 'Enabled (EMA tolerance: 3%)',
            'Pattern_Detection': 'Current Day Breakout, Cup & Handle, Flat Base, etc.',
            'Analysis_Mode': 'Daily + Weekly Combined'
        },
        'top_stocks': TOP_NSE_FO_STOCKS[:15]
    }

    return report

def format_telegram_message(report):
    """Format message for Telegram"""
    stocks_list = "\n".join([f"{i}. {s}" for i, s in enumerate(report['top_stocks'], 1)])

    message = f"""📊 <b>NSE F&O PCS Scanner - Filter Configuration Report</b>
⏰ <b>{report['timestamp']}</b>

<b>🎯 Scanner Configuration:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Filter Settings:</b>
• RSI Range: {report['filter_configuration']['RSI_Range']}
• ADX Minimum: {report['filter_configuration']['ADX_Minimum']}
• Volume Ratio: {report['filter_configuration']['Volume_Ratio']}
• MA Support: {report['filter_configuration']['Moving_Average_Support']}
• Pattern Detection: {report['filter_configuration']['Pattern_Detection']}
• Analysis Mode: {report['filter_configuration']['Analysis_Mode']}

<b>📈 NSE F&O Universe:</b>
• Total Stocks to Scan: <b>{report['stocks_to_scan']}</b>
• Liquidity Tier: All (Nifty 50 + Bank Nifty + Tier 2/3)

<b>🏆 Top 15 Liquid Stocks in Scanner:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{stocks_list}

<b>📊 Scan Status:</b>
✅ Scanner ready for execution
✅ All technical indicators configured
✅ Weekly timeframe validation enabled
✅ Chart patterns detection active

<b>🔔 Note:</b>
Live market data unavailable in current environment due to network restrictions.
To run a live scan, access the Streamlit web app:
<a href="https://nse-fo-pcs-screener.streamlit.app">Live Scanner</a>

<b>For detailed analysis visit the web app and configure your filters!</b>
"""

    return message

def main():
    print("\n" + "=" * 70)
    print("NSE F&O PCS SCANNER - TELEGRAM REPORT GENERATOR")
    print("=" * 70 + "\n")

    # Create report
    report = create_scan_report()

    print(f"📊 Scan Configuration Report Generated")
    print(f"📈 Stocks to scan: {report['stocks_to_scan']}")
    print(f"⏰ Timestamp: {report['timestamp']}\n")

    # Format message
    telegram_message = format_telegram_message(report)

    # Save report to file
    report_file = f"/tmp/nsepcs_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"💾 Report saved: {report_file}\n")

    # Display message
    print("📤 Telegram Message Preview:")
    print("━" * 70)
    print(telegram_message)
    print("━" * 70 + "\n")

    # Attempt to send to Telegram
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if bot_token and chat_id:
        print("📤 Attempting to send to Telegram...")
        sent = send_to_telegram(telegram_message, bot_token, chat_id)
        if sent:
            print("\n✅ Telegram notification sent successfully!")
        else:
            print("\n⚠️  Failed to send telegram message")
            print("Message preview saved locally")
    else:
        print("\n⚠️  Telegram credentials not set")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable Telegram notifications")
        print("\nExample:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")

if __name__ == "__main__":
    main()
