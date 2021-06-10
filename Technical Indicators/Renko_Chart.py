# -*- coding: utf-8 -*-
"""
Created on Sat Jun  5 08:10:24 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
from stocktrends import Renko

ticker = "AAPL"
ohlcv = yf.download(ticker,dt.date.today()-dt.timedelta(365),dt.datetime.today())

def ATR(data, n):
    df = data.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC'] = abs(df['High']-df['Adj Close'].shift(1))
    df['L-PC'] = abs(df['Low']-df['Adj Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df.drop(['H-L', 'H-PC', 'L-PC'], axis=1, inplace = True)
    #df.dropna(inplace=True)
    return df


def Renko_data(data):
    df = data.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:, [0,1,2,3,5,6]]
    df.columns=['date', 'open', 'high', 'low', 'close', 'volume']
    renko_df = Renko(df)
    renko_df.brick_size=round(ATR(df, 120)['ATR'][-1], 0)
    dfr = renko_df.get_ohlc_data()
    return dfr

renko = Renko_data(ohlcv)