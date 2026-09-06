#!/usr/bin/env python3
"""
Standalone Telegram Stock Scanner
Analyzes NSE F&O stocks for trading opportunities and sends results to Telegram
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
import yfinance as yf
from typing import List, Dict, Optional, Tuple
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NSE F&O Stock Universe
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS',
    'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS', 'DIVISLAB.NS',
    'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS',
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS',
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS',
    'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS',
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS',
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'JKCEMENT.NS', 'JSWSTEEL.NS',
    'JUBILANT.NS', 'KALYANKJIL.NS', 'KANNANHOT.NS', 'KPITTECH.NS', 'KEC.NS',
    'KOTAKBANK.NS', 'KSCL.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS',
    'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LUPIN.NS', 'LUXIND.NS', 'MAPMYINDIA.NS',
    'MARUTI.NS', 'MCDOWELL-N.NS', 'METROPOLIS.NS', 'MFSL.NS', 'MGL.NS',
    'MINDTREE.NS', 'BAJAJFINSV.NS', 'MOTHERSUMI.NS', 'MPHASIS.NS', 'MRTI.NS',
    'MSUMI.NS', 'MTARTECH.NS', 'MUTHOOTFIN.NS', 'NIFTY.NS', 'BANKNIFTY.NS'
]


class SimpleStockAnalyzer:
    """Simple stock analyzer for technical pattern detection"""

    def __init__(self):
        self.logger = logger

    def get_stock_data(self, symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """Fetch stock data from Yahoo Finance"""
        try:
            df = yf.download(symbol, period=period, progress=False)
            if df is None or len(df) == 0:
                return None

            # Calculate technical indicators
            df['RSI'] = self._calculate_rsi(df['Close'])
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['EMA_20'] = df['Close'].ewm(span=20).mean()

            # Bollinger Bands
            ma = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = ma + (std * 2)
            df['BB_lower'] = ma - (std * 2)
            df['BB_middle'] = ma

            # MACD
            df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_hist'] = df['MACD'] - df['MACD_signal']

            # ADX approximation
            df['ADX'] = self._calculate_adx(df)

            # Volume analysis
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            return df.dropna()
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX approximation"""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        # Simple approximation
        return (abs(df['Close'].diff()) / atr * 100).rolling(period).mean()

    def is_bullish(self, df: pd.DataFrame) -> bool:
        """Check if stock shows bullish signals"""
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # Check multiple bullish conditions
        bullish_signals = 0

        # RSI between 45-65 (bullish momentum)
        if 45 <= latest['RSI'] <= 65:
            bullish_signals += 1

        # Price above SMA20
        if latest['Close'] > latest['SMA_20']:
            bullish_signals += 1

        # MACD histogram positive
        if latest['MACD_hist'] > 0:
            bullish_signals += 1

        # Volume above average
        if latest['Volume_Ratio'] > 1.2:
            bullish_signals += 1

        # ADX > 20 (strong trend)
        if latest['ADX'] > 20:
            bullish_signals += 1

        return bullish_signals >= 3

    def detect_patterns(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """Detect chart patterns"""
        patterns = []

        if len(df) < 20:
            return patterns

        latest = df.iloc[-1]

        # Pattern 1: Price above all key MAs (Uptrend)
        if (latest['Close'] > latest['EMA_20'] and
            latest['EMA_20'] > latest['SMA_50'] and
            latest['Close'] > latest['SMA_20']):

            strength = min(100, 50 + (latest['RSI'] - 40) * 0.5 + (latest['ADX'] - 20) * 2)
            patterns.append({
                'type': 'Uptrend (MA Alignment)',
                'strength': strength,
                'success_rate': 75,
                'pcs_suitability': 80,
                'confidence': 'HIGH' if strength >= 75 else 'MEDIUM'
            })

        # Pattern 2: Price near lower BB with RSI < 30 (Oversold bounce)
        if (latest['Close'] < latest['BB_lower'] * 1.05 and
            latest['RSI'] < 35):

            strength = min(100, 60 + (35 - latest['RSI']) + (latest['ADX'] - 15) * 1.5)
            patterns.append({
                'type': 'Oversold Bounce',
                'strength': strength,
                'success_rate': 70,
                'pcs_suitability': 85,
                'confidence': 'MEDIUM' if strength >= 70 else 'LOW'
            })

        # Pattern 3: MACD Crossover
        if len(df) > 2:
            prev_hist = df.iloc[-2]['MACD_hist']
            curr_hist = latest['MACD_hist']

            if prev_hist <= 0 and curr_hist > 0:  # Bullish crossover
                strength = min(100, 65 + (latest['RSI'] - 40))
                patterns.append({
                    'type': 'MACD Bullish Crossover',
                    'strength': strength,
                    'success_rate': 72,
                    'pcs_suitability': 80,
                    'confidence': 'MEDIUM'
                })

        # Pattern 4: Volume Breakout
        if latest['Volume_Ratio'] > 1.8 and latest['Close'] > latest['SMA_20']:
            strength = min(100, 70 + (latest['Volume_Ratio'] - 1.8) * 10)
            patterns.append({
                'type': 'Volume Breakout',
                'strength': strength,
                'success_rate': 76,
                'pcs_suitability': 75,
                'confidence': 'HIGH' if strength >= 75 else 'MEDIUM'
            })

        return patterns


class TelegramNotifier:
    """Send notifications to Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logger

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=10
            )
            if response.status_code == 200:
                self.logger.info("✓ Message sent to Telegram")
                return True
            else:
                self.logger.error(f"Telegram error: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error sending to Telegram: {e}")
            return False


def format_result_message(symbol: str, data: Dict) -> str:
    """Format stock result as Telegram message"""
    clean_symbol = symbol.replace('.NS', '')

    if not data.get('patterns'):
        return ""

    best_pattern = max(data['patterns'], key=lambda x: x['strength'])
    strength = best_pattern['strength']

    # Confidence emoji
    if strength >= 85:
        emoji = "🟢"
        conf_text = "HIGH"
    elif strength >= 70:
        emoji = "🟡"
        conf_text = "MEDIUM"
    else:
        emoji = "🔴"
        conf_text = "LOW"

    message = f"""
{emoji} <b>{clean_symbol}</b> - {conf_text}
━━━━━━━━━━━━
<b>Pattern:</b> {best_pattern['type']}
<b>Strength:</b> {strength:.0f}%
<b>Success Rate:</b> {best_pattern['success_rate']}%

<b>Price:</b> ₹{data['price']:.2f}
<b>RSI:</b> {data['rsi']:.1f}
<b>ADX:</b> {data['adx']:.1f}
<b>Vol Ratio:</b> {data['volume_ratio']:.2f}x
"""
    return message.strip()


def main():
    """Main execution"""

    # Get Telegram config
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("Missing Telegram credentials:")
        logger.error("  Set TELEGRAM_BOT_TOKEN")
        logger.error("  Set TELEGRAM_CHAT_ID")
        sys.exit(1)

    # Initialize components
    analyzer = SimpleStockAnalyzer()
    notifier = TelegramNotifier(bot_token, chat_id)

    logger.info("Starting NSE F&O Stock Analysis...")

    # Get stocks to analyze (limit to first 50 for testing)
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:50]

    results = []

    for i, symbol in enumerate(stocks_to_scan):
        clean_symbol = symbol.replace('.NS', '')
        logger.info(f"[{i+1}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...")

        try:
            # Get data
            df = analyzer.get_stock_data(symbol)
            if df is None or len(df) < 20:
                continue

            # Detect patterns
            patterns = analyzer.detect_patterns(df, symbol)
            if not patterns:
                continue

            # Filter HIGH confidence only
            high_conf_patterns = [p for p in patterns if p['strength'] >= 85]
            if not high_conf_patterns:
                continue

            # Get metrics
            latest = df.iloc[-1]

            result = {
                'symbol': symbol,
                'price': latest['Close'],
                'rsi': latest['RSI'],
                'adx': latest['ADX'],
                'volume_ratio': latest['Volume_Ratio'],
                'patterns': high_conf_patterns
            }

            results.append(result)

        except Exception as e:
            logger.warning(f"Error with {clean_symbol}: {e}")
            continue

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    if not results:
        logger.info("No HIGH confidence patterns found")
        notifier.send_message("📊 NSE F&O Scanner\n\nNo HIGH confidence patterns today.")
        return

    # Send header
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    header = f"""
📊 <b>NSE F&O Stock Scanner</b>
━━━━━━━━━━━━━━━━━━━
<b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}
<b>Found:</b> {len(results)} HIGH Confidence

Detailed results:
"""
    notifier.send_message(header)

    # Send individual results (top 10)
    for result in results[:10]:
        msg = format_result_message(result['symbol'], result)
        if msg:
            notifier.send_message(msg)
            time.sleep(0.5)  # Rate limiting

    if len(results) > 10:
        notifier.send_message(f"\n📈 +{len(results)-10} more stocks found")

    logger.info(f"✓ Sent {min(10, len(results))} results to Telegram")


if __name__ == "__main__":
    main()
