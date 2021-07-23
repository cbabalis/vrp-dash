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


## APIS start
sample_df = []

def load_matrix(selected_matrix, delim='\t', pre_path='data/'):
    """Method to load a matrix of data as table.

    Args:
        selected_matrix (str): name of the file in disk to be loaded.
        delim (str, optional): delimiter for the file to be read. Defaults to '\t'.
        pre_path (str, optional): path leading to file. Defaults to 'data/'.

    Returns:
        dataframe: dataframe containing the file contents.
    """
    matrix_filepath = pre_path + selected_matrix
    sample_df = pd.read_csv(matrix_filepath, delimiter=delim)
    sample_df = sample_df.fillna(0)
    print("full loaded matrix path is ", matrix_filepath)
    return sample_df


def get_table_selections(selected_dataset, selected_names):
    """Method to get all table parameters and to return a selection of them.

    Args:
        selected_names (list): list of names to be acquired from dataset.

    Returns:
        [type]: [description]
    """
    print("type of selected_names is ", type(selected_names))
    dff = load_matrix(selected_dataset)
    filter_col = 'brand:en'
    dff = dff[dff[filter_col].isin(selected_names)]
    #dff[pd.DataFrame(dff[filter_col].tolist()).isin(selected_names).any(1).values]
    #dff = dff[dff[filter_col] == selected_names]
    return dff

## APIS end

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
            dcc.Dropdown(id='name-availability-radio',
                         multi=True,),
        ], className='three columns'),
    ], className='row',
                style= {'padding-left' : '50px'}), # closes the div for first line (matrix and year)
    html.Hr(),
    html.Button('Καταχώρηση Παραμέτρων', id='submit-val', n_clicks=0, style=white_button_style),
    html.Hr(),
    # end of filters
    # table here
    html.Div(id='display_supermarkets_table',  className='tableDiv'),
    html.Hr(),
    # end of table
])


@app.callback(
    Output('dataset-availability-radio', 'options'),
    Input('dataset-availability-radio', 'value'))
def get_list_of_dataset_files(selected_dataset):
    """ Method to get the dataset files found on disk.
    """
    # get files from given datapath
    my_path = 'data/'
    onlyfiles = [f for f in listdir(my_path) if isfile(join(my_path, f))]
    # return all files found in folder
    return [{'label': i, 'value': i} for i in onlyfiles]


@app.callback(
    Output('name-availability-radio', 'options'),
    [Input('dataset-availability-radio', 'value'),
    Input('name-availability-radio', 'value')])
def set_products_options(selected_matrix, selected_country):
    # have dataset as global
    global sample_df
    sample_df = load_matrix(selected_matrix)
    if not selected_matrix:
        return "No matrix has been selected."
    else:
        filter_col = 'brand:en'
        return [{'label': i, 'value': i} for i in sample_df[filter_col].unique()]


@app.callback(
    Output('display_supermarkets_table', 'children'),
    [Input('submit-val', 'n_clicks')],
    [State('dataset-availability-radio', 'value'),
    State('name-availability-radio', 'value')
    ])
def set_display_table(n_clicks, selected_dataset, selected_names):
    # todo code here
    dff = get_table_selections(selected_dataset, selected_names)
    return html.Div([
        dash_table.DataTable(
            id='main-table',
            columns=[{'name': i, 'id': i, 'hideable':True} for i in dff.columns],
             data=dff.to_dict('rows'),
             editable=True,
             filter_action='native',
             sort_action='native',
             sort_mode="multi",
             column_selectable="single",
             row_selectable="multi",
             row_deletable=True,
             selected_columns=[],
             selected_rows=[],
            #  page_action="native",
            #  page_current= 0,
             page_size= 10,
             style_table={
                'maxHeight': '50%',
                'overflowY': 'scroll',
                'width': '100%',
                'minWidth': '10%',
            },
            style_header={'backgroundColor': 'rgb(200,200,200)', 'width':'auto'},
            style_cell={'backgroundColor': 'rgb(230,230,230)','color': 'black','height': 'auto','minWidth': '100px', 'width': '150px', 'maxWidth': '180px','overflow': 'hidden', 'textOverflow': 'ellipsis', },#minWidth': '0px', 'maxWidth': '180px', 'whiteSpace': 'normal'},
            #style_cell={'minWidth': '120px', 'width': '150px', 'maxWidth': '180px'},
            style_data={'whiteSpace': 'auto','height': 'auto','width': 'auto'},
            tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in dff.to_dict('records')
            ],
            tooltip_header={i: i for i in dff.columns},
    tooltip_duration=None
        )
    ])



if __name__ == "__main__":
    app.run_server(debug=True, port=8054) #  host='147.102.154.65', 