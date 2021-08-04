""" Module to implement a dash app for executing VRP on it."""

import random
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


image = 'url("assets/ampeli-dash.png")'

colorscales = px.colors.named_colorscales()

white_button_style = {'background-color': 'white',
                      'color': 'black',
                      #'height': '50px',
                      #'width': '100px',
                      'margin-top': '50px',
                      'margin-left': '50px'}

matrix_text = '''
#### Επίλυση VRP προβλημάτων μέσω εφαρμογής####
'''


help_text = '''
ΕΠΕΞΗΓΗΣΕΙΣ ΤΗΣ ΕΦΑΡΜΟΓΗΣ
'''


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("Υπολογισμός Προβλήματος Δρομολόγησης Οχημάτων",  style={'textAlign':'center'}),
    html.Hr(),
    # text here
    html.Div([
    dcc.Markdown(matrix_text),
    dcc.ConfirmDialogProvider(children=html.Button(
            'Οδηγίες Χρήσης',
            style={'float': 'right','margin': 'auto'}
        ),
        id='danger-danger-provider',
        message=help_text,
    ),
    html.Div(id='output-provider')
    ],
             className='row'),
    # filters here
    html.Div([
        html.Div([
            html.Div([
                html.Label("ΔΙΑΘΕΣΙΜΑ ΣΥΝΟΛΑ ΔΕΔΟΜΕΝΩΝ",
                    style={'font-weight': 'bold',
                            'fontSize' : '17px',
                            'margin-left':'auto',
                            'margin-right':'auto',
                            'display':'block'}),
                dcc.Dropdown(id='availability-radio', #available-dataset-radio
                            style={"display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                    # "width":"60%"
                    }), # style solution here: https://stackoverflow.com/questions/51193845/moving-objects-bar-chart-using-dash-python
            ], className='six columns'),
            html.Div([
                html.Label("ΕΠΙΛΟΓΗ ΥΠΟΣΥΝΟΛΟΥ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='year-radio'), #available-names-radio
            ], className='three columns'),
        ], className='row',
                 style= {'padding-left' : '50px'}), # closes the div for first line (matrix and year)
        html.Hr(),
        html.Div([
            # geospatial filters
            html.Div([
                html.H5("ΒΑΣΙΚΕΣ ΠΑΡΑΜΕΤΡΟΙ ΠΡΟΒΛΗΜΑΤΟΣ"),
                html.Label("ΑΡΙΘΜΟΣ ΟΧΗΜΑΤΩΝ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='countries-radio', # vehicles-number
                                options=[{'label': l, 'value': l} for l in range(1,10)],
                                value=''),
                html.Label("ΚΟΜΒΟΣ ΕΚΚΙΝΗΣΗΣ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='cities-radio', # start-node-radio
                             multi=True,
                             options=[]),],
                                        style = {'width': '440px',
                                            'fontSize' : '15px',
                                            'padding-left' : '50px',
                                            'display': 'inline-block',
                                            }),
            # product filters
            html.Div([
                html.H5("ΧΩΡΗΤΙΚΟΤΗΤΑ"),
                html.Label("ΚΑΤΗΓΟΡΙΕΣ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='products-radio', # capacity
                                options=[{'label': l, 'value': l} for l in range(1,10)],
                                value=''),
                html.Label("ΠΡΟΪΟΝ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='products-radio-val',
                             multi=True,
                             options=[]),],
                                        style = {'width': '440px',
                                            'fontSize' : '15px',
                                            'padding-left' : '50px',
                                            'display': 'inline-block'}),
            
            # values filters
            html.Div([
                html.Label("ΣΤΑΤΙΣΤΙΚΑ ΣΤΟΙΧΕΙΑ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='column-sum',
                                options=[{'label': l, 'value': l} for l in range(1,10)],
                                value=''),
                html.Label("ΕΠΙΛΟΓΗ ΓΡΑΦΗΜΑΤΟΣ",
                        style={'font-weight': 'bold',
                                'fontSize' : '17px'}),
                dcc.Dropdown(id='chart-choice',
                                options=[{'label': l, 'value': l} for l in range(1,10)],
                                value='Γράφημα Στήλης',
                                ), #labelStyle={'display': 'inline-block', 'text-align': 'justify'}), this is about Radioitems
                html.Button('Καταχώρηση Παραμέτρων', id='submit-val', n_clicks=0, style=white_button_style),
            ],style = {'width': '350px',
                                            'fontSize' : '15px',
                                            'padding-left' : '50px',
                                            'display': 'inline-block'}),
        ],className='row'),
    ],style = {'background-image':image,
                                    'background-size':'cover',
                                    'background-position':'right'}),
    # table here
    html.Hr(),
    html.Div(id='display-selected-table',  className='tableDiv'),
    html.Hr(),
    
    # graphs here
    html.Hr(),
    dcc.Graph(id='indicator-graphic-multi-sum'),
    html.Hr(),
    # maps here
    html.Div([
            html.Div([
                html.Label("ΔΙΑΘΕΣΙΜΕΣ ΧΡΩΜΑΤΙΚΕΣ ΕΠΙΛΟΓΕΣ",
                    style={'font-weight': 'bold',
                            'fontSize' : '15px',
                            'margin-left':'auto',
                            'margin-right':'auto',
                            'display':'block'}),
                dcc.Dropdown(id='availability-colors',
                            options=[{"value": x, "label": x} 
                                        for x in colorscales],
                            value='speed',
                            style={"display": "block",
                    "margin-left": "auto",
                    "margin-right": "auto",
                    # "width":"60%"
                    }), # style solution here: https://stackoverflow.com/questions/51193845/moving-objects-bar-chart-using-dash-python
            ], className='four columns'),
            
        ], className='row',
                 style= {'padding-left' : '50px'}), # closes the div for first line (matrix and year)
    html.Hr(),
    html.Div(children=[
        dcc.Graph(id='map-fig'),
    ], style = {'display': 'inline-block', 'height': '178%', 'width': '95%'}),
    # end of maps
    html.Button('Δημιουργία Σεναρίου Προς Διερεύνηση', id='csv_to_disk', n_clicks=0),
    html.Div(id='download-link'),
    html.Div(
        [
            html.Button("Αποθήκευση αποτελεσμάτων με βάση τις επιλογές του χρήστη σε αρχείο CSV", id="btn_csv"),
            Download(id="download-dataframe-csv"),
        ],
    ),
    html.Div(
        html.A(html.Button("Μετάβαση στον υπολογισμό μητρώου προέλευσης-προορισμού", className='three columns'),
        href='http://147.102.154.65:8056/'), # https://github.com/plotly/dash-html-components/issues/16
    )
])



if __name__ == "__main__":
    app.run_server(debug=False,port=8054) #  host='147.102.154.65', 