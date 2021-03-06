"""Capacited Vehicles Routing Problem (CVRP)."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import google_vrps.google_basic_ops as gbo # for common printing
import pdb


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    # create a file in order to save the solution steps.
    sol_fpath = gbo.create_results_name()
    print("solution name filepath is ", sol_fpath)
    print(f'Objective: {solution.ObjectiveValue()}')
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        gbo.write_solution_to_file(sol_fpath, plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))
    dist_load = "total_distance of all routes is " + str(total_distance) +\
        "m and total load of all routes is " + str(total_load)
    gbo.write_solution_to_file(sol_fpath, dist_load)


def get_solution(data, manager, routing, solution):
    """Method to modify the print_solution and to return a tuple
    of <veh_id:[nodes list]> pairs, <veh_id:demand> pairs and
    <veh_id:distance> pairs respectively.

    Args:
        data ([type]): [description]
        manager ([type]): [description]
        routing ([type]): [description]
        solution ([type]): [description]

    Returns:
        [type]: [description]
    """
    route_list = get_route_list(data, manager, routing, solution)
    route_load = {}
    return route_list
    #return (route_list, route_demand, route_dist)


def get_route_list(data, manager, routing, solution):
    route_list = {}
    max_route_distance = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_list[vehicle_id] = []
        route_distance = 0
        while not routing.IsEnd(index):
            route_list[vehicle_id].append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        route_list[vehicle_id].append(manager.IndexToNode(index))
        #_set_route_distance(vehicle_id, route_distance, route_list)
    return route_list


def capacitated_vrp(cvrp_data):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = cvrp_data

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


    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(1)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)
        sol = get_solution(data, manager, routing, solution)
        return sol
    else:
        print("No solution for cvrp found!")


if __name__ == '__main__':
    capacitated_vrp()