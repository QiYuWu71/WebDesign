# fintech512-bigbucks

BigBucks is an web application for Hedge Fund BigBucks. It provides services for users to track accounts, buy and sell stocks, manage portfolios, analyze risk and returns, and so on.

## Getting started

Our BigBucks application is running on flaskr. You should use flaskr to run the code.

Before you run, you can create a virtualenv and activate it first::

    $ python3 -m venv .venv
    $ . .venv/bin/activate

To exit the virtualenv::

    $ deactivate

Then you need to install all the packages required in the requirements.txt.

To run the code using the commands below, you need a `flask version>=2.2.x`. At any time you update or install a package in the .venv, you need to deactivate and re-activate it.

To install the package `dateutil`, you should use::

    $ pip install python-dateutil

Meanwhile, you need your own API key for getting data from "https://www.alphavantage.co/". Therefore, you should new a file in the flaskr directory called "config.py" with your api_key defined there, using api_key = "".

## Run

.. code-block:: text

    $ flask --app flaskr init-db
    $ flask --app flaskr run --debugger

Open http://127.0.0.1:5000 in a browser.

Every user should register and login to see his/her own accounts and reports, buy/sell a stock, without seeing other people's stuff.

If you are an administrator, you should register by inputing an administrative code; otherwise, you can leave the bar blank.

## Note



