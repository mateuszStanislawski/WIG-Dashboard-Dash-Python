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
                html.Div([
                    dcc.Dropdown(
                        id="stock_picker3",
                        options = options,
                        value="CDR.PL",
                        multi=False
                        )],style={"display":"inline-block","verticalAlign":"top", "width":"20%"}),
                html.Div([
                    html.Div([dcc.Graph(id="candle-plot")
                    ],className="eight columns"),
                html.Div([dcc.Graph(id="box-plot")
                ],className="four columns"),
                ],className="row"),
                html.Div([
                    html.Div([dcc.Graph(id="my-graph")], className="row", style={"margin": "auto"}),
                        html.Div([
                            html.Div(dcc.Slider(id="select-range1", updatemode='drag',
                              marks={
                                    0: '0',
                                    15: '15',
                                    30: '30',
                                    45: '45',
                                    60: '60',
                                    75: '75',
                                    90: '90'
                              },
                              min=0, max=90, value=30), className="row", style={"padding": 10}),
                            html.Div(dcc.Slider(id="select-range2", updatemode='drag',
                              marks={
                                    0: '0',
                                    15: '15',
                                    30: '30',
                                    45: '45',
                                    60: '60',
                                    75: '75',
                                    90: '90'
                              },
                              min=0, max=90, value=15), className="row", style={"padding": 10})
                              ],className = "row")

                        ],className="six columns",style={"margin-right":0,"padding":0}),

                    html.Div([
                        dcc.Graph(id="plot-graph")
                    ], className="six columns",style={"margin-left":0,"padding":0}),
                ],className="row")

])

@app.callback(Output("candle-plot", "figure"),
            [Input("stock_picker3", "value")])
def update_graph(stock_ticker):
    df = StooqDailyReader(stock_ticker, start="2020-01-01").read()
    fig = {
            "data":go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'])]),
            'layout':{
                    'xaxis':{
                        'title':'Data'},
                    'yaxis':{
                         'title':'Cena zamknięcia'}
                    }
         }
    return fig

@app.callback(Output("my-graph", 'figure'),
            [Input("select-range1", 'value'),
             Input("select-range2", 'value'),
             Input("stock_picker3", "value")])
def update_ma(range1, range2, stock_picker):
    #start = datetime.strptime(start_date[:10], '%Y-%m-%d')
    #end = datetime.strptime(end_date[:10], '%Y-%m-%d')
    df = StooqDailyReader(stock_picker, start="2020-01-01").read()
    df = df.sort_values(by='Date')

    rolling_mean1 = df['Close'].rolling(window=range1).mean()
    rolling_mean2 = df['Close'].rolling(window=range2).mean()
    trace1 = go.Scatter(x=df.index, y=df['Close'],
                        mode='lines', name=stock_picker)
    trace_a = go.Scatter(x=df.index, y=rolling_mean1, mode='lines', yaxis='y', name=f'SMA {range1}')
    trace_b = go.Scatter(x=df.index, y=rolling_mean2, mode='lines', yaxis='y', name=f'SMA {range2}')
    layout1 =  go.Layout({'title': 'Stock Price With Moving Average',
                         "legend": {"orientation": "h","xanchor":"left"},
                         "xaxis": {
                             "rangeselector": {
                                 "buttons": [
                                     {"count": 6, "label": "6M", "step": "month",
                                      "stepmode": "backward"},
                                     {"count": 1, "label": "1Y", "step": "year",
                                      "stepmode": "backward"},
                                     {"count": 1, "label": "YTD", "step": "year",
                                      "stepmode": "todate"}
                                 ]
                             }}})
    fig = {'data': [trace1],
              'layout': layout1
              }
    fig['data'].append(trace_a)
    fig['data'].append(trace_b)


    return fig


@app.callback(Output("plot-graph", 'figure'),
            [Input("stock_picker3", "value")])
def update_return(stock_picker):

    #start = datetime.strptime(start_date[:10], '%Y-%m-%d')
    #end = datetime.strptime(end_date[:10], '%Y-%m-%d')
    df = StooqDailyReader(stock_picker, start="2020-01-01" ).read()
    df_wig = StooqDailyReader("WIG.PL", start="2020-01-01" ).read()
    df = df.sort_values(by='Date')
    df_wig = df_wig.sort_values(by='Date')

    stocks = pd.DataFrame({"Date": df.index, str(stock_picker): df["Close"],
                           "WIG": df_wig["Close"]})
    stocks = stocks.set_index('Date')
    stock_return = stocks.apply(lambda x: ((x - x[0]) / x[0])*100)

    trace2 = go.Scatter(x=stock_return.index, y=stock_return[str(stock_picker)], mode='lines', name=str(stock_picker))
    trace3 = go.Scatter(x=stock_return.index, y=stock_return['WIG'], mode='lines', name="WIG")
    fig = {'data': [trace2],
           'layout':{
            'xaxis':{
                'title':'Data'
            },
            'yaxis':{
                 'title':'Cena zamknięcia'
            }
        }
           }
    fig['data'].append(trace3)
    return fig

@app.callback(Output("box-plot", "figure"),
            [Input("stock_picker3", "value")])
def update_graph(stock_ticker):
    df = StooqDailyReader(stock_ticker, start="2020-01-01").read()
    df_box = df[["Close"]]
    fig = {
            "data":px.box(df_box, y=df_box.columns),
            'layout':{'title': {'text':'DISPLAY ME!'}}
    }
    return fig
