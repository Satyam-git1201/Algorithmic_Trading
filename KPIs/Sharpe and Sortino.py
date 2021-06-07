# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 07:28:26 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
import pandas as pd

ticker = '^GSPC'
SnP = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

def CAGR(data):
    df = data.copy()
    df['Daily Returns']=df['Adj Close'].pct_change()
    df['cum_return'] = (1+df['Daily Returns']).cumprod()
    n = len(df)/252                         #number of trading days in a typical year
    CAGR = (df['cum_return'][-1])**(1/n) - 1
    return CAGR

def volatility(data):
     df = data.copy()
     df['Daily Returns']=df['Adj Close'].pct_change()
     vol = df['Daily Returns'].std()*np.sqrt(252)
     return vol


def sharpe_ratio(data, rf):
    df = data.copy()
    sharpe = (CAGR(df)-rf)/volatility(df)
    return sharpe

sharpe_ratio(SnP, 0.022)



def sortino_ratio(data, rf):
    df=data.copy()
    df['Daily_Returns'] = df['Adj Close'].pct_change()
    neg_vol = df[df['Daily_Returns']<0]['Daily_Returns'].std()*np.sqrt(252)
    sortino = (CAGR(df)-rf)/neg_vol
    return sortino
sortino_ratio(SnP, 0.022)