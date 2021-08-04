from collections import defaultdict
from heapq import *
import pdb

def dijkstra(edges, f, t):
    g = defaultdict(list)
    for l,r,c in edges:
        g[l].append((c,r))

    q, seen, mins = [(0,f,())], set(), {f: 0}
    while q:
        (cost,v1,path) = heappop(q)
        if v1 not in seen:
            seen.add(v1)
            path = (v1, path)
            if v1 == t: return (cost, path)

            for c, v2 in g.get(v1, ()):
                if v2 in seen: continue
                prev = mins.get(v2, None)
                next = cost + c
                if prev is None or next < prev:
                    mins[v2] = next
                    heappush(q, (next, v2, path))

def get_stop_code(i, stops):
    if stops:
        stop_elems = stops[i].split(",")
        return stop_elems[0].split("=")[-1]

def get_cost(i, stops):
    current_lat = float(get_element(i, stops, elem=7))
    current_long = float(get_element(i, stops, elem=8))
    next_lat = float(get_element(i+1, stops, elem=7))
    next_long = float(get_element(i+1, stops, elem=8))
    cost = compute_cost(current_lat, current_long, next_lat, next_long)
    return cost

def get_element(i, stops, elem):
    if stops:
        try:
            stop_elems = stops[i].split(",")
            return stop_elems[elem].split("=")[-1]
        except:
            # if anything goes wrong, just return a really big number
            # (so as not to be useful in a dijkstra)
            print("Error for elems!")
            return 100000000

def compute_cost(curr_lat, curr_long, next_lat, next_long):
    cost = ((curr_lat - next_lat)**2 + (curr_long - next_long)**2)**(0.5)
    return cost


if __name__ == "__main__":
    with open('stops.txt', 'r') as f:
        routes = f.readlines()

    stops = []
    for r in routes:
        stops.extend(r.split("Stop("))

    edges = []
    for i in range(1, len(stops)-1):
        stop_code = get_stop_code(i, stops)
        next_code = get_stop_code(i+1, stops)
        cost = get_cost(i, stops)
        edges.append((stop_code, next_code, cost))

        print("=== Dijkstra ===")
        dijkstra_path = ''
        print ("10349 -> 10409:")
        dijkstra_path = dijkstra(edges, "10349", "10409")
        print(dijkstra_path)
