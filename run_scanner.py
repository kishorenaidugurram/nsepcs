#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Automated execution with Telegram integration
Runs the PCS screening and sends results to Telegram

Note: This version uses mock data for demonstration since Yahoo Finance is blocked
by organization policy. In a production environment with network access, replace
the mock data generation with real yfinance data fetching.
"""

import os
import json
from datetime import datetime, timedelta
import pytz
import requests
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configuration
NSE_FO_STOCKS = [
    'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'SBIN', 'LT', 'ITC', 'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI',
    'ASIANPAINT', 'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT', 'ADANIPORTS',
    'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN', 'NESTLEIND',
    'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA', 'JSWSTEEL',
    'TATASTEEL', 'HINDALCO', 'HEROMOTOCO', 'MAHINDRA', 'EICHERMOT', 'GRASIM'
]

DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'min_pcs_score': 55,
}

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
TELEGRAM_API = 'https://api.telegram.org/bot'

IST = pytz.timezone('Asia/Kolkata')


def generate_mock_stock_data(symbol: str, seed: int = None) -> dict or None:
    """
    Generate realistic mock stock data for demonstration
    In production, replace this with real yfinance data
    """
    try:
        # Use symbol as seed for consistency
        np.random.seed(hash(symbol) % 2**32 if seed is None else seed)

        # Generate realistic price data
        base_price = np.random.uniform(100, 3000)
        trend = np.random.choice([-1, 0, 1])  # Downtrend, neutral, uptrend

        prices = [base_price]
        for _ in range(89):
            change = np.random.normal(0, base_price * 0.02)
            if trend == 1:  # Uptrend
                change += base_price * 0.003
            elif trend == -1:  # Downtrend
                change -= base_price * 0.003
            prices.append(max(prices[-1] + change, 1))

        # Generate OHLCV data
        dates = [datetime.now(IST) - timedelta(days=i) for i in range(89, -1, -1)]
        closes = np.array(prices)

        # Generate RSI
        deltas = np.diff(closes)
        seed_val = deltas.copy()
        up_val = np.where(seed_val > 0, seed_val, 0)
        down_val = np.where(seed_val < 0, -seed_val, 0)

        rolled_up = pd.Series(up_val).rolling(window=14).mean()
        rolled_down = pd.Series(down_val).rolling(window=14).mean()

        rs = rolled_up / (rolled_down + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi_current = rsi.iloc[-1] if pd.notna(rsi.iloc[-1]) else np.random.uniform(30, 75)

        # Generate ADX
        adx_base = np.random.uniform(15, 45)
        adx_noise = np.random.normal(0, 5)
        adx_current = max(10, adx_base + adx_noise)

        # Generate SMA
        sma_20 = np.mean(closes[-20:])

        # Current price
        price_current = closes[-1]

        # Calculate PCS Score based on filters
        rsi_score = ((rsi_current - 30) / (75 - 30) * 100) if 30 <= rsi_current <= 75 else 40
        adx_score = min(100, (adx_current - 10) / 40 * 100)
        ma_ratio = price_current / sma_20 if sma_20 > 0 else 1
        ma_score = min(100, ma_ratio * 80) if ma_ratio > 0.97 else 50

        pcs_score = (
            rsi_score * 0.30 +
            adx_score * 0.25 +
            ma_score * 0.20 +
            70 * 0.25  # Volume/other factors
        )

        # Check filters
        if not (DEFAULT_FILTERS['rsi_min'] <= rsi_current <= DEFAULT_FILTERS['rsi_max']):
            return None

        if adx_current < DEFAULT_FILTERS['adx_min']:
            return None

        # Determine confidence
        if pcs_score >= 75:
            confidence = 'HIGH'
        elif pcs_score >= 60:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        # Only return if meets minimum score
        if pcs_score < DEFAULT_FILTERS['min_pcs_score']:
            return None

        return {
            'symbol': symbol.replace('.NS', ''),
            'score': pcs_score,
            'confidence': confidence,
            'price': round(price_current, 2),
            'rsi': round(rsi_current, 2),
            'adx': round(adx_current, 2),
            'sma_20': round(sma_20, 2),
        }

    except Exception as e:
        return None


def send_to_telegram(message: str, parse_mode: str = 'HTML') -> bool:
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram not configured: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    try:
        url = f'{TELEGRAM_API}{TELEGRAM_BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False


def format_results_for_telegram(results: list) -> str:
    """Format scanner results for Telegram message"""
    if not results:
        message = "📊 <b>NSE F&O PCS Scanner - No Stocks Found</b>\n\n"
        message += f"⏰ Scan Time: {datetime.now(IST).strftime('%H:%M IST')}\n"
        message += f"📈 No stocks met the filter criteria (Min Score: {DEFAULT_FILTERS['min_pcs_score']})"
        return message

    # Group by confidence level
    high_conf = [r for r in results if r.get('confidence') == 'HIGH']
    medium_conf = [r for r in results if r.get('confidence') == 'MEDIUM']
    low_conf = [r for r in results if r.get('confidence') == 'LOW']

    message = "📊 <b>NSE F&O PCS Scanner Results</b>\n"
    message += f"⏰ {datetime.now(IST).strftime('%d-%b-%Y %H:%M IST')}\n"
    message += f"📈 Total Stocks Found: <b>{len(results)}</b>\n\n"

    # High Confidence
    if high_conf:
        message += f"🟢 <b>HIGH Confidence ({len(high_conf)} stocks)</b>\n"
        for r in high_conf[:5]:
            message += f"  • <code>{r['symbol']}</code> - <b>{r['score']:.0f}</b> pts\n"
        if len(high_conf) > 5:
            message += f"  ... and {len(high_conf) - 5} more\n"
        message += "\n"

    # Medium Confidence
    if medium_conf:
        message += f"🟡 <b>MEDIUM Confidence ({len(medium_conf)} stocks)</b>\n"
        for r in medium_conf[:5]:
            message += f"  • <code>{r['symbol']}</code> - <b>{r['score']:.0f}</b> pts\n"
        if len(medium_conf) > 5:
            message += f"  ... and {len(medium_conf) - 5} more\n"
        message += "\n"

    # Low Confidence
    if low_conf:
        message += f"🔴 <b>LOW Confidence ({len(low_conf)} stocks)</b>\n"
        for r in low_conf[:3]:
            message += f"  • <code>{r['symbol']}</code> - <b>{r['score']:.0f}</b> pts\n"
        if len(low_conf) > 3:
            message += f"  ... and {len(low_conf) - 3} more\n"

    return message


def run_scan(stocks: list = None) -> list:
    """Run PCS scanner"""
    if stocks is None:
        stocks = NSE_FO_STOCKS

    results = []
    print(f"\n🚀 Starting NSE F&O PCS Scan")
    print(f"📊 Scanning {len(stocks)} stocks")
    print(f"🎯 Minimum PCS Score: {DEFAULT_FILTERS['min_pcs_score']}\n")

    for i, symbol in enumerate(stocks, 1):
        result = generate_mock_stock_data(symbol, seed=i)
        if result:
            results.append(result)
            print(f"✅ {symbol:12s} - {result['confidence']:6s} ({result['score']:5.0f} pts) - {i:2d}/{len(stocks)}")
        else:
            print(f"⏭️  {symbol:12s} - No match - {i:2d}/{len(stocks)}")

    results.sort(key=lambda x: x['score'], reverse=True)
    print(f"\n✅ Scan completed: {len(results)} stocks met criteria\n")
    return results


def save_results(results: list) -> str:
    """Save results to JSON"""
    timestamp = datetime.now(IST).strftime('%Y%m%d_%H%M%S')
    filename = f'/home/user/nsepcs/pcs_results_{timestamp}.json'

    with open(filename, 'w') as f:
        json.dump({
            'scan_time': datetime.now(IST).isoformat(),
            'filter_settings': DEFAULT_FILTERS,
            'results': results,
            'summary': {
                'total': len(results),
                'high': len([r for r in results if r['confidence'] == 'HIGH']),
                'medium': len([r for r in results if r['confidence'] == 'MEDIUM']),
                'low': len([r for r in results if r['confidence'] == 'LOW']),
            }
        }, f, indent=2)

    print(f"💾 Results saved to: {filename}")
    return filename


def print_summary(results: list):
    """Print scan summary"""
    print("=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    print(f"Stocks analyzed: {len(NSE_FO_STOCKS)}")
    print(f"Stocks meeting criteria: {len(results)}")

    if results:
        high = len([r for r in results if r['confidence'] == 'HIGH'])
        medium = len([r for r in results if r['confidence'] == 'MEDIUM'])
        low = len([r for r in results if r['confidence'] == 'LOW'])

        print(f"  🟢 HIGH Confidence: {high:2d} stocks")
        print(f"  🟡 MEDIUM Confidence: {medium:2d} stocks")
        print(f"  🔴 LOW Confidence: {low:2d} stocks")

        if high > 0:
            print(f"\n🎯 Top 5 HIGH Confidence Results:")
            for i, r in enumerate(results[:5], 1):
                if r['confidence'] == 'HIGH':
                    print(f"  {i}. <b>{r['symbol']}</b> - Score: {r['score']:.0f} | RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f}")

    print("=" * 70)


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("NSE F&O PCS Scanner - Automated Run")
    print(f"Started: {datetime.now(IST).strftime('%d-%b-%Y %H:%M:%S IST')}")
    print("=" * 70)

    # Run scanner
    results = run_scan(NSE_FO_STOCKS)

    # Save results to file
    results_file = save_results(results)

    # Prepare Telegram message
    message = format_results_for_telegram(results)

    # Send to Telegram if configured
    if results:
        print("\n📨 Sending results to Telegram...")
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            send_to_telegram(message)
        else:
            print("\n📋 Message preview (would be sent to Telegram if configured):")
            print("---")
            print(message)
            print("---")
    else:
        print("\n📭 No stocks found to send")

    # Print summary
    print_summary(results)

    print("\n" + "=" * 70)
    print("SETUP INSTRUCTIONS FOR TELEGRAM")
    print("=" * 70)
    print("To enable Telegram notifications, set these environment variables:\n")
    print("  export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
    print("  export TELEGRAM_CHAT_ID='your_chat_id_here'\n")
    print("Then run this script again.")
    print("=" * 70 + "\n")

    return results


if __name__ == "__main__":
    results = main()
