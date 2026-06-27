# Compatibility module for 'ta' library using talib
import talib
import numpy as np
import pandas as pd

class RSIIndicator:
    def __init__(self, close, window=14):
        self.close = close
        self.window = window
        self._rsi = None

    def rsi(self):
        if self._rsi is None:
            self._rsi = talib.RSI(np.array(self.close, dtype=float), timeperiod=self.window)
        return self._rsi

class SMAIndicator:
    def __init__(self, close, window=20):
        self.close = close
        self.window = window
        self._sma = None

    def sma_indicator(self):
        if self._sma is None:
            self._sma = talib.SMA(np.array(self.close, dtype=float), timeperiod=self.window)
        return self._sma

class EMAIndicator:
    def __init__(self, close, window=20):
        self.close = close
        self.window = window
        self._ema = None

    def ema_indicator(self):
        if self._ema is None:
            self._ema = talib.EMA(np.array(self.close, dtype=float), timeperiod=self.window)
        return self._ema

class BollingerBands:
    def __init__(self, close, window=20, window_dev=2):
        self.close = close
        self.window = window
        self.window_dev = window_dev
        self._upper = None
        self._lower = None
        self._middle = None

    def bollinger_hband(self):
        if self._upper is None:
            self._upper, self._middle, self._lower = talib.BBANDS(
                np.array(self.close, dtype=float),
                timeperiod=self.window,
                nbdevup=self.window_dev,
                nbdevdn=self.window_dev
            )
        return self._upper

    def bollinger_lband(self):
        if self._lower is None:
            self._upper, self._middle, self._lower = talib.BBANDS(
                np.array(self.close, dtype=float),
                timeperiod=self.window,
                nbdevup=self.window_dev,
                nbdevdn=self.window_dev
            )
        return self._lower

    def bollinger_mavg(self):
        if self._middle is None:
            self._upper, self._middle, self._lower = talib.BBANDS(
                np.array(self.close, dtype=float),
                timeperiod=self.window,
                nbdevup=self.window_dev,
                nbdevdn=self.window_dev
            )
        return self._middle

class MACD:
    def __init__(self, close, window_slow=26, window_fast=12, window_sign=9):
        self.close = close
        self._macd = None
        self._signal = None
        self._hist = None

    def macd(self):
        if self._macd is None:
            self._macd, self._signal, self._hist = talib.MACD(np.array(self.close, dtype=float))
        return self._macd

    def macd_signal(self):
        if self._signal is None:
            self._macd, self._signal, self._hist = talib.MACD(np.array(self.close, dtype=float))
        return self._signal

    def macd_diff(self):
        if self._hist is None:
            self._macd, self._signal, self._hist = talib.MACD(np.array(self.close, dtype=float))
        return self._hist

class ADXIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window
        self._adx = None

    def adx(self):
        if self._adx is None:
            self._adx = talib.ADX(
                np.array(self.high, dtype=float),
                np.array(self.low, dtype=float),
                np.array(self.close, dtype=float),
                timeperiod=self.window
            )
        return self._adx

class AverageTrueRange:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window
        self._atr = None

    def average_true_range(self):
        if self._atr is None:
            self._atr = talib.ATR(
                np.array(self.high, dtype=float),
                np.array(self.low, dtype=float),
                np.array(self.close, dtype=float),
                timeperiod=self.window
            )
        return self._atr

class StochasticOscillator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window
        self._k = None

    def stoch(self):
        if self._k is None:
            self._k, _ = talib.STOCH(
                np.array(self.high, dtype=float),
                np.array(self.low, dtype=float),
                np.array(self.close, dtype=float),
                fastk_period=self.window
            )
        return self._k

class WilliamsRIndicator:
    def __init__(self, high, low, close, window=14):
        self.high = high
        self.low = low
        self.close = close
        self.window = window
        self._wr = None

    def williams_r(self):
        if self._wr is None:
            self._wr = talib.WILLR(
                np.array(self.high, dtype=float),
                np.array(self.low, dtype=float),
                np.array(self.close, dtype=float),
                timeperiod=self.window
            )
        return self._wr

# Namespace classes for organization
class momentum:
    @staticmethod
    def RSIIndicator(close, window=14):
        return RSIIndicator(close, window)

    @staticmethod
    def StochasticOscillator(high, low, close, window=14):
        return StochasticOscillator(high, low, close, window)

    @staticmethod
    def WilliamsRIndicator(high, low, close, window=14):
        return WilliamsRIndicator(high, low, close, window)

class trend:
    @staticmethod
    def SMAIndicator(close, window=20):
        return SMAIndicator(close, window)

    @staticmethod
    def EMAIndicator(close, window=20):
        return EMAIndicator(close, window)

    @staticmethod
    def MACD(close, window_slow=26, window_fast=12, window_sign=9):
        return MACD(close, window_slow, window_fast, window_sign)

    @staticmethod
    def ADXIndicator(high, low, close, window=14):
        return ADXIndicator(high, low, close, window)

class volatility:
    @staticmethod
    def BollingerBands(close, window=20, window_dev=2):
        return BollingerBands(close, window, window_dev)

    @staticmethod
    def AverageTrueRange(high, low, close, window=14):
        return AverageTrueRange(high, low, close, window)
