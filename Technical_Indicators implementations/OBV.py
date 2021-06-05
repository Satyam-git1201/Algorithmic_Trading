# -*- coding: utf-8 -*-
"""
Created on Sat Jun  5 06:40:14 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt

# Download historical data for required stocks
ticker = "AAPL"
ohlcv = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

#function for On Balance Volume

def OBV(Data):
    df = Data.copy()
    df['trend']=df['Adj Close'].pct_change()
    df['direction']=np.where(df['trend']>=0, 1, -1)
    df['direction'][0] = 0
    df['vol_trend'] = df['Volume']*df['direction']
    df['OBV'] = df['vol_trend'].cumsum()
    return df

obv = OBV(ohlcv)
    