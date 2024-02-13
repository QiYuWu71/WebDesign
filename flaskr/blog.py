from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.get_db_data import get_cur_user, get_stocks_for_cur_user, get_tracks_for_cur_user, all_stock, get_tracks_for_all_user, get_price_df
from flaskr.update_db import update_index_data, update_stock_data
from flaskr.plot import plot_compare_price, plot_holdings_pie, plot_frontier_table, plot_spy_index, extract_spy
from flaskr.buy_sell import buy_sell_action
from flaskr.eff_frontier import sharpratio_calculate
import plotly.express as px
import statsmodels.api as sm
import numpy as np
from flaskr.get_data import get_company_name
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.utils

bp = Blueprint("blog", __name__)


@bp.route("/")
@login_required
def index():
    """Homepage after user login.
    Show user information, username and balance.
    Show stock symbol and num of shares user has.
    Show all the stock buy/sell tracks, latest track first.
    Show analytics graphs of user stock account."""
    if g.user['is_admin'] == 1:
        return admin()

    db = get_db()
    u_dict = get_cur_user(db, g)

    update_index_data(db) # 3.29: update index historical data when render index.html

    stocks, s_list, stock_symbol_list = get_stocks_for_cur_user(db, g) 
    track_list, track_price_list, cur_price_list, holding_list = get_tracks_for_cur_user(db, g, stock_symbol_list)

    # draw a line plot to show the level of spy index data
    spy_dict = plot_spy_index(db)
    # draw a table to show the efficient frontier dataframe
    frontier_data = plot_frontier_table(g)
    # bar chart comparison of track price and current price
    graphJSON = plot_compare_price(stock_symbol_list, track_price_list, cur_price_list)
    # pie chart shows the percentage of each holdings

    graphJSON2 = plot_holdings_pie(stock_symbol_list, holding_list)
    
    prices_df = get_price_df(stock_symbol_list)
    daily_returns = prices_df.pct_change()
    year_returns = daily_returns.mean()*255

    daily_cov = daily_returns.cov()
    year_cov = daily_cov * 255

    portfolio_return = []
    portfolio_volatility = []
    stock_weight = []

    num_assets = len(stock_symbol_list)
    num_portfolio = 5000

    for single_portfolio in range(num_portfolio):
        weight = np.random.random(num_assets)
        weight /= np.sum(weight)
        returns = np.dot(weight, year_returns)

        volatility = np.sqrt(np.dot(np.dot(weight, year_cov), weight.T))

        portfolio_return.append(returns)
        portfolio_volatility.append(volatility)
        stock_weight.append(weight)

    portfolio = {'Return':portfolio_return,
                'Volatility':portfolio_volatility}
    for counter , ticker in enumerate(stock_symbol_list):
        portfolio[ticker + ' weight'] = [weight[counter] for weight in stock_weight]

    df = pd.DataFrame(portfolio)
    
    fig3 = px.scatter(df, x="Volatility", y="Return",
        )
    
    fig3.update_layout(title="Efficient frontier",title_x=0.5)
    
    graphJSON3= json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template("blog/index.html", tracks=track_list, user=u_dict, stocks=stocks,frontier = frontier_data,spy_df = spy_dict, graphJSON=graphJSON,graphJSON2=graphJSON2,graphJSON3=graphJSON3)
    

@bp.route("/admin")
@login_required
def admin():
    """Homepage after user login.
    Show user information, username and balance.
    Show stock symbol and num of shares user has.
    Show all the stock buy/sell tracks, latest track first.
    Show analytics graphs of user stock account."""
    db = get_db()
    u_dict = get_cur_user(db, g)

    update_index_data(db) # 3.29: update index historical data when render index.html
    
    # get stock symbol and total chares of all the users from database, table stock, display on website
    stocks = all_stock()

    if not stocks.empty:
        for stock in set(stocks['stock_symbol']):
            update_stock_data(db, stock) 

    # get all user stock buy/sell track from database, table track (add username)
    track_list = get_tracks_for_all_user(db)
    # draw a line plot to show the level of spy index data
    spy_dict = plot_spy_index(db)
    # draw a table to show the efficient frontier dataframe
    frontier_data = pd.DataFrame(columns = ['Exp_return','Volatility','Sharp'])

    # aggregate stock df for weights calculation
    if not stocks.empty:
        weights_df = stocks.groupby('stock_symbol').apply(lambda df:pd.Series({"curr_price": df["curr_price"].values[0],"shares":sum(df["shares"].values)})).reset_index()
        weights_df.set_index('stock_symbol',inplace=True)
    
        weights_df = weights_df.transpose()
        return_df = get_price_df(weights_df.columns)
        if len(weights_df)!=0:
            sharp = pd.DataFrame(sharpratio_calculate(return_df,weights_df),index=[0])
            frontier_data = pd.concat([frontier_data,sharp],ignore_index=True)
       
            #frontier_data = pd.concat([frontier_data,sharpratio_calculate(return_df,weights_df)],ignore_index=True)
        

    return render_template("blog/admin.html",tracks = track_list, stocks=stocks.to_dict('records'),frontier = frontier_data,spy_df = spy_dict)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a buy/sell stock track for the current user.
    User input stock symbol, num of shares, BUY/SELL
    Update database according to user input."""
    if request.method == "POST":
        
        stock_symbol = request.form["stock_symbol"]
        num_share = int(request.form["num_share"])
        buysell = request.form["buy_or_sell"]

        stock_name = get_company_name(stock_symbol)

        error = None

        if not stock_symbol:
            error = "Stock_symbol is required."
        if not num_share:
            error = "Number of shares is required."
        if not buysell:
            error = "Buy/Sell option is required."

        if error is not None:
            flash(error)
        else:
            track_price, buy_sell_flag, new_balance, error = buy_sell_action(stock_symbol, num_share, buysell, g, error)     
            if error is None:
                # add buy/sell stock track into database, update balance in database
                db = get_db()
                db.execute(
                    "INSERT INTO track (stock_symbol, stock_name, track_price, num_share, author_id, buy_or_sell) VALUES (?, ?, ?, ?, ?, ?)",
                    (stock_symbol, stock_name, track_price, num_share, g.user["id"], buy_sell_flag),
                )
                db.execute(
                    "UPDATE user SET balance = ? WHERE id = ?", 
                    (new_balance, g.user["id"])
                )
                db.commit()
                
            # return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/charts", methods=("GET", "POST"))
@login_required
def charts():
    db=get_db()
    stocks = db.execute(
        "SELECT stock_symbol, stock_name, total_shares"
        " FROM stock s JOIN user u ON s.author_id = u.id"
        " WHERE id = ?", (g.user["id"],)
    ).fetchall()
    stock_symbol_list = []

    for s in stocks:
        stock_symbol_list.append(s["stock_symbol"])
    
    if request.method == "POST":
        stock_symbol = request.form["stock_selection"] 

        stock_symbol=[stock_symbol]

        prices_df=get_price_df(stock_symbol)
        prices_df=prices_df.reset_index()
        fig3 = px.line(prices_df, x="date", y=prices_df.columns,
        hover_data={"date": "|%B %d, %Y"},
        title='Stock Price For 5 Years',
        )
        
        fig3.update_xaxes(
            dtick="M1",
            tickformat="%b\n%Y")
        fig3.update_xaxes(title_text="Date")
        fig3.update_yaxes(title_text="Price")
        fig3.update_layout(
            title='Stock Price For 5 Years',
    title_x=0.5  
)
        graphJSON3= json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)


        ret_df=get_price_df(stock_symbol)
        ret_df=(ret_df-ret_df.shift())/ret_df.shift()
        ret_df=ret_df.reset_index().dropna()

        fig4 = px.scatter(ret_df, x="date", y=ret_df.columns,
            hover_data={"date": "|%B %d, %Y"},
            title='Simple Return For 5 Years')
        fig4.update_xaxes(
            dtick="M1",
            tickformat="%b\n%Y")
        fig4.update_xaxes(title_text="Date")
        fig4.update_yaxes(title_text="Simple Return")
        fig4.update_layout(
            title_x=0.5
        )
        graphJSON4= json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)


        corr_df=ret_df.copy().set_index(['date'])
        fig5 = go.Figure()
        for i in corr_df.columns:
            x=corr_df[i].shift().dropna()
            y=corr_df[i][1:]
            fig5.add_trace(go.Scatter(  # 
                x=x, 
                y=y,   
                mode='markers',                         
                name=i))
        fig5.update_xaxes(title_text="Simple Return (-1)")
        fig5.update_yaxes(title_text="Simple Return")
        fig5.update_layout(
                title='Today’s Return vs. Yesterday’s Return',
                title_x=0.5  
        )
        graphJSON5= json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder)


        fig6 = px.histogram(ret_df, x=ret_df.columns[1], nbins=30,title="Histogram of Simple Return")
        fig6.update_layout(
            title_x=0.5
        )
        fig6.update_xaxes(title_text="Return")
        fig6.update_yaxes(title_text="Count")
        graphJSON6= json.dumps(fig6, cls=plotly.utils.PlotlyJSONEncoder)


        ret_df2=get_price_df(stock_symbol)
        spy_df2= extract_spy(db)
        spy_df2=spy_df2.rename(columns={'date_time':'date'})
        spy_df2=spy_df2.rename(columns={'index_value':'S&P 500'})
        spy_df2=spy_df2.set_index(['date'])
        total_df=ret_df2.join(spy_df2,how='right')

        total_df=(total_df-total_df.shift())/total_df.shift()
        cum_ret_df=total_df.dropna().apply(lambda x:(1 + x).cumprod())-1
        cum_ret_df=cum_ret_df.reset_index()

        fig7 = px.line(cum_ret_df, x="date", y=cum_ret_df.columns,
        hover_data={"date": "|%B %d, %Y"},
        title='Stock and S&P 500 Cumulative Returns')
        fig7.update_xaxes(
            dtick="M1",
            tickformat="%b\n%Y")
        fig7.update_xaxes(title_text="Date")
        fig7.update_yaxes(title_text="Cumulative Returns")
        fig7.update_layout(
            title_x=0.5
        )
        graphJSON7= json.dumps(fig7, cls=plotly.utils.PlotlyJSONEncoder)


        total_df2=total_df.reset_index()

        fig8 = px.line(total_df2, x="date", y=total_df2.columns,
        hover_data={"date": "|%B %d, %Y"},
        title='Daily Percentage Change in Price for Stock and SPX')
        fig8.update_xaxes(
            dtick="M1",
            tickformat="%b\n%Y")
        fig8.update_xaxes(title_text="Date")
        fig8.update_yaxes(title_text="Daily Percentage Change")
        fig8.update_layout(
            title_x=0.5
        )
        graphJSON8= json.dumps(fig8, cls=plotly.utils.PlotlyJSONEncoder)

        
        fig9 = px.scatter(total_df, x="S&P 500", y=total_df.columns[0], trendline="ols",
                          title="Scatter graph of Stock Return vs. Market Return")
        fig9.update_layout(
            title_x=0.5
        )
        graphJSON9= json.dumps(fig9, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template("blog/charts.html",stock_symbol=stock_symbol[0],stock_symbol_list=stock_symbol_list,graphJSON3=graphJSON3,graphJSON4=graphJSON4,graphJSON5=graphJSON5,graphJSON6=graphJSON6,graphJSON7=graphJSON7,graphJSON8=graphJSON8,graphJSON9=graphJSON9)
    
    
    
    return render_template("blog/charts.html",stock_symbol_list=stock_symbol_list)

