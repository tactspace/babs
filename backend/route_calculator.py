import json
from typing import List, Dict, Tuple, Any
from tomtom import get_route
from models import RouteSegment, RouteResult, DriverBreak, DriverBreakType, ChargingStop
from charging_stations import load_charging_stations, calculate_distance

# Constants for cost calculation
DRIVER_HOURLY_WAGE = 35  # euros per hour
CHARGING_RATE_PER_KWH = 0.6  # euros per kWh
AVERAGE_CONSUMPTION = 1.2  # kWh per km for electric trucks

# Driver regulation constants
MAX_CONTINUOUS_DRIVING_HOURS = 4.5  # hours
MAX_DAILY_DRIVING_HOURS = 9.0  # hours
MANDATORY_REST_HOURS = 11.0  # hours
SHORT_BREAK_MINUTES = 45  # minutes

def calculate_detailed_route(
    start_point: Tuple[float, float], 
    end_point: Tuple[float, float],
    truck_type: str = "electric"
) -> Dict[str, Any]:
    """
    Calculate a detailed route with cost breakdown
    
    Args:
        start_point: (latitude, longitude) of starting point
        end_point: (latitude, longitude) of ending point
        truck_type: Type of truck ("electric" or "diesel")
        
    Returns:
        Dictionary with route details and cost breakdown
    """
    # Load charging stations
    charging_stations = load_charging_stations("data/public_charge_points.csv")
    
    # Get route from TomTom API
    route_data = get_route(start_point, end_point)
    
    if not route_data:
        return {"error": "Failed to calculate route"}
    
    # Extract basic route information
    distance_meters = route_data["distance"]
    distance_km = distance_meters / 1000
    duration_seconds = route_data["duration"]
    duration_hours = duration_seconds / 3600
    
    # Extract coordinates for the route
    coordinates = []
    for point in route_data["coordinates"]:
        coordinates.append({
            "latitude": point["latitude"],
            "longitude": point["longitude"]
        })
    
    # Extract detailed path coordinates for finding nearby stations
    path_coordinates = []
    try:
        # Extract all points from all legs of the route
        for leg in route_data["full_response"]["routes"][0]["legs"]:
            for point in leg["points"]:
                path_coordinates.append((point["latitude"], point["longitude"]))
    except (KeyError, IndexError) as e:
        # Fall back to the simplified coordinates if detailed path extraction fails
        path_coordinates = [(start_point[0], start_point[1]), (end_point[0], end_point[1])]
    
    # Find nearby charging stations
    nearby_stations = find_nearby_charging_stations(path_coordinates, charging_stations)
    
    # Calculate driver cost based on duration
    driver_cost = DRIVER_HOURLY_WAGE * duration_hours
    
    # Calculate energy consumption and charging cost
    energy_consumption = distance_km * AVERAGE_CONSUMPTION
    charging_cost = energy_consumption * CHARGING_RATE_PER_KWH
    
    # Calculate total cost
    total_cost = driver_cost + charging_cost
    
    # Create route segments for visualization
    route_segments = []
    
    # Calculate driver breaks based on driving regulations
    driver_breaks = calculate_driver_breaks(path_coordinates, duration_hours)
    
    # Calculate charging stops
    charging_stops = calculate_charging_stops(path_coordinates, energy_consumption, nearby_stations)
    
    # For simplicity, we'll create one segment for the entire route
    route_segments.append({
        "start_point": [start_point[0], start_point[1]],
        "end_point": [end_point[0], end_point[1]],
        "distance": distance_meters,
        "duration": duration_seconds,
        "energy_consumption": energy_consumption
    })
    
    # Create nearby charging stations list for visualization
    nearby_charging_stations = []
    for station in nearby_stations[:10]:  # Limit to 10 stations for visualization
        nearby_charging_stations.append({
            "id": station.id,
            "name": station.operator_name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "price_per_kWh": station.price_per_kWh
        })
    
    # Create result object
    result = {
        "total_distance": distance_meters,
        "total_duration": calculate_total_duration(duration_seconds, driver_breaks, charging_stops),
        "driving_duration": duration_seconds,
        "total_energy_consumption": energy_consumption,
        "total_cost": total_cost,
        "cost_breakdown": {
            "driver_cost": driver_cost,
            "charging_cost": charging_cost
        },
        "route_segments": route_segments,
        "coordinates": coordinates,
        "feasible": True,
        "charging_stops": charging_stops,
        "nearby_charging_stations": nearby_charging_stations,
        "driver_breaks": driver_breaks
    }
    
    return result

def find_nearby_charging_stations(route_path, charging_stations, radius_km=50):
    """
    Find charging stations that are within a certain radius of the route path
    
    Args:
        route_path: List of (latitude, longitude) points along the route
        charging_stations: List of charging station objects
        radius_km: Radius in kilometers to consider a station "nearby"
        
    Returns:
        List of nearby charging stations
    """
    nearby_stations = []
    
    # Sample the route path (don't check every point to improve performance)
    sample_rate = max(1, len(route_path) // 10)  # Sample about 10 points along the route
    sampled_path = [route_path[i] for i in range(0, len(route_path), sample_rate)]
    
    # Add start and end points if they're not already included
    if route_path[0] not in sampled_path:
        sampled_path.insert(0, route_path[0])
    if route_path[-1] not in sampled_path:
        sampled_path.append(route_path[-1])
    
    # Check each charging station against sampled path points
    for station in charging_stations:
        station_pos = (station.latitude, station.longitude)
        
        # Check if station is within radius of any point on the sampled path
        for point in sampled_path:
            distance = calculate_distance(point, station_pos)
            if distance <= radius_km:
                nearby_stations.append(station)
                break  # No need to check other path points for this station
    
    return nearby_stations

def calculate_driver_breaks(route_path, duration_hours):
    """
    Calculate required driver breaks based on regulations:
    - 45 minute break after 4.5 hours of continuous driving
    - Maximum 9 hours of driving per day
    - 11 hour mandatory rest after 9 hours of driving
    
    Args:
        route_path: List of (latitude, longitude) points along the route
        duration_hours: Total driving duration in hours
        
    Returns:
        List of driver breaks
    """
    driver_breaks = []
    
    # No breaks needed if duration is less than MAX_CONTINUOUS_DRIVING_HOURS
    if duration_hours <= MAX_CONTINUOUS_DRIVING_HOURS:
        return driver_breaks
    
    # Calculate number of short breaks needed (45 minutes after every 4.5 hours)
    num_short_breaks = int(duration_hours / MAX_CONTINUOUS_DRIVING_HOURS)
    
    # Calculate if a long rest is needed (11 hours after 9 hours of driving)
    needs_long_rest = duration_hours > MAX_DAILY_DRIVING_HOURS
    
    # Sample points along the route for break locations
    sampled_points = []
    if len(route_path) > 1:
        step = len(route_path) // (num_short_breaks + (1 if needs_long_rest else 0) + 1)
        if step > 0:
            for i in range(step, len(route_path), step):
                if i < len(route_path):
                    sampled_points.append(route_path[i])
    
    # Add short breaks
    for i in range(num_short_breaks):
        if i < len(sampled_points):
            location = sampled_points[i]
            break_time = (i + 1) * MAX_CONTINUOUS_DRIVING_HOURS * 3600  # seconds from start
            driver_breaks.append({
                "break_type": DriverBreakType.SHORT_BREAK,
                "location": [location[0], location[1]],
                "start_time": break_time,
                "duration": SHORT_BREAK_MINUTES * 60  # convert to seconds
            })
    
    # Add long rest if needed
    if needs_long_rest and sampled_points:
        location = sampled_points[-1] if sampled_points else route_path[-1]
        break_time = MAX_DAILY_DRIVING_HOURS * 3600  # seconds from start
        driver_breaks.append({
            "break_type": DriverBreakType.LONG_REST,
            "location": [location[0], location[1]],
            "start_time": break_time,
            "duration": MANDATORY_REST_HOURS * 3600  # convert to seconds
        })
    
    return driver_breaks

def calculate_charging_stops(route_path, energy_consumption, nearby_stations):
    """
    Calculate charging stops along the route
    
    Args:
        route_path: List of (latitude, longitude) points along the route
        energy_consumption: Total energy consumption in kWh
        nearby_stations: List of nearby charging stations
        
    Returns:
        List of charging stops
    """
    charging_stops = []
    
    # If energy consumption is low or no nearby stations, no charging needed
    if energy_consumption < 200 or not nearby_stations:
        return charging_stops
    
    # Sort stations by price
    sorted_stations = sorted(nearby_stations, key=lambda s: s.price_per_kWh)
    
    # Select the cheapest station
    best_station = sorted_stations[0]
    
    # Calculate charging parameters
    arrival_battery_level = 50  # Assume 50 kWh remaining on arrival
    departure_battery_level = energy_consumption * 0.8  # Charge to 80% of total consumption
    charging_time = (departure_battery_level - arrival_battery_level) * 60 / 150  # Assume 150 kW charging rate
    charging_cost = (departure_battery_level - arrival_battery_level) * best_station.price_per_kWh
    
    # Add charging stop at approximately the middle of the route
    if len(route_path) > 2:
        mid_point = route_path[len(route_path) // 2]
        charging_stops.append({
            "charging_station": {
                "id": best_station.id,
                "name": best_station.operator_name,
                "latitude": best_station.latitude,
                "longitude": best_station.longitude,
                "price_per_kWh": best_station.price_per_kWh
            },
            "arrival_battery_level": arrival_battery_level,
            "departure_battery_level": departure_battery_level,
            "charging_time": charging_time,
            "charging_cost": charging_cost
        })
    
    return charging_stops

def calculate_total_duration(driving_duration, driver_breaks, charging_stops):
    """
    Calculate total trip duration including breaks and charging
    
    Args:
        driving_duration: Driving time in seconds
        driver_breaks: List of driver breaks
        charging_stops: List of charging stops
        
    Returns:
        Total duration in seconds
    """
    total_duration = driving_duration
    
    # Add break durations
    for brk in driver_breaks:
        total_duration += brk["duration"]
    
    # Add charging times
    for stop in charging_stops:
        total_duration += stop["charging_time"]
    
    return total_duration

def calculate_multi_route(routes: List[Dict]) -> Dict[str, Any]:
    """
    Calculate multiple routes with detailed cost information
    
    Args:
        routes: List of route dictionaries with start and end points
        
    Returns:
        Dictionary with all route results
    """
    results = []
    total_distance = 0
    total_duration = 0
    total_cost = 0
    
    for route in routes:
        start_point = (route["start_point"][0], route["start_point"][1])
        end_point = (route["end_point"][0], route["end_point"][1])
        truck_type = route.get("truck_type", "electric")
        
        route_result = calculate_detailed_route(start_point, end_point, truck_type)
        
        if "error" not in route_result:
            results.append(route_result)
            total_distance += route_result["total_distance"]
            total_duration += route_result["total_duration"]
            total_cost += route_result["total_cost"]
    
    return {
        "routes": results,
        "total_distance": total_distance,
        "total_duration": total_duration,
        "total_cost": total_cost
    }
