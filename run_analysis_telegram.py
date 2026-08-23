#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Automated Analysis & Telegram Notifier
Runs the PCS screening analysis and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import from streamlit_app (extract ProfessionalPCSScanner class)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default filter criteria
DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'ma_support': True,
    'ma_type': 'EMA',
    'ma_tolerance': 3,
    'min_volume_ratio': 1.2,
    'volume_breakout_ratio': 2.0,
    'lookback_days': 20,
    'pattern_strength_min': 65,
    'show_charts': False,
    'show_news': False,
}

# NSE F&O stocks (subset from streamlit_app)
NSE_FO_STOCKS = [
    "NIFTY", "BANKNIFTY", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS", "ASIANPAINT.NS", "BHARTIARTL.NS",
    "SUNPHARMA.NS", "TATAMOTORS.NS", "ADANIENT.NS", "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "INDUSINDBK.NS", "TECHM.NS", "TITAN.NS", "NESTLEIND.NS",
    "ULTRACEMCO.NS", "POWERGRID.NS", "NTPC.NS", "ONGC.NS", "COALINDIA.NS",
    "JSWSTEEL.NS", "TATASTEEL.NS", "HINDALCO.NS"
]


def send_telegram_message(message_text, is_html=False):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured. Skipping Telegram notification.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        parse_mode = "HTML" if is_html else "Markdown"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message_text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Telegram message sent successfully")
            return True
        else:
            logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error sending Telegram message: {str(e)}")
        return False


def format_telegram_message(results, filters):
    """Format results for Telegram"""
    if not results:
        message = "🔍 NSE F&O PCS Scan Complete\n\n❌ No stocks found meeting criteria"
        return message

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Build message
    lines = []
    lines.append("🎯 NSE F&O PCS Scan Results")
    lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")
    lines.append("")
    lines.append(f"✅ Found <b>{len(results)}</b> stocks with confirmed patterns")
    lines.append("")

    # Add summary stats
    total_patterns = sum(len(r['patterns']) for r in results)
    avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])
    high_confidence = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')

    lines.append("<b>📊 Summary:</b>")
    lines.append(f"  • Stocks: {len(results)}")
    lines.append(f"  • Patterns: {total_patterns}")
    lines.append(f"  • Avg Strength: {avg_strength:.1f}%")
    lines.append(f"  • High Confidence: {high_confidence}")
    lines.append("")

    # Add top 10 stocks
    lines.append("<b>🏆 Top Opportunities:</b>")
    for i, result in enumerate(results[:10], 1):
        symbol = result['symbol'].replace('.NS', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
        price = result['current_price']
        rsi = result['rsi']

        lines.append(f"{i}. <b>{symbol}</b> ({confidence})")
        lines.append(f"   Price: ₹{price:.2f} | RSI: {rsi:.0f} | Strength: {max_strength:.0f}%")

    lines.append("")
    lines.append("<i>Run 'streamlit run streamlit_app.py' for detailed analysis</i>")

    return "\n".join(lines)


def run_analysis(max_stocks=None):
    """Run the PCS screening analysis"""
    try:
        # Import the scanner class from streamlit_app
        # For now, we'll use a simplified version that imports what we need
        import streamlit_app

        scanner = streamlit_app.ProfessionalPCSScanner()

        # Use all F&O stocks or limit if specified
        stocks_to_scan = NSE_FO_STOCKS if not max_stocks else NSE_FO_STOCKS[:max_stocks]

        logger.info(f"🚀 Starting PCS scan for {len(stocks_to_scan)} stocks...")

        results = []
        processed = 0

        for symbol in stocks_to_scan:
            try:
                processed += 1
                logger.info(f"Analyzing {symbol} ({processed}/{len(stocks_to_scan)})")

                # Get stock data
                data = scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                    data, DEFAULT_FILTERS['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = scanner.detect_patterns(data, symbol, DEFAULT_FILTERS)
                if not patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Create result entry
                stock_result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data
                }

                results.append(stock_result)
                logger.info(f"✅ {symbol} passed filters ({len(patterns)} pattern(s))")

            except Exception as e:
                logger.warning(f"⚠️  Error processing {symbol}: {str(e)}")
                continue

        logger.info(f"✅ Scan complete! Found {len(results)} stocks")
        return results

    except Exception as e:
        logger.error(f"❌ Error during analysis: {str(e)}")
        return []


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Screener - Automated Analysis")
    logger.info("=" * 60)

    # Check Telegram configuration
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info("✅ Telegram configured - results will be sent")
    else:
        logger.warning("⚠️  Telegram not configured - results will only be printed")
        logger.info("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars to enable")

    # Run analysis
    logger.info("Starting PCS analysis...")
    results = run_analysis(max_stocks=50)  # Scan first 50 stocks for speed

    # Format results
    message = format_telegram_message(results, DEFAULT_FILTERS)

    # Print results
    print("\n" + "=" * 60)
    print(message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))
    print("=" * 60 + "\n")

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram_message(message, is_html=True)

    # Save results to JSON
    results_json = {
        'timestamp': datetime.now().isoformat(),
        'stocks_found': len(results),
        'stocks': [
            {
                'symbol': r['symbol'],
                'price': round(r['current_price'], 2),
                'rsi': round(r['rsi'], 1),
                'adx': round(r['adx'], 1),
                'patterns': len(r['patterns']),
                'max_strength': max(p['strength'] for p in r['patterns'])
            }
            for r in results[:10]
        ]
    }

    with open('scan_results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    logger.info("Results saved to scan_results.json")


if __name__ == "__main__":
    main()
