# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 08:04:20 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

ticker = 'MSFT'
ohlcv = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

def MACD(data, a, b, c):
    df = data.copy()
    df['MA_fast']=df['Adj Close'].ewm(span=a, min_periods=a).mean()
    df['MA_slow']=df['Adj Close'].ewm(span=b, min_periods=b).mean()
    df['MACD'] = df['MA_fast']-df['MA_slow']
    df['Signal'] = df['MACD'].ewm(span=c, min_periods=c).mean()
    df.dropna(inplace=True)
    return df

MACD(ohlcv, 12, 26,9).iloc[:, [5,8,9]].plot()
plt.style.use('seaborn-dark')