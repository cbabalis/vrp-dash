""" This module prints routes to paths.

"""


import networkx as nx
import osmnx as ox
from shapely.geometry import LineString, mapping
import geopandas as gpd
from ipyleaflet import *
import pdb


def convert_node_ids_to_nodes(df, veh_id_dict):
    """ Method to convert a dictionary of <vehicle:[list_of_node_ids]>
    to <vehicle:[list of nodes]>

    Args:
        df ([type]): [description]
        node_dict ([type]): [description]
    """
    # initialize the new dictionary.
    veh_node_dict = {}
    # for each vehicle, create a new entry in the dictionary and
    # add the nodes of the dataframe that correspond to the
    # equivalent id.
    pdb.set_trace()
    lon_lat_df = df[['longitude', 'latitude']]
    for veh in veh_id_dict:
        points = veh_id_dict[veh]
        node_list = []
        for point in points:
            lon_lat_dict = lon_lat_df.iloc[int(point)].to_dict()
            node_list.append(lon_lat_dict)
        veh_node_dict[veh] = node_list.copy()
    return veh_node_dict


def plot_path(lat, long, origin_point, destination_point):
    
    """
    Given a list of latitudes and longitudes, origin 
    and destination point, plots a path on a map
    
    Parameters
    ----------
    lat, long: list of latitudes and longitudes
    origin_point, destination_point: co-ordinates of origin
    and destination
    Returns
    -------
    Nothing. Only shows the map.
    """
    # adding the lines joining the nodes
    fig = go.Figure(go.Scattermapbox(
        name = "Path",
        mode = "lines",
        lon = long,
        lat = lat,
        marker = {'size': 10},
        line = dict(width = 4.5, color = 'blue')))
    # adding source marker
    fig.add_trace(go.Scattermapbox(
        name = "Source",
        mode = "markers",
        lon = [origin_point[1]],
        lat = [origin_point[0]],
        marker = {'size': 12, 'color':"red"}))
     
    # adding destination marker
    fig.add_trace(go.Scattermapbox(
        name = "Destination",
        mode = "markers",
        lon = [destination_point[1]],
        lat = [destination_point[0]],
        marker = {'size': 12, 'color':'green'}))
    
    # getting center for plots:
    lat_center = np.mean(lat)
    long_center = np.mean(long)
    # defining the layout using mapbox_style
    fig.update_layout(mapbox_style="stamen-terrain",
        mapbox_center_lat = 30, mapbox_center_lon=-80)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      mapbox = {
                          'center': {'lat': lat_center, 
                          'lon': long_center},
                          'zoom': 13})
    fig.show()


def main():
    pass


if __name__ == '__main__':
    main()