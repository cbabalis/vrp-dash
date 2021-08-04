""" Module to fast prototype the merge of the network modeled by networkx tools from OSM and custom input.
"""

import pandas as pd
import osmnx as ox
import networkx as nx
import input_output_operations as io_ops
import network_operations as net_ops
import network_scenarios as net_scens
import pdb


def assign_POIs_to_graph(graph, pois_df):
    """Method to get a dataframe with points of interest and to
    match the nearest node in the network to each one of them.

    Args:
        graph (graph): graph of the network
        pois_fp (DataFrame): DataFrame that contains points of interest
    """
    # create a list with all nodes to be merged to network
    pois_coords = _get_pois_coords_list(pois_df)
    # finally get a list with all node ids of interest, interpreted to network
    poi_nodes = []
    for poi in pois_coords:
        poi_nodes.append(ox.get_nearest_node(graph, poi))
    print(len(poi_nodes))
    poi_nodes = _unique(poi_nodes)
    print("unique are " , len(poi_nodes))
    return poi_nodes


def _get_pois_coords_list(df, col='coordinates'):
    """Method to retrieve points of interest from a dataframe,
    to convert them to tuple containing (lat, lon) pairs and
    to return a list full of tuples

    Args:
        df ([type]): [description]
        col (str, optional): [description]. Defaults to 'coords'.

    Returns:
        [type]: [description]
    """
    # create an empty list
    coords_list = []
    raw_coords_list = []
    # get the coordinates as string from the dataframe
    for index, row in df.iterrows():
        raw_coords_list.append(row[col])
    # convert string to comma separated float coordinates
    for elem in raw_coords_list:
        temp = elem.split(",")
        tuplex = (float(temp[0]), float(temp[1]))
        coords_list.append(tuplex)
    return coords_list


def _unique(li):
    unique_li = []
    for elem in li:
        if elem not in unique_li:
            unique_li.append(elem)
    return unique_li


def enhance_network_nodes_with_field(nodes, poi_nodes_list, new_field, field_name):
    """Method to add new fields to the nodes of the network.
    It adds the points of interest as well as loads to them.

    Args:
        nodes (DataFrame): Nodes of the network (road network)
        poi_nodes_list (list): List of nodes IDs that contain points of interest
    """
    net_ops.add_new_column_to_dataframe(nodes, name=new_field)
    for poi in poi_nodes_list:
        nodes[new_field][nodes['osmid'] == poi] = field_name


def create_distance_matrix(graph, pois_list):
    """Method to create a distance matrix from a dataframe of nodes and
    to return it in compliance with google OR-Tools.
    ref: https://developers.google.com/optimization/routing/vrp

    Args:
        graph (Graph): graphml representation of the graph
        pois_list (list): list of ids of points of interest
    """
    # create an empty dictionary for the distance matrix
    data = create_data_model()
    # create a list of nodes that correspond to distance matrix rows.
    dist_matrix_nodes_dict = {}
    # populate distance matrix by computing distances from each node to each other
    #pois_list = net_ops.fast_check_network_integrity(pois_list, graph)
    for start_node in pois_list:
        curr_row = net_ops.compute_distance_from_other_nodes(start_node, pois_list, graph)
        data['distance_matrix'].append(curr_row)
        dist_matrix_nodes_dict[start_node] = curr_row
    return (data, dist_matrix_nodes_dict)


def create_data_model():
    data = {}
    data['distance_matrix'] = []
    data['num_vehicles'] = 4
    data['depot'] = 0
    return data


def flora(src_graph_fp, csv_src_fp, results_csv_fpath, new_col='traffic'):
    # get the graph from disk
    graph = net_ops.load_graph_from_disk(src_graph_fp)
    nodes, edges = net_ops.get_nodes_edges(graph)
    # read the points of interest to df
    pois_df = io_ops.convert_csv_to_nodes(csv_src_fp)
    poi_nodes = assign_POIs_to_graph(graph, pois_df)
    # assign new fields and values to nodes of the network
    enhance_network_nodes_with_field(nodes, poi_nodes, new_field='supermarkets', field_name='AB')
    # create distance matrix
    data, dist_matrix_nodes_dict = create_distance_matrix(graph, poi_nodes)
    return data


def main():
    # read input (file with custom data and network)
    # match custom input to network
    # add traffic to edges that connect nodes of custom input
    skat = flora('results/greece-athens.graphml', 'data/supermarkets.csv', '')


if __name__ == '__main__':
    main()