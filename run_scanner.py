#!/usr/bin/env python3
"""
Stock Scanner - Runs NSE PCS scanner and saves results
"""

import sys
import os
import logging
from datetime import datetime
import pandas as pd
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    get_nse_non_fno_stocks,
    fetch_stock_data_cached
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_scanner(universe_type="NSE F&O Stocks (219)", max_stocks=None):
    """
    Run the stock scanner with default filters

    Args:
        universe_type: "NSE F&O Stocks (219)" or "NSE Non-F&O Stocks (800+)"
        max_stocks: Maximum stocks to scan (None = all)

    Returns:
        list: Qualifying stocks with their details
    """

    logger.info(f"Starting scanner - Universe: {universe_type}")

    # Select stock universe
    if universe_type == "NSE F&O Stocks (219)":
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    else:
        logger.info("Fetching NSE Non-F&O stocks...")
        stocks_to_scan = get_nse_non_fno_stocks()

    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    logger.info(f"Scanning {len(stocks_to_scan)} stocks")

    # Default filters (matching Streamlit app defaults)
    config = {
        'stocks_to_scan': stocks_to_scan,
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
            'rectangle_top': True,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': True,
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': False,
        'enhancements': {
            'delivery_volume': False,
            'fno_consolidation': False,
            'breakout_pullback': False,
            'enhanced_sr': False
        }
    }

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    # Scan stocks
    for i, symbol in enumerate(stocks_to_scan, 1):
        try:
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(stocks_to_scan)} stocks scanned")

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
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

            # Create result entry
            stock_result = {
                'symbol': symbol,
                'clean_symbol': symbol.replace('.NS', '').replace('^', ''),
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'best_pattern': max(patterns, key=lambda x: x['strength']) if patterns else None,
            }

            results.append(stock_result)
            logger.info(f"✓ {stock_result['clean_symbol']} - Patterns found: {len(patterns)}")

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            continue

    logger.info(f"Scan complete. Found {len(results)} qualifying stocks")
    return results


def save_results_to_csv(results, filename=None):
    """Save results to CSV file"""
    if not results:
        return None

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/claude-0/-home-user-nsepcs/0f821919-47d0-5372-aa4d-845b71125a7a/scratchpad/scanner_results_{timestamp}.csv"

    # Create directory if needed
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Prepare data for CSV
    csv_data = []
    for stock in results:
        pattern = stock['best_pattern']
        csv_data.append({
            'Symbol': stock['clean_symbol'],
            'Price': stock['current_price'],
            'Pattern': pattern['type'],
            'Strength': pattern['strength'],
            'RSI': stock['rsi'],
            'ADX': stock['adx'],
            'Volume_Ratio': stock['volume_ratio'],
        })

    df = pd.DataFrame(csv_data)
    df.to_csv(filename, index=False)
    logger.info(f"Results saved to: {filename}")
    return filename


def save_results_to_text(results, filename=None):
    """Save results as formatted text file"""
    if not results:
        return None

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/claude-0/-home-user-nsepcs/0f821919-47d0-5372-aa4d-845b71125a7a/scratchpad/scanner_results_{timestamp}.txt"

    # Create directory if needed
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Sort by pattern strength
    results.sort(key=lambda x: x['best_pattern']['strength'], reverse=True)

    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("NSE PCS STOCK SCANNER RESULTS\n")
        f.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}\n")
        f.write(f"Total Stocks Found: {len(results)}\n")
        f.write("=" * 80 + "\n\n")

        for idx, stock in enumerate(results, 1):
            pattern = stock['best_pattern']
            f.write(f"{idx}. {stock['clean_symbol']}\n")
            f.write(f"   Price: ₹{stock['current_price']:.2f}\n")
            f.write(f"   Pattern: {pattern['type']} ({pattern['strength']:.0f}% strength)\n")
            f.write(f"   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n")
            f.write(f"   Volume Ratio: {stock['volume_ratio']:.2f}x\n")
            f.write("\n")

    logger.info(f"Results saved to: {filename}")
    return filename


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE PCS Stock Scanner")
    logger.info("=" * 60)

    # Run scanner
    results = run_scanner(universe_type="NSE F&O Stocks (219)")

    # Save results
    csv_file = save_results_to_csv(results)
    text_file = save_results_to_text(results)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SCAN COMPLETE: Found {len(results)} qualifying stocks")
    if csv_file:
        logger.info(f"CSV saved to: {csv_file}")
    if text_file:
        logger.info(f"Text saved to: {text_file}")
    logger.info("=" * 60)

    return len(results) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
