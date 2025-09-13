from typing import List, Tuple, Dict, Optional
import math
import tomtom
from models import (
    TruckModel, ChargingStation, RouteSegment, DriverBreak, 
    ChargingStop, RouteResult, RouteRequest
)
from charging_stations import load_charging_stations, find_nearest_charging_stations
from trucks import load_truck_specs, calculate_energy_consumption, calculate_charging_time
from compliance import calculate_required_breaks, is_route_compliant
from cost_calculator import calculate_total_route_cost


def find_optimal_route(request: RouteRequest) -> RouteResult:
    """
    Find the optimal route for an e-truck between start and end points
    
    Args:
        request: RouteRequest object containing start, end, truck model, etc.
        
    Returns:
        RouteResult object with the optimal route
    """
    # Load truck specifications
    trucks = load_truck_specs("data/truck_specs.csv")
    truck = trucks.get(request.truck_model)
    
    if not truck:
        raise ValueError(f"Unknown truck model: {request.truck_model}")
    
    # Set initial battery level (default to full if not specified)
    initial_battery = request.initial_battery_level or truck.battery_capacity
    
    # Load charging stations
    charging_stations = load_charging_stations("data/public_charge_points.csv")
    
    # Get initial route from TomTom API
    route_data = tomtom.get_route(request.start_point, request.end_point, vehicle_type="truck")
    
    if not route_data:
        return RouteResult(
            total_distance=0,
            total_duration=0,
            driving_duration=0,
            total_energy_consumption=0,
            total_cost=0,
            route_segments=[],
            driver_breaks=[],
            charging_stops=[],
            feasible=False
        )
    
    # Extract route information
    total_distance_m = route_data["distance"]
    total_distance_km = total_distance_m / 1000
    total_duration_s = route_data["duration"]
    
    # Calculate energy consumption
    total_energy_consumption = calculate_energy_consumption(total_distance_km, truck)
    
    # Check if route is feasible with a single charge
    if total_energy_consumption <= initial_battery:
        # Route is feasible without charging stops
        route_segment = RouteSegment(
            start_point=request.start_point,
            end_point=request.end_point,
            distance=total_distance_m,
            duration=total_duration_s,
            energy_consumption=total_energy_consumption
        )
        
        # Calculate driver breaks
        route_points = [(p["latitude"], p["longitude"]) for p in route_data["coordinates"]]
        segment_durations = [total_duration_s]  # Simplified - in reality would be per segment
        driver_breaks = calculate_required_breaks(total_duration_s, route_points, segment_durations)
        
        # Calculate total duration including breaks
        break_duration = sum(b.duration for b in driver_breaks)
        total_duration_with_breaks = total_duration_s + break_duration
        
        # Create result
        result = RouteResult(
            total_distance=total_distance_m,
            total_duration=total_duration_with_breaks,
            driving_duration=total_duration_s,
            total_energy_consumption=total_energy_consumption,
            total_cost=0,  # No charging cost
            route_segments=[route_segment],
            driver_breaks=driver_breaks,
            charging_stops=[],
            feasible=True
        )
        
        return result
    
    # Route requires charging stops
    # For simplicity, we'll implement a greedy algorithm that adds charging stops
    # whenever the battery level gets below a threshold
    
    # Extract route points
    route_points = [(p["latitude"], p["longitude"]) for p in route_data["coordinates"]]
    
    # Initialize variables
    current_battery = initial_battery
    current_position = request.start_point
    remaining_route = route_points
    route_segments = []
    charging_stops = []
    accumulated_driving = 0
    total_driving_time = 0
    
    while remaining_route:
        # Calculate how far we can go with current battery
        max_range_km = current_battery / truck.consumption
        
        # Find the furthest point we can reach
        reachable_distance = 0
        next_point_index = 0
        
        for i in range(1, len(remaining_route)):
            segment_distance = calculate_distance(
                remaining_route[i-1], 
                remaining_route[i]
            )
            
            if reachable_distance + segment_distance > max_range_km:
                next_point_index = i - 1
                break
            
            reachable_distance += segment_distance
            next_point_index = i
        
        # If we can reach the destination
        if next_point_index == len(remaining_route) - 1:
            # Create final segment
            segment = RouteSegment(
                start_point=current_position,
                end_point=request.end_point,
                distance=reachable_distance * 1000,  # Convert to meters
                duration=total_duration_s * (reachable_distance / total_distance_km),  # Estimate duration
                energy_consumption=reachable_distance * truck.consumption
            )
            
            route_segments.append(segment)
            current_battery -= segment.energy_consumption
            total_driving_time += segment.duration
            break
        
        # We need to find a charging station
        next_position = remaining_route[next_point_index]
        
        # Find nearby charging stations
        nearby_stations = find_nearest_charging_stations(
            next_position,
            charging_stations,
            max_distance=20.0,  # Look for stations within 20km
            truck_suitable_only=True
        )
        
        if not nearby_stations:
            # No charging stations found, route is not feasible
            return RouteResult(
                total_distance=total_distance_m,
                total_duration=0,
                driving_duration=0,
                total_energy_consumption=total_energy_consumption,
                total_cost=0,
                route_segments=[],
                driver_breaks=[],
                charging_stops=[],
                feasible=False
            )
        
        # Choose the charging station with lowest price
        best_station = min(nearby_stations, key=lambda s: s.price_per_kWh)
        
        # Create route segment to charging station
        station_position = (best_station.latitude, best_station.longitude)
        
        # Get route to charging station
        detour_route = tomtom.get_route(current_position, station_position, vehicle_type="truck")
        
        if not detour_route:
            # Can't route to charging station
            continue
        
        detour_distance_m = detour_route["distance"]
        detour_distance_km = detour_distance_m / 1000
        detour_duration_s = detour_route["duration"]
        detour_energy = calculate_energy_consumption(detour_distance_km, truck)
        
        # Check if we can reach the charging station
        if detour_energy > current_battery:
            # Can't reach this charging station
            continue
        
        # Create segment to charging station
        segment = RouteSegment(
            start_point=current_position,
            end_point=station_position,
            distance=detour_distance_m,
            duration=detour_duration_s,
            energy_consumption=detour_energy
        )
        
        route_segments.append(segment)
        current_battery -= detour_energy
        accumulated_driving += detour_duration_s
        total_driving_time += detour_duration_s
        
        # Charge to 80% of battery capacity (common practice for fast charging)
        target_battery_level = 0.8 * truck.battery_capacity
        energy_to_charge = target_battery_level - current_battery
        
        # Calculate charging time
        charging_time = calculate_charging_time(
            current_battery,
            target_battery_level,
            truck,
            best_station.max_power_kW
        )
        
        # Calculate charging cost
        charging_cost = energy_to_charge * best_station.price_per_kWh
        
        # Create charging stop
        charging_stop = ChargingStop(
            charging_station=best_station,
            arrival_battery_level=current_battery,
            departure_battery_level=target_battery_level,
            charging_time=charging_time,
            charging_cost=charging_cost
        )
        
        charging_stops.append(charging_stop)
        current_battery = target_battery_level
        
        # Update current position and remaining route
        current_position = station_position
        
        # Recalculate route from charging station to destination
        new_route = tomtom.get_route(current_position, request.end_point, vehicle_type="truck")
        if not new_route:
            return RouteResult(
                total_distance=total_distance_m,
                total_duration=0,
                driving_duration=0,
                total_energy_consumption=total_energy_consumption,
                total_cost=0,
                route_segments=[],
                driver_breaks=[],
                charging_stops=[],
                feasible=False
            )
        
        remaining_route = [(p["latitude"], p["longitude"]) for p in new_route["coordinates"]]
    
    # Calculate driver breaks
    segment_durations = [segment.duration for segment in route_segments]
    all_points = [segment.start_point for segment in route_segments]
    all_points.append(request.end_point)
    
    driver_breaks = calculate_required_breaks(total_driving_time, all_points, segment_durations)
    
    # Calculate total duration including breaks and charging
    break_duration = sum(b.duration for b in driver_breaks)
    charging_duration = sum(stop.charging_time for stop in charging_stops)
    total_duration = total_driving_time + break_duration + charging_duration
    
    # Calculate total distance
    total_distance = sum(segment.distance for segment in route_segments)
    
    # Calculate total energy consumption
    total_energy = sum(segment.energy_consumption for segment in route_segments)
    
    # Calculate total cost
    cost_result = calculate_total_route_cost(
        total_distance / 1000,  # Convert to km
        truck,
        charging_stops
    )
    
    # Create final result
    result = RouteResult(
        total_distance=total_distance,
        total_duration=total_duration,
        driving_duration=total_driving_time,
        total_energy_consumption=total_energy,
        total_cost=cost_result["total_charging_cost_EUR"],
        route_segments=route_segments,
        driver_breaks=driver_breaks,
        charging_stops=charging_stops,
        feasible=True
    )
    
    return result


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