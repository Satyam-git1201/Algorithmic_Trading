# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 09:12:38 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

ticker = 'MSFT'
ohlcv = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

#Average True Range Function
def ATR(data, n):
    df = data.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC'] = abs(df['High']-df['Adj Close'].shift(1))
    df['L-PC'] = abs(df['Low']-df['Adj Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df.drop(['H-L', 'H-PC', 'L-PC'], axis=1, inplace = True)
    df.dropna(inplace=True)
    return df
    
ATR(ohlcv, 20)

#Bollinger Band Function
n=20
def Bollinger(Data, n):
    df = Data.copy()
    df['MA'] = df['Adj Close'].rolling(n).mean()
    df['BB_up'] = df['MA'] + 2*df['MA'].rolling(n).std()
    df['BB_down'] = df['MA'] - 2*df['MA'].rolling(n).std()
    df['Range'] = df['BB_up']-df['BB_down']
    df.dropna(inplace=True)
    return df
Bollinger_band = Bollinger(ohlcv, 20)
Bollinger_band.iloc[-100:,[-4, -3, -2]].plot()    #Band Visualization

