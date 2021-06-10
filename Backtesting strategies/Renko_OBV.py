# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 22:40:50 2021

@author: kumar
"""
import numpy as np
import pandas as pd
from stocktrends import Renko
import statsmodels.api as sm
from alpha_vantage.timeseries import TimeSeries
import copy
import time

def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Adj Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Adj Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2

def slope(ser,n):
    "function to calculate the slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)

def OBV(DF):
    """function to calculate On Balance Volume"""
    df = DF.copy()
    df['daily_ret'] = df['Adj Close'].pct_change()
    df['direction'] = np.where(df['daily_ret']>=0,1,-1)
    df['direction'][0] = 0
    df['vol_adj'] = df['Volume'] * df['direction']
    df['obv'] = df['vol_adj'].cumsum()
    return df['obv']

def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*78)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*78)
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr
    

def max_drawdown(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd

def Renko_data(data):
    df = data.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:, [0,1,2,3,4,5]]
    df.columns=['date', 'open', 'high', 'low', 'close', 'volume']
    renko_df = Renko(df)
    renko_df.brick_size=max(0.5, round(ATR(data, 120)['ATR'][-1], 0))
    dfr = renko_df.get_ohlc_data()
    dfr['num_bars']=np.where(dfr['uptrend']==True, 1, -1)
    for i in range(1, len(dfr)):
        if dfr['num_bars'][i]>0 and dfr['num_bars'][i-1]>0:
            dfr['num_bars'][i]+=dfr['num_bars'][i-1]
        elif dfr['num_bars'][i]<0 and dfr['num_bars'][i-1]<0:
            dfr['num_bars'][i]+=dfr['num_bars'][i-1]
    dfr.drop_duplicates(subset = 'date',inplace = True, keep='last')
    return dfr

#getting the data for selected tickers
tickers = ["MSFT","AAPL","FB","AMZN","INTC", "CSCO","IBM"]        
ts = TimeSeries(key='WE8WV4LYOKN8CXRM', output_format='pandas')

ohlc_intraday = {} # directory with ohlc value for each stock   
api_call_count = 1
start_time = time.time()

for ticker in tickers:
    try:
        print('Getting data for ', ticker)
        data = ts.get_intraday(symbol=ticker,interval='5min', outputsize='full')[0]
        api_call_count+=1
        data.columns = ["Open","High","Low","Adj Close","Volume"]
        data = data.iloc[::-1]
        data = data.between_time('09:35', '16:00') #remove data outside regular trading hours
        ohlc_intraday[ticker] = data
        if api_call_count==5:
            api_call_count = 1
            time.sleep(60 - ((time.time() - start_time) % 60.0))
    except:
        print('failed to get data')



#merging this data with renko data
df = copy.deepcopy(ohlc_intraday)
ohlc_renko = {}
tickers_signal = {}
tickers_return = {}
for ticker in tickers:
    renko = Renko_data(df[ticker])
    renko.columns = ["Date","open","high","low","close","uptrend","bar_num"]
    df[ticker]["Date"] = df[ticker].index
    ohlc_renko[ticker] = df[ticker].merge(renko.loc[:,["Date","bar_num"]],how="outer",on="Date")
    ohlc_renko[ticker]["bar_num"].fillna(method='ffill',inplace=True)
    ohlc_renko[ticker]["obv"]= OBV(ohlc_renko[ticker])
    ohlc_renko[ticker]["obv_slope"]= slope(ohlc_renko[ticker]["obv"],5)
    tickers_signal[ticker] = ""
    tickers_return[ticker] = []

#Identifying signal and correspondingly calculating return for each ticker across all periods
for ticker in tickers:
    print("calculating daily returns for ",ticker)
    for i in range(len(ohlc_intraday[ticker])):
        if tickers_signal[ticker] == "":
            tickers_return[ticker].append(0)
            if ohlc_renko[ticker]["bar_num"][i]>=2 and ohlc_renko[ticker]["obv_slope"][i]>30:
                tickers_signal[ticker] = "Buy"
            elif ohlc_renko[ticker]["bar_num"][i]<=-2 and ohlc_renko[ticker]["obv_slope"][i]<-30:
                tickers_signal[ticker] = "Sell"
        
        elif tickers_signal[ticker] == "Buy":
            tickers_return[ticker].append((ohlc_renko[ticker]["Adj Close"][i]/ohlc_renko[ticker]["Adj Close"][i-1])-1)
            if ohlc_renko[ticker]["bar_num"][i]<=-2 and ohlc_renko[ticker]["obv_slope"][i]<-30:
                tickers_signal[ticker] = "Sell"
            elif ohlc_renko[ticker]["bar_num"][i]<2:
                tickers_signal[ticker] = ""
                
        elif tickers_signal[ticker] == "Sell":
            tickers_return[ticker].append((ohlc_renko[ticker]["Adj Close"][i-1]/ohlc_renko[ticker]["Adj Close"][i])-1)
            if ohlc_renko[ticker]["bar_num"][i]>=2 and ohlc_renko[ticker]["obv_slope"][i]>30:
                tickers_signal[ticker] = "Buy"
            elif ohlc_renko[ticker]["bar_num"][i]>-2:
                tickers_signal[ticker] = ""
    ohlc_renko[ticker]["ret"] = np.array(tickers_return[ticker])  
    
#calculating KPIs of the strategy

renko_obv = pd.DataFrame()
for ticker in tickers:
    renko_obv[ticker]=ohlc_renko[ticker]["ret"]
renko_obv['ret'] = renko_obv.mean(axis=1)
print(CAGR(renko_obv))
print(sharpe(renko_obv,0.025))
print(max_drawdown(renko_obv))
    

(1+renko_obv['ret']).cumprod().plot()

#KPIs for individual stocks:
cagr = {}
sharpe_ratios = {}
max_dd = {}
for ticker in tickers:
    print("calculating KPIs for ",ticker)      
    cagr[ticker] =  CAGR(ohlc_renko[ticker])
    sharpe_ratios[ticker] =  sharpe(ohlc_renko[ticker],0.025)
    max_dd[ticker] =  max_drawdown(ohlc_renko[ticker])

KPI_df = pd.DataFrame([cagr,sharpe_ratios,max_dd],index=["Return","Sharpe Ratio","Max Drawdown"]) 
