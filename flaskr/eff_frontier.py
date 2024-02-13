import pandas as pd
import numpy as np
from flaskr.get_data import get_rf

def return_calculate(df):
    """
    3.28
    calculate return functions
    Params:
    Dataframe:param df: daily price with dates,
         columns: stock_symbol lists
         index: dates(datetime)  float
    str:param method: (Discrete, Classic, Log) return
    str:param dateColumn: the column name of the dates column

    Return:
    returns df: Dataframe of calculated return
        columns: stock_symbol lists
        index: dates(datetime)  float

    """

    vars = list(df.columns.values)
    
    price = df.loc[:,vars].values
    price_2 = price[1:] / price[:-1]

    price_2 = np.log(price_2)

    #dates = df[dateColumn].values[1:]
    result = pd.DataFrame(columns=vars, data=price_2,index=df.index[1:])

    return result



def weights_calculate(df):

    """
    3.29
    calculate weights function, return the weights for each stock in the portfolio
    Params:
    df:Dataframe track price and hold shares,
         columns: stock_symbol lists
         index: "shares"     int
                "curr_price" float
    Return: 
    weights_df: Dataframe 
        columns: stock_symbol lists
        index: "weights"     float
    """

    total_value = np.sum(df.loc["shares",:] * df.loc["curr_price",:])
    weights = df.loc["shares",:].values * df.loc["curr_price",:].values / total_value
    weights_df = pd.DataFrame(columns=df.columns, data=weights.reshape(1,-1), index=["weights"])

    return weights_df


def volatility_calculate(return_df,weights_df):
    """
    Functions to calculate the volatility for efficient frontier.
    """
    log_returns = return_calculate(return_df)
    cov_mat = log_returns.cov().values
    weights = weights_calculate(weights_df)
    weights = weights.values


    vol = weights@cov_mat@weights.T

    return np.sqrt(vol)



def sharpratio_calculate(return_df,weights_df):
    """
    Functions to calculate the sharp ratio for the portfolio investment.
    """
    log_returns = return_calculate(return_df)
    exp_returns = log_returns.mean().values*255
    cov_mat = log_returns.cov().values*255
    weights = weights_calculate(weights_df)
    weights = weights.values

    rf_10years = get_rf()
    rf = np.exp(rf_10years/10)-1
    vol = weights@cov_mat@weights.T
    vol = vol[0][0]
    exp_returns = exp_returns.reshape(-1,1)
    exp_total_return = weights@exp_returns
    exp_total_return = exp_total_return[0][0]
    sharp = (exp_total_return- rf)/np.sqrt(vol)
    return {'Exp_return':round(exp_total_return,4),'Volatility':round(np.sqrt(vol),4),'Sharp':round(sharp,4)}
