#!/usr/bin/env python3
"""
Automated NSE F&O PCS Scanner - Runs non-interactively and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import pytz
import asyncio
from telegram import Bot
import traceback

# Import from the streamlit app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

def get_default_filters():
    """Return default filter settings"""
    return {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
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
        'pattern_filters': {
            'current_day_breakout': True,
            'cup_and_handle': True,
            'flat_base': True,
            'bump_and_run': True,
            'rectangle_bottom': True,
            'rectangle_top': False,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': False,
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': False,
        'export_results': True,
        'stocks_limit': len(COMPLETE_NSE_FO_UNIVERSE),
        'enhancements': {
            'delivery_volume': True,
            'fno_consolidation': True,
            'breakout_pullback': True,
            'enhanced_sr': True
        }
    }

def run_analysis():
    """Run the PCS analysis with default filters"""
    print("=" * 80)
    print("NSE F&O PCS SCREENER - AUTOMATED ANALYSIS")
    print("=" * 80)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    print(f"\n📅 Analysis Date: {current_time.strftime('%Y-%m-%d %H:%M IST')}\n")

    # Get default filters
    config = get_default_filters()
    print(f"🎯 Scanning {len(config['stocks_to_scan'])} stocks with default filters...")
    print(f"   RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    print(f"   ADX Minimum: {config['adx_min']}")
    print(f"   Pattern Strength: {config['pattern_strength_min']}%\n")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    # Run analysis
    total_stocks = len(config['stocks_to_scan'])
    for i, symbol in enumerate(config['stocks_to_scan']):
        progress = ((i + 1) / total_stocks) * 100
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        print(f"[{progress:3.0f}%] Analyzing {clean_symbol}...", end='\r')

        try:
            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Process enhancements
            enhancement_results = {}

            if config.get('enhancements', {}).get('delivery_volume', False):
                try:
                    delivery_analysis = scanner.analyze_delivery_volume_percentage(symbol)
                    enhancement_results['delivery_volume'] = delivery_analysis
                except Exception as e:
                    pass

            if config.get('enhancements', {}).get('fno_consolidation', False):
                try:
                    consolidation_analysis = scanner.detect_fno_consolidation_near_resistance(
                        data, symbol, lookback_days=20
                    )
                    enhancement_results['fno_consolidation'] = consolidation_analysis
                except Exception as e:
                    pass

            if config.get('enhancements', {}).get('breakout_pullback', False):
                try:
                    breakout_analysis = scanner.detect_breakout_pullback_strong_green(
                        data, lookback_days=30
                    )
                    enhancement_results['breakout_pullback'] = breakout_analysis
                except Exception as e:
                    pass

            if config.get('enhancements', {}).get('enhanced_sr', False):
                try:
                    sr_analysis = scanner.enhanced_support_resistance_analysis(
                        data, lookback_days=50
                    )
                    enhancement_results['enhanced_sr'] = sr_analysis
                except Exception as e:
                    pass

            # Create stock result
            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'enhancements': enhancement_results
            }

            results.append(stock_result)

        except Exception as e:
            continue

    print(f"\n✅ Analysis complete!\n")

    # Sort results by pattern strength
    results.sort(
        key=lambda x: max(p['strength'] for p in x['patterns']) if x['patterns'] else 0,
        reverse=True
    )

    return results, config

def format_telegram_message(results):
    """Format results for Telegram message"""
    if not results:
        return "❌ No stocks meeting the filter criteria found today."

    # Group by confidence level
    high_confidence = []
    medium_confidence = []
    low_confidence = []

    for result in results:
        if not result['patterns']:
            continue

        max_strength = max(p['strength'] for p in result['patterns'])
        if max_strength >= 85:
            high_confidence.append(result)
        elif max_strength >= 70:
            medium_confidence.append(result)
        else:
            low_confidence.append(result)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"🎯 <b>NSE F&O PCS Screener Results</b>\n"
    message += f"📅 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n\n"

    # High Confidence
    if high_confidence:
        message += f"🟢 <b>HIGH CONFIDENCE ({len(high_confidence)})</b>\n"
        for r in high_confidence[:5]:  # Limit to 5 per group for message size
            max_strength = max(p['strength'] for p in r['patterns'])
            message += f"  • <b>{r['clean_symbol']}</b> - ₹{r['current_price']:.2f} (Strength: {max_strength:.0f}%)\n"
        if len(high_confidence) > 5:
            message += f"  ... and {len(high_confidence)-5} more\n"
        message += "\n"

    # Medium Confidence
    if medium_confidence:
        message += f"🟡 <b>MEDIUM CONFIDENCE ({len(medium_confidence)})</b>\n"
        for r in medium_confidence[:5]:
            max_strength = max(p['strength'] for p in r['patterns'])
            message += f"  • <b>{r['clean_symbol']}</b> - ₹{r['current_price']:.2f} (Strength: {max_strength:.0f}%)\n"
        if len(medium_confidence) > 5:
            message += f"  ... and {len(medium_confidence)-5} more\n"
        message += "\n"

    # Low Confidence
    if low_confidence:
        message += f"🔴 <b>LOW CONFIDENCE ({len(low_confidence)})</b>\n"
        for r in low_confidence[:5]:
            max_strength = max(p['strength'] for p in r['patterns'])
            message += f"  • <b>{r['clean_symbol']}</b> - ₹{r['current_price']:.2f} (Strength: {max_strength:.0f}%)\n"
        if len(low_confidence) > 5:
            message += f"  ... and {len(low_confidence)-5} more\n"
        message += "\n"

    message += f"📊 Total Stocks Found: {len(results)}"

    return message

def format_detailed_report(results):
    """Format detailed CSV report"""
    if not results:
        return None

    report_data = []
    for result in results:
        if not result['patterns']:
            continue

        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
        pattern_names = ', '.join(p['type'] for p in result['patterns'][:2])

        report_data.append({
            'Symbol': result['clean_symbol'],
            'Price': f"₹{result['current_price']:.2f}",
            'RSI': f"{result['rsi']:.1f}",
            'ADX': f"{result['adx']:.1f}",
            'Volume Ratio': f"{result['volume_ratio']:.2f}x",
            'Strength': f"{max_strength:.0f}%",
            'Confidence': confidence,
            'Patterns': pattern_names
        })

    df = pd.DataFrame(report_data)
    return df

async def send_to_telegram(message, telegram_token, telegram_chat_id):
    """Send message to Telegram"""
    try:
        bot = Bot(token=telegram_token)
        await bot.send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False

def main():
    """Main execution function"""
    # Run analysis
    results, config = run_analysis()

    # Print summary
    print(f"📊 RESULTS SUMMARY")
    print(f"=" * 80)
    print(f"Total stocks found: {len(results)}")

    if results:
        # Calculate confidence distribution
        high = sum(1 for r in results if max(p['strength'] for p in r['patterns']) >= 85)
        medium = sum(1 for r in results if 70 <= max(p['strength'] for p in r['patterns']) < 85)
        low = sum(1 for r in results if max(p['strength'] for p in r['patterns']) < 70)

        print(f"  🟢 High Confidence: {high}")
        print(f"  🟡 Medium Confidence: {medium}")
        print(f"  🔴 Low Confidence: {low}\n")

        # Top 10 stocks
        print("📈 TOP 10 STOCKS BY STRENGTH:")
        for i, r in enumerate(results[:10], 1):
            max_strength = max(p['strength'] for p in r['patterns'])
            print(f"  {i:2d}. {r['clean_symbol']:12s} - ₹{r['current_price']:8.2f} - Strength: {max_strength:5.0f}%")

    print(f"\n" + "=" * 80)

    # Save results to JSON
    results_json = []
    for r in results:
        max_strength = max(p['strength'] for p in r['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        results_json.append({
            'symbol': r['clean_symbol'],
            'price': r['current_price'],
            'rsi': r['rsi'],
            'adx': r['adx'],
            'volume_ratio': r['volume_ratio'],
            'strength': max_strength,
            'confidence': confidence,
            'patterns': [p['type'] for p in r['patterns']],
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        })

    # Save to file
    output_file = '/home/user/nsepcs/scan_results.json'
    with open(output_file, 'w') as f:
        json.dump(results_json, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")

    # Save CSV report
    df = format_detailed_report(results)
    if df is not None:
        csv_file = '/home/user/nsepcs/scan_results.csv'
        df.to_csv(csv_file, index=False)
        print(f"💾 CSV report saved to: {csv_file}")

    # Format and prepare Telegram message
    message = format_telegram_message(results)

    # Try to send to Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if telegram_token and telegram_chat_id:
        print(f"\n📤 Sending results to Telegram...")
        success = asyncio.run(send_to_telegram(message, telegram_token, telegram_chat_id))
        if success:
            print("✅ Message sent to Telegram!")
    else:
        print(f"\n⚠️  Telegram credentials not found in environment variables.")
        print(f"   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram sending.")
        print(f"\n📱 Message to send to Telegram:")
        print(f"{message}")

    return results

if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
