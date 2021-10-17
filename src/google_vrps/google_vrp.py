"""Simple Vehicles Routing Problem (VRP).

   This is a sample using the routing library python wrapper to solve a VRP
   problem.
   A description of the problem can be found here:
   http://en.wikipedia.org/wiki/Vehicle_routing_problem.

   Distances are in meters.
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import google_vrps.google_basic_ops as gbo
import flora
import pdb


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    # create a file in order to save the solution steps.
    sol_fpath = gbo.create_results_name()
    print(f'Objective: {solution.ObjectiveValue()}')
    max_route_distance = 0
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
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        print(plan_output)
        gbo.write_solution_to_file(sol_fpath, plan_output)
        max_route_distance = max(route_distance, max_route_distance)
    print('Maximum of the route distances: {}m'.format(max_route_distance))
    gbo.write_solution_to_file(sol_fpath, "route distance: "+str(max_route_distance))


def get_solution(data, manager, routing, solution):
    """Method that modified the print_solution and returns
    a dictionary of <veh_id:[nodes list]> pairs and <dist_id:distance>
    pairs.

    Args:
        data ([type]): [description]
        manager ([type]): [description]
        routing ([type]): [description]
        solution ([type]): [description]

    Returns:
        [type]: [description]
    """
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


def _set_route_distance(vehicle_id, route_distance, route_list):
    route_id = str(vehicle_id) + '_route_distance'
    route_list[route_id] = route_distance


def google_vrp(data):
    """Entry point of the program."""
    # Instantiate the data problem.
    #data = flora_data_model() #TODOcreate_data_model()

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
        300000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)
        # get solution and return it
        sol = get_solution(data, manager, routing, solution)
        return sol
    else:
        print('No solution found !')


if __name__ == '__main__':
    google_vrp()