# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 09:11:43 2021

@author: kumar
"""
import numpy as np
import pandas as pd
from stocktrends import Renko
import statsmodels.api as sm
from alpha_vantage.timeseries import TimeSeries
import copy
import time

def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a = 12; b =26, c =9"""
    df = DF.copy()
    df["MA_Fast"]=df["Adj Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Adj Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return (df["MACD"],df["Signal"])

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

tickers = ["BAC","AAPL","F","GE","NOK", "NIO","PLTR","T","AMD","BB"]        
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

ohlc_intraday1 = copy.deepcopy(ohlc_intraday)
for ticker in tickers:
    if ohlc_intraday1[ticker].shape[0]==1560:
        ohlc_intraday1[ticker].drop(ohlc_intraday1[ticker].index[:78], axis=0, inplace=True)
        
tickers = ohlc_intraday.keys()

#merging renko dataframe with ohlc_intraday data
ohlc_renko = {}
df = copy.deepcopy(ohlc_intraday1)
tickers_signal = {}
tickers_return = {}
for ticker in tickers:
    renko = Renko_data(df[ticker])
    renko.columns = ["Date","open","high","low","close","uptrend","bar_num"]
    df[ticker]["Date"] = df[ticker].index
    ohlc_renko[ticker] = df[ticker].merge(renko.loc[:,["Date","bar_num"]],how="outer",on="Date")
    ohlc_renko[ticker]["bar_num"].fillna(method='ffill',inplace=True)
    ohlc_renko[ticker]["macd"]= MACD(ohlc_renko[ticker],12,26,9)[0]
    ohlc_renko[ticker]["macd_sig"]= MACD(ohlc_renko[ticker],12,26,9)[1]
    ohlc_renko[ticker]["macd_slope"] = slope(ohlc_renko[ticker]["macd"],5)
    ohlc_renko[ticker]["macd_sig_slope"] = slope(ohlc_renko[ticker]["macd_sig"],5)
    tickers_signal[ticker] = ""
    tickers_return[ticker] = []
   
#identifying signals and calculation returns

for ticker in tickers:
    for i in range(len(ohlc_intraday1[ticker])):
        if tickers_signal[ticker] == "":
            tickers_return[ticker].append(0)
            if i > 0:
                if ohlc_renko[ticker]["bar_num"][i]>=2 and ohlc_renko[ticker]["macd"][i]>ohlc_renko[ticker]["macd_sig"][i] and ohlc_renko[ticker]["macd_slope"][i]>ohlc_renko[ticker]["macd_sig_slope"][i]:
                    tickers_signal[ticker] = "Buy"
                elif ohlc_renko[ticker]["bar_num"][i]<=-2 and ohlc_renko[ticker]["macd"][i]<ohlc_renko[ticker]["macd_sig"][i] and ohlc_renko[ticker]["macd_slope"][i]<ohlc_renko[ticker]["macd_sig_slope"][i]:
                    tickers_signal[ticker] = "Sell"
        
        elif tickers_signal[ticker] == "Buy":
            tickers_return[ticker].append((ohlc_renko[ticker]["Adj Close"][i]/ohlc_renko[ticker]["Adj Close"][i-1])-1)
            if i > 0:
                if ohlc_renko[ticker]["bar_num"][i]<=-2 and ohlc_renko[ticker]["macd"][i]<ohlc_renko[ticker]["macd_sig"][i] and ohlc_renko[ticker]["macd_slope"][i]<ohlc_renko[ticker]["macd_sig_slope"][i]:
                    tickers_signal[ticker] = "Sell"
                elif ohlc_renko[ticker]["macd"][i]<ohlc_renko[ticker]["macd_sig"][i] and ohlc_renko[ticker]["macd_slope"][i]<ohlc_renko[ticker]["macd_sig_slope"][i]:
                    tickers_signal[ticker] = ""
                
        elif tickers_signal[ticker] == "Sell":
            tickers_return[ticker].append((ohlc_renko[ticker]["Adj Close"][i-1]/ohlc_renko[ticker]["Adj Close"][i])-1)
            if i > 0:
                if ohlc_renko[ticker]["bar_num"][i]>=2 and ohlc_renko[ticker]["macd"][i]>ohlc_renko[ticker]["macd_sig"][i] and ohlc_renko[ticker]["macd_slope"][i]>ohlc_renko[ticker]["macd_sig_slope"][i]:
                    tickers_signal[ticker] = "Buy"
                elif ohlc_renko[ticker]["macd"][i]>ohlc_renko[ticker]["macd_sig"][i] and ohlc_renko[ticker]["macd_slope"][i]>ohlc_renko[ticker]["macd_sig_slope"][i]:
                    tickers_signal[ticker] = ""
    ohlc_renko[ticker]["ret"] = np.array(tickers_return[ticker])
     

#calculating KPIs of the strategy

renko_macd = pd.DataFrame()
for ticker in tickers:
    renko_macd[ticker]= ohlc_renko[ticker]["ret"]
renko_macd['ret'] = renko_macd.mean(axis=1)
print(CAGR(renko_macd))
print(sharpe(renko_macd,0.025))
print(max_drawdown(renko_macd))
    
#visualization

(1+renko_macd['ret']).cumprod().plot()

#KPIs for individual stocks:
cagr = {}
sharpe_ratios = {}
max_dd = {}
for ticker in tickers:    
    cagr[ticker] =  CAGR(ohlc_renko[ticker])
    sharpe_ratios[ticker] =  sharpe(ohlc_renko[ticker],0.025)
    max_dd[ticker] =  max_drawdown(ohlc_renko[ticker])

KPI_df = pd.DataFrame([cagr,sharpe_ratios,max_dd],index=["Return","Sharpe Ratio","Max Drawdown"]) 

    


