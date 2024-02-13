import sqlite3
from datetime import date, datetime as dt, timedelta
from dateutil.relativedelta import relativedelta
import click
from flask import current_app
from flask import g
from flaskr.get_data import init_stock_data, get_cur_price, get_his_prices
import pandas as pd

def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """
    If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_spy(db):
    """
    3.28:
    Initialize SPY index data storage
    """

    spy = init_stock_data("SPY")
    for row_index, row in spy.iterrows():
        
        db.execute(
         "INSERT INTO SPY (date_time, index_value) VALUES (?, ?)",
        (dt.strftime(row['date'],"%Y-%m-%d %H:%M:%S"), row['price']),
        )

def init_db():
    """Clear existing data and create new tables."""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    
    init_spy(db)
    db.commit()
    

@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
