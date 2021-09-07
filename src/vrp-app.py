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
import flora
import pdb
import network_operations
import vrp_plots
import time

## variables
image = 'url("assets/Banner_Fleet.jpg")'
selected_dff = []
lon_lat_struct_of_POIs = ''
solution_found = False


## APIS start
sample_df = []
vrp_options = [
            {'label': 'Time Windows', 'value': 'tw'},
            {'label': 'Capacitated', 'value': 'capacitated'},
            {'label': 'Pickups and Deliveries', 'value': 'pickdel'}
]

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
    if selected_names:
        print("type of selected_names is ", type(selected_names))
    dff = load_matrix(selected_dataset)
    filter_col = 'brand:en'
    dff = dff[dff[filter_col].isin(selected_names)]
    #dff[pd.DataFrame(dff[filter_col].tolist()).isin(selected_names).any(1).values]
    #dff = dff[dff[filter_col] == selected_names]
    return dff


def create_distance_matrix_from_selection(dff):
    """Method to create a distance matrix (OD Matrix) from a given
    selection of dataframe.

    Args:
        dff (dataframe): User selection of data (POIs)

    Returns:
        [list]: list of lists containing distances
    """
    distance_matrix = []
    return distance_matrix


def call_vrp_parameters(num_vehicles, depot=0, demands=[], vehicle_capacities=[],
                        time_windows=[], depot_capacity=0, vehicle_load_time=0,
                        vehicle_unload_time=0, dff_selection_path='results/selection.csv'):
    """Method to initialize and create the appropriate dataset for the VRP to run.

    Args:
        num_vehicles ([type]): [description]
        depot (int, optional): [description]. Defaults to 0.
        demands (list, optional): [description]. Defaults to [].
        vehicle_capacities (list, optional): [description]. Defaults to [].
        time_windows (list, optional): [description]. Defaults to [].
        depot_capacity (int, optional): [description]. Defaults to 0.
        vehicle_load_time (int, optional): [description]. Defaults to 0.
        vehicle_unload_time (int, optional): [description]. Defaults to 0.
    """
    # prepare data in order to be run by google or vrp.
    selected_dff.to_csv(dff_selection_path, sep='\t')
    od_dist = network_operations.compute_distance_matrix(dff_selection_path)[0]
    # check the parameters and run the corresponding VRP problem respectively.
    # check the number of vehicles. if it is empty then no VRP can be run.
    global solution_found
    solution_found = False
    solution = _select_vrp_params(od_dist, num_vehicles, depot, demands,
                                  vehicle_capacities, time_windows, depot_capacity,
                                  vehicle_load_time,vehicle_unload_time, dff_selection_path)#google_basic_vrp(od_dist, num_vehicles)
    if solution:
        print("solution has been found!")
        solution_found = True
    # assign node ids to "real" network nodes in a special struct.
    global lon_lat_struct_of_POIs
    lon_lat_struct_of_POIs = vrp_plots.convert_node_ids_to_nodes(selected_dff, solution)


def _select_vrp_params(od_dist, num_vehicles, depot=0, demands=[], vehicle_capacities=[],
                        time_windows=[], depot_capacity=0, vehicle_load_time=0,
                        vehicle_unload_time=0, dff_selection_path='results/selection.csv'):
    solution = ''
    if demands and _are_there_time_windows(time_windows):
        #solution = combo_vrp(od_dist, num_vehicles, depot, demands, vehicle_capacities, time_windows)
        pass
    elif demands:
        solution = google_capacitated_vrp(od_dist, num_vehicles, demands, vehicle_capacities)
    elif _are_there_time_windows(time_windows):
        solution = google_time_windows_vrp(od_dist, num_vehicles, time_windows)
    elif vehicle_load_time:
        #solution = vrp_extra_params(num_vehicles, vehicle_load_time, vehicle_unload_time, depot_capacity)
        pass
    else:
        pdb.set_trace()
        solution = google_basic_vrp(od_dist, num_vehicles)
    return solution


def _are_there_time_windows(time_windows):
    assert len(time_windows) == 2, "time windows list is empty!"
    start_time, end_time = time_windows
    if (start_time == end_time) or (len(time_windows) != 2):
        return False
    return True


def google_basic_vrp(od_dist, num_vehicles):
    """Method to prepare google vrp with just basic params.

    Args:
        od_dist (list): list of lists representing od matrix
        num_vehicles (int): number of vehicles

    Returns:
        [dict]: dictionary of vehicle id with nodes to visit
    """
    data = {}
    data['distance_matrix'] = od_dist
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    import google_vrps.google_vrp as gvrp
    solution = gvrp.google_vrp(data)
    return solution


def google_capacitated_vrp(od_dist, num_vehicles, demands, vehicle_capacities):
    data = {}
    data['distance_matrix'] = od_dist
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    # generate demands of points of interest
    data['demands'] = _generate_pois_demands(od_dist, demands)
    # generate capacity of vehicles
    data['vehicle_capacities'] = _generate_vehicle_capacities(od_dist, num_vehicles, demands, vehicle_capacities)
    # run capacitated vrp
    import google_vrps.google_cvrp as gcvrp
    gcvrp.capacitated_vrp(data)


def google_time_windows_vrp(od_dist, num_vehicles, time_windows):
    # create data model for time windows
    data = {}
    data['time_matrix'] = od_dist
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    data['time_windows'] = _generate_time_windows(od_dist, time_windows)
    # run time windows vrp
    import google_vrps.google_twvrp as gtwvrp
    gtwvrp.time_windows_vrp(data)

## APIS end

####  help functions in APIs  ####

def _generate_pois_demands(od_dist, demands, randomness=0):
    if not randomness:
        demands_list = [demands for demand in range(len(od_dist))]
        return demands_list
    else:
        #TODO randomness should be implemented
        print("no randomness has been implemented!")
        demands_list = [demands for demand in range(len(od_dist))]
        return demands_list


def _generate_vehicle_capacities(od_dist, num_vehicles, demands, vehicle_capacities, randomness=0):
    # TODO no implementation of randomness yet
    assert vehicle_capacities * num_vehicles > len(od_dist) * demands, "not enough capacity"
    if not randomness:
        capacities = [vehicle_capacities for cap in range(num_vehicles)]
        return capacities


def _generate_time_windows(od_dist, time_windows):
    """method to generate time windows for google vrp.

    Args:
        od_dist (list): list of lists representing od matrix.
        time_windows (list): list containing two numbers of time window [min, max]

    Returns:
        [list]: time windows for data
    """
    tw = tuple(time_windows)
    time_matrix = [tw for elem in range(len(od_dist))]
    return time_matrix


#### end of help functions in APIs  ####


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
    html.Button('ΚΑΤΑΧΩΡΗΣΗ ΣΥΝΟΛΟΥ ΔΕΔΟΜΕΝΩΝ ΚΑΙ ΕΠΙΛΟΓΩΝ', id='submit-val', n_clicks=0, style=white_button_style),
    html.Hr(),
    # end of filters
    # table here
    html.Div(id='display_supermarkets_table',  className='tableDiv'),
    html.Hr(),
    # end of table
    # vrp parameters
    html.Div([
        html.Div([
            html.Div([
                html.Label("ΕΠΙΛΟΓΗ ΠΑΡΑΜΕΤΡΩΝ VRP",
                            style={'font-weight': 'bold',
                                    'fontSize' : '17px'}),
                dcc.Checklist(
                    id='vrp-checklist',
                    options=vrp_options,
                    value=[]
                ),
            ]),
        ], className='row',
            style= {'padding-left' : '50px'}),
        # simple vrp params
        html.Div([
            html.Div([
                html.Label("ΕΠΙΛΟΓΗ ΒΑΣΙΚΩΝ ΠΑΡΑΜΕΤΡΩΝ VRP",
                            style={'font-weight': 'bold',
                                    'fontSize' : '17px'}),
                html.Label("ΑΡΙΘΜΟΣ ΟΧΗΜΑΤΩΝ"),
                dcc.Slider(id='num_vehicles',
                min=1,
                max=75,
                value=1,
                step=1,
                marks={
                    1: {'label': '1', 'style': {'color': '#77b0b1'}},
                    75: {'label': '75', 'style': {'color': '#f50'}}
                    }
                ),
                html.Div(id='num_vehicles_output', style={'margin-top': 2}),
            ]),
            ], className='row',
            style= {'padding-left':'50px','width': '20%', 'display': 'inline-block', 'vertical-align': 'middle'}),
        # capacitated and time windows
        html.Div([
            html.Div([
                html.Label("ΕΠΙΛΟΓΗ ΠΡΟΣΘΕΤΩΝ ΠΑΡΑΜΕΤΡΩΝ VRP",
                            style={'font-weight': 'bold',
                                    'fontSize' : '17px'}),
                html.Label("ΖΗΤΗΣΗ ΑΝΑ ΚΑΤΑΣΤΗΜΑ"),
                dcc.Slider(id='demand',
                min=0,
                max=100,
                value=0,
                step=1,
                marks={
                    0: {'label': '0', 'style': {'color': '#77b0b1'}},
                    100: {'label': '100', 'style': {'color': '#f50'}}
                    }
                ),
                html.Div(id='demand_output', style={'margin-top': 2}),
                # truck capacity
                html.Label("ΧΩΡΗΤΙΚΟΤΗΤΑ ΟΧΗΜΑΤΟΣ"),
                dcc.Slider(id='capacity',
                min=10,
                max=80,
                value=20,
                step=1,
                marks={
                    10: {'label': '10', 'style': {'color': '#77b0b1'}},
                    80: {'label': '80', 'style': {'color': '#f50'}}
                    }
                ),
                html.Div(id='capacity_output', style={'margin-top': 2}),
                # time windows
                html.Label("ΟΡΙΣΜΟΣ ΧΡΟΝΟΠΑΡΑΘΥΡΩΝ"),
                dcc.RangeSlider(
                    id='tw_range_slider',
                    min=8,
                    max=20,
                    step=1,
                    value=[0,0]
                ),
                html.Div(id='tw_range_slider_output', style={'margin-top': 2}),
            ]),
            ], className='row',
            style= {'padding-left':'50px','width': '20%', 'display': 'inline-block', 'vertical-align': 'middle'}),
        # end of capacitated and time windows
        html.Div([
            html.Div([
                # depot capacity
                html.Label("ΕΠΙΛΟΓΗ ΑΛΛΩΝ ΠΑΡΑΜΕΤΡΩΝ VRP",
                            style={'font-weight': 'bold',
                                    'fontSize' : '17px'}),
                html.Label("ΜΕΓΙΣΤΟΣ ΑΡΙΘΜΟΣ ΟΧΗΜΑΤΩΝ ΠΡΟΣ ΤΑΥΤΟΧΡΟΝΗ ΑΝΑΧΩΡΗΣΗ"),
                dcc.Slider(id='depot_capacity',
                min=1,
                max=10,
                value=2,
                step=1,
                marks={
                    1: {'label': '1', 'style': {'color': '#77b0b1'}},
                    10: {'label': '10', 'style': {'color': '#f50'}}
                    }
                ),
                html.Div(id='depot_capacity_output', style={'margin-top': 2}),
                html.Hr(),
                #vehicle load time
                html.Label("ΧΡΟΝΟΣ ΦΟΡΤΩΣΗΣ ΟΧΗΜΑΤΟΣ"),
                dcc.Slider(id='vehicle_load_time',
                min=0,
                max=60,
                value=0,
                step=1,
                marks={
                    0: {'label': '0', 'style': {'color': '#77b0b1'}},
                    60: {'label': '60', 'style': {'color': '#f50'}}
                    }
                ),
                html.Div(id='vehicle_load_time_output', style={'margin-top': 2}),
                # vehicle unload time
                html.Label("ΧΡΟΝΟΣ ΕΚΦΟΡΤΩΣΗΣ ΟΧΗΜΑΤΟΣ"),
                dcc.Slider(id='vehicle_unload_time',
                min=0,
                max=60,
                value=0,
                step=1,
                marks={
                    0: {'label': '0', 'style': {'color': '#77b0b1'}},
                    60: {'label': '60', 'style': {'color': '#f50'}}
                    }
                ),
                html.Div(id='vehicle_unload_time_output', style={'margin-top': 2}),
            ]),
        ], className='row',
            style= {'padding-left':'50px','width': '20%', 'display': 'inline-block', 'vertical-align': 'middle'}),
        # end of extra params
        # extra params
    ],style = {'background-image':image,
                'background-size':'cover',
                'background-position':'right'}),
    # button here
    html.Button('ΚΑΤΑΧΩΡΗΣΗ ΠΑΡΑΜΕΤΡΩΝ ΔΡΟΜΟΛΟΓΗΣΗΣ ΟΧΗΜΑΤΩΝ', id='vrp_submit_val', n_clicks=0, style=white_button_style),
    html.Button('ΑΠΕΙΚΟΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ΣΕ ΧΑΡΤΗ', id='submit-map', n_clicks=0, style=white_button_style),
    html.Div(id='container-button-basic', style={'margin-top': 20}),
    html.Div(id='vrp-solution-state'),
    html.Hr(),
    html.Div(children=[
        dcc.Graph(id='map-fig'),
    ], style = {'display': 'inline-block', 'height': '178%', 'width': '95%'}),
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
    # assign dff selection to selected dff for further operations.
    global selected_dff
    selected_dff = dff.copy()
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

### VRP parameters feedback-output

@app.callback(Output('num_vehicles_output', 'children'),
              Input('num_vehicles', 'value'))
def display_value(value):
    return 'Αριθμός Οχημάτων: {} οχήματα'.format(value)


@app.callback(Output('demand_output', 'children'),
              Input('demand', 'value'))
def display_value(value):
    return 'Ζήτηση: {} μονάδες'.format(value)


@app.callback(Output('capacity_output', 'children'),
              Input('capacity', 'value'))
def display_value(value):
    return 'Χωρητικότητα Οχήματος: {} μονάδες'.format(value)


@app.callback(Output('tw_range_slider_output', 'children'),
              Input('tw_range_slider', 'value'))
def display_value(value):
    return 'Χρονοπαράθυρο: {} '.format(value)


@app.callback(Output('depot_capacity_output', 'children'),
              Input('depot_capacity', 'value'))
def display_value(value):
    return 'Οχήματα που εκκινούν ταυτόχρονα: {} οχήματα'.format(value)


@app.callback(Output('vehicle_load_time_output', 'children'),
              Input('vehicle_load_time', 'value'))
def display_value(value):
    return 'Χρόνος φόρτωσης: {} λεπτά'.format(value)


@app.callback(Output('vehicle_unload_time_output', 'children'),
              Input('vehicle_unload_time', 'value'))
def display_value(value):
    return 'Χρόνος εκφόρτωσης: {} λεπτά'.format(value)


@app.callback(
    Output('container-button-basic', 'children'),
    [Input('vrp_submit_val', 'n_clicks')],
    [State('num_vehicles', 'value'),
     State('demand', 'value'),
     State('capacity', 'value'),
     State('tw_range_slider', 'value')])
def update_output(click_value, num_vehicles, demand, capacity, tw_range):
    call_vrp_parameters(num_vehicles, depot=0, demands=demand, vehicle_capacities=capacity, time_windows=tw_range)


@app.callback(Output('vrp-solution-state', 'children'),
              Input('vrp_submit_val', 'n_clicks'),)
def update_solution_msg(btn_click):
    # compute timestamp and name the filename.
    msg = 'Αναζήτηση Λύσης.'
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if ('vrp_submit_val' in changed_id):
        msg = _has_solution_found()
    return html.Div(msg)


def _has_solution_found(timer=60):
    global solution_found
    current_timer = 0
    while not solution_found:
        time.sleep(1)
        current_timer += 1
        if current_timer > timer:
            return "Δεν βρέθηκε λύση."
    return "Βρέθηκε λύση με τις δοθείσες παραμέτρους"

### end of VRP parameters feedback output


@app.callback(
    Output('map-fig', 'figure'),
    [Input('submit-map', 'n_clicks')])
def print_vrp_to_map(click_value):
    """TODO: params and code here
    """
    fig = vrp_plots.plot_vehicles_with_routes(lon_lat_struct_of_POIs)
    return fig



if __name__ == "__main__":
    app.run_server(debug=True, port=8054) #  host='147.102.154.65', 