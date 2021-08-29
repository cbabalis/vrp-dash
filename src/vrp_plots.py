""" This module prints routes to paths.

"""


import networkx as nx
import osmnx as ox
from shapely.geometry import LineString, mapping
import geopandas as gpd
from ipyleaflet import *
import plotly.express as px
import network_operations as net_ops
import osmnx as ox
import networkx as nx
import plotly.graph_objects as go
import numpy as np
import pdb
import osrm
from osrm import Point, simple_route
import requests
import folium
import polyline


css_cols = ['aliceblue','aqua','aquamarine','azure','beige','bisque','black','blanchedalmond','blue','blueviolet','brown','burlywood','cadetblue','chartreuse','chocolate','coral','cornflowerblue','cornsilk','crimson','cyan','darkblue','darkcyan','darkgoldenrod','darkgray','darkgrey','darkgreen','darkkhaki','darkmagenta','darkolivegreen','darkorange','darkorchid','darkred','darksalmon','darkseagreen','darkslateblue','darkslategray','darkslategrey','darkturquoise','darkviolet','deeppink','deepskyblue','dimgray','dimgrey','dodgerblue','firebrick','floralwhite','forestgreen','fuchsia','gainsboro','ghostwhite','gold','goldenrod','gray','grey','green','greenyellow','honeydew','hotpink','indianred','indigo','ivory','khaki','lavender','lavenderblush','lawngreen','lemonchiffon','lightblue','lightcoral','lightcyan','lightgoldenrodyellow','lightgray','lightgrey','lightgreen','lightpink','lightsalmon','lightseagreen','lightskyblue','lightslategray','lightslategrey','lightsteelblue','lightyellow','lime','limegreen','linen','magenta','maroon','mediumaquamarine','mediumblue','mediumorchid','mediumpurple','mediumseagreen','mediumslateblue','mediumspringgreen','mediumturquoise','mediumvioletred','midnightblue','mintcream','mistyrose','moccasin','navajowhite','navy','oldlace','olive','olivedrab','orange','orangered','orchid','palegoldenrod','palegreen','paleturquoise','palevioletred','papayawhip','peachpuff','peru','pink','plum','powderblue','purple','red','rosybrown','royalblue','rebeccapurple','saddlebrown','salmon','sandybrown','seagreen','seashell','sienna','silver','skyblue','slateblue','slategray','springgreen','steelblue','tan','teal','thistle','tomato','turquoise','violet','yellow','yellowgreen']

def convert_node_ids_to_nodes(df, veh_id_dict):
    """ Method to convert a dictionary of <vehicle:[list_of_node_ids]>
    to <vehicle:[list of nodes]>

    Args:
        df ([type]): [description]
        node_dict ([type]): [description]
    """
    # initialize the new dictionary.
    veh_node_dict = {}
    # get only lon-lat columns of the initial structure
    lon_lat_df = df[['longitude', 'latitude']]
    # for each vehicle, create a new entry in the dictionary and
    # add the nodes of the dataframe that correspond to the
    # equivalent id.
    for veh in veh_id_dict:
        points = veh_id_dict[veh]
        node_list = []
        for point in points:
            lon_lat_dict = lon_lat_df.iloc[int(point)].to_dict()
            node_list.append(lon_lat_dict)
        veh_node_dict[veh] = node_list.copy()
    return veh_node_dict


def plot_vehicles_with_routes(veh_node_dict):
    """Method to plot vehicles and routes VRP result.

    Args:
        veh_node_dict ([type]): [description]

    Returns:
        [type]: [description]
    """
    # initialize graph and figure
    fig = ''
    graph_filepath = '/home/blaxeep/workspace/osm_project/results/greece-athens.graphml'
    graph = net_ops.load_graph_from_disk(graph_filepath)
    # initialize color of each line.
    colorscales = css_cols
    # initialize figure
    fig = go.Figure()
    for vehicle in veh_node_dict:
        # if and continue ensure that the vehicles have been used (not empty vehicles)
        if (len(veh_node_dict[vehicle]) < 3):
            continue
        # get color for the current vehicle
        col = colorscales.pop()
        # if not fig:
        #     lon = veh_node_dict[0][0]['longitude']
        #     lat = veh_node_dict[0][0]['latitude']
        #    fig = _initialize_figure(lon, lat, col)
        # create paths for each vehicle and add them to the figure
        paint_vehicle_route(fig, veh_node_dict[vehicle], graph, veh_id=vehicle, colorlist=css_cols)
    # return the final figure
    return fig


def _initialize_figure(lon, lat, col):
    fig = go.Figure(go.Scattermapbox(
        name = "Path",
        mode = "lines",
        lon = lon,
        lat = lat,
        marker = {'size': 10},
        line = dict(width=4.5, color=col)))
    return fig


def paint_vehicle_route(fig, nodes_list, graph, veh_id, colorlist):
    # create empty lists of lines and lat, lon of nodes
    lat_lines_list = []
    lon_lines_list = []
    lat_nodes_list = []
    lon_nodes_list = []
    pois_list = list(nodes_list)
    for idx in range(len(pois_list)-1):
        origin_node = _get_osrm_point_coords(pois_list[idx])
        if (idx+1) > len(pois_list):
            dest_node = _get_osrm_point_coords(pois_list[0])
        else:
            dest_node = _get_osrm_point_coords(pois_list[idx+1])
        # collect all lines between the points of interest and
        set_geometry_between_two_points(origin_node, dest_node, lat_lines_list, lon_lines_list)
        # collect all points by latitude and longitude respectively
        set_coords_of_two_points(origin_node, dest_node, lat_nodes_list, lon_nodes_list)
    # paint all collected points with the given color to the graph
    paint_data_to_figure(fig, lat_nodes_list, lon_nodes_list, lat_lines_list, lon_lines_list, veh_id, colorlist)


def set_geometry_between_two_points(origin_node, dest_node, lat_list, lon_list):
    # get a json with geometry of route between the two nodes
    # inside it
    result = simple_route(origin_node, dest_node)
    # decode geometry
    geom = result['routes'][0]['geometry']
    route_lines = polyline.decode(geom)
    assign_geometry_lines_to_lists(route_lines, lat_list, lon_list)


def assign_geometry_lines_to_lists(route_lines, lat_list, lon_list):
    for line in route_lines:
        lat, lon = line
        lat_list.append(lat)
        lon_list.append(lon)


def set_coords_of_two_points(origin_node, dest_node, lat_list, lon_list):
    lat_list.append(origin_node.latitude)
    lon_list.append(origin_node.longitude)
    lat_list.append(dest_node.latitude)
    lon_list.append(dest_node.longitude)


def paint_data_to_figure(fig, lat_nodes_list, lon_nodes_list, lat_lines_list, lon_lines_list, veh_id, colorlist):
        fig.add_trace(go.Scattermapbox(
            name = "Path of vehicle " + str(veh_id),
            mode = "lines",
            lon = lon_lines_list,
            lat = lat_lines_list,
            marker = {'size': 10},
            line = dict(width = 4.5, color = colorlist.pop())))
        # adding source marker
        fig.add_trace(go.Scattermapbox(
            name = "Nodes visited by vehicle " + str(veh_id),
            mode = "markers",
            lon = lon_nodes_list,
            lat = lat_nodes_list,
            marker = {'size': 15, 'color':colorlist.pop(), 'opacity':0.8},
            ))
        
        
        # getting center for plots:
        lat_center = np.mean(lat_lines_list)
        long_center = np.mean(lon_lines_list)
        # defining the layout using mapbox_style
        fig.update_layout(mapbox_style="open-street-map", #"stamen-terrain",
            mapbox_center_lat = 30, mapbox_center_lon=-80)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                        mapbox = {
                            'center': {'lat': lat_center, 
                            'lon': long_center},
                            'zoom': 13})


def _get_osrm_point_coords(lon_lat_dict):
    return Point(latitude=lon_lat_dict['latitude'],
                 longitude=lon_lat_dict['longitude'])


test_data = {0: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.713160600000002, 'latitude': 37.993684026168}, {'longitude': 23.7143225, 'latitude': 38.002765126168}, {'longitude': 23.713945499999998, 'latitude': 38.002842226168}, {'longitude': 23.718667526140898, 'latitude': 38.0106859000985}, {'longitude': 23.7188093, 'latitude': 38.028381326167995}, {'longitude': 23.730810791097603, 'latitude': 38.058340994155}, {'longitude': 23.737992819906896, 'latitude': 38.0876087409059}, {'longitude': 23.742188100000003, 'latitude': 38.086888226168}, {'longitude': 23.739454401525197, 'latitude': 38.0602136918249}, {'longitude': 23.7282419, 'latitude': 38.033252526168}, {'longitude': 23.724806, 'latitude': 37.993414826168}, {'longitude': 23.7287563, 'latitude': 37.986576326168}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 1: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.6870391, 'latitude': 38.020329626168}, {'longitude': 23.680572, 'latitude': 38.038801826168}, {'longitude': 23.749412200000002, 'latitude': 38.014249526168}, {'longitude': 23.752506399999998, 'latitude': 37.991257126168}, {'longitude': 23.750271376694798, 'latitude': 37.9114748463772}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 2: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.695334600000002, 'latitude': 37.957527926168}, {'longitude': 23.678609299999998, 'latitude': 37.947447526168}, {'longitude': 23.6534678, 'latitude': 37.969916626168}, {'longitude': 23.7072129, 'latitude': 37.976888626168}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 3: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 4: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 5: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 6: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 7: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 8: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}], 9: [{'longitude': 23.762025412372104, 'latitude': 37.887964699939204}, {'longitude': 23.862925399999998, 'latitude': 37.950393026168}, {'longitude': 23.762025412372104, 'latitude': 37.887964699939204}]}


def main():
    fig = plot_vehicles_with_routes(test_data)
    fig.show()


if __name__ == '__main__':
    main()