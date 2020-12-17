import requests
from urllib.parse import urlencode
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from datetime import datetime
import os
from pandas_datareader.stooq import StooqDailyReader
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import pathlib
import plotly.express as px

from app import app

#get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
nsdq = pd.read_csv(DATA_PATH.joinpath("stock.csv"))

nsdq.set_index('Symbol', inplace=True)
options = []

for tic in nsdq.index:
    #{'label':'user sees', 'value': 'script sees'}
    mydict = {}
    mydict["label"] = nsdq.loc[tic]["Name"] + " " + tic
    mydict["value"] = tic + ".PL"
    options.append(mydict)

layout = html.Div([
            html.Div([
                html.H1("Stock Dashboard"),
                html.Div([
                    html.H6("Wpisz symbol:", style={'paddingRight':'30px'}),
                    dcc.Dropdown(
                        id="stock_picker",
                        options = options,
                        value=["CDR.PL"],
                        multi=True
                        )
                ],style={"display":"inline-block","verticalAlign":"top", "width":"30%"}),
                html.Div([html.H6("Wybierz date początkową i końcową:"),
                        dcc.DatePickerRange(id="my_date_picker",
                                            min_date_allowed = datetime(2015,1,1),
                                            max_date_allowed = datetime.today(),
                                            start_date = datetime(2019,1,1),
                                            end_date = datetime.today()

                        )
                ], style={"display":"inline-block"}),
                html.Div([
                        html.Button(id="submit_button",
                                    n_clicks=0,
                                    children="Submit",
                                    style={"fontsize":24,"marginLeft":"30px"})

                ],style={"display":"inline-block"}),

            ],className = "row"),
            html.Div([
                html.Div([
                    dcc.Graph(id="multiple_stocks")
                ], className = "eight columns"),
                html.Div([
                    dcc.Graph(id="correlation")
                ], className = "four columns")

            ], className = "row"),


])
@app.callback(Output("multiple_stocks", "figure"),
            [Input("submit_button","n_clicks")],
            [State("stock_picker", "value"),
             State("my_date_picker", "start_date"),
             State("my_date_picker", "end_date")
            ])
def update_graph(n_clicks, stock_ticker, start_date, end_date):
    start = datetime.strptime(start_date[:10], '%Y-%m-%d')
    end = datetime.strptime(end_date[:10], '%Y-%m-%d')

    traces = []
    df = pd.DataFrame()
    for tic in stock_ticker:
        #df = yf.Ticker(tic).history(start = start, end = end)
        df[tic] = StooqDailyReader(tic, start=start, end=end ).read()["Close"]

    column_maxes = df.max()
    df_max = column_maxes.max()
    column_mins = df.min()
    df_min = column_mins.min()
    normalized_df = (df - df_min) / (df_max - df_min)

    fig = px.line(normalized_df, x=normalized_df.index, y=normalized_df.columns,title='Ceny zamknięcia wybranych spółek notowanych na WIG')
    return fig

@app.callback(Output("correlation", "figure"),
                [Input("submit_button","n_clicks")],
                [State("stock_picker", "value"),
                 State("my_date_picker", "start_date"),
                 State("my_date_picker", "end_date")
                ])
def update_graph(n_clicks, stock_ticker, start_date, end_date):
    start = datetime.strptime(start_date[:10], '%Y-%m-%d')
    end = datetime.strptime(end_date[:10], '%Y-%m-%d')

    traces = []
    df = pd.DataFrame()
    for tic in stock_ticker:
        #df = yf.Ticker(tic).history(start = start, end = end)
        df[tic] = StooqDailyReader(tic, start=start, end=end ).read()["Close"]

    corr = df.corr()
    fig = px.imshow(corr, color_continuous_scale="Greens", title='Korelacje cen zamknięcia wybranych spółek notowanych na WIG')
    return fig
