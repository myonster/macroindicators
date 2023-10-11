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



def cloud(ticker):
    ticker= yf.Ticker(ticker)
    df = ticker.history(period='5Y', interval='1wk')

    # Calculate the components of the Ichimoku Cloud
    high_prices = df['High']
    close_prices = df['Close']
    low_prices = df['Low']
    
    # Conversion Line = (9-period high + 9-period low)/2
    period9_high = high_prices.rolling(window=9).max()
    period9_low = low_prices.rolling(window=9).min()
    df['conversion_line'] = (period9_high + period9_low) / 2 

    # Base Line = (26-period high + 26-period low)/2
    period26_high = high_prices.rolling(window=26).max()
    period26_low = low_prices.rolling(window=26).min()
    df['base_line'] = (period26_high + period26_low) / 2 

    # Leading Span A = (Conversion Line + Base Line) / 2
    df['leading_span_A'] = ((df['conversion_line'] + df['base_line']) / 2).shift(26)

    # Leading Span B = (52-period high + 52-period low)/2
    period52_high = high_prices.rolling(window=52).max()
    period52_low = low_prices.rolling(window=52).min()
    df['leading_span_B'] = ((period52_high + period52_low) / 2).shift(26)

    # Lagging Span = Close shifted 26 periods in the past
    df['lagging_span'] = close_prices.shift(-26)

    # Create buy/sell signals
    df['indicator'] = np.where((df['conversion_line'] > df['base_line']) & (df['Close'] > df['leading_span_A']) & (df['Close'] > df['leading_span_B']), 1, 0)
    df['consecutive'] = df.indicator.groupby((df.indicator != df.indicator.shift()).cumsum()).transform('size') * df.indicator
    df['weekly_ichimoku'] = np.where(df['indicator'] == 1,'ON','OFF')
    
    df = df[['Close','indicator','consecutive','weekly_ichimoku']]

    combo = np.where(df.iloc[-1,3] == 'ON',df.iloc[-1,3] + '(' + df.iloc[-1,2].astype(str) + ')','OFF')

    return combo


def tenkan(ticker):
    ticker = yf.Ticker(ticker)
    df = ticker.history(period='5Y', interval='1wk')

    # Calculate the components of the Ichimoku Cloud
    high_prices = df['High']
    close_prices = df['Close']
    low_prices = df['Low']
    
    # Conversion Line = (9-period high + 9-period low)/2
    period9_high = high_prices.rolling(window=9).max()
    period9_low = low_prices.rolling(window=9).min()
    df['conversion_line'] = (period9_high + period9_low) / 2 

    # Base Line = (26-period high + 26-period low)/2
    period26_high = high_prices.rolling(window=26).max()
    period26_low = low_prices.rolling(window=26).min()
    df['base_line'] = (period26_high + period26_low) / 2 

    # Create buy/sell signals based on Conversion Line and Base Line interaction
    df['indicator'] = np.where(df['conversion_line'] > df['base_line'], 1, -1)
    df['consecutive'] = df.indicator.groupby((df.indicator != df.indicator.shift()).cumsum()).transform('size') * df.indicator
    df['conversion_base_interaction'] = np.where(df['indicator'] == 1, 'ON', 'OFF')
    
    df = df[['Close', 'indicator', 'consecutive', 'conversion_base_interaction']]

    combo = np.where(df.iloc[-1, 3] == 'ON', df.iloc[-1, 3] + '(' + df.iloc[-1, 2].astype(str) + ')', 'OFF')

    return combo


def roc(ticker):
    ticker = yf.Ticker(ticker)
    df = ticker.history(period='10Y', interval='1d')

    # Calculate the Rate of Change (ROC)
    close_prices = df['Close']
    df['ROC'] = ((close_prices - close_prices.shift(252)) / close_prices.shift(252)) * 100
    
    df['indicator'] = np.where(df['ROC'] > 0, 1, -1)
    df['consecutive'] = df.indicator.groupby((df.indicator != df.indicator.shift()).cumsum()).transform('size') * df.indicator
    df['rocONOFF'] = np.where(df['indicator'] == 1, 'ON', 'OFF')
    
    df = df[['Close', 'indicator', 'consecutive', 'rocONOFF']]

    combo = np.where(df.iloc[-1, 3] == 'ON', df.iloc[-1, 3] + '(' + df.iloc[-1, 2].astype(str) + ')', 'OFF')

    return combo


def kijun(ticker):
    ticker= yf.Ticker(ticker)
    df = ticker.history(period='5Y',interval = '1wk')

    #date as column
    df = df.reset_index()
    
    def remove_timezone(dt):
        return dt.replace(tzinfo=None)
    
    df['Date'] = df['Date'].apply(remove_timezone)
    
    #Conversion line
    nine_period_high = df['High'].rolling(window= 9).max()
    nine_period_low = df['Low'].rolling(window= 9).min()
    df['conversion'] = (nine_period_high + nine_period_low) /2
    #base line
    period26_high = df['High'].rolling(window=26).max()
    period26_low = df['Low'].rolling(window=26).min()
    df['base'] = (period26_high + period26_low) / 2
    #leading span A
    df['leading_a'] = ((df['conversion'] + df['base']) / 2).shift(26)
    #leading span B
    period52_high = df['High'].rolling(window=52).max()
    period52_low = df['Low'].rolling(window=52).min()
    df['leading_b'] = ((period52_high + period52_low) / 2).shift(26)
    
    df['CloudTop'] = np.where((df['leading_a'] > df['leading_b']),df['leading_a'],df['leading_b'])
    df['indicator'] = np.where(df['Close']>df['CloudTop'],1,0)
    df['consecutive'] = df.indicator.groupby((df.indicator != df.indicator.shift()).cumsum()).transform('size') * df.indicator
    df['Cloud'] = np.where(df['indicator'] == 1,'ON','OFF')


    df = df[['Date','Close','leading_a','leading_b','CloudTop','indicator','consecutive','Cloud']]

    combo = np.where(df.iloc[-1,7] == 'ON',df.iloc[-1,7] + '(' + df.iloc[-1,6].astype(str) + ')','OFF')

    return combo
