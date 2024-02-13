import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime as dt, timedelta
from flaskr.get_db_data import user_stock, get_price_df
from flaskr.eff_frontier import sharpratio_calculate


# bar chart comparison of track price and current price
def plot_compare_price(stock_symbol_list, track_price_list, cur_price_list):
    fig = go.Figure(data=[
        go.Bar(name='Track Price', x=stock_symbol_list, y=track_price_list),
        go.Bar(name='Current Price', x=stock_symbol_list, y=cur_price_list)
    ])
    # Change the bar mode=
    fig.update_layout(barmode='group',title="Track Price vs. Current Price (unit: $)",title_x=0.5, autosize=False,
        legend=dict(
        x=0,
        y=1,
        traceorder='normal',
        font=dict(
            family='sans-serif',
            size=12,
            color='black'
        ),
        bgcolor='#E2E2E2',
        bordercolor='#FFFFFF',
        borderwidth=2
    ))
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

# pie chart shows the percentage of each holdings
def plot_holdings_pie(stock_symbol_list, holding_list):
    labels = stock_symbol_list
    values = holding_list
    fig2 = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig2.update_layout(barmode='group',title="Current holdings (unit: $)",title_x=0.5)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON2

# draw a table to show the efficient frontier dataframe
def plot_frontier_table(g):
    frontier_data = pd.DataFrame(columns = ['Exp_return','Volatility','Sharp'])
    weights_df = user_stock(g.user['id'])
    return_df = get_price_df(weights_df.columns)
    if len(weights_df)!=0:
        sharp = pd.DataFrame(sharpratio_calculate(return_df,weights_df),index=[0])
        frontier_data = pd.concat([frontier_data,sharp],ignore_index=True)
    return frontier_data

def extract_spy(db):
    rows = db.execute(
        "SELECT date_time, index_value from SPY ORDER BY date_time"
    ).fetchall()
    spy_df = pd.DataFrame(rows, columns=["date_time", "index_value"])
    return spy_df

# draw a line plot to show the level of spy index data
def plot_spy_index(db):
    spy_df = extract_spy(db)
    spy_df['date_time'] = spy_df['date_time'].apply(lambda x:dt.strftime(x,'%Y-%m-%d'))
    spy_dict = dict({"date_time":spy_df["date_time"].values.tolist(),"index_value":spy_df["index_value"].values.tolist()})
    # data = [go.Scatter(x=spy_df["date_time"], y=spy_df["index_value"])]
    # layout = go.Layout(title="SPY Index Value", xaxis=dict(title="Date"), yaxis=dict(title="Index Value"))
    # fig = go.Figure(data=data, layout=layout)
    # plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return spy_dict