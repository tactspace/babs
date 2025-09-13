import csv
import math
from typing import List, Tuple, Dict, Optional, Set
import networkx as nx
import matplotlib.pyplot as plt
import folium
from folium import plugins
from models import ChargingStation


def load_charging_stations(file_path: str) -> List[ChargingStation]:
    """
    Load charging stations from CSV file
    
    Args:
        file_path: Path to the CSV file containing charging station data
        
    Returns:
        List of ChargingStation objects
    """
    charging_stations = []
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean and convert the price field (remove € symbol)
            price_str = row['price_€/kWh'].replace('€', '')
            
            station = ChargingStation(
                id=int(row['ID']),
                country=row['country'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                truck_suitability=row['truck_suitability'],
                operator_name=row['operator_name'],
                max_power_kW=float(row['max_power_kW']),
                price_per_kWh=float(price_str)
            )
            charging_stations.append(station)
    
    return charging_stations


def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate the Haversine distance between two points in kilometers
    
    Args:
        point1: (latitude, longitude) of first point
        point2: (latitude, longitude) of second point
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


def find_nearest_charging_stations(
    point: Tuple[float, float],
    charging_stations: List[ChargingStation],
    max_distance: float = 50.0,  # km
    truck_suitable_only: bool = True,
    limit: int = 5
) -> List[ChargingStation]:
    """
    Find the nearest charging stations to a given point
    
    Args:
        point: (latitude, longitude) of the point
        charging_stations: List of all available charging stations
        max_distance: Maximum distance in kilometers to search
        truck_suitable_only: If True, only return stations suitable for trucks
        limit: Maximum number of stations to return
        
    Returns:
        List of nearest ChargingStation objects
    """
    stations_with_distance = []
    
    for station in charging_stations:
        # Skip stations not suitable for trucks if requested
        if truck_suitable_only and station.truck_suitability != "yes":
            continue
            
        distance = calculate_distance(point, (station.latitude, station.longitude))
        
        if distance <= max_distance:
            stations_with_distance.append((station, distance))
    
    # Sort by distance
    stations_with_distance.sort(key=lambda x: x[1])
    
    # Return only the stations, not the distances
    return [station for station, _ in stations_with_distance[:limit]]


def build_charging_station_graph(charging_stations: List[ChargingStation], max_edge_distance: float = 400.0) -> nx.Graph:
    """
    Build a graph where nodes are charging stations and edges represent possible routes between them.
    
    Args:
        charging_stations: List of ChargingStation objects
        max_edge_distance: Maximum distance in km between stations to create an edge (default 400km)
        
    Returns:
        NetworkX Graph object where:
        - Nodes are ChargingStation objects
        - Edges have attributes:
            - distance: Distance in km between stations
            - weight: Edge weight (currently set to 1)
    """
    # Create empty undirected graph
    G = nx.Graph()
    
    # Add all charging stations as nodes
    for station in charging_stations:
        G.add_node(station.id, station=station)
    
    # Create edges between stations within max_edge_distance
    for i, station1 in enumerate(charging_stations):
        for station2 in charging_stations[i+1:]:
            distance = calculate_distance(
                (station1.latitude, station1.longitude),
                (station2.latitude, station2.longitude)
            )
            
            # Only create edge if stations are within max_edge_distance
            if distance <= max_edge_distance:
                G.add_edge(
                    station1.id,
                    station2.id,
                    distance=distance,
                    weight=1  # Currently set to 1 as requested
                )
    
    return G

def visualize_charging_graph_map(graph: nx.Graph, output_file: str = "charging_graph_map.html"):
    """
    Create an interactive map visualization of the charging station graph using Folium
    
    Args:
        graph: NetworkX graph of charging stations
        output_file: Path to save the HTML map file
    """
    # Calculate center of the map
    lats = [graph.nodes[node]['station'].latitude for node in graph.nodes()]
    lons = [graph.nodes[node]['station'].longitude for node in graph.nodes()]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add nodes (charging stations)
    for node in graph.nodes():
        station = graph.nodes[node]['station']
        
        # Create popup text
        popup_text = f"""
        <b>{station.operator_name}</b><br>
        Power: {station.max_power_kW} kW<br>
        Price: {station.price_per_kWh}€/kWh<br>
        Truck Suitable: {station.truck_suitability}
        """
        
        # Add marker
        folium.CircleMarker(
            location=[station.latitude, station.longitude],
            radius=5,
            color='blue',
            fill=True,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)
    
    # Add edges (connections)
    for edge in graph.edges():
        station1 = graph.nodes[edge[0]]['station']
        station2 = graph.nodes[edge[1]]['station']
        
        # Draw line between connected stations
        points = [
            [station1.latitude, station1.longitude],
            [station2.latitude, station2.longitude]
        ]
        
        folium.PolyLine(
            points,
            weight=1,
            color='gray',
            opacity=0.5
        ).add_to(m)
    
    # Add edge count and node count to the map
    title_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    width: 250px; 
                    height: 60px; 
                    z-index:9999; 
                    background-color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid gray;">
            <h4>Charging Station Network</h4>
            Stations: {graph.number_of_nodes()}<br>
            Connections: {graph.number_of_edges()}
        </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save the map
    m.save(output_file)

# Example usage:
if __name__ == "__main__":
    # Load charging stations
    stations = load_charging_stations("data/public_charge_points.csv")

    print(stations[0])
    
    # Build graph
    graph = build_charging_station_graph(stations)
    
    # Print some basic graph statistics
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    
    # Example: Find shortest path between two stations
    start_station = stations[0]
    end_station = stations[-1]
    try:
        path = nx.shortest_path(graph, start_station.id, end_station.id, weight='weight')
        print(f"Shortest path from station {start_station.id} to {end_station.id}:")
        for station_id in path:
            station = graph.nodes[station_id]['station']
            print(f"  Station {station.id}: {station.operator_name} at ({station.latitude}, {station.longitude})")
    except nx.NetworkXNoPath:
        print("No path exists between these stations")

    # visualize_charging_graph_2d(graph)
    visualize_charging_graph_map(graph)
        