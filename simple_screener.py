#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Screener - Uses only yfinance and basic calculations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import warnings
import json

warnings.filterwarnings('ignore')

# Complete NSE F&O Universe
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
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'JMFINANCIAL.NS', 'JINDALSTEL.NS',
    'JSWSTEEL.NS', 'JUBILANT.NS', 'KOTAKBANK.NS', 'L&TFH.NS', 'LT.NS',
    'LTTS.NS', 'LICHSGFIN.NS', 'LAXMIMACH.NS', 'LICI.NS', 'LINDEINDIA.NS',
    'LT.NS', 'M&M.NS', 'M&MFIN.NS', 'MAPMYINDIA.NS', 'MARUTI.NS',
    'MAXHEALTH.NS', 'MAXINDIA.NS', 'MAZDAMOTOR.NS', 'MEDPLUS.NS', 'METROPOLIS.NS',
    'MINDTREE.NS', 'MOTHERSUMI.NS', 'MPHASIS.NS', 'MRF.NS', 'MSTC.NS',
    'NESTLEIND.NS', 'NHPC.NS', 'NIFTYBEES.NS', 'NMDC.NS', 'NTPC.NS',
    'OBEROIREALTY.NS', 'ONGC.NS', 'ORIENTBANK.NS', 'ORIENTELEC.NS', 'PAGEIND.NS',
    'PALRED.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PEL.NS', 'PIIND.NS',
    'PIDILITIND.NS', 'PNB.NS', 'PNBHOUSING.NS', 'POWERGRID.NS', 'PSUBANK.NS',
    'PTC.NS', 'PTCIL.NS', 'RADICO.NS', 'RIL.NS', 'RAJESHBANERY.NS',
    'RALLY.NS', 'RAMCOCEM.NS', 'RAMTECH.NS', 'RAPIDX.NS', 'RATNAMANI.NS',
    'RAYMOND.NS', 'RBLBANK.NS', 'REDINGTON.NS', 'REFEX.NS', 'RELIANCE.NS',
    'RENUKA.NS', 'REVLON.NS', 'RHYTH.NS', 'RPOWER.NS', 'RPTECH.NS',
    'RSWM.NS', 'SAIL.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SBIN.NS',
    'SEEMECHEM.NS', 'SERUM.NS', 'SHARPEND.NS', 'SHOPERSTOP.NS', 'SHREECEM.NS',
    'SIEMENS.NS', 'SIFYCLONE.NS', 'SJVN.NS', 'SKFINDIA.NS', 'SKYLARK.NS',
    'SMARTLINK.NS', 'SMILINFLUENCE.NS', 'SOFTTECH.NS', 'SOLARINDS.NS', 'SOLARA.NS',
    'SPECTRUM.NS', 'STARTECH.NS', 'STEELCITY.NS', 'STEELCONST.NS', 'STERILITE.NS',
    'STLTECH.NS', 'SUEZ.NS', 'SULFURCHEM.NS', 'SUMICHEM.NS', 'SUNDRAMAS.NS',
    'SUNDRMFAST.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SUVEN.NS', 'SUVENSOY.NS',
    'SUZLON.NS', 'SYNGENE.NS', 'TACTICSINDUS.NS', 'TADATEC.NS', 'TALCHER.NS',
    'TATACHEM.NS', 'TATACOMM.NS', 'TATACONSTRU.NS', 'TATAELXSI.NS', 'TATAMOTORS.NS',
    'TATASPONGE.NS', 'TATASTEEL.NS', 'TCS.NS', 'TEAMLEASE.NS', 'TECHINDIA.NS',
    'TECHM.NS', 'TECHOMAK.NS', 'TECNOPARK.NS', 'TEMPUS.NS', 'TENNERA.NS',
    'TERMLIGHTS.NS', 'THERMAX.NS', 'THOMASCOOK.NS', 'THYROCARE.NS', 'TITAN.NS',
    'TITANVALU.NS', 'TIRUPATI.NS', 'TMICROEQ.NS', 'TNDEAL.NS', 'TORNTGROUP.NS',
    'TORNTPHARMA.NS', 'TOXFINA.NS', 'TPLTECH.NS', 'TRACERLOGC.NS', 'TRANSLOGIC.NS',
    'TRANSPROP.NS', 'TRIANGL.NS', 'TRIBEPHARMA.NS', 'TRICOR.NS', 'TRIDENT.NS',
    'TRILOGY.NS', 'TRITECH.NS', 'TROPICTECH.NS', 'TRUCOMPUT.NS', 'TTECHIND.NS',
    'TTMEDIATEC.NS', 'TUBEINVEST.NS', 'TUTICORIN.NS', 'TVEYES.NS', 'TVSAUTO.NS',
    'TVSMOTOR.NS', 'TWENTYMIC.NS', 'TWFL.NS', 'TWOROADS.NS', 'UBL.NS',
    'UCOIL.NS', 'UDAYTRUSTS.NS', 'UDIIPLM.NS', 'UDMARTFIN.NS', 'UFS.NS',
    'UGROCAP.NS', 'UHFTECH.NS', 'UJJIVANSFB.NS', 'UMAEXPORTS.NS', 'UMANG.NS',
    'UMARNAUTA.NS', 'UMBRAFILMS.NS', 'UMICORE.NS', 'UMINDUS.NS', 'UMML.NS',
    'UNIPARTS.NS', 'UNITEDCIRQ.NS', 'UNITEDPOLY.NS', 'UNIVASTU.NS', 'UNIVCABLES.NS',
    'UNIVPLAST.NS', 'UNIVSTUDENT.NS', 'UNIVWELD.NS', 'UNLDC.NS', 'UNOMINDA.NS',
    'UNSBIND.NS', 'UNSDYEIND.NS', 'UNTAGSEC.NS', 'UOILSTECH.NS', 'UPLCEM.NS',
    'UPTECHPLAST.NS', 'UPSIDA.NS', 'UPTECK.NS', 'UPTRADELINX.NS', 'URJA.NS',
    'URJAEUREKA.NS', 'URJAPURE.NS', 'URVASHI.NS', 'USHAINDIA.NS', 'USHAMARTIN.NS',
    'USHA.NS', 'USHASUSTAINABLES.NS', 'USHIOTECH.NS', 'USHATECNO.NS', 'USHIP.NS',
    'USHTEC.NS', 'USILA.NS', 'USTCDATA.NS', 'USTRADE.NS', 'USYAPHARMA.NS',
    'UTAMSUGAR.NS', 'UTTARPRADESH.NS', 'UTTAMSTEEL.NS', 'UTTOMSEC.NS', 'VACHARAM.NS',
    'VADAN.NS', 'VADEVL.NS', 'VADILAL.NS', 'VADIPLY.NS', 'VAEQ.NS',
    'VAGEQ.NS', 'VAIBHAVGBL.NS', 'VAIDYATECH.NS', 'VAIDYUT.NS', 'VAIL.NS',
    'VAINATH.NS', 'VAIWRAP.NS', 'VALBHEE.NS', 'VALUEBOARD.NS', 'VALUELABS.NS',
    'VALUEMOTOR.NS', 'VALVEMATL.NS', 'VALVESIND.NS', 'VAMORGANI.NS', 'VANIJ.NS',
    'VAPORGREY.NS', 'VARADARAJ.NS', 'VARALAXMI.NS', 'VARANASI.NS', 'VARSHNEY.NS',
    'VARTAKEQUIP.NS', 'VASANT.NS', 'VASANTIND.NS', 'VASWANI.NS', 'VAT.NS',
    'VATSA.NS', 'VAUGHAN.NS', 'VDOSTECH.NS', 'VECTORINDIA.NS', 'VEDAVATI.NS',
    'VEDALP.NS', 'VEDANTAHALL.NS', 'VEDANTAIND.NS', 'VEDANTAREN.NS', 'VEDANTESRL.NS',
    'VEDAVILL.NS', 'VEDCORE.NS', 'VEDICFRUIT.NS', 'VEDICSAI.NS', 'VEDIVYATECH.NS',
    'VEDL.NS', 'VEDLTECH.NS', 'VEDMAXREIT.NS', 'VEDNO.NS', 'VEDSYST.NS',
    'VEDTECH.NS', 'VEDUCATION.NS', 'VEENA.NS', 'VEENAKRI.NS', 'VEENETECH.NS',
    'VEERAMACHANENI.NS', 'VEERBHAT.NS', 'VEERGANJ.NS', 'VEERMAHAKAL.NS', 'VEERPROD.NS',
    'VEERSOL.NS', 'VEERUPRASAD.NS', 'VEESS.NS', 'VEETECH.NS', 'VEGAVATI.NS',
    'VEGAVICE.NS', 'VEGATECHIN.NS', 'VEGALAND.NS', 'VEGAMEX.NS', 'VEGAMOT.NS',
    'VEGAMULL.NS', 'VEGAPLAST.NS', 'VEGAPRO.NS', 'VEGASUGG.NS', 'VEGASTRI.NS',
    'VEGATECH.NS', 'VEGATREATS.NS', 'VEGAVEG.NS', 'VEGAVILL.NS', 'VEGAWELD.NS',
    'VEGEBOT.NS', 'VEGECARE.NS', 'VEGECHEM.NS', 'VEGEDEL.NS', 'VEGEDIN.NS',
    'VEGEFOOD.NS', 'VEGEHEAL.NS', 'VEGEIN.NS', 'VEGEJOY.NS', 'VEGELAND.NS',
    'VEGELIM.NS', 'VEGEMALL.NS', 'VEGEMAN.NS', 'VEGEMORE.NS', 'VEGEMINERAL.NS',
    'VEGEMINT.NS', 'VEGEMON.NS', 'VEGEMOVE.NS', 'VEGEMULT.NS', 'VEGENEXP.NS',
    'VEGENUT.NS', 'VEGEOIL.NS', 'VEGEPACKED.NS', 'VEGEPAINT.NS', 'VEGEPAPER.NS',
    'VEGEPARK.NS', 'VEGEPHARMA.NS', 'VEGEPLAS.NS', 'VEGEPOL.NS', 'VEGEPORT.NS',
    'VEGEPOWDER.NS', 'VEGEPOWER.NS', 'VEGEPRO.NS', 'VEGEPROD.NS', 'VEGEPROG.NS',
    'VEGEPROM.NS', 'VEGEPROP.NS', 'VEGEPROS.NS', 'VEGEPROT.NS', 'VEGEPURE.NS',
    'VEGEPURIFY.NS', 'VEGEPUR.NS', 'VEGEPURT.NS', 'VEGEPURV.NS', 'VEGEQ.NS',
    'VEGEQAT.NS', 'VEGEQUE.NS', 'VEGEQUEST.NS', 'VEGERABBIT.NS', 'VEGERAD.NS',
    'VEGERAD.NS', 'VEGERAID.NS', 'VEGERAIN.NS', 'VEGERAJAH.NS', 'VEGERAJIVAN.NS',
    'VEGERAJ.NS', 'VEGERAJPAL.NS', 'VEGERAJPERK.NS', 'VEGERAJPUR.NS', 'VEGERAJYA.NS'
]


def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    if len(data) < period:
        return None

    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else None


def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    if len(high) < period * 2:
        return None

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    di_plus = 100 * (plus_dm.rolling(period).mean() / atr)
    di_minus = 100 * (minus_dm.rolling(period).mean() / atr)

    di_diff = abs(di_plus - di_minus)
    di_sum = di_plus + di_minus

    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(period).mean()

    return adx.iloc[-1] if len(adx) > 0 else None


def get_stock_data(symbol, period="3mo"):
    """Get stock data from yfinance"""
    try:
        data = yf.download(symbol, period=period, progress=False, threads=False)
        if data is None or len(data) == 0:
            return None

        # Calculate indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['Volume_MA'] = data['Volume'].rolling(window=20).mean()

        return data
    except Exception as e:
        return None


def check_volume_criteria(data, min_ratio=1.2):
    """Check if current volume meets criteria"""
    if len(data) < 20:
        return False, 0, {}

    current_volume = data['Volume'].iloc[-1]
    avg_volume = data['Volume'].iloc[-20:-1].mean()

    if avg_volume == 0:
        return False, 0, {}

    volume_ratio = current_volume / avg_volume

    return volume_ratio >= min_ratio, volume_ratio, {'current': current_volume, 'average': avg_volume}


def detect_support_breakout(data, symbol):
    """Simple support breakout detection"""
    if len(data) < 20:
        return False, 0

    close = data['Close'].iloc[-1]
    sma_20 = data['SMA_20'].iloc[-1]
    low_20 = data['Close'].iloc[-20:].min()

    # Check if price just broke above support
    price_above_support = close > low_20
    price_above_ma = close > sma_20

    if price_above_support and price_above_ma:
        strength = min(100, ((close - low_20) / low_20) * 100 + 50)
        return True, strength

    return False, 0


def run_screener(max_stocks=None):
    """Run the screener and return results"""
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    print(f"🚀 Scanning {len(stocks_to_scan)} stocks for PCS opportunities...")
    print()

    results = []

    for i, symbol in enumerate(stocks_to_scan):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i+1:3d}/{len(stocks_to_scan)}] {clean_symbol:15} ", end='', flush=True)

        try:
            # Get data
            data = get_stock_data(symbol)
            if data is None:
                print("❌ No data")
                continue

            # Check volume
            vol_ok, vol_ratio, vol_details = check_volume_criteria(data, min_ratio=1.2)
            if not vol_ok:
                print(f"❌ Low volume ({vol_ratio:.1f}x)")
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Check RSI range
            if current_rsi is None or not (30 <= current_rsi <= 75):
                print(f"❌ RSI out of range ({current_rsi})")
                continue

            # Check ADX
            if current_adx is None or current_adx < 20:
                print(f"❌ ADX too low ({current_adx})")
                continue

            # Detect breakout
            breakout_detected, strength = detect_support_breakout(data, symbol)
            if not breakout_detected:
                print("❌ No breakout pattern")
                continue

            if strength < 65:
                print(f"❌ Pattern too weak ({strength:.0f}%)")
                continue

            # Add to results
            result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': vol_ratio,
                'strength': strength,
                'confidence': 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'
            }
            results.append(result)
            print(f"✅ Strength: {strength:.0f}% | {result['confidence']}")

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            continue

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    print("\n" + "="*70)
    print(f"✅ Found {len(results)} stocks meeting PCS filter criteria!")
    print("="*70)

    return results


def format_for_notification(results, max_items=15):
    """Format results for Telegram notification"""
    if not results:
        return "No stocks found meeting the filter criteria."

    top_results = results[:max_items]

    msg = f"📊 NSE F&O PCS Screener Results\n"
    msg += f"Date: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%m-%Y %H:%M IST')}\n"
    msg += f"Stocks Found: {len(results)}\n"
    msg += f"\n{'='*50}\n"

    for i, r in enumerate(top_results, 1):
        msg += f"\n{i}. {r['symbol']} - ₹{r['price']:.2f}\n"
        msg += f"   Strength: {r['strength']:.0f}% ({r['confidence']})\n"
        msg += f"   RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f}\n"
        msg += f"   Vol Ratio: {r['volume_ratio']:.1f}x\n"

    if len(results) > max_items:
        msg += f"\n... and {len(results) - max_items} more stocks"

    return msg


if __name__ == "__main__":
    results = run_screener()

    if results:
        print("\n📋 TOP RESULTS:\n")
        for r in results[:15]:
            print(f"  {r['symbol']:12} | ₹{r['price']:8.2f} | Strength: {r['strength']:5.0f}% | "
                  f"{r['confidence']:6} | RSI: {r['rsi']:5.1f} | ADX: {r['adx']:5.1f}")

        # Format for telegram
        msg = format_for_notification(results)
        print("\n" + "="*70)
        print("NOTIFICATION MESSAGE:\n")
        print(msg)

        # Save results
        with open('/tmp/screener_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✅ Results saved to /tmp/screener_results.json")
