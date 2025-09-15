import json
import math
from typing import List, Dict, Tuple, Any
from models import ChargingStation, Driver
from charging_stations import load_charging_stations, calculate_distance
from tomtom import get_route
import folium
from folium.plugins import MarkerCluster, PolyLineOffset
import branca.colormap as cm
import numpy as np

# Constants - matching those in optimizer.py
AVERAGE_TRUCK_SPEED = 70  # km/h
INTERVAL_TIME = 45  # minutes
DRIVER_HOURLY_WAGE = 35  # euros per hour
ELECTRIC_COST_PER_KWH = 0.6  # euros per kWh
AVERAGE_CONSUMPTION = 1.2  # kWh per km

# Driver regulation constants
MAX_CONTINUOUS_DRIVING_HOURS = 4.5  # hours
MAX_DAILY_DRIVING_HOURS = 9.0  # hours
MANDATORY_REST_HOURS = 11.0  # hours
SHORT_BREAK_MINUTES = 45  # minutes

def calculate_base_routes(routes: List[Dict], charging_stations: List[ChargingStation]) -> Dict[str, Any]:
    """
    Calculate base routes where each driver drives a single route with required breaks
    
    Args:
        routes: List of route dictionaries with start and end coordinates
        charging_stations: List of charging stations
        
    Returns:
        Dictionary with route details, costs, and breaks
    """
    results = {
        "routes": [],
        "total_distance": 0,
        "total_duration": 0,
        "total_cost": 0,
        "total_energy": 0,
        "breaks": []
    }
    
    for route_idx, route in enumerate(routes):
        start_coord = (route["start_coord"]["latitude"], route["start_coord"]["longitude"])
        end_coord = (route["end_coord"]["latitude"], route["end_coord"]["longitude"])
        
        # Get route from TomTom API
        route_data = get_route(start_coord, end_coord)
        if not route_data:
            print(f"Could not get route for {start_coord} to {end_coord}")
            continue
        
        # Extract route details
        distance_meters = route_data["distance"]
        distance_km = distance_meters / 1000
        duration_seconds = route_data["duration"]
        duration_hours = duration_seconds / 3600
        
        # Extract coordinates for visualization
        coordinates = []
        for point in route_data["coordinates"]:
            coordinates.append([point["latitude"], point["longitude"]])
        
        # Calculate energy consumption
        energy_consumption = distance_km * AVERAGE_CONSUMPTION
        
        # Calculate driver cost
        driver_cost = DRIVER_HOURLY_WAGE * duration_hours
        if driver_cost <= 0:
            print(f"Warning: Invalid driver cost calculation: {DRIVER_HOURLY_WAGE} * {duration_hours} = {driver_cost}")
            # Ensure we have a valid value
            driver_cost = DRIVER_HOURLY_WAGE * max(duration_hours, 0.1)  # At least 6 minutes of work
        
        # Calculate charging cost - assume one charging stop if distance > 300km
        charging_cost = 0
        charging_stops = []
        
        if distance_km > 300:
            # Find charging stations near the midpoint
            mid_idx = len(coordinates) // 2
            mid_point = coordinates[mid_idx]
            
            # Find nearest charging station to midpoint
            nearest_station = None
            min_distance = float('inf')
            
            for station in charging_stations:
                if station.truck_suitability == "yes":
                    station_pos = (station.latitude, station.longitude)
                    dist = calculate_distance(mid_point, station_pos)
                    if dist < min_distance:
                        min_distance = dist
                        nearest_station = station
            
            if nearest_station:
                # Calculate charging details
                charge_amount = energy_consumption * 0.8  # 80% of total consumption
                
                # Check if price_per_kWh exists and is not None
                price_per_kwh = getattr(nearest_station, 'price_per_kWh', None)
                if price_per_kwh is None or price_per_kwh == 0:
                    price_per_kwh = ELECTRIC_COST_PER_KWH  # Use default value
                    
                charging_cost = charge_amount * price_per_kwh
                charging_time = charge_amount / 150 * 60  # minutes (assuming 150 kW charging)
                
                charging_stops.append({
                    "station_id": nearest_station.id,
                    "station_name": nearest_station.operator_name,
                    "location": (nearest_station.latitude, nearest_station.longitude),
                    "charge_amount": charge_amount,
                    "charging_cost": charging_cost,
                    "charging_time": charging_time
                })
        
        # Calculate driver breaks
        breaks = []
        if duration_hours > MAX_CONTINUOUS_DRIVING_HOURS:
            # Calculate number of short breaks needed
            num_short_breaks = math.floor(duration_hours / MAX_CONTINUOUS_DRIVING_HOURS)
            
            # Add short breaks at regular intervals
            for i in range(num_short_breaks):
                break_time = (i + 1) * MAX_CONTINUOUS_DRIVING_HOURS * 3600  # seconds from start
                break_idx = int((i + 1) * len(coordinates) / (num_short_breaks + 1))
                break_location = coordinates[break_idx]
                
                breaks.append({
                    "break_type": "short_break",
                    "location": break_location,
                    "start_time": break_time,
                    "duration": SHORT_BREAK_MINUTES * 60  # seconds
                })
            
            # Add long rest if needed
            if duration_hours > MAX_DAILY_DRIVING_HOURS:
                long_rest_time = MAX_DAILY_DRIVING_HOURS * 3600  # seconds from start
                rest_idx = int(MAX_DAILY_DRIVING_HOURS / duration_hours * len(coordinates))
                rest_location = coordinates[rest_idx]
                
                breaks.append({
                    "break_type": "long_rest",
                    "location": rest_location,
                    "start_time": long_rest_time,
                    "duration": MANDATORY_REST_HOURS * 3600  # seconds
                })
        
        # Calculate total break time
        break_time = sum(brk["duration"] for brk in breaks)
        
        # Calculate total charging time
        charging_time = sum(stop["charging_time"] * 60 for stop in charging_stops)  # convert to seconds
        
        # Calculate total cost
        total_cost = driver_cost + charging_cost
        
        # Calculate total duration including breaks and charging
        total_duration = duration_seconds + break_time + charging_time
        
        # Add route to results
        route_result = {
            "route_idx": route_idx,
            "start_coord": start_coord,
            "end_coord": end_coord,
            "distance_km": distance_km,
            "duration_hours": duration_hours,
            "energy_consumption": energy_consumption,
            "driver_cost": driver_cost,
            "charging_cost": charging_cost,
            "total_cost": total_cost,
            "total_duration": total_duration,
            "breaks": breaks,
            "charging_stops": charging_stops,
            "coordinates": coordinates
        }
        
        results["routes"].append(route_result)
        results["total_distance"] += distance_km
        results["total_duration"] += total_duration
        results["total_cost"] += total_cost
        results["total_energy"] += energy_consumption
        results["breaks"].extend(breaks)
    
    return results

def visualize_base_routes(results: Dict[str, Any], output_file: str = "visualization_base.html"):
    """
    Visualize base routes with breaks and charging stops
    
    Args:
        results: Results dictionary from calculate_base_routes
        output_file: Output HTML file path
    """
    # Create map centered on Europe
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=5)
    
    # Add routes
    route_colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 'lightred', 'darkblue']
    
    # Create a feature group for each route
    for i, route in enumerate(results["routes"]):
        # Create a feature group for this route
        route_group = folium.FeatureGroup(name=f"Route {i+1}")
        
        # Add route polyline with detailed coordinates
        color = route_colors[i % len(route_colors)]
        
        # Create a polyline with the exact coordinates from TomTom API
        folium.PolyLine(
            route["coordinates"],
            color=color,
            weight=4,
            opacity=0.8,
            tooltip=f"Route {i+1}: {route['distance_km']:.1f} km"
        ).add_to(route_group)
        
        # Add start marker
        folium.Marker(
            route["start_coord"],
            icon=folium.Icon(color='green', icon='play', prefix='fa'),
            tooltip=f"Start Route {i+1}"
        ).add_to(route_group)
        
        # Add end marker
        folium.Marker(
            route["end_coord"],
            icon=folium.Icon(color='red', icon='stop', prefix='fa'),
            tooltip=f"End Route {i+1}"
        ).add_to(route_group)
        
        # Add break markers
        for brk in route["breaks"]:
            icon_color = 'orange' if brk["break_type"] == "short_break" else 'cadetblue'
            icon_name = 'coffee' if brk["break_type"] == "short_break" else 'bed'
            
            folium.Marker(
                brk["location"],
                icon=folium.Icon(color=icon_color, icon=icon_name, prefix='fa'),
                tooltip=f"{brk['break_type'].replace('_', ' ')} - {brk['duration']/60:.0f} min"
            ).add_to(route_group)
        
        # Add charging stop markers
        for stop in route["charging_stops"]:
            folium.Marker(
                stop["location"],
                icon=folium.Icon(color='blue', icon='bolt', prefix='fa'),
                tooltip=f"Charging: {stop['charge_amount']:.1f} kWh, €{stop['charging_cost']:.2f}"
            ).add_to(route_group)
        
        # Add route-specific information as a popup
        route_info_html = f"""
        <div style="min-width: 200px;">
            <h4>Route {i+1} Details</h4>
            <table style="width:100%; border-collapse: collapse;">
                <tr><td style="padding:3px;"><b>Distance:</b></td><td style="text-align:right;">{route['distance_km']:.1f} km</td></tr>
                <tr><td style="padding:3px;"><b>Duration:</b></td><td style="text-align:right;">{route['total_duration']/3600:.1f} hours</td></tr>
                <tr><td style="padding:3px;"><b>Driver Cost:</b></td><td style="text-align:right;">€{route['driver_cost']:.2f}</td></tr>
                <tr><td style="padding:3px;"><b>Charging Cost:</b></td><td style="text-align:right;">€{route['charging_cost']:.2f}</td></tr>
                <tr><td style="padding:3px;"><b>Total Cost:</b></td><td style="text-align:right;">€{route['total_cost']:.2f}</td></tr>
                <tr><td style="padding:3px;"><b>Energy:</b></td><td style="text-align:right;">{route['energy_consumption']:.1f} kWh</td></tr>
                <tr><td style="padding:3px;"><b>Breaks:</b></td><td style="text-align:right;">{len(route['breaks'])}</td></tr>
                <tr><td style="padding:3px;"><b>Charging Stops:</b></td><td style="text-align:right;">{len(route['charging_stops'])}</td></tr>
            </table>
        </div>
        """
        
        # Add the route info as a popup on the route line
        mid_point_idx = len(route["coordinates"]) // 2
        mid_point = route["coordinates"][mid_point_idx]
        
        folium.Marker(
            mid_point,
            popup=folium.Popup(route_info_html, max_width=300),
            icon=folium.DivIcon(
                icon_size=(150, 36),
                icon_anchor=(75, 18),
                html=f'<div style="background-color:{color}; color:white; padding:3px 6px; border-radius:3px; font-weight:bold;">Route {i+1}</div>'
            )
        ).add_to(route_group)
        
        # Add the feature group to the map
        route_group.add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 1px solid grey; border-radius: 5px;">
        <p><i class="fa fa-play" style="color: green;"></i> Start</p>
        <p><i class="fa fa-stop" style="color: red;"></i> End</p>
        <p><i class="fa fa-coffee" style="color: orange;"></i> Short Break (45 min)</p>
        <p><i class="fa fa-bed" style="color: cadetblue;"></i> Long Rest (11 hours)</p>
        <p><i class="fa fa-bolt" style="color: blue;"></i> Charging Stop</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add detailed summary information
    summary_html = f"""
    <div style="position: fixed; top: 50px; right: 50px; z-index: 1000; background-color: white; padding: 10px; border: 1px solid grey; border-radius: 5px; max-width: 300px;">
        <h3>Base Route Summary</h3>
        <table style="width:100%; border-collapse: collapse;">
            <tr><td style="padding:3px;"><b>Total Distance:</b></td><td style="text-align:right;">{results["total_distance"]:.1f} km</td></tr>
            <tr><td style="padding:3px;"><b>Total Duration:</b></td><td style="text-align:right;">{results["total_duration"]/3600:.1f} hours</td></tr>
            <tr><td style="padding:3px;"><b>Total Cost:</b></td><td style="text-align:right;">€{results["total_cost"]:.2f}</td></tr>
            <tr><td style="padding:3px;"><b>Total Energy:</b></td><td style="text-align:right;">{results["total_energy"]:.1f} kWh</td></tr>
            <tr><td style="padding:3px;"><b>Number of Breaks:</b></td><td style="text-align:right;">{len(results["breaks"])}</td></tr>
        </table>
        
        <h4>Individual Route Costs</h4>
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <th style="text-align:left; padding:3px;">Route</th>
                <th style="text-align:right; padding:3px;">Cost</th>
                <th style="text-align:right; padding:3px;">Time (h)</th>
            </tr>
            {
                ''.join([
                    f'<tr><td style="padding:3px;">Route {i+1}</td><td style="text-align:right;">€{route["total_cost"]:.2f}</td><td style="text-align:right;">{route["total_duration"]/3600:.1f}</td></tr>'
                    for i, route in enumerate(results["routes"])
                ])
            }
        </table>
    </div>
    """
    m.get_root().html.add_child(folium.Element(summary_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save the map
    m.save(output_file)
    print(f"Visualization saved to {output_file}")
    
    # Also create a comparison visualization if report.json exists
    try:
        with open("report.json", "r") as f:
            optimized_results = json.load(f)
        
        create_comparison_visualization(results, optimized_results, "comparison_visualization.html")
    except:
        print("Could not create comparison visualization (report.json not found)")

def create_comparison_visualization(base_results: Dict[str, Any], optimized_results: Dict[str, Any], output_file: str):
    """
    Create a visualization comparing base routes with optimized routes
    
    Args:
        base_results: Results from calculate_base_routes
        optimized_results: Results from optimize_routes
        output_file: Output HTML file path
    """
    # Create map centered on Europe
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=5)
    
    # Add base routes
    base_group = folium.FeatureGroup(name="Base Routes")
    for i, route in enumerate(base_results["routes"]):
        color = 'blue'
        folium.PolyLine(
            route["coordinates"],
            color=color,
            weight=4,
            opacity=0.7,
            tooltip=f"Base Route {i+1}: {route['distance_km']:.1f} km"
        ).add_to(base_group)
    base_group.add_to(m)
    
    # Add optimized routes
    opt_group = folium.FeatureGroup(name="Optimized Routes")
    for i, route in enumerate(optimized_results["routes"]):
        color = 'red'
        
        # Extract coordinates from iterations
        coords = []
        for iteration in route.get("iterations", []):
            start_pos = iteration.get("start_position", None)
            end_pos = iteration.get("end_position", None)
            if start_pos and end_pos:
                coords.append([start_pos[0], start_pos[1]])
                coords.append([end_pos[0], end_pos[1]])
        
        if coords:
            folium.PolyLine(
                coords,
                color=color,
                weight=4,
                opacity=0.7,
                tooltip=f"Optimized Route {i+1}"
            ).add_to(opt_group)
    opt_group.add_to(m)
    
    # Add truck swaps
    swap_group = folium.FeatureGroup(name="Truck Swaps")
    for swap in optimized_results.get("truck_swaps", []):
        location = swap.get("station_location", None)
        if location:
            folium.Marker(
                location,
                icon=folium.Icon(color='green', icon='exchange', prefix='fa'),
                tooltip=f"Truck Swap: Driver {swap.get('driver1_id')} ↔ Driver {swap.get('driver2_id')}"
            ).add_to(swap_group)
    swap_group.add_to(m)
    
    # Add comparison information
    base_total_cost = base_results["total_cost"]
    base_total_duration = base_results["total_duration"]
    base_total_energy = base_results["total_energy"]
    
    opt_total_cost = sum(
        sum(iter.get("sum_cost", 0) for iter in route.get("iterations", []))
        for route in optimized_results.get("routes", [])
    )
    opt_total_duration = sum(
        sum(iter.get("time_elapsed_minutes", 0) * 60 for iter in route.get("iterations", []))
        for route in optimized_results.get("routes", [])
    )
    opt_total_energy = base_total_energy  # Assume same energy consumption for simplicity
    
    cost_savings = base_total_cost - opt_total_cost
    cost_savings_percent = (cost_savings / base_total_cost) * 100 if base_total_cost > 0 else 0
    
    time_savings = base_total_duration - opt_total_duration
    time_savings_percent = (time_savings / base_total_duration) * 100 if base_total_duration > 0 else 0
    
    comparison_html = f"""
    <div style="position: fixed; top: 50px; right: 50px; z-index: 1000; background-color: white; padding: 10px; border: 1px solid grey; border-radius: 5px; max-width: 350px;">
        <h3>Route Comparison</h3>
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <th style="text-align:left; padding:3px;"></th>
                <th style="text-align:right; padding:3px;">Base</th>
                <th style="text-align:right; padding:3px;">Optimized</th>
                <th style="text-align:right; padding:3px;">Savings</th>
            </tr>
            <tr>
                <td style="padding:3px;"><b>Total Cost</b></td>
                <td style="text-align:right;">€{base_total_cost:.2f}</td>
                <td style="text-align:right;">€{opt_total_cost:.2f}</td>
                <td style="text-align:right; color:green;">€{cost_savings:.2f} ({cost_savings_percent:.1f}%)</td>
            </tr>
            <tr>
                <td style="padding:3px;"><b>Total Time</b></td>
                <td style="text-align:right;">{base_total_duration/3600:.1f}h</td>
                <td style="text-align:right;">{opt_total_duration/3600:.1f}h</td>
                <td style="text-align:right; color:green;">{time_savings/3600:.1f}h ({time_savings_percent:.1f}%)</td>
            </tr>
        </table>
        
        <p><b>Key Findings:</b></p>
        <ul>
            <li>Truck swaps save {time_savings/3600:.1f} hours ({time_savings_percent:.1f}%)</li>
            <li>Cost reduction of €{cost_savings:.2f} ({cost_savings_percent:.1f}%)</li>
            <li>Optimized routes use {len(optimized_results.get("truck_swaps", []))} driver swaps</li>
        </ul>
    </div>
    """
    m.get_root().html.add_child(folium.Element(comparison_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save the map
    m.save(output_file)
    print(f"Comparison visualization saved to {output_file}")

# Example usage
if __name__ == "__main__":
    # Load charging stations
    stations = load_charging_stations("data/public_charge_points.csv")
    
    # Define routes
    routes = [
        {
            "start_coord": {"latitude": stations[11].latitude, "longitude": stations[11].longitude},  
            "end_coord": {"latitude": stations[0].latitude, "longitude": stations[0].longitude}     
        },
        {
            "start_coord": {"latitude": stations[10].latitude, "longitude": stations[10].longitude},  
            "end_coord": {"latitude": stations[18].latitude, "longitude": stations[18].longitude}     
        },
        {
            "start_coord": {"latitude": stations[21].latitude, "longitude": stations[21].longitude},  
            "end_coord": {"latitude": stations[3].latitude, "longitude": stations[3].longitude}     
        },
        {
            "start_coord": {"latitude": stations[16].latitude, "longitude": stations[16].longitude},  
            "end_coord": {"latitude": stations[6].latitude, "longitude": stations[6].longitude}     
        },
    ]
    
    # Calculate base routes
    results = calculate_base_routes(routes, stations)
    
    # Save results to JSON
    with open("base_routes.json", "w") as f:
        json.dump(results, f, indent=2, default=lambda x: str(x) if isinstance(x, tuple) else x)
    
    # Visualize routes
    visualize_base_routes(results, "visualization_base.html")
    print("Base routes calculated and visualized in visualization_base.html")
