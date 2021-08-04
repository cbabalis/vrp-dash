""" Module to run network scenarios using network_operations."""

import pandas
import networkx
import osmnx as ox
import network_operations as net_ops
import min_path_ops.min_path_operations as min_ops
import time
import min_path_ops.dijkstra as dijkstra
import geopandas as gpd
from os import listdir  # in need for searching in folders
from os.path import isfile, join  # in need for searching in folders
import input_output_operations as io_ops
import pdb


def get_sum_of_two_shortest_paths_edges(graph, edges, start1, end1,
                                        start2, end2, new_col='traffic'):
    # add new column to dataframe
    net_ops.add_new_column_to_dataframe(edges, new_col)
    # execute min path and update edges
    update_edges_list_with_min_path_traffic(graph, edges, start1, end1, new_col)
    update_edges_list_with_min_path_traffic(graph, edges, start2, end2, new_col)
    # get all edges with traffic and return them
    updated_edges = edges.loc[edges[new_col] > 0]
    return updated_edges


def update_edges_list_with_min_path_traffic(graph, edges, start1,
                                            end1, new_col, val=100):
    try:
        shortest_path = net_ops.get_shortest_path(graph, start1, end1)
        min_path_pairs = net_ops.get_nodes_pairs(shortest_path)
        net_ops.update_edge_list(min_path_pairs, edges, new_col, val)
    except networkx.exception.NetworkXNoPath:
        print("no path between ", start1, end1)


def split_list_ids_to_single_rows(edges):
    single_id_rows = net_ops.split_osmid_field(edges)
    single_id_rows_to_df = pandas.concat(single_id_rows)
    return single_id_rows_to_df


def write_traffic_edges_to_csv(edges, results_csv_fpath,
                               col_name='traffic', threshold=0.1):
    traffic_edges = edges[edges[col_name] > threshold]
    single_id_rows_to_df = split_list_ids_to_single_rows(traffic_edges)
    single_id_rows_to_df.to_csv(results_csv_fpath)
    


def scenario_two_paths(graph, edges, s1, e1, s2, e2, new_col,
                       csv_fname):
    traffic_edges = get_sum_of_two_shortest_paths_edges(graph,
                                                        edges,
                                                        s1, e1,
                                                        s2, e2,
                                                        new_col)
    single_id_rows_to_df = split_list_ids_to_single_rows(traffic_edges)
    single_id_rows_to_df.to_csv(csv_fname)


def simple_scenario_ipynb():
    place_name = 'Greece'
    cf = '["highway"~"motorway|motorway_link|trunk|secondary|primary"]'
    net_type = 'drive'
    graph = net_ops.get_network_graph(place_name, net_type, cf)
    nodes, edges = net_ops.get_nodes_edges(graph)
    scenario_two_paths(graph, edges, 3744263637, 300972555, 295512257, 1604968703, 'traffic', 'loaded_edges.csv')


def tatiana_scenario(src_graph_fp, csv_src_fp, results_csv_fpath, new_col='traffic'):
    # get the graph from disk
    graph = net_ops.load_graph_from_disk(src_graph_fp)
    nodes, edges = net_ops.get_nodes_edges(graph)
    # read the csv file (form: n1, n2, n3, ...n)
    # create pairs from csv file
    pairs = io_ops.get_u_v_pairs_from_file(csv_src_fp)
    # compute minimum paths and update traffic
    net_ops.add_new_column_to_dataframe(edges, new_col)
    for pair in pairs:
        u, v, traffic = pair
        if u is not v:
            update_edges_list_with_min_path_traffic(graph, edges, u,
                                            v, new_col, traffic)
    pdb.set_trace()
    #net_ops.add_u_v_coords_to_edges(nodes, edges)
    write_traffic_edges_to_csv(edges, results_csv_fpath, new_col, threshold=0.1)
    pdb.set_trace()


def scenario_all_nodes_with_all(pairs_list, graph, edges, new_col,
                                results_csv_fpath):
    # create and initialize new column
    net_ops.add_new_column_to_dataframe(edges, new_col)
    # get every pair of list of pairs and run a min path between them
    # updating the traffic in each route.
    start_time = time.time()
    pair_counter = 0 # TODO to be removed when not debugging
    #length = len(pairs_list)
    for pair in pairs_list:
        u, v = pair
        update_edges_list_with_min_path_traffic(graph, edges, u, v, new_col)
        #print("pair ", u, v, "\tupdated successfully\t(", pair_counter, "/", length, ")")
        #pair_counter += 1
    print("--- %s seconds min path ---" % (time.time() - start_time))
    # split the list type of id to an id/row and write the result to a file.
    #single_id_rows_to_df = split_list_ids_to_single_rows(edges)
    #single_id_rows_to_df.to_csv(results_csv_fpath)
    #return single_id_rows_to_df


def scenario_all_in_all(src_graph_fp, csv_src_fp, results_csv_fpath, node):
    # read the csv file and get the list of nodes
    df = pandas.read_csv(csv_src_fp, sep=';')
    nodes_list = df[node].to_list()
    combo_list = net_ops.get_all_list_combinations(nodes_list)
    
    # get the network graph
    #cf = '["highway"~"motorway|motorway_link|trunk|secondary|primary"]'
    #graph = net_ops.get_network_graph('Greece', 'drive', cf)
    graph = net_ops.load_graph_from_disk(src_graph_fp)
    nodes, edges = net_ops.get_nodes_edges(graph)
    scenario_all_nodes_with_all(combo_list, graph, edges, 'traffic', results_csv_fpath)
    write_traffic_edges_to_csv(edges, results_csv_fpath, new_col='traffic', threshold=0.1)


def custom_dijkstra(src_graph_fp, results_folder, origin_node, dest_node):
    graph = net_ops.load_graph_from_disk(src_graph_fp)
    nodes, edges = net_ops.get_nodes_edges(graph)
    dijkstra_edges = min_ops.create_dijkstra_edge_list(edges, nodes)
    dijkstra_path = dijkstra.dijkstra(dijkstra_edges, origin_node, dest_node)
    
    dist, dijkstra_node_list = min_ops.refine_dijkstra_results(dijkstra_path)
    dijkstra_nodes_df = min_ops.get_dijkstra_matching_df(nodes, dijkstra_node_list, id='osmid')
    # write results to files
    dijkstra_edges_df = min_ops.get_dijkstra_matching_df(edges, dijkstra_node_list, id='u')
    write_results_to_disk(results_folder, origin_node, dest_node, dijkstra_nodes_df, dijkstra_edges_df)


def write_results_to_disk(results_folder, origin_node, dest_node,
                          dijkstra_nodes_df, dijkstra_edges_df):
    """ doc here IMP """
    # create filepaths for nodes and edges respectively
    min_path_fname = results_folder + str(origin_node) +'_to_' + str(dest_node)
    nodes_fpath = min_path_fname + 'dijkstra_nodes.csv'
    edges_fpath = min_path_fname + 'dijkstra_edges.csv'
    # write nodes and edges to csv
    dijkstra_nodes_df.to_csv(nodes_fpath)
    dijkstra_edges_df.to_csv(edges_fpath)


def custom_dijkstra_all_vs_all(src_graph_fp, csv_src_fp, results_csv_fpath, node):
    # read the csv file and get the list of nodes
    df = pandas.read_csv(csv_src_fp, sep=';')
    nodes_list = df[node].to_list()
    combo_list = net_ops.get_all_list_combinations(nodes_list)
    graph = net_ops.load_graph_from_disk(src_graph_fp)
    nodes, edges = net_ops.get_nodes_edges(graph)
    # get edges of network in appropriate form for custom dijkstra
    dijkstra_edges = min_ops.create_dijkstra_edge_list(edges, nodes)
    #TODO here we are
    custom_dijkstra_all_nodes_vs_all(combo_list, graph, edges, 'traffic',
                                dijkstra_edges, results_csv_fpath)


def custom_dijkstra_all_nodes_vs_all(pairs_list, graph, edges, new_col,
                                dijkstra_node_list, results_csv_fpath):
    # create and initialize new column
    net_ops.add_new_column_to_dataframe(edges, new_col)
    # get every pair of list of pairs and run a min path between them
    # updating the traffic in each route.
    start_time = time.time()
    pair_counter = 0 # TODO to be removed when not debugging
    #length = len(pairs_list)
    for pair in pairs_list:
        u, v = pair
        update_edges_list_with_custom_dijkstra_traffic(graph, edges, u, v, new_col, dijkstra_node_list)
        #print("pair ", u, v, "\tupdated successfully\t(", pair_counter, "/", length, ")")
        #pair_counter += 1
    print("--- %s seconds custom min path ---" % (time.time() - start_time))


def update_edges_list_with_custom_dijkstra_traffic(graph, edges, start1,
                                            end1, new_col, dijkstra_edges):
    try:
        dijkstra_path = dijkstra.dijkstra(dijkstra_edges, start1, end1)
        dist, dijkstra_node_list = min_ops.refine_dijkstra_results(dijkstra_path)
        min_path_pairs = net_ops.get_nodes_pairs(dijkstra_node_list)
        net_ops.update_edge_list(min_path_pairs, edges, new_col, 100)
    except TypeError:
        print("no path between ", start1, end1)


def k_best_scenario(src_graph_fp, results_csv_fpath, node, k_nodes=[]):
    """ Method to run a k-best scenario with mandatory "passing"
    through every one of the k_nodes. If no k_nodes list is given then
    a simple dijkstra is executed (k=1).
    
    :param:
    """
    # load network
    graph = net_ops.load_graph_from_disk(src_graph_fp)
    nodes, edges = net_ops.get_nodes_edges(graph)
    dijkstra_edges = min_ops.create_dijkstra_edge_list(edges, nodes)
    # initialize the k_best parameters
    k_res = []
    k_nodes = [3744263637, 300972555, 295512257, 1604968703]
    min_ops.k_best(dijkstra_edges, k_nodes, '', '', k_res)
    dist, k_best_list = min_ops.refine_k_best_results(k_res)
    pdb.set_trace()

#####################################################

def get_network_lvls_scenario(src_csv_fpath, orig_node, dest_node, dest_name):
    """ Scenario where a min path is run between O-D points.
    
    Destination should be downloaded in high detail. Same goes for the
    neighbour local networks too.
    """
    # get neighbours from file
    neighbor_dict = get_neighbors_from_file(src_csv_fpath)
    # search for the neighbors of the given node and download them
    graph = create_detailed_network(neighbor_dict, dest_name)
    # create the big network and save it.
    pdb.set_trace()
    # run a min path there


def get_neighbors_from_file(src_csv_fpath):
    content = ''
    neighbor_dict = {}
    with open(src_csv_fpath, 'r') as f:
        content = f.readlines()
    for line in content:
        key, val = line.split(":")
        val = val.replace("\n", "")
        vals = [x for x in val.split(",")]
        vals = [val.strip() for val in vals]
        print(vals)
        neighbor_dict[key] = vals
    return neighbor_dict


def create_detailed_network(neighbor_dict, dest_name):
    assert (dest_name in neighbor_dict), "destination name not in network!"
    neighbors = neighbor_dict[dest_name]
    graph = get_greece_graph()
    for neighbor in neighbors:
        try:
            neighbor_graph = ox.graph_from_place(neighbor, network_type='drive')
            graph = networkx.compose(graph, neighbor_graph)
        except ValueError as e:
            print ('%s neighbour cannot be downloaded' % neighbor)
    return graph


def get_greece_graph():
    place_name = "Greece"
    ox.config(use_cache=True, log_console=True)
    #cf = '["highway"~"motorway|motorway_link|trunk|secondary|primary"]'
    cf = '["highway"~"motorway|motorway_link"]'
    greece_graph = ox.graph_from_place(place_name, network_type='drive', custom_filter=cf)
    return greece_graph


#############################
def get_athens_local_networks_scenario(src_csv_fpath, src_graph_folder,
                                       dest_area, origin_node, dest_node):
    #save_acquired_from_file_graphs_to_disk(src_csv_fpath, dest_graph_fpath)
    # get neighbors of dictionary
    neighbor_dict = get_neighbors_from_file(src_csv_fpath)
    # get all graphs that represent the local networks of an area respectively
    graphs_in_disk_list = get_graph_files_from_disk(src_graph_folder)
    # acquire all graphs in the disk that match the neighbor_dict and
    # create a super-network joining all local networks
    super_graph = create_super_network(neighbor_dict, src_graph_folder,
                                       graphs_in_disk_list, dest_area)
    # save graph to disk
    supergraph_dest = '../results/supergraph.graphml'
    ox.save_graphml(super_graph, supergraph_dest)
    return super_graph


def get_graph_files_from_disk(source_folder):
    """ method to get the files where graphs (in graphml) are saved.
    """
    sf = source_folder
    onlyfiles = [f for f in listdir(sf) if isfile(join(sf, f))]
    return onlyfiles


def create_super_network(neighbor_dict, src_graph_folder,
                         graphs_in_disk_list, dest_area):
    """ method to create a graph from an abstract high-level graph and
    local graphs."""
    # get greek high-level network
    greece_path = '../results/greece.graphml'
    graph = net_ops.load_graph_from_disk(greece_path)
    # get the neighbors of the destination area
    local_graphs = neighbor_dict[dest_area]
    # acquire all neighbors that have a graph representation in disk
    for lc in local_graphs:
        for gdl in graphs_in_disk_list:
            if lc in gdl:
                gdl_path = src_graph_folder + str(gdl)
                loc_graph = net_ops.load_graph_from_disk(gdl_path)
                graph = networkx.compose(graph, loc_graph)
                print("%s found and merged to graph." % lc)
                break
        else:
            print("%s not found in disk. Procceed without it." % lc)
    return graph


def save_acquired_from_file_graphs_to_disk(src_csv_fpath, dest_graph_fpath):
    """ Method to get names from a file, to acquire graphs from OSM data
    and to save graphs to disk.
    
    :param src_csv_path: str, filepath where the csv with the adjacency matrix is.
    :param dest_graph_fpath: str, folder WITH slash in the end where the graph
        results are being saved.
    """
    neighbor_dict = get_neighbors_from_file(src_csv_fpath)
    for neighbor in neighbor_dict:
        local_graph = get_graph_from_osm(neighbor)
        if local_graph:
            destination = dest_graph_fpath + str(neighbor) +str('.graphml')
            ox.save_graphml(local_graph, destination)
        else:
            print("graph named %s cannot be acquired" % neighbor)


def get_graph_from_osm(place_name):
    try:
        neighbor_graph = ox.graph_from_place(place_name, network_type='drive')
    except ValueError as e:
        print('%s neighbour cannot be downloaded' % place_name)
        return False
    return neighbor_graph


def plot_route_in_graph(graph,u,v):
    """ todo doc and move"""
    shortest_path = net_ops.get_shortest_path(graph, u, v)
    rc = ['r', 'y', 'c']
    fig, ax = ox.plot_graph_route(graph, shortest_path)


def run_tavros_scenario():
    super_graph = get_athens_local_networks_scenario('../data/dimoi_athinas.csv', '../results/graphs/',
                                       'Tavros', 3744263637, 8067989857)
    custom_dijkstra('../results/supergraph.graphml', '../results/', 3744263637, 8067989857)
    plot_route_in_graph(super_graph, 3744263637, 8067989857)
    
    #babis
    nodes, edges = net_ops.get_nodes_edges(super_graph)
    net_ops.write_nodes_edges_to_disk(nodes, edges, 'supergraph', '../results/')


#######################

def supermarkets_vrp_google_scenario(athens_network_path,
                                     supermarkets_path,
                                     results_path):
    # load athens network path and get nodes and edges
    graph = net_ops.load_graph_from_disk(athens_network_path)
    # get and update athens nodes with supermarket field
    nodes, edges = net_ops.get_nodes_edges(graph)
    nodes['supermarket'] = 'None'
    # load supermarkets path
    supermarkets = gpd.read_file(supermarkets_path)
    # project supermarkets nodes in athens network
    ###### HERE works net_sm_nodes = net_ops.get_matched_node_ids(supermarkets, graph)
    net_nodes = net_ops.populate_net_nodes_with_sm_nodes(graph, nodes, supermarkets)
    sm_nodes = net_nodes[net_nodes['supermarket_id'] != 0]
    #sm_nodes = sm_nodes[1:60]
    dist_matrix = net_ops.create_adj_matrix_of_supermarkets(sm_nodes, graph)
    return dist_matrix
    # create adjacency matrix with minimum paths ready for google vrp
    # run google vrp
    # get results


def main():
    tatiana_scenario('../results/creta_graph-secondary.graphml', '../data/creta.csv', '../results/giorgos_traffic-cf.csv')
    #tatiana_scenario('../results/giorgos_regional_graph-cf.graphml', '../data/16_regions.csv', '../results/giorgos_traffic-cf.csv')
    #tatiana_scenario('../results/prim_sec_graph.graphml', '../data/tat_4_step_csv.csv', '../results/giorgos_traffic.csv')
    #supermarkets_vrp_google_scenario('../results/attica_graph.graphml',
    #                                 '../data/supermarkets-attica.geojson',
    #                                 '../results/')
    #run_tavros_scenario()
    #save_acquired_from_file_graphs_to_disk('../data/dimoi_athinas.csv', '../results/graphs/')
    #n = get_network_lvls_scenario('../data/dimoi_athinas.csv',3744263637, 300972555, 'Zografou')
    #k_best_scenario('../results/greece.graphml', 'results.csv', 'osmid')
    #custom_dijkstra_all_vs_all('../results/gr', 'results.csv', 'osmid',)
    #scenario_all_in_all('../results/greece.graphml', '../data/POINTS_NUTS3_MAINLAND3.csv', '../results/POINTS_NUTS3_MAINLAND3_RESULTS.csv', 'node_id')
    #simple_scenario_ipynb()


if __name__ == '__main__':
    main()