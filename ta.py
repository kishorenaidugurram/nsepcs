"""
Minimal technical analysis wrapper for streamlit_app.py
Implements indicators directly using pandas/numpy
"""

import pandas as pd
import numpy as np

class momentum:
    @staticmethod
    def RSIIndicator(close, window=14):
        class RSIWrapper:
            def __init__(self, rsi_values):
                self._rsi = rsi_values
            def rsi(self):
                return self._rsi

        # Calculate RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return RSIWrapper(rsi)

    @staticmethod
    def WilliamsRIndicator(high, low, close, window=14):
        class WRWrapper:
            def __init__(self, wr_values):
                self._wr = wr_values
            def williams_r(self):
                return self._wr

        # Calculate Williams %R
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)

        return WRWrapper(wr)

    @staticmethod
    def StochasticOscillator(high, low, close, window=14, smooth_k=3, smooth_d=3):
        class StochWrapper:
            def __init__(self, stoch_values):
                self._stoch = stoch_values
            def stoch(self):
                return self._stoch

        # Calculate Stochastic
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        stoch_k = k_percent.rolling(window=smooth_k).mean()

        return StochWrapper(stoch_k)

class trend:
    @staticmethod
    def SMAIndicator(close, window=20):
        class SMAWrapper:
            def __init__(self, sma_values):
                self._sma = sma_values
            def sma_indicator(self):
                return self._sma
        return SMAWrapper(close.rolling(window=window).mean())

    @staticmethod
    def EMAIndicator(close, window=20):
        class EMAWrapper:
            def __init__(self, ema_values):
                self._ema = ema_values
            def ema_indicator(self):
                return self._ema
        return EMAWrapper(close.ewm(span=window, adjust=False).mean())

    @staticmethod
    def MACD(close, fast=12, slow=26, signal=9):
        class MACDWrapper:
            def __init__(self, macd_values, signal_values, hist_values):
                self._macd = macd_values
                self._signal = signal_values
                self._hist = hist_values

            def macd(self):
                return self._macd

            def macd_signal(self):
                return self._signal

            def macd_diff(self):
                return self._hist

        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return MACDWrapper(macd, signal_line, histogram)

    @staticmethod
    def ADXIndicator(high, low, close, window=14):
        class ADXWrapper:
            def __init__(self, adx_values):
                self._adx = adx_values
            def adx(self):
                return self._adx

        # Simplified ADX calculation
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm = plus_dm.where(plus_dm > 0, 0)
        minus_dm = minus_dm.where(minus_dm > 0, 0)

        plus_di = 100 * (plus_dm.rolling(window=window).mean() / (high - low).rolling(window=window).mean())
        minus_di = 100 * (minus_dm.rolling(window=window).mean() / (high - low).rolling(window=window).mean())

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=window).mean()

        return ADXWrapper(adx)

class volatility:
    @staticmethod
    def BollingerBands(close, window=20, std=2):
        class BBWrapper:
            def __init__(self, upper, lower, middle):
                self._upper = upper
                self._lower = lower
                self._middle = middle
            def bollinger_hband(self):
                return self._upper
            def bollinger_lband(self):
                return self._lower
            def bollinger_mavg(self):
                return self._middle

        sma = close.rolling(window=window).mean()
        std_dev = close.rolling(window=window).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return BBWrapper(upper, lower, sma)

    @staticmethod
    def AverageTrueRange(high, low, close, window=14):
        class ATRWrapper:
            def __init__(self, atr_values):
                self._atr = atr_values
            def average_true_range(self):
                return self._atr

        # Calculate True Range
        hl = high - low
        hc = abs(high - close.shift(1))
        lc = abs(low - close.shift(1))
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()

        return ATRWrapper(atr)
