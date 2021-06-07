# -*- coding: utf-8 -*-
"""
Created on Sat Jun  5 06:47:46 2021

@author: kumar
"""
import yfinance as yf
import numpy as np
import datetime as dt
import statsmodels.api as sm
import pandas as pd

# Download historical data for required stocks
ticker = "AAPL"
ohlcv = yf.download(ticker,dt.date.today()-dt.timedelta(1825),dt.datetime.today())

#function to determine slope

def slope(series,n):
     
    slope = [i*0 for i in range(n-1)]
    for i in range(n, len(series)+1):
        y = series[i-n:i]
        x = np.array(range(n))
        y_scaled = (y-y.min())/(y.max()-y.min())
        x_scaled = (x-x.min())/(x.max()-x.min())
        x_scaled = sm.add_constant(x_scaled)     #adds constant column so that mapping occurs on y=mx+c
        model = sm.OLS(y_scaled, x_scaled)
        results = model.fit()
        #results.summary()
        slope.append(results.params[-1])
    slopes_angle = (np.rad2deg(np.arctan(np.array(slope)))) 
    return np.array(slopes_angle)
    
ohlcv['Slopes']=slope(ohlcv['Adj Close'], 5)   

ohlcv.iloc[:, [4,6]].plot(subplots=True)


    