import csv
import math
from typing import List, Tuple, Dict, Optional, Set
import networkx as nx
import matplotlib.pyplot as plt
import folium
from folium import plugins
from models import ChargingStation
import json
import time
from typing import Dict, Any


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

def compute_and_cache_station_distances(graph: nx.Graph, output_file: str = "graph_computation.json") -> Dict[str, Any]:
    """
    Compute distances between all station pairs in the graph using TomTom API
    and cache the results to a JSON file.
    
    Args:
        graph: NetworkX graph with charging stations
        output_file: Path to save the cached distances
    """
    # Initialize cache dictionary
    distance_cache = {}
    
    # Get all edges in the graph
    edges = list(graph.edges())
    total_edges = len(edges)
    
    print(f"Computing distances for {total_edges} station pairs...")
    
    for idx, (station1_id, station2_id) in enumerate(edges, 1):
        station1 = graph.nodes[station1_id]['station']
        station2 = graph.nodes[station2_id]['station']
        
        # Create cache key
        cache_key = f"{station1_id}_{station2_id}"
        
        print(f"Processing pair {idx}/{total_edges}: {station1.operator_name} -> {station2.operator_name}")
        
        # Get route using TomTom API
        start_point = (station1.latitude, station1.longitude)
        end_point = (station2.latitude, station2.longitude)
        
        try:
            from tomtom import get_route
            route_data = get_route(start_point, end_point)
            
            if route_data:
                # Store in cache with source and destination coordinates
                cache_entry = {
                    "source": {
                        "latitude": station1.latitude,
                        "longitude": station1.longitude
                    },
                    "destination": {
                        "latitude": station2.latitude,
                        "longitude": station2.longitude
                    },
                    "api_response": route_data["full_response"]
                }
                
                distance_cache[cache_key] = cache_entry
                
                # Update graph edge with actual distance
                graph.edges[station1_id, station2_id]['distance'] = route_data['distance'] / 1000  # Convert to km
                
                # Save cache periodically (every 10 pairs)
                if idx % 10 == 0:
                    with open(output_file, 'w') as f:
                        json.dump(distance_cache, f, indent=2)
                    print(f"Saved cache after {idx} pairs")
                
                # Add delay to respect API rate limits
                time.sleep(1)
            
        except Exception as e:
            print(f"Error computing distance for pair {station1_id}-{station2_id}: {e}")
            continue
    
    # Final save of the cache
    with open(output_file, 'w') as f:
        json.dump(distance_cache, f, indent=2)

    # Also export the graph to a json file
    with open('final_graph.json', 'w') as f:
        json.dump(graph.edges(), f, indent=2)
    
    print(f"Completed! Cached {len(distance_cache)} station pairs to {output_file}")
    return distance_cache

def generate_graph(num_stations:int):
    stations = load_charging_stations("data/public_charge_points.csv")
    graph = build_charging_station_graph(stations[:num_stations])
    return graph

def update_graph_weights(graph: nx.Graph, hourly_rate: float = 35.0) -> nx.Graph:
    """
    Update graph edge weights using cached route data and driver costs
    
    Args:
        graph: NetworkX graph with charging stations
        cache_file: Path to the cached distances JSON file
        hourly_rate: Driver's hourly pay rate in euros (default: €35/hour)
        
    Returns:
        Updated graph with weights based on driver costs
    """
    # Load cached distances
    with open('graph_computation.json', 'r') as f:
        distance_cache = json.load(f)
    
    # Update edge weights based on cached data
    for edge in graph.edges():
        station1_id, station2_id = edge
        
        # Check both possible key combinations (1_2 and 2_1)
        cache_key = f"{station1_id}_{station2_id}"
        reverse_key = f"{station2_id}_{station1_id}"
        
        cache_entry = distance_cache.get(cache_key) or distance_cache.get(reverse_key)
        
        if cache_entry:
            try:
                # Extract distance and time from API response
                distance_meters = cache_entry['api_response']['routes'][0]['summary']['lengthInMeters']
                travel_time_seconds = cache_entry['api_response']['routes'][0]['summary']['travelTimeInSeconds']
                
                # Convert to more readable units
                distance_km = distance_meters / 1000
                travel_time_hours = travel_time_seconds / 3600
                
                # Calculate driver cost for this route
                driver_cost = travel_time_hours * hourly_rate
                
                # Store all relevant data in edge attributes
                graph.edges[station1_id, station2_id].update({
                    'weight': driver_cost,  # Main weight is now the driver cost
                    'driving_distance': distance_km,
                    'travel_time_seconds': travel_time_seconds,
                    'travel_time_hours': travel_time_hours,
                    'driver_cost': driver_cost
                })
                
            except (KeyError, IndexError) as e:
                print(f"Error processing cache entry for {cache_key}: {e}")
                continue
        else:
            print(f"No cached data found for edge {station1_id}-{station2_id}")
    
    return graph

def visualize_weighted_charging_graph_map(graph: nx.Graph, output_file: str = "weighted_charging_map.html"):
    """
    Create an interactive map visualization of the charging station graph with weights and edge information
    
    Args:
        graph: NetworkX graph with weighted edges
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
        
        # Create station popup text
        popup_text = f"""
        <div style="width: 200px;">
            <b>{station.operator_name}</b><br>
            Power: {station.max_power_kW} kW<br>
            Price: {station.price_per_kWh}€/kWh<br>
            Truck Suitable: {station.truck_suitability}<br>
            Station ID: {station.id}
        </div>
        """
        
        # Add marker
        folium.CircleMarker(
            location=[station.latitude, station.longitude],
            radius=5,
            color='blue',
            fill=True,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Station {station.id}: {station.operator_name}"
        ).add_to(m)
    
    # Add edges (connections) with weight information
    for edge in graph.edges(data=True):
        station1 = graph.nodes[edge[0]]['station']
        station2 = graph.nodes[edge[1]]['station']
        edge_data = edge[2]  # This contains all edge attributes
        
        # Get edge attributes
        driver_cost = edge_data.get('driver_cost', 0)
        distance = edge_data.get('driving_distance', 0)
        time_hours = edge_data.get('travel_time_hours', 0)
        
        # Create points for the line
        points = [
            [station1.latitude, station1.longitude],
            [station2.latitude, station2.longitude]
        ]
        
        # Create detailed edge tooltip
        tooltip_text = f"""
        <div style="width: 200px;">
            <b>Route Information:</b><br>
            Distance: {distance:.1f} km<br>
            Travel Time: {time_hours:.1f} hours<br>
            Driver Cost: €{driver_cost:.2f}<br>
            From: {station1.operator_name}<br>
            To: {station2.operator_name}
        </div>
        """
        
        # Calculate edge color based on cost (red = expensive, green = cheap)
        # First collect all costs to determine range
        all_costs = [e[2].get('driver_cost', 0) for e in graph.edges(data=True)]
        max_cost = max(all_costs)
        min_cost = min(all_costs)
        
        # Normalize cost between 0 and 1
        if max_cost != min_cost:
            normalized_cost = (driver_cost - min_cost) / (max_cost - min_cost)
        else:
            normalized_cost = 0
            
        # Create color gradient from green (low cost) to red (high cost)
        color = f'#{int(255 * normalized_cost):02x}{int(255 * (1-normalized_cost)):02x}00'
        
        # Draw the edge with cost-based color and tooltip
        edge_line = folium.PolyLine(
            points,
            weight=2,
            color=color,
            opacity=0.8,
            tooltip=tooltip_text
        )
        edge_line.add_to(m)
        
        # Add cost label at midpoint
        mid_lat = (station1.latitude + station2.latitude) / 2
        mid_lon = (station1.longitude + station2.longitude) / 2
        
        # Add a small circle at midpoint with cost information
        folium.CircleMarker(
            location=[mid_lat, mid_lon],
            radius=2,
            color=color,
            fill=True,
            popup=f"€{driver_cost:.2f}",
            tooltip=f"Cost: €{driver_cost:.2f}"
        ).add_to(m)
    
    # Add legend
    legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; 
                    right: 50px; 
                    width: 150px; 
                    height: 90px; 
                    background-color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid gray;
                    z-index: 9999;">
            <h4>Cost Legend</h4>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #00ff00; margin-right: 5px;"></div>
                <span>Low Cost (€{min_cost:.2f})</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; background-color: #ff0000; margin-right: 5px;"></div>
                <span>High Cost (€{max_cost:.2f})</span>
            </div>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add graph statistics
    stats_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    width: 250px; 
                    background-color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid gray;
                    z-index: 9999;">
            <h4>Network Statistics</h4>
            Stations: {graph.number_of_nodes()}<br>
            Routes: {graph.number_of_edges()}<br>
            Avg Cost: €{sum(all_costs)/len(all_costs):.2f}<br>
            Min Cost: €{min_cost:.2f}<br>
            Max Cost: €{max_cost:.2f}
        </div>
    '''
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Save the map
    m.save(output_file)

def visualize_shortest_route_map(graph: nx.Graph, path: List[int], output_file: str = "shortest_route_map.html"):
    """
    Create an interactive map visualization of the shortest route between charging stations
    using actual route coordinates from TomTom API cache
    
    Args:
        graph: NetworkX graph with charging stations
        path: List of station IDs representing the shortest path
        output_file: Path to save the HTML map file
    """
    # Load cached route data
    with open('graph_computation.json', 'r') as f:
        distance_cache = json.load(f)
    
    # Create map centered on the first station
    start_station = graph.nodes[path[0]]['station']
    m = folium.Map(location=[start_station.latitude, start_station.longitude], zoom_start=6)
    
    # Track total metrics
    total_distance = 0
    total_time = 0
    total_cost = 0
    
    # Create a feature group for the route
    route_group = folium.FeatureGroup(name="Complete Route")
    
    # Add stations and route segments
    for i in range(len(path)-1):
        current_id = path[i]
        next_id = path[i+1]
        
        current_station = graph.nodes[current_id]['station']
        next_station = graph.nodes[next_id]['station']
        
        # Get edge data
        edge_data = graph.edges[current_id, next_id]
        
        # Get cached route data
        cache_key = f"{current_id}_{next_id}"
        reverse_key = f"{next_id}_{current_id}"
        cache_entry = distance_cache.get(cache_key) or distance_cache.get(reverse_key)
        
        if cache_entry:
            # Extract route points
            route_points = cache_entry['api_response']['routes'][0]['legs'][0]['points']
            route_coords = [[point['latitude'], point['longitude']] for point in route_points]
            
            # Get segment metrics
            distance = edge_data['driving_distance']
            time_hours = edge_data['travel_time_hours']
            cost = edge_data['driver_cost']
            
            # Update totals
            total_distance += distance
            total_time += time_hours
            total_cost += cost
            
            # Create segment tooltip
            segment_tooltip = f"""
            <div style="width: 200px;">
                <b>Route Segment {i+1}</b><br>
                From: {current_station.operator_name}<br>
                To: {next_station.operator_name}<br>
                Distance: {distance:.1f} km<br>
                Time: {time_hours:.1f} hours<br>
                Cost: €{cost:.2f}
            </div>
            """
            
            # Draw actual route line
            folium.PolyLine(
                route_coords,
                weight=4,
                color='blue',
                opacity=0.8,
                tooltip=segment_tooltip
            ).add_to(route_group)
            
            # Add direction arrow at midpoint
            mid_idx = len(route_coords) // 2
            if mid_idx > 0:
                folium.RegularPolygonMarker(
                    location=route_coords[mid_idx],
                    number_of_sides=3,
                    radius=6,
                    rotation=45,
                    color='blue',
                    fill=True,
                    popup=f"Segment {i+1}"
                ).add_to(route_group)
        
        # Add station markers
        station_popup = f"""
        <div style="width: 200px;">
            <b>{current_station.operator_name}</b><br>
            Power: {current_station.max_power_kW} kW<br>
            Price: {current_station.price_per_kWh}€/kWh<br>
            Coordinates: ({current_station.latitude:.4f}, {current_station.longitude:.4f})<br>
            Stop #{i+1} of {len(path)}
        </div>
        """
        
        # Different colors for start, intermediate and end stations
        if i == 0:  # Start station
            color = 'green'
            radius = 8
        elif i == len(path)-2:  # Station before last
            color = 'orange'
            radius = 8
        else:  # Intermediate stations
            color = 'blue'
            radius = 6
            
        folium.CircleMarker(
            location=[current_station.latitude, current_station.longitude],
            radius=radius,
            color=color,
            fill=True,
            popup=folium.Popup(station_popup, max_width=300),
            tooltip=f"Stop #{i+1}: {current_station.operator_name}"
        ).add_to(route_group)
    
    # Add final station
    final_station = graph.nodes[path[-1]]['station']
    final_popup = f"""
    <div style="width: 200px;">
        <b>{final_station.operator_name}</b><br>
        Power: {final_station.max_power_kW} kW<br>
        Price: {final_station.price_per_kWh}€/kWh<br>
        Coordinates: ({final_station.latitude:.4f}, {final_station.longitude:.4f})<br>
        Final Stop
    </div>
    """
    
    folium.CircleMarker(
        location=[final_station.latitude, final_station.longitude],
        radius=8,
        color='red',
        fill=True,
        popup=folium.Popup(final_popup, max_width=300),
        tooltip=f"Final Stop: {final_station.operator_name}"
    ).add_to(route_group)
    
    route_group.add_to(m)
    
    # Add route summary
    summary_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    width: 250px; 
                    background-color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid gray;
                    z-index: 9999;">
            <h4>Route Summary</h4>
            <b>Stops:</b> {len(path)}<br>
            <b>Total Distance:</b> {total_distance:.1f} km<br>
            <b>Total Time:</b> {total_time:.1f} hours<br>
            <b>Total Cost:</b> €{total_cost:.2f}<br>
            <b>Start:</b> {start_station.operator_name}<br>
            <b>End:</b> {final_station.operator_name}
        </div>
    '''
    m.get_root().html.add_child(folium.Element(summary_html))
    
    # Add legend
    legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; 
                    right: 50px; 
                    width: 150px; 
                    background-color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid gray;
                    z-index: 9999;">
            <h4>Legend</h4>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: green; margin-right: 5px;"></div>
                <span>Start Station</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: blue; margin-right: 5px;"></div>
                <span>Intermediate</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: red; margin-right: 5px;"></div>
                <span>End Station</span>
            </div>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save the map
    m.save(output_file)

# Example usage:
if __name__ == "__main__":
    # Load charging stations
    stations = load_charging_stations("data/public_charge_points.csv")

    print(stations[0])
    
    # Build graph
    graph = build_charging_station_graph(stations[:25])
    updated_graph = update_graph_weights(graph)

    print(updated_graph)

    
    # Print some basic graph statistics
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    
    # Example: Find shortest path between two stations
    start_station = stations[0]
    end_station = stations[20]
    try:
        path = nx.shortest_path(graph, start_station.id, end_station.id, weight='weight')
        print(f"\nMost cost-effective path from {start_station.operator_name} to {end_station.operator_name}:")
        
        # Print path details
        for i in range(len(path)-1):
            current_id = path[i]
            next_id = path[i+1]
            edge_data = graph.edges[current_id, next_id]
            current_station = graph.nodes[current_id]['station']
            print(f"  {current_station.operator_name} -> {edge_data['driving_distance']:.1f} km, "
                  f"{edge_data['travel_time_hours']:.1f} hours, €{edge_data['driver_cost']:.2f}")
        
        final_station = graph.nodes[path[-1]]['station']
        print(f"  {final_station.operator_name} (destination)")
        
        # Visualize the route
        visualize_shortest_route_map(graph, path)
        
    except nx.NetworkXNoPath:
        print("No path exists between these stations")
        