""" todo list """


import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_table import DataTable
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import base64
import plotly.graph_objects as go
# flask
from urllib.parse import quote as urlquote
from flask import Flask, send_from_directory
# following two lines for reading filenames from disk
from os import listdir
from os.path import isfile, join
import os
cwd = os.getcwd()
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame
import pdb


white_button_style = {'background-color': 'white',
                      'color': 'black',
                      #'height': '50px',
                      #'width': '100px',
                      'margin-top': '50px',
                      'margin-left': '50px'}


help_text = "text for help. TODO to be written and be read from separate file"


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div([
    html.H1("Υπολογισμός Προβλήματος Δρομολόγησης Οχημάτων",  style={'textAlign':'center'}),
    html.Hr(),
    # text here
    html.Div([
    dcc.ConfirmDialogProvider(children=html.Button(
            'Οδηγίες Χρήσης',
            style={'float': 'right','margin': 'auto'}
        ),
        id='danger-danger-provider',
        message=help_text,
    ),
    html.Div(id='output-provider')
    ],className='row'),
    
    # filters here
    html.Div([
        html.Div([
            html.Label("ΔΙΑΘΕΣΙΜΑ ΣΥΝΟΛΑ ΔΕΔΟΜΕΝΩΝ",
                style={'font-weight': 'bold',
                        'fontSize' : '17px',
                        'margin-left':'auto',
                        'margin-right':'auto',
                        'display':'block'}),
            dcc.Dropdown(id='dataset-availability-radio',
                        style={"display": "block",
                            "margin-left": "auto",
                            "margin-right": "auto",
                }), # style solution here: https://stackoverflow.com/questions/51193845/moving-objects-bar-chart-using-dash-python
        ], className='six columns'),
        html.Div([
            html.Label("ΕΠΙΛΟΓΗ ΥΠΟΣΥΝΟΛΟΥ",
                    style={'font-weight': 'bold',
                            'fontSize' : '17px'}),
            dcc.Dropdown(id='name-availability-radio'),
        ], className='three columns'),
    ], className='row',
                style= {'padding-left' : '50px'}), # closes the div for first line (matrix and year)
    html.Hr(),
    # end of filters
])



@app.callback(
    Output('selected_supermarkets_radio', 'options'),
    [Input('dataset-availability-radio', 'value'),
    Input('name_availability_radio', 'value')])
def set_cities_options(selected_matrix, selected_supermarket_name):
    #sample_df = load_matrix(selected_matrix)
    return [{'label': i, 'value': i} for i in sample_df[selected_supermarket_name].unique()]



if __name__ == "__main__":
    app.run_server(debug=False,port=8054) #  host='147.102.154.65', 