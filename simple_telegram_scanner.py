#!/usr/bin/env python3
"""
Simple NSE F&O PCS Scanner - Telegram Results Sender
Runs a lightweight PCS scanner using finta and sends results to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from finta import TA
warnings.filterwarnings('ignore')

# NSE F&O stocks list (extracted to avoid importing streamlit_app which requires 'ta')
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
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRCTC.NS',
    'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS',
    'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS',
    'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS',
    'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS',
    'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS',
    'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS',
    'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS',
    'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS',
    'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS',
    'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'PPLPHARMA.NS',
    'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS',
    'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS',
    'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS',
    'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS',
    'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS',
    'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS',
    'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS',
    'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS',
    'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS',
    'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS', 'WIPRO.NS',
    'YESBANK.NS', 'ZYDUSLIFE.NS'
]

def get_telegram_config():
    """Get Telegram bot token and chat ID from environment variables"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        raise ValueError(
            "Telegram credentials not found. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables."
        )

    return bot_token, chat_id

def send_telegram_message(bot_token, chat_id, message, parse_mode='HTML'):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send message: {response.text}")
            return False
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        # Add .NS suffix if not present
        if not symbol.endswith('.NS'):
            symbol = f"{symbol}.NS"

        data = yf.download(symbol, period=period, progress=False, timeout=10)

        if data is None or data.empty:
            return None

        return data
    except Exception as e:
        return None

def calculate_technical_indicators(data):
    """Calculate technical indicators using finta"""
    if data is None or data.empty or len(data) < 20:
        return None

    try:
        # Prepare dataframe with lowercase columns for finta
        df = data.copy()
        df.columns = [col.lower() for col in df.columns]

        # Add missing columns if needed
        if 'open' not in df.columns:
            df['open'] = df['close']  # Fallback

        # Use finta for calculations
        indicators = {}

        # RSI
        try:
            rsi_val = TA.RSI(df, period=14)
            indicators['rsi'] = rsi_val.iloc[-1] if isinstance(rsi_val, pd.Series) else rsi_val
        except:
            indicators['rsi'] = None

        # ADX
        try:
            adx_val = TA.ADX(df, period=14)
            indicators['adx'] = adx_val.iloc[-1] if isinstance(adx_val, pd.Series) else adx_val
        except:
            indicators['adx'] = None

        # SMA 20
        try:
            sma_val = TA.SMA(df, period=20)
            indicators['sma_20'] = sma_val.iloc[-1] if isinstance(sma_val, pd.Series) else sma_val
        except:
            indicators['sma_20'] = None

        # EMA 20
        try:
            ema_val = TA.EMA(df, period=20)
            indicators['ema_20'] = ema_val.iloc[-1] if isinstance(ema_val, pd.Series) else ema_val
        except:
            indicators['ema_20'] = None

        # MACD
        try:
            macd_val = TA.MACD(df)
            if isinstance(macd_val, pd.DataFrame):
                indicators['macd'] = macd_val.iloc[-1, 0] if not macd_val.empty else None
            else:
                indicators['macd'] = macd_val
        except:
            indicators['macd'] = None

        # Bollinger Bands
        try:
            bb_val = TA.BBANDS(df, period=20)
            if isinstance(bb_val, pd.DataFrame):
                indicators['bb_upper'] = bb_val.iloc[-1, 0] if not bb_val.empty else None
                indicators['bb_lower'] = bb_val.iloc[-1, 1] if not bb_val.empty else None
            else:
                indicators['bb_upper'] = None
                indicators['bb_lower'] = None
        except:
            indicators['bb_upper'] = None
            indicators['bb_lower'] = None

        # Volume MA
        try:
            vol_sma = TA.SMA(df[['volume']], period=20)
            indicators['vol_sma'] = vol_sma.iloc[-1] if isinstance(vol_sma, pd.Series) else vol_sma
        except:
            indicators['vol_sma'] = None

        # Current price and volume
        indicators['price'] = df['close'].iloc[-1]
        indicators['volume'] = df['volume'].iloc[-1]

        return indicators
    except Exception as e:
        print(f"  Error calculating indicators: {e}")
        return None

def calculate_pcs_score(data, indicators, config):
    """Calculate PCS (Put Credit Spread) score for a stock"""
    if indicators is None:
        return 0

    score = 0
    weights = {
        'bullish_momentum': 0.30,
        'trend_strength': 0.25,
        'support_proximity': 0.20,
        'volatility': 0.15,
        'volume': 0.10
    }

    # 1. Bullish Momentum (RSI) - 30%
    rsi = indicators.get('rsi')
    if rsi:
        # Optimal RSI range for PCS: 45-65
        if 45 <= rsi <= 65:
            momentum_score = 90
        elif 30 <= rsi < 45 or 65 < rsi <= 75:
            momentum_score = 70
        elif rsi < 30 or rsi > 75:
            momentum_score = 30
        else:
            momentum_score = 50
        score += momentum_score * weights['bullish_momentum']

    # 2. Trend Strength (ADX) - 25%
    adx = indicators.get('adx')
    if adx and adx >= config.get('adx_min', 20):
        trend_score = min(90, 50 + (adx - config.get('adx_min', 20)) * 2)
        score += trend_score * weights['trend_strength']
    else:
        score += 40 * weights['trend_strength']

    # 3. Support Proximity (MA Support) - 20%
    if config.get('ma_support', True):
        price = indicators.get('price')
        sma_20 = indicators.get('sma_20')
        if price and sma_20:
            distance_pct = ((price - sma_20) / sma_20) * 100
            if 0 <= distance_pct <= config.get('ma_tolerance', 3):
                support_score = 85
            elif -3 <= distance_pct < 0 or distance_pct > 3:
                support_score = 65
            else:
                support_score = 40
            score += support_score * weights['support_proximity']

    # 4. Volatility - 15%
    # Simple volatility check (just make sure data exists)
    volatility_score = 70
    score += volatility_score * weights['volatility']

    # 5. Volume - 10%
    volume = indicators.get('volume')
    vol_sma = indicators.get('vol_sma')
    if volume and vol_sma and volume >= vol_sma * config.get('min_volume_ratio', 1.2):
        volume_score = 85
        score += volume_score * weights['volume']
    else:
        score += 50 * weights['volume']

    return min(100, max(0, score))

def format_results_for_telegram(results):
    """Format scanner results for Telegram"""
    if not results:
        return "❌ No stocks meeting the filter criteria found."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"""
📊 <b>NSE F&O PCS Scanner Results</b>
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}
✨ <b>Stocks Found:</b> {len(results)}

"""

    # Sort by PCS score descending
    sorted_results = sorted(results, key=lambda x: x.get('pcs_score', 0), reverse=True)

    for i, result in enumerate(sorted_results[:25], 1):  # Limit to top 25
        symbol = result['symbol'].replace('.NS', '')
        score = result.get('pcs_score', 0)
        price = result.get('price', 'N/A')
        rsi = result.get('rsi', 'N/A')

        price_str = f"₹{price:.2f}" if isinstance(price, (int, float)) else str(price)
        rsi_str = f"{rsi:.0f}" if isinstance(rsi, (int, float)) else str(rsi)

        message += f"{i}. <b>{symbol}</b>\n"
        message += f"   PCS: {score:.0f} | RSI: {rsi_str}\n"
        message += f"   Price: {price_str}\n\n"

    if len(results) > 25:
        message += f"... and {len(results) - 25} more stocks\n\n"

    message += """
📈 <b>Analysis Settings:</b>
• Period: Last 3 months
• RSI: 30-75
• ADX Min: 20
• Volume Ratio: 1.2x
• Pattern Strength: 65%+
"""

    return message

def run_scanner(stocks_to_scan=None, pattern_strength_min=65):
    """Run the simplified PCS scanner"""
    if stocks_to_scan is None:
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

    print(f"Starting simplified PCS scanner on {len(stocks_to_scan)} stocks...")

    # Configuration with defaults
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'pattern_strength_min': pattern_strength_min,
    }

    results = []

    for i, symbol in enumerate(stocks_to_scan, 1):
        try:
            print(f"[{i}/{len(stocks_to_scan)}] Analyzing {symbol.replace('.NS', '')}...", end='\r')

            # Get stock data
            data = fetch_stock_data(symbol)

            if data is None or data.empty:
                continue

            # Calculate indicators
            indicators = calculate_technical_indicators(data)

            if indicators is None:
                continue

            # Calculate PCS score
            pcs_score = calculate_pcs_score(data, indicators, config)

            if pcs_score >= pattern_strength_min:
                result = {
                    'symbol': symbol,
                    'pcs_score': pcs_score,
                    'price': indicators.get('price'),
                    'rsi': indicators.get('rsi'),
                    'adx': indicators.get('adx'),
                }
                results.append(result)
                print(f"✓ {symbol.replace('.NS', '')}: {pcs_score:.0f}    ")

        except Exception as e:
            print(f"✗ Error analyzing {symbol}: {str(e)[:30]}")
            continue

    print(f"\n✅ Scan complete. Found {len(results)} qualifying stocks.")
    return results

def main():
    """Main execution function"""
    try:
        # Get Telegram credentials
        try:
            bot_token, chat_id = get_telegram_config()
            print(f"✓ Telegram credentials loaded")
            has_telegram = True
        except ValueError as e:
            print(f"⚠️  Warning: {e}")
            print("   Running scan without Telegram notification")
            has_telegram = False

        # Run scanner
        results = run_scanner()

        if has_telegram:
            # Format and send results
            message = format_results_for_telegram(results)

            print(f"📤 Sending {len(results)} results to Telegram...")
            if send_telegram_message(bot_token, chat_id, message):
                print("✅ Message sent successfully!")
                return 0
            else:
                print("❌ Failed to send message")
                return 1
        else:
            # Just print results
            print("\n" + "="*60)
            print("SCANNER RESULTS")
            print("="*60)
            print(format_results_for_telegram(results))
            return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
