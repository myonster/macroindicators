import numpy as np
import yfinance as yf


def vol20(ticker):
    ticker= yf.Ticker(ticker)
    df = ticker.history(period='21D')
    px_last_list = df['Close'].tolist()
    px_last_list.insert(0,0)
    px_last_list.pop()
    df.loc[:,'1daypricelag'] = px_last_list
    df['daily%ret'] = df['Close']/df['1daypricelag'] -1
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.iloc[1:]


    return df['daily%ret'].std()*np.sqrt(250)


def vol60(ticker):
    ticker= yf.Ticker(ticker)
    df = ticker.history(period='61D')
    px_last_list = df['Close'].tolist()
    px_last_list.insert(0,0)
    px_last_list.pop()
    df.loc[:,'1daypricelag'] = px_last_list
    df['daily%ret'] = df['Close']/df['1daypricelag'] -1
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.iloc[1:]


    return df['daily%ret'].std()*np.sqrt(250)


def Z_G(ticker,z_limit,g_limit):

    #identify ticker to use for df
    ticker= yf.Ticker(ticker)
    df = ticker.history(period='5Y')
    
    #function to calculate moving average
    def moving_avg(window_size,name,list_of_value):
        windows = list_of_value.rolling(window_size)
        a = windows.mean()
        a_list = a.tolist()
        final_a = a_list[window_size - 1:]
    
        empty = []
        while len(empty) < (window_size - 1):
            empty.append(0)
        
            if len(empty) == (window_size - 1):
                break
    
        empty.extend(final_a)
        df.loc[:, name ] = empty
        return
      
        
    #function to calculate SD    
    def std(window_size,name,list_of_value):
        windows = list_of_value.rolling(window_size)
        a = windows.std()
        a_list = a.tolist()
        final_a = a_list[window_size - 1:]
    
        empty = []
        while len(empty) < (window_size - 1):
            empty.append(0)
        
            if len(empty) == (window_size - 1):
                break
    
        empty.extend(final_a)
        df.loc[:, name ] = empty
    
        return
    
    
    #create price lag column
    px_last_list = df['Close'].tolist()
    px_last_list.insert(0,0)
    px_last_list.pop()
    px_last_list
    df.loc[:,'1daypricelag'] = px_last_list
    
    
    #create returns column
    df.loc[:,'Returns'] = (df['Close']/df['1daypricelag']) - 1
    
    
    #create returns lag column
    px_last_list = df['Returns'].tolist()
    px_last_list.insert(0,0)
    px_last_list.pop()
    px_last_list
    df.loc[:,'1dayreturnlag'] = px_last_list
    
    std(20,'Vol 20D Raw',df['1dayreturnlag'])
    std(60,'Vol 60D Raw',df['1dayreturnlag'])
    
    df['Vol 20D'] = df['Vol 20D Raw'] * np.sqrt(250)
    df['Vol 60D'] = df['Vol 60D Raw'] * np.sqrt(250)
    
    std(10,'Gamma',df['Vol 60D'])
    
    #date as column
    df = df.reset_index()
    
    def remove_timezone(dt):
        return dt.replace(tzinfo=None)
    
    df['Date'] = df['Date'].apply(remove_timezone)
    
    df = df.astype({'Close':'float',
                    'Gamma':'float'})
    
    #create moving averages and standard deviations
    moving_avg(200,'200D MA',df['1daypricelag'])
    moving_avg(65,'MM 13W',df['1daypricelag'])
    std(65,'SD 13W',df['1daypricelag'])
    
    df['Normalisation'] = (df['1daypricelag'] - df['MM 13W'])/df['SD 13W']
    moving_avg(10,'Z Score', df['Normalisation'])
    
    df = df[['Date','Close','Gamma','Z Score']]

    df['indicator'] = np.where((df['Z Score'] > z_limit) &(df['Gamma'] < g_limit),1,0)
    df['consecutive'] = df.indicator.groupby((df.indicator != df.indicator.shift()).cumsum()).transform('size') * df.indicator
    df['monthlyind'] = np.where(df['indicator'] == 1,'ON','OFF')
    
    combo = np.where(df.iloc[-1,6] == 'ON',df.iloc[-1,6] + '(' + df.iloc[-1,5].astype(str) + ')','OFF')
    
    return combo
