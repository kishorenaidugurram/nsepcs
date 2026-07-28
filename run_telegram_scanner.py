#!/usr/bin/env python3
"""
Headless NSE F&O PCS Scanner with Telegram Integration
Simplified stock trend analyzer that sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import logging
import yfinance as yf
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Top NSE F&O stocks (by liquidity/volume)
TOP_NSE_FO_STOCKS = [
    'NIFTY.NS', 'BANKNIFTY.NS',
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS',
    'LT.NS', 'ITC.NS', 'AXISBANK.NS', 'HDFC.NS', 'KOTAKBANK.NS', 'MARUTI.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'ASIANPAINT.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS',
    'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS',
    'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS',
    'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS',
    'BHARTIARTL.NS', 'BPCL.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS',
    'BRITANNIA.NS', 'COLPAL.NS', 'DABUR.NS', 'MARICO.NS', 'GODREJCP.NS',
    'BOSCHLTD.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'EICHERMOT.NS', 'CUMMINSIND.NS'
]


class SimpleStockAnalyzer:
    """Simplified stock analyzer using yfinance"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data using yfinance"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data is None or len(data) < 20:
                logger.debug(f"Insufficient data for {symbol}: {len(data) if data is not None else 0} rows")
                return None

            # Calculate basic technical indicators
            data['RSI'] = self._calculate_rsi(data['Close'], 14)
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['EMA_20'] = data['Close'].ewm(span=20).mean()

            # Bollinger Bands
            bb_mid = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_upper'] = bb_mid + (bb_std * 2)
            data['BB_lower'] = bb_mid - (bb_std * 2)
            data['BB_middle'] = bb_mid

            # MACD
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            data['MACD'] = ema_12 - ema_26
            data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
            data['MACD_hist'] = data['MACD'] - data['MACD_signal']

            # ADX (simplified)
            data['ADX'] = self._calculate_adx(data, 14)

            # ATR
            data['ATR'] = self._calculate_atr(data, 14)

            return data
        except Exception as e:
            logger.debug(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        try:
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            rsi = np.zeros_like(prices)
            rsi[:period] = 100. - 100. / (1. + rs)

            for i in range(period, len(prices)):
                delta = deltas[i-1]
                if delta > 0:
                    upval = delta
                    downval = 0.
                else:
                    upval = 0.
                    downval = -delta

                up = (up * (period - 1) + upval) / period
                down = (down * (period - 1) + downval) / period
                rs = up / down if down != 0 else 0
                rsi[i] = 100. - 100. / (1. + rs)

            return pd.Series(rsi, index=prices.index)
        except:
            return pd.Series(50, index=prices.index)  # Default neutral RSI

    def _calculate_adx(self, data, period=14):
        """Calculate simplified ADX"""
        try:
            high_diff = data['High'].diff()
            low_diff = -data['Low'].diff()

            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

            tr = np.maximum(
                data['High'] - data['Low'],
                np.maximum(
                    abs(data['High'] - data['Close'].shift()),
                    abs(data['Low'] - data['Close'].shift())
                )
            )

            atr = pd.Series(tr).rolling(window=period).mean()
            plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
            minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)

            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()

            return adx
        except:
            return pd.Series(20, index=data.index)  # Default neutral ADX

    def _calculate_atr(self, data, period=14):
        """Calculate ATR"""
        try:
            tr = np.maximum(
                data['High'] - data['Low'],
                np.maximum(
                    abs(data['High'] - data['Close'].shift()),
                    abs(data['Low'] - data['Close'].shift())
                )
            )
            return pd.Series(tr).rolling(window=period).mean()
        except:
            return pd.Series(0, index=data.index)

    def detect_trends(self, data, symbol, config):
        """Detect trading trends based on technical indicators"""
        if data is None or len(data) < 2:
            return []

        try:
            results = []
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_macd = data['MACD'].iloc[-1]
            current_macd_signal = data['MACD_signal'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            ema_20 = data['EMA_20'].iloc[-1]

            # Check RSI filter
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                return []

            # Check ADX filter
            if pd.isna(current_adx) or current_adx < config['adx_min']:
                return []

            # Check MA support
            if config['ma_support']:
                ma_value = sma_20 if config['ma_type'] == 'SMA' else ema_20
                if pd.isna(ma_value) or current_price < ma_value * (1 - config['ma_tolerance']/100):
                    return []

            # Detect bullish trends
            if not pd.isna(current_macd) and not pd.isna(current_macd_signal):
                if current_macd > current_macd_signal and current_rsi < 70:
                    results.append({
                        'pattern_type': 'Bullish MACD Crossover',
                        'pattern_strength': min(100, current_adx * 1.5),
                        'confidence': 'HIGH' if current_adx > 30 else 'MEDIUM',
                        'support_level': sma_20,
                        'price': current_price,
                    })

                # Detect price above moving averages
                sma_50 = data['SMA_50'].iloc[-1]
                if not pd.isna(sma_20) and not pd.isna(sma_50):
                    if current_price > sma_20 and sma_20 > sma_50:
                        results.append({
                            'pattern_type': 'Bullish MA Stack',
                            'pattern_strength': min(100, (current_rsi - config['rsi_min']) / max(1, config['rsi_max'] - config['rsi_min']) * 100),
                            'confidence': 'MEDIUM',
                            'support_level': sma_20,
                            'price': current_price,
                        })

                # Detect RSI oversold bounce
                if config['rsi_min'] <= current_rsi < 40 and current_macd > current_macd_signal:
                    bb_lower = data['BB_lower'].iloc[-1]
                    results.append({
                        'pattern_type': 'Oversold Bounce Setup',
                        'pattern_strength': 100 - current_rsi,
                        'confidence': 'MEDIUM',
                        'support_level': bb_lower if not pd.isna(bb_lower) else sma_20,
                        'price': current_price,
                    })

            return results
        except Exception as e:
            logger.debug(f"Error detecting trends for {symbol}: {str(e)}")
            return []


def get_config():
    """Get scanner configuration with defaults"""
    return {
        'stocks_to_scan': TOP_NSE_FO_STOCKS,
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
    }


def run_scanner(config, limit_stocks=None):
    """Run the scanner analysis"""
    analyzer = SimpleStockAnalyzer()
    results = []
    stocks_to_scan = config['stocks_to_scan']

    if limit_stocks:
        stocks_to_scan = stocks_to_scan[:limit_stocks]

    logger.info(f"Starting scan of {len(stocks_to_scan)} stocks...")

    total = len(stocks_to_scan)
    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            logger.info(f"[{i+1}/{total}] Analyzing {clean_symbol}...")

            # Get stock data
            data = analyzer.get_stock_data(symbol, period="3mo")
            if data is None:
                logger.debug(f"  ✗ No data available for {clean_symbol}")
                continue

            # Detect trends
            trends = analyzer.detect_trends(data, symbol, config)

            if not trends:
                logger.debug(f"  ✗ No trends detected for {clean_symbol}")
                continue

            # Process each trend
            for trend in trends:
                result = {
                    'symbol': clean_symbol,
                    'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                    'price': data['Close'].iloc[-1],
                    'pattern': trend.get('pattern_type', 'Unknown'),
                    'strength': trend.get('pattern_strength', 0),
                    'confidence': trend.get('confidence', 'MEDIUM'),
                }

                # Add pattern-specific details
                for key in ['support_level']:
                    if key in trend:
                        result[key] = trend[key]

                results.append(result)
                logger.info(f"  ✓ {clean_symbol}: {trend.get('pattern_type', 'Unknown')} "
                          f"(₹{data['Close'].iloc[-1]:.2f}, strength: {trend.get('pattern_strength', 0):.0f}%)")

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {str(e)}")
            continue

    logger.info(f"Scan complete! Found {len(results)} trend matches")
    return results


def format_telegram_message(results):
    """Format results for Telegram message"""
    if not results:
        return "📊 No patterns detected in today's NSE F&O scan."

    # Sort by strength
    results_sorted = sorted(results, key=lambda x: x.get('strength', 0), reverse=True)

    # Group by confidence level
    high_conf = [r for r in results_sorted if r.get('confidence') == 'HIGH']
    med_conf = [r for r in results_sorted if r.get('confidence') == 'MEDIUM']
    low_conf = [r for r in results_sorted if r.get('confidence') == 'LOW']

    ist = pytz.timezone('Asia/Kolkata')
    message = "🚀 <b>NSE F&O PCS Scanner Results</b>\n"
    message += f"📅 {datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')}\n"
    message += f"📊 Total Patterns: {len(results)}\n\n"

    if high_conf:
        message += f"<b>🟢 HIGH Confidence ({len(high_conf)})</b>\n"
        for r in high_conf[:5]:  # Show top 5
            msg = f"  • <code>{r['symbol']:<10}</code> {r['pattern']} | ₹{r['price']:.2f}\n"
            message += msg
        if len(high_conf) > 5:
            message += f"  ... and {len(high_conf) - 5} more\n"
        message += "\n"

    if med_conf:
        message += f"<b>🟡 MEDIUM Confidence ({len(med_conf)})</b>\n"
        for r in med_conf[:5]:  # Show top 5
            msg = f"  • <code>{r['symbol']:<10}</code> {r['pattern']} | ₹{r['price']:.2f}\n"
            message += msg
        if len(med_conf) > 5:
            message += f"  ... and {len(med_conf) - 5} more\n"
        message += "\n"

    if low_conf:
        message += f"<b>🔴 LOW Confidence ({len(low_conf)})</b>\n"
        for r in low_conf[:3]:  # Show top 3
            msg = f"  • <code>{r['symbol']:<10}</code> {r['pattern']} | ₹{r['price']:.2f}\n"
            message += msg
        if len(low_conf) > 3:
            message += f"  ... and {len(low_conf) - 3} more\n"

    message += "\n<i>⚠️ Not financial advice. Always DYOR before trading.</i>"

    return message


def send_telegram_message(message, chat_id=None, bot_token=None):
    """Send message to Telegram"""
    try:
        from telegram import Bot
        from telegram.error import TelegramError
    except ImportError:
        logger.error("Telegram bot library not installed. Install with: pip install python-telegram-bot")
        return False

    # Get credentials from environment
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured")
        logger.info("To enable Telegram notifications, set these environment variables:")
        logger.info("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        logger.info("  export TELEGRAM_CHAT_ID='your_chat_id'")
        return False

    try:
        bot = Bot(token=bot_token)
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        logger.info("✓ Message sent to Telegram successfully")
        return True
    except TelegramError as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {str(e)}")
        return False


def save_results_to_file(results, filename=None):
    """Save results to JSON file for backup"""
    if filename is None:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/pcs_scan_results_{timestamp}.json"

    try:
        # Convert to serializable format
        data = {
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            'total_results': len(results),
            'results': results
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Results saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save results: {str(e)}")
        return None


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("NSE F&O Stock Trend Scanner - Headless Mode")
    logger.info("="*60)

    # Get configuration
    config = get_config()

    # Run scanner (limit to first 50 stocks for quicker scan)
    results = run_scanner(config, limit_stocks=50)

    # Save results to file
    save_results_to_file(results)

    # Format and send Telegram message
    if results:
        message = format_telegram_message(results)

        # Print to stdout
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(message)
        print("="*60 + "\n")

        # Try to send to Telegram
        send_telegram_message(message)
    else:
        logger.warning("No results found in this scan")
        message = "📊 No patterns detected in today's NSE F&O scan."
        print(f"\n{message}\n")

    logger.info("Scan completed")


if __name__ == "__main__":
    main()
