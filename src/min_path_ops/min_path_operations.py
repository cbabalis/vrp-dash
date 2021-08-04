""" Module to execute minimum path algorithms and operations such as 
graphs, adjacency lists, etc.
"""

import math
import pandas as pd
import min_path_ops.dijkstra as dijkstra
import pdb


def compute_distance_between_points(x1, y1, x2, y2):
    """ Method to compute distance between A(x1, y1) and B(x2, y2) and
    to return the result.
    """
    distance = math.sqrt( ((x1 - x2)**2) + ((y1-y2)**2) )
    return distance


def get_node_coords_by_id(node_list, id, col_id='node'):
    """ Method to return the (X, Y) of a node given the id only.
    """
    a_node = node_list[node_list[col_id]==id]
    coords = get_geometry_of_point(a_node.x, a_node.y)
    return coords


def get_geometry_of_point(point):
    """ Method to return the geometry (X, Y) of a point.
    """
    x = float(point.x)
    y = float(point.y)
    return (x, y)


def create_dijkstra_edge_list(edges, nodes):
    """ Method to create a list of edges ready for dijkstra.
    
    Edges should be a list of:
    [(start_node1, end_node1, cost),
     (start_node2, end_node2, cost),
     ...]
    return list_of_edges
    """
    dijkstra_edge_list = []
    for edge in edges.itertuples():
        start_node = edge.u
        end_node = edge.v
        cost = edge.length#compute_travel_cost(start_node, end_node, nodes)
        dijkstra_edge = (start_node, end_node, cost)
        dijkstra_edge_list.append(dijkstra_edge)
    return dijkstra_edge_list


def compute_travel_cost(u, v, node_list, id='osmid'):
    """ Method to compute travel cost based on distance."""
    # check if u, v are in node list
    if u not in node_list[id] or v not in node_list[id]:
        return -1 # TODO should throw an exception here.
    # if they are then get their coordinates and
    u_x, u_y = get_node_coords_by_id(node_list, u, col_id=id)
    v_x, v_y = get_node_coords_by_id(node_list, v, col_id=id)
    # compute their distance
    dist = compute_distance_between_points(u_x, u_y, v_x, v_y)
    # return the distance as the travel cost
    return dist


def refine_dijkstra_results(dijkstra_struct):
    """ Method to refine dijkstra structure that contains results.
    
    Dijkstra structure is as follows:
    (dist, (n1, (n2, (n3, ...))))
    It is a tuple inside a tuple recursively.
    
    Return: distance and a list of nodes defining the path.
    """
    # split distance and path of nodes
    dist = dijkstra_struct[0]
    path = dijkstra_struct[1]
    # process nodes. Iterate tuple until empty and remove nodes one by
    # one until the empty tuple is being found.
    nodes_path = []
    get_nodes_from_tuple(nodes_path, path)
    return dist, nodes_path


def get_nodes_from_tuple(nodes_path, tuple_struct):
    """ recursive method which iterates a tuple containing a tuple
    etc. and collecting tuple of tuples' values in a list.
    """
    if not tuple_struct:
        return
    nodes_path.append(tuple_struct[0])
    get_nodes_from_tuple(nodes_path, tuple_struct[1])


def get_dijkstra_matching_df(df, dijkstra_nodes_list, id='osmid'):
    """ Method to find and get nodes that are inside minimum path and
    to get nodes and edges inside the initial network.
    :param nodes: pandas dataframe for nodes.
    :param dijkstra_nodes_list: a list with dijkstra nodes.
    """
    # create an empty pandas dataframe
    dijkstra_df = pd.DataFrame(columns=df.columns)
    # populate new dataframe with the dijkstra nodes
    for dn in dijkstra_nodes_list:
        row = df[df[id] == dn]
        dijkstra_df = dijkstra_df.append(row)
    return dijkstra_df


def k_best(dijkstra_edges, mandatory_nodes_list, median_node,
           end_node, results_list):
    """ Solves a minimum path by following certain nodes as given.
    
    Algorithm
    ---------
    k_best(mandatory_list, median, end, results_list):
        if mandatory_list is empty:
            return
        if median == end:
            end = mandatory_list.pop_last_item()
            median = mandatory_list.pop_last_item()
            results_list.append(dijkstra(median, end))
            return k_best(mandatory_list, median, end, results_list)
        end = median
        median = mandatory_list.pop()
        results_list.append(dijkstra(median, end))
        return k_best(mandatory_list, median, end, results_list)
    
    Explanation
    -----------
    It is a recursive routine/algorithm. It has end condition,
    start condition and recursive part.
    
    END CONDITION: list of mandatory nodes is empty. Exits.
    START CONDITION: median == end. Special nodes for starting the algo.
    run a dijkstra with (end-1, end) nodes and get the result.
    RECURSION:
        - start from the end of the path.
        - move nodes by -1 position in list. So:
            * end = median
            * median = median - 1
        - re-run a dijkstra and
        - return a k-best.
    
    Args:
        dijkstra_edges (list): edges that consist a dijkstra path.
        mandatory_nodes_list (list): list of all mandatory nodes k-best
                                    has to visit.
        median_node (int): a node between origin and destination in path.
        end_node (int): the ending node for a dijkstra path.
        results_list (list): list of dijkstra runs.

    Returns:
        Nothing is being returned actually. results_list is being updated.
    """
    #pdb.set_trace()
    if not mandatory_nodes_list:
        return
    if median_node == end_node:
        end_node = mandatory_nodes_list.pop()
        median_node = mandatory_nodes_list.pop()
        dijkstra_path = dijkstra.dijkstra(dijkstra_edges, median_node, end_node)
        results_list.append(dijkstra_path)
        return k_best(dijkstra_edges, mandatory_nodes_list,
                      median_node, end_node, results_list)
    end_node = median_node
    median_node = mandatory_nodes_list.pop()
    dijkstra_path = dijkstra.dijkstra(dijkstra_edges, median_node, end_node)
    results_list.append(dijkstra_path)
    return k_best(dijkstra_edges, mandatory_nodes_list,
                    median_node, end_node, results_list)


def refine_k_best_results(results_list):
    """Method to refine the results of a k-best algorithm.
    
    Goal of this method is to take a recursive tuples list and 
    extract the tuple elements one by one in a new list. In addition,
    it computes and returns the total distance of the local min-paths
    that have run.

    Args:
        results_list (list): A list which contains a tuple of tuples
        in a recursive way.

    Returns:
        float, list: total distance, list with k_best paths
    """
    total_distance = 0
    k_best_nodes_list = []
    for a_tuple in results_list:
        dist, nodes_path = refine_dijkstra_results(a_tuple)
        total_distance += dist
        k_best_nodes_list.extend(nodes_path)
    return total_distance, k_best_nodes_list
        