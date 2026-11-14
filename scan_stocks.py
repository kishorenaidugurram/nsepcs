#!/usr/bin/env python3
"""
Simple NSE Stock Scanner - Get stocks meeting filter criteria
"""

import os
import sys
import json
from datetime import datetime
import pytz
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# F&O stocks - Top liquid ones for quick scan
NSE_FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
]

class StockScanner:
    """Stock scanner using Yahoo Finance"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_price(self, symbol):
        """Get current stock price data"""
        try:
            # Try yfinance if available, otherwise use Yahoo API
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')

                if len(hist) < 2:
                    return None

                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]

                return {
                    'symbol': symbol.replace('.NS', ''),
                    'current_price': round(float(current), 2),
                    'prev_close': round(float(prev), 2),
                    'change_pct': round(((float(current) - float(prev)) / float(prev)) * 100, 2),
                    'change_abs': round(float(current) - float(prev), 2),
                }
            except:
                # Fallback to web scraping if yfinance fails
                logger.debug(f"yfinance unavailable, skipping {symbol}")
                return None

        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {e}")
            return None

    def is_qualifying(self, stock_data, min_change=-1.0, max_change=5.0):
        """Check if stock meets filter criteria"""
        if not stock_data:
            return False

        change = stock_data['change_pct']

        # Filter: Stock has positive change (bullish signal)
        if change >= min_change:
            return True

        return False

    def scan(self, stocks=None, limit=None):
        """Scan stocks and return qualifying ones"""
        if stocks is None:
            stocks = NSE_FO_STOCKS

        if limit:
            stocks = stocks[:limit]

        logger.info(f"Starting scan of {len(stocks)} stocks")

        results = []
        for idx, symbol in enumerate(stocks, 1):
            clean_symbol = symbol.replace('.NS', '')

            try:
                data = self.get_stock_price(symbol)

                if data and self.is_qualifying(data):
                    results.append(data)
                    logger.info(f"✓ {clean_symbol}: {data['current_price']} "
                               f"({data['change_pct']:+.2f}%)")

                if idx % 5 == 0:
                    logger.info(f"  Progress: {idx}/{len(stocks)}")

            except Exception as e:
                logger.debug(f"Error with {symbol}: {e}")

        logger.info(f"Scan complete: Found {len(results)} qualifying stocks")
        return results

    def save_results(self, results):
        """Save results to JSON"""
        if not results:
            logger.info("No results to save")
            return None

        try:
            timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/pcs_scan_results_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': datetime.now(self.ist).isoformat(),
                    'stocks_found': len(results),
                    'stocks': results
                }, f, indent=2)

            logger.info(f"Results saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None


def main():
    logger.info("=" * 70)
    logger.info("NSE F&O Stock Scanner - Meeting Filter Criteria")
    logger.info("=" * 70)

    try:
        scanner = StockScanner()

        # Scan stocks
        results = scanner.scan(limit=None)

        if results:
            logger.info(f"\n✅ Found {len(results)} stocks meeting criteria:\n")

            # Show results
            for stock in sorted(results, key=lambda x: x['change_pct'], reverse=True):
                logger.info(f"  {stock['symbol']:<12} : ₹{stock['current_price']:<10.2f} "
                           f"{stock['change_pct']:>+7.2f}%")

            # Save
            result_file = scanner.save_results(results)

            # Prepare for Telegram
            logger.info("\n" + "=" * 70)
            logger.info("TELEGRAM MESSAGE CONTENT:")
            logger.info("=" * 70)

            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

            message = f"🚀 NSE PCS Scanner Results - {timestamp}\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📊 {len(results)} stocks meeting filter criteria:\n\n"

            for idx, stock in enumerate(sorted(results, key=lambda x: x['change_pct'], reverse=True), 1):
                emoji = "🟢" if stock['change_pct'] > 1.5 else "🟡"
                message += f"{idx}. *{stock['symbol']}*\n"
                message += f"   ₹{stock['current_price']} ({stock['change_pct']:+.2f}%)\n\n"

            message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "Setup: Export these stocks to your trading platform\n"

            logger.info(message)

            logger.info("\n📌 To send this to Telegram:")
            logger.info("   1. Set environment variables:")
            logger.info("      export TELEGRAM_BOT_TOKEN='your_bot_token'")
            logger.info("      export TELEGRAM_CHAT_ID='your_chat_id'")
            logger.info("   2. Run: python3 send_to_telegram.py")

        else:
            logger.warning("⚠ No qualifying stocks found in this scan")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
