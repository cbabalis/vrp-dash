"""Vehicles Routing Problem (VRP) by google.

https://developers.google.com/optimization/routing/vrp"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import flora
import network_operations as net_ops
import input_output_operations as io_ops
import pandas as pd
import pdb
import optops


def create_data_model():
    data = {}
    data['distance_matrix'] = []
    data['num_vehicles'] = 4
    data['depot'] = 0
    return data


def convert_list_data_to_ints(a_list):
    """ Method to get a list of floats and to return them as ints.

    Args:
        a_list (list): list of floats
    return:
        list of ints
    """
    int_list = [[int(float(j)) for j in i] for i in a_list]
    return int_list


def print_results_to_map(or_result, data_csvfile):
    """Method to read VRP result and original data file and to print
    the result to map

    Args:
        or_result (str): text with VRP result
        data_csvfile (str): filepath of original data position in disk
    """
    # read data from disk
    supermarkets = pd.read_csv(data_csvfile, delimiter='\t')
    result = io_ops.get_route_node_ids_from_textfile(or_result)
    # update dataframes with results
    pdb.set_trace()
    add_route_to_df(supermarkets, result)


def add_route_to_df(df, routes, new_col='routes'):
    """Method to add a new column (route) to dataframe and
    the corresponding nodes of the route.

    Args:
        df (dataframe): Dataframe to work on (add new column)
        routes (dict): dictionary of <route_id: nodes_list> pairs
        new_col (str, optional): Name of the new column. Defaults to 'routes'.
    """
    # add new column to dataframe
    df[new_col] = -1
    # populate new column with data
    for route in routes:
        _populate_df_with_route(routes, route, df)


def _populate_df_with_route(routes_dict, route_id, df):
    """Method to populate a dataframe with routes

    Args:
        routes_dict ([type]): [description]
        route_id ([type]): [description]
        df ([type]): [description]
    """
    pass


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    max_route_distance = 0
    written_result = ''
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += ' {} -> '.format(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        written_result += plan_output
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        print(plan_output)
        max_route_distance = max(route_distance, max_route_distance)
    print('Maximum of the route distances: {}m'.format(max_route_distance))
    return written_result


def main():
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    #data = flora.flora('results/graphs/attica-graph.graphml', 'data/supermarkets.csv', '') #create_data_model()
    data_csvfile = 'data/super_sample_tabs.csv'
    data = create_data_model()
    od_result = net_ops.compute_distance_matrix(data_csvfile)
    data['distance_matrix'] = od_result[0].values.tolist()
    data['distance_matrix'] = convert_list_data_to_ints(data['distance_matrix'])
    #pdb.set_trace()
    # following line is for kasselouris od matrix
    #io_ops.write_od_to_csv(data['distance_matrix'], 'data/kassel_results.csv')

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        20000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100000)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    written_solution = ''
    or_result = 'results/or_results.txt'
    solution_paths = optops.get_all_routes(data, manager, routing, solution)
    if solution:
        written_solution = print_solution(data, manager, routing, solution)
        with open(or_result, 'w') as f:
            f.write(written_solution)
    pdb.set_trace()
    # process the results and print them to map
    print_results_to_map(or_result, data_csvfile)


if __name__ == '__main__':
    main()