""" Module to manipulate input/output operations. csv files, data files, etc.

@author: Babis Babalis
@e-mail: babisbabalis@gmail.com
"""

import csv
import pandas as pd
import pdb

def get_u_v_pairs_from_file(in_file):
    """Method to read a csv file and to get all the (u,v) pairs inside
    it with their cost values, too.

    Args:
        in_file (str): file path from disk
    
    Return:
        pairs_list (list): a list of <start_node, end_node, traffic_load> tuples
    
    Example:
    list_of_pairs = get_u_v_pairs_from_file('bob/my_file.csv')
    """
    lines = []
    # read the lines
    with open(in_file, 'r') as a_file:
        lines = a_file.readlines()
    # process the lines of the file accordingly
    nodes_dict = _convert_lines_to_dict(lines)
    pairs_list = _convert_dict_to_every_pair_combo(nodes_dict)
    return pairs_list


def _convert_lines_to_dict(raw_lines):
    a_dict = {}
    for line in raw_lines:
        key, val = line.split(":")
        val = _get_polished_value(val)
        a_dict[key] = val
    return a_dict


def _get_polished_value(raw_val):
    val = raw_val.strip("\n")
    val = val.split(",")
    return val


def _convert_dict_to_every_pair_combo(nodes_dict):
    """method to convert a dictionary of the following form:
    {key1: [],
     key2: [],
     key3: []}
     to a list of all combinations of keys

    Args:
        nodes_dict (dict): dictionary with nodes and values.
    """
    pairs = []
    # get the keys of the dictionary
    nodes = nodes_dict.keys()
    # and iterate it in order to create the adjacency matrix
    for node in nodes:
        pair_set = _create_pairs_starting_with(node, nodes_dict)
        pairs.extend(pair_set)
    return pairs


def _create_pairs_starting_with(key, node_dict):
    pairs = []
    start_node = key
    values = node_dict[key]
    end_nodes = node_dict.keys()
    for val, end_node in zip(values, end_nodes):
        pair = (int(start_node), int(end_node), float(val))
        pairs.append(pair)
    return pairs


def convert_csv_to_nodes(csv_filepath, cols=['latitude', 'longitude', '@id', 'brand']):
    """Method to convert a csv file (from OSM) to nodes that are able to be
    integrated to nodes of a road network.

    Args:
        csv_filepath (str): The path in the disk where the csv file is found.
        
    return:
        nodes_list (list): A list of nodes with information to be integrated in a road network.
    """
    # read the raw file from disk
    osm_raw_data_nodes = pd.read_csv(csv_filepath, delimiter='\t')
    # get only the columns needed and rename them (if necessary) to a new dataframe
    osm_nodes_with_coords = osm_raw_data_nodes[['latitude', 'longitude', '@id', 'brand']]
    if '@id' in osm_nodes_with_coords.columns:
        osm_nodes_with_coords.rename(columns={'@id':'node_id'}, inplace=True)
    # process ids of points of interest
    osm_nodes_with_coords = _process_raw_osm_id(osm_nodes_with_coords)
    # create a new column with coordinates ready to be inserted to the graph
    osm_nodes_with_coords = _create_coord_column(osm_nodes_with_coords)
    # return the new dataframe
    return osm_nodes_with_coords


def get_route_node_ids_from_textfile(txtfilepath):
    """Method to read a file in the disk and to convert its data to a dictionary
    of <vehicle: list of ids> pairs.

    Args:
        txtfilepath (str): Path where the text file is found on disk.
    
    return:
        a dictionary
    """
    routes_dict = {}
    # read the file contents
    file_contents = ''
    with open(txtfilepath, 'r') as f:
        file_contents = f.read()
    # split the contents to the vehicles accordingly and
    # split the nodes for each vehicle
    text_routes_list = _convert_text_to_routes_text_list(file_contents)
    return text_routes_list


def _convert_text_to_routes_text_list(text_contents):
    """Method to split raw text to data corresponding to routes and
    to return a list of nodes

    Args:
        text_contents (str): contents of a file (raw)
    """
    routes_dict = {}
    route_id = 0
    # remove all spaces
    text_contents = text_contents.replace(" ", "")
    # split text to route chunks
    routes_text = text_contents.split("\n")    
    # remove all inappropriate text (first entry)
    del routes_text[0]
    for route in routes_text:
        # fill results dictionary with corresponding nodes in list form
        route_nodes = route.split("->")
        route_nodes = _refine_route_nodes(route_nodes)
        routes_dict[route_id] = route_nodes
        route_id += 1
    return routes_dict


def _refine_route_nodes(route_nodes):
    """Method to remove any "Route for vehicle... text and
    to convert string to integer.

    Args:
        route_nodes (list): list of nodes

    Returns:
        [list]: list of integer nodes
    """
    refined_routes = []
    # remove all text not necessary
    for route in route_nodes:
        if route.startswith("Route"):
            print("Node is not going to be included: ", route)
        elif route:
            # make nodes int and return them
            refined_routes.append(int(route))
    return refined_routes


def write_od_to_csv(od_list, file_to_write_in_disk):
    """Method to write an origin-destination list of lists to a csv file.

    Args:
        od_list (list): List of lists
        file_to_write_in_disk (str): filepath for the results.
    """
    with open(file_to_write_in_disk, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(od_list)


def _process_raw_osm_id(df, id_col='node_id'):
    """Method to process the raw osm id and to return just a numeric id.

    Args:
        df (dataframe): pandas dataframe that contains all the nodes of interest.
        id_col (str, optional): name of the column where ID is found. Default is 'node_id'
    
    returns:
        df (dataframe): the updated dataframe
    """
    df[id_col] = df[id_col].str.replace("way/", "")
    df[id_col] = df[id_col].str.replace("node/", "")
    return df


def _create_coord_column(df, coord_col='coordinates', lat='latitude', lon='longitude'):
    df[coord_col] = df[lat].apply(str).str.cat(df[lon].astype(str), sep=",")
    return df