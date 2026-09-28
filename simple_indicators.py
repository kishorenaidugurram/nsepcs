"""
Simple technical indicators implementation to replace the 'ta' library
"""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

class RSI:
    @staticmethod
    def rsi(df, column='Close', length=14):
        """Calculate Relative Strength Index"""
        if len(df) < length + 1:
            return pd.Series([np.nan] * len(df), index=df.index)

        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class MACD:
    @staticmethod
    def macd(df, column='Close', fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = df[column].ewm(span=fast).mean()
        ema_slow = df[column].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

class BBands:
    @staticmethod
    def bollinger_bands(df, column='Close', length=20, std=2):
        """Calculate Bollinger Bands"""
        sma = df[column].rolling(window=length).mean()
        std_dev = df[column].rolling(window=length).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        return upper_band, sma, lower_band

class ADX:
    @staticmethod
    def adx(df, length=14):
        """Calculate Average Directional Index"""
        high_diff = df['High'].diff()
        low_diff = -df['Low'].diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        tr = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift()),
            abs(df['Low'] - df['Close'].shift())
        ], axis=1).max(axis=1)

        atr = tr.rolling(window=length).mean()

        plus_di = 100 * (plus_dm.rolling(window=length).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=length).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=length).mean()

        return adx, plus_di, minus_di

class Momentum:
    @staticmethod
    def momentum(df, column='Close', length=20):
        """Calculate Momentum"""
        return df[column] - df[column].shift(length)

class SMA:
    @staticmethod
    def sma(df, column='Close', length=20):
        """Calculate Simple Moving Average"""
        return df[column].rolling(window=length).mean()

class EMA:
    @staticmethod
    def ema(df, column='Close', length=20):
        """Calculate Exponential Moving Average"""
        return df[column].ewm(span=length).mean()

class TA:
    """Wrapper class to mimic ta library structure"""

    @staticmethod
    def rsi(df, column='Close', length=14, **kwargs):
        return RSI.rsi(df, column, length)

    @staticmethod
    def macd(df, column='Close', fast=12, slow=26, signal=9, **kwargs):
        macd_line, signal_line, histogram = MACD.macd(df, column, fast, slow, signal)
        return pd.DataFrame({
            'macd': macd_line,
            'macdh': histogram,
            'macds': signal_line
        })

    @staticmethod
    def bbands(df, column='Close', length=20, std=2, **kwargs):
        upper, middle, lower = BBands.bollinger_bands(df, column, length, std)
        return pd.DataFrame({
            'BBU': upper,
            'BBM': middle,
            'BBL': lower
        })

    @staticmethod
    def adx(df, length=14, **kwargs):
        adx_val, plus_di, minus_di = ADX.adx(df, length)
        return pd.DataFrame({
            'ADX': adx_val,
            'DMP': plus_di,
            'DMN': minus_di
        })

    @staticmethod
    def momentum(df, column='Close', length=20, **kwargs):
        return Momentum.momentum(df, column, length)

    @staticmethod
    def sma(df, column='Close', length=20, **kwargs):
        return SMA.sma(df, column, length)

    @staticmethod
    def ema(df, column='Close', length=20, **kwargs):
        return EMA.ema(df, column, length)

# Create default instance for direct access
ta = TA()
