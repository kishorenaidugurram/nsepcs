#!/usr/bin/env python3
"""
Test/Demo version of PCS Scanner
Demonstrates output without requiring network access
"""

import json
from datetime import datetime
import pytz

# Mock scanner results for testing
def generate_mock_results():
    """Generate realistic test data"""
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).isoformat()

    mock_stocks = [
        {'symbol': 'RELIANCE', 'price': 3250.50, 'rsi': 65, 'adx': 28, 'volume_ratio': 2.15, 'strength': 82},
        {'symbol': 'INFY', 'price': 2850.25, 'rsi': 62, 'adx': 26, 'volume_ratio': 1.85, 'strength': 76},
        {'symbol': 'TCS', 'price': 3650.75, 'rsi': 68, 'adx': 31, 'volume_ratio': 1.95, 'strength': 79},
        {'symbol': 'HDFCBANK', 'price': 1980.30, 'rsi': 60, 'adx': 24, 'volume_ratio': 1.65, 'strength': 72},
        {'symbol': 'ICICIBANK', 'price': 1250.80, 'rsi': 64, 'adx': 27, 'volume_ratio': 2.05, 'strength': 78},
        {'symbol': 'WIPRO', 'price': 420.50, 'rsi': 58, 'adx': 22, 'volume_ratio': 1.55, 'strength': 68},
        {'symbol': 'MARUTI', 'price': 12850.20, 'rsi': 66, 'adx': 29, 'volume_ratio': 1.75, 'strength': 75},
        {'symbol': 'ASIANPAINT', 'price': 3280.90, 'rsi': 61, 'adx': 25, 'volume_ratio': 1.45, 'strength': 70},
    ]

    return {
        'timestamp': timestamp,
        'scan_date': datetime.now(ist).strftime('%Y-%m-%d %H:%M IST'),
        'stocks_found': len(mock_stocks),
        'results': mock_stocks
    }


def display_results(data):
    """Display results in Telegram format"""
    print("\n" + "="*60)
    print("NSE F&O PCS Scanner - TEST OUTPUT")
    print("="*60 + "\n")

    print(f"NSE F&O PCS Scanner Results")
    print(f"{data['scan_date']}\n")
    print(f"Found: {data['stocks_found']} stocks\n")

    for i, stock in enumerate(data['results'], 1):
        confidence = "HIGH" if stock['strength'] >= 80 else "MEDIUM" if stock['strength'] >= 70 else "LOW"
        print(f"{i}. {stock['symbol']}")
        print(f"   Price: Rs {stock['price']:,.2f}")
        print(f"   RSI: {stock['rsi']:.0f} | ADX: {stock['adx']:.0f}")
        print(f"   Volume: {stock['volume_ratio']:.2f}x | Strength: {stock['strength']:.0f}%")
        print(f"   Confidence: {confidence}\n")

    print("Parameters:")
    print("- Min Pattern Strength: 65%")
    print("- Volume Ratio: 1.0x minimum")
    print("- ADX Minimum: 15")
    print("- RSI Range: 30-80\n")

    print("Disclaimer: For research purposes only.")
    print("="*60 + "\n")


def main():
    """Test the scanner output"""
    print("Generating test data...")
    data = generate_mock_results()

    print("\n1. TELEGRAM MESSAGE OUTPUT:")
    print("-" * 60)
    display_results(data)

    print("\n2. JSON OUTPUT:")
    print("-" * 60)
    print(json.dumps(data, indent=2))

    print("\n3. SAVING TO FILE:")
    print("-" * 60)
    filename = f"/tmp/test_pcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to: {filename}")

    print("\n✓ TEST COMPLETE")
    print("  - The scanner output format is shown above")
    print("  - Results are saved as JSON for processing")
    print("  - Messages are sent to Telegram when configured")
    print("\nTo run the real scanner:")
    print("  python3 run_scanner_simple.py")


if __name__ == "__main__":
    main()
