# External dependencies
import numpy as np
import pandas as pd



def HA(df, ohlc=['Open', 'High', 'Low', 'Close']):
    """
    Function to compute Heiken Ashi Candles (HA)
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
        
    Returns :
        df : Pandas DataFrame with new columns added for 
            Heiken Ashi Close (HA_$ohlc[3])
            Heiken Ashi Open (HA_$ohlc[0])
            Heiken Ashi High (HA_$ohlc[1])
            Heiken Ashi Low (HA_$ohlc[2])
    """

    ha_open = 'HA_' + ohlc[0]
    ha_high = 'HA_' + ohlc[1]
    ha_low = 'HA_' + ohlc[2]
    ha_close = 'HA_' + ohlc[3]
    
    df[ha_close] = (df[ohlc[0]] + df[ohlc[1]] + df[ohlc[2]] + df[ohlc[3]]) / 4

    df[ha_open] = 0.00
    for i in range(0, len(df)):
        if i == 0:
            df[ha_open].iat[i] = (df[ohlc[0]].iat[i] + df[ohlc[3]].iat[i]) / 2
        else:
            df[ha_open].iat[i] = (df[ha_open].iat[i - 1] + df[ha_close].iat[i - 1]) / 2
            
    df[ha_high]=df[[ha_open, ha_close, ohlc[1]]].max(axis=1)
    df[ha_low]=df[[ha_open, ha_close, ohlc[2]]].min(axis=1)

    return df

def SMA(df, base, target, period):
    """
    Function to compute Simple Moving Average (SMA)
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        base : String indicating the column name from which the SMA needs to be computed from
        target : String indicates the column name to which the computed data needs to be stored
        period : Integer indicates the period of computation in terms of number of candles
        
    Returns :
        df : Pandas DataFrame with new column added with name 'target'
    """

    df[target] = df[base].rolling(window=period).mean()
    df[target].fillna(0, inplace=True)

    return df

def STDDEV(df, base, target, period):
    """
    Function to compute Standard Deviation (STDDEV)
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        base : String indicating the column name from which the SMA needs to be computed from
        target : String indicates the column name to which the computed data needs to be stored
        period : Integer indicates the period of computation in terms of number of candles
        
    Returns :
        df : Pandas DataFrame with new column added with name 'target'
    """

    df[target] = df[base].rolling(window=period).std()
    df[target].fillna(0, inplace=True)

    return df

def EMA(df, base, target, period, alpha=False):
    """
    Function to compute Exponential Moving Average (EMA)
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        base : String indicating the column name from which the EMA needs to be computed from
        target : String indicates the column name to which the computed data needs to be stored
        period : Integer indicates the period of computation in terms of number of candles
        alpha : Boolean if True indicates to use the formula for computing EMA using alpha (default is False)
        
    Returns :
        df : Pandas DataFrame with new column added with name 'target'
    """

    con = pd.concat([df[:period][base].rolling(window=period).mean(), df[period:][base]])
    
    if (alpha == True):
        # (1 - alpha) * previous_val + alpha * current_val where alpha = 1 / period
        df[target] = con.ewm(alpha=1 / period, adjust=False).mean()
    else:
        # ((current_val - previous_val) * coeff) + previous_val where coeff = 2 / (period + 1)
        df[target] = con.ewm(span=period, adjust=False).mean()
    
    df[target].fillna(0, inplace=True)
    return df

def ATR(df, period, ohlc=['open', 'high', 'low', 'close']):
    """
    Function to compute Average True Range (ATR)
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
        
    Returns :
        df : Pandas DataFrame with new columns added for 
            True Range (TR)
            ATR (ATR_$period)
    """
    atr = 'ATR_' + str(period)

    # Compute true range only if it is not computed and stored earlier in the df
    if not 'TR' in df.columns:
        df['h-l'] = df[ohlc[1]] - df[ohlc[2]]
        df['h-yc'] = abs(df[ohlc[1]] - df[ohlc[3]].shift())
        df['l-yc'] = abs(df[ohlc[2]] - df[ohlc[3]].shift())
         
        df['TR'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)
         
        df.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

    # Compute EMA of true range using ATR formula after ignoring first row
    EMA(df, 'TR', atr, period, alpha=True)
    
    return df

def SuperTrend(df, period, multiplier, ohlc=['Open', 'High', 'Low', 'Close']):
    """
    Function to compute SuperTrend
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        multiplier : Integer indicates value to multiply the ATR
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
        
    Returns :
        df : Pandas DataFrame with new columns added for 
            True Range (TR), ATR (ATR_$period)
            SuperTrend (ST_$period_$multiplier)
            SuperTrend Direction (STX_$period_$multiplier)
    """

    ATR(df, period, ohlc=ohlc)
    atr = 'ATR_' + str(period)
    st = 'ST_' + str(period) + '_' + str(multiplier)
    # stx = 'STX_' + str(period) + '_' + str(multiplier)
    stx = 'st_signal'
    
    """
    SuperTrend Algorithm :
    
        BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
        
        FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
                            THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
        FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND)) 
                            THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)
        
        SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                        Current FINAL UPPERBAND
                    ELSE
                        IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                            Current FINAL LOWERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                                Current FINAL LOWERBAND
                            ELSE
                                IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                    Current FINAL UPPERBAND
    """
    
    # Compute basic upper and lower bands
    df['basic_ub'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 + multiplier * df[atr]
    df['basic_lb'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 - multiplier * df[atr]

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or df[ohlc[3]].iat[i - 1] > df['final_ub'].iat[i - 1] else df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or df[ohlc[3]].iat[i - 1] < df['final_lb'].iat[i - 1] else df['final_lb'].iat[i - 1]
       
    # Set the Supertrend value
    df[st] = 0.00
    for i in range(period, len(df)):
        df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] <= df['final_ub'].iat[i] else \
                        df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] >  df['final_ub'].iat[i] else \
                        df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] >= df['final_lb'].iat[i] else \
                        df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] <  df['final_lb'].iat[i] else 0.00 
        
        #df[st].iat[i] = round(df[st].iat[i], 2)
        
    # Mark the trend direction up/down
    df[stx] = np.where((df[st] > 0.00), np.where((df[ohlc[3]] < df[st]), 'down',  'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)
    
    df.fillna(0, inplace=True)
    # df.to_csv('Signal_{}_{}'.format())
    return df
    # return df.tail(1)[stx]

def MACD(df, fastEMA=12, slowEMA=26, signal=9, base='Close'):
    """
    Function to compute Moving Average Convergence Divergence (MACD)
    
    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        fastEMA : Integer indicates faster EMA
        slowEMA : Integer indicates slower EMA
        signal : Integer indicates the signal generator for MACD
        base : String indicating the column name from which the MACD needs to be computed from (Default Close)
        
    Returns :
        df : Pandas DataFrame with new columns added for 
            Fast EMA (ema_$fastEMA)
            Slow EMA (ema_$slowEMA)
            MACD (macd_$fastEMA_$slowEMA_$signal)
            MACD Signal (signal_$fastEMA_$slowEMA_$signal)
            MACD Histogram (MACD (hist_$fastEMA_$slowEMA_$signal)) 
    """

    fE = "ema_" + str(fastEMA)
    sE = "ema_" + str(slowEMA)
    #macd = "macd_" + str(fastEMA) + "_" + str(slowEMA) + "_" + str(signal)
    #sig = "signal_" + str(fastEMA) + "_" + str(slowEMA) + "_" + str(signal)
    macd = "macd"
    sig = "signal"
    hist = "hist_" + str(fastEMA) + "_" + str(slowEMA) + "_" + str(signal)

    # Compute fast and slow EMA    
    EMA(df, base, fE, fastEMA)
    EMA(df, base, sE, slowEMA)
    
    # Compute MACD
    df[macd] = np.where(np.logical_and(np.logical_not(df[fE] == 0), np.logical_not(df[sE] == 0)), df[fE] - df[sE], 0)
    
    # Compute MACD Signal
    EMA(df, macd, sig, signal)
    
    # Compute MACD Histogram
    df[hist] = np.where(np.logical_and(np.logical_not(df[macd] == 0), np.logical_not(df[sig] == 0)), df[macd] - df[sig], 0)
    # df['macd_signal'] = np.where((df[macd] != 0.00), np.where( ((df[macd] < df[sig]) & (df[macd]<0))   , 'down',  np.where(((df[macd] > df[sig]) & (df[macd]>0)) , 'up', 'NA')), np.NaN)
    df['macd_signal'] = np.where((df[macd] != 0.00), np.where( (df[macd] < df[sig])   , 'down',  np.where((df[macd] > df[sig]) , 'up', 'NA')), np.NaN)
    
    return df

# def SuperTrend_EMA(df, period, multiplier, ohlc=['Open', 'High', 'Low', 'Close'], period_emahl, period_emac):
#     """
#     Function to compute SuperTrend
    
#     Args :
#         df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
#         period : Integer indicates the period of computation in terms of number of candles
#         multiplier : Integer indicates value to multiply the ATR
#         ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
        
#     Returns :
#         df : Pandas DataFrame with new columns added for 
#             True Range (TR), ATR (ATR_$period)
#             SuperTrend (ST_$period_$multiplier)
#             SuperTrend Direction (STX_$period_$multiplier)
#     """

#     ATR(df, period, ohlc=ohlc)
#     atr = 'ATR_' + str(period)
#     st = 'ST_' + str(period) + '_' + str(multiplier)

#     # stx = 'STX_' + str(period) + '_' + str(multiplier)
#     stx = 'signal'
#     # Compute basic upper and lower bands
#     df['basic_ub'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 + multiplier * df[atr]
#     df['basic_lb'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 - multiplier * df[atr]

#     # Compute final upper and lower bands
#     df['final_ub'] = 0.00
#     df['final_lb'] = 0.00
#     for i in range(period, len(df)):
#         df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or df[ohlc[3]].iat[i - 1] > df['final_ub'].iat[i - 1] else df['final_ub'].iat[i - 1]
#         df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or df[ohlc[3]].iat[i - 1] < df['final_lb'].iat[i - 1] else df['final_lb'].iat[i - 1]
       
#     # Set the Supertrend value
#     df[st] = 0.00
#     for i in range(period, len(df)):
#         df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] <= df['final_ub'].iat[i] else \
#                         df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] >  df['final_ub'].iat[i] else \
#                         df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] >= df['final_lb'].iat[i] else \
#                         df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] <  df['final_lb'].iat[i] else 0.00 
        
#         #df[st].iat[i] = round(df[st].iat[i], 2)
        
#     # Mark the trend direction up/down
#     df[stx] = np.where((df[st] > 0.00), np.where((df[ohlc[3]] < df[st]), 'down',  'up'), np.NaN)

#     # Remove basic and final bands from the columns
#     df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)
    
#     df.fillna(0, inplace=True)

#     ema_h = 'ema_{}_{}'.format(ohlc[1], str(period_emahl))
#     ema_l = 'ema_{}_{}'.format(ohlc[2], str(period_emahl))   
#     ema_c = 'ema_{}_{}'.format(ohlc[3], str(period_emc)) 
     

#     EMA(df, ohlc[1],ema_h,period_emahl,True)
#     EMA(df, ohlc[2],ema_l,period_emahl,True)
#     EMA(df, ohlc[3],ema_c,period_emc,True)

#     df['ema_sginal'] =  'up' if df[ema_c] > df[ema_h] else 'down' if   df[ema_c] < df[ema_l] else 'neutral'
    
#     return df


# def Stochastic(df, period, ohlc=['open', 'high', 'low', 'close'] ):
#     low_period = 'L_'+ str(period)
#     high_period = 'H_'+ str(period)
#     df[low_period] = df[ohlc[2]].rolling(window=period).min()
#     df[high_period] = df[ohlc[1]].rolling(window=period).max()
#     df['%K'] = 100*((df[ohlc[3]] - df[low_period]) / (df[high_period] - df[low_period]) )
#     df['%D'] = df['%K'].rolling(window=3).mean()
#     df['Sell Entry'] = ((df['%K'] < df['%D']) & (df['%K'].shift(1) > df['%D'].shift(1))) & (df['%D'] > 70)
#     df['Buy Entry'] = ((df['%K'] > df['%D']) & (df['%K'].shift(1) < df['%D'].shift(1))) & (df['%D'] < 30)
#     return df


# def Klinger(df, short_period,long_period,signal_period):
#     df["hlct"] = ( df["high"] + df["low"] + df["close"] )
    
#     ema_sp = 'ema_{}'.format(short_period)
#     ema_lp = 'ema_{}'.format(long_period)
    
    
    
    
#     for i  in range(len(df)):
#         if i ==0:
#             continue
        
#         if 
        
#     print("===================> done volume")

#     df =  EMA(df, 'SV', ema_sp, short_period)
#     df =  EMA(df, 'SV', ema_lp, long_period)

#     df['KVO'] = (df[ema_sp] -  df[ema_lp])
#     df =  EMA(df, 'KVO', 'KVOSignal', signal_period)
#     return df



def Klinger(df, short_period,long_period,signal_period):
    df["hlct"] = ( df["high"] + df["low"] + df["close"] )
    
    ema_sp = 'ema_{}'.format(short_period)
    ema_lp = 'ema_{}'.format(long_period)
    
    
    
    df["SV"] = np.NaN
    for i  in range(len(df)):
        df["SV"].iat[i] = df["volume"].iat[i] if df["hlct"].iat[i] >= df["hlct"].iat[i-1] else - df["volume"].iat[i]

    print("===================> done volume")

    df =  EMA(df, 'SV', ema_sp, short_period)
    df =  EMA(df, 'SV', ema_lp, long_period)

    df['KVO'] = (df[ema_sp] -  df[ema_lp])
    df =  EMA(df, 'KVO', 'KVOSignal', signal_period)
    return df


def trix(df, n):
    """Calculate TRIX for given data.

    :param df: pandas.DataFrame
    :param n:
    :return: pandas.DataFrame
    """
    df_temp = df.copy()
    df_temp.reset_index(inplace=True,drop=True)
    EX1 = df_temp['close'].ewm(span=n, min_periods=n).mean()
    EX2 = EX1.ewm(span=n, min_periods=n).mean()
    EX3 = EX2.ewm(span=n, min_periods=n).mean()
    i = 0
    ROC_l = [np.nan]
    while i + 1 <= df_temp.index[-1]:
        ROC = (EX3[i + 1] - EX3[i]) / EX3[i]
        ROC_l.append(ROC)
        i = i + 1
    Trix = pd.Series(ROC_l)
    # print(Trix)
    df['Trix'] = Trix.values
    return df