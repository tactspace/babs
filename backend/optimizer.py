import json
import networkx as nx
from typing import List, Dict, Tuple, Any, Optional
import math
from models import ChargingStation
from charging_stations import load_charging_stations, calculate_distance
from tomtom import get_route

# Constants
TARGET_SEGMENT_DISTANCE = 300  # km
DISTANCE_TOLERANCE = 50  # km
AVERAGE_TRUCK_SPEED = 70  # km/h
INTERVAL_TIME = 45  # minutes
DRIVER_HOURLY_WAGE = 35  # euros per hour
ALIGNMENT_THRESHOLD = 0.3

def optimize_routes(routes: List[Dict], charging_stations: List[ChargingStation]) -> Dict[str, Any]:
    """
    Optimize routes by finding charging stations in the direction of the destination
    
    Args:
        routes: List of route dictionaries, each with start_coord and end_coord
        charging_stations: List of available charging stations
    
    Returns:
        Dictionary with optimized route details
    """
    
    # Initialize results
    results = {
        "routes": [],
        "total_distance": 0,
        "iterations": []
    }
    
    # Process each route
    for route_idx, route in enumerate(routes):
        print(f"Processing route {route_idx+1}/{len(routes)}")
        
        start_coord = (route["start_coord"]["latitude"], route["start_coord"]["longitude"])
        end_coord = (route["end_coord"]["latitude"], route["end_coord"]["longitude"])
        
        # Get the base route from TomTom API
        base_route = get_route(start_coord, end_coord)
        if not base_route:
            print(f"Could not get route for {start_coord} to {end_coord}")
            continue
            
        # Extract route details
        total_distance_meters = base_route["distance"]
        total_distance_km = total_distance_meters / 1000
        
        print(f"Route {route_idx+1}: {total_distance_km:.1f} km")
        
        # Process the route in iterations
        current_position = start_coord
        remaining_distance = total_distance_km
        iterations = []
        iteration_count = 0
        
        while remaining_distance > 0:
            iteration_count += 1
            print(f"Current Position: {current_position}, Iteration {iteration_count}, remaining distance: {remaining_distance:.1f} km")
            
            # Find optimal charging station in the direction of destination
            next_station = find_optimal_next_station(
                current_position,
                end_coord,
                charging_stations,
                TARGET_SEGMENT_DISTANCE,
                DISTANCE_TOLERANCE
            )
            
            if not next_station:
                print(f"Could not find suitable charging station from {current_position}")
                break
                
            next_position = (next_station.latitude, next_station.longitude)
            segment_distance = calculate_distance(current_position, next_position)
            
            # Update remaining distance
            remaining_distance -= segment_distance

            total_time_elapsed_in_this_iteration = ((segment_distance / AVERAGE_TRUCK_SPEED) * 3600) / 60
            total_time_elapsed_in_this_iteration += INTERVAL_TIME

            # Cost to company is only the time driver was on the road and not the time spent charging
            cost_to_company = DRIVER_HOURLY_WAGE * (segment_distance / AVERAGE_TRUCK_SPEED)
            
            # Record this iteration
            iterations.append({
                "iteration": iteration_count,
                "start_position": current_position,
                "end_position": next_position,
                "distance": segment_distance,
                "charging_station": {
                    "id": next_station.id,
                    "name": next_station.operator_name,
                    "location": next_position
                },
                "time_elapsed_minutes": total_time_elapsed_in_this_iteration,
                "cost_to_company": cost_to_company
            })
            
            # Update current position for next iteration
            current_position = next_position
            
            # If we're close enough to destination, finish
            if remaining_distance < TARGET_SEGMENT_DISTANCE + DISTANCE_TOLERANCE:
                # Final segment to destination
                final_segment = get_route(current_position, end_coord)
                if final_segment:
                    final_distance = final_segment["distance"] / 1000
                    final_time_elapsed = ((final_distance / AVERAGE_TRUCK_SPEED) * 3600) / 60 
                    final_cost_to_company = DRIVER_HOURLY_WAGE * (final_distance / AVERAGE_TRUCK_SPEED)
                    iterations.append({
                        "iteration": iteration_count + 1,
                        "start_position": current_position,
                        "end_position": end_coord,
                        "distance": final_distance,
                        "is_final": True,
                        "cost_to_company": final_cost_to_company,
                        "time_elapsed_minutes": final_time_elapsed
                    })
                    
                    remaining_distance = 0
        
        # Add route results
        route_result = {
            "start_coord": start_coord,
            "end_coord": end_coord,
            "total_distance": total_distance_km,
            "iterations": iterations
        }
        
        results["routes"].append(route_result)
        results["total_distance"] += total_distance_km
        results["iterations"].extend(iterations)
    
    return results

def map_coords_to_charging_station(coords: Tuple[float, float], charging_stations: List[ChargingStation]) -> ChargingStation:
    """Map coordinates to a charging station"""
    for station in charging_stations:
        if station.latitude == coords[0] and station.longitude == coords[1]:
            return station
    return None

def find_optimal_next_station(
    start_position: Tuple[float, float],
    end_position: Tuple[float, float],
    charging_stations: List[ChargingStation],
    target_distance: float,
    tolerance: float,
    alignment_threshold: float = ALIGNMENT_THRESHOLD
) -> Optional[ChargingStation]:
    """
    Find the optimal charging station that balances:
    1. Being within reasonable driving distance (target_distance ± tolerance)
    2. Being in the general direction of the destination (alignment > alignment_threshold)
    3. Being as close as possible to the final destination
    
    The algorithm:
    - Filters for truck-suitable charging stations
    - Checks if stations are within target distance range
    - Verifies stations are reasonably aligned with the direction to destination
    - Sorts candidates by proximity to final destination
    - Falls back to relaxed alignment criteria if no suitable stations found
    
    Args:
        start_position: (latitude, longitude) of starting point
        end_position: (latitude, longitude) of final destination
        charging_stations: List of available charging stations
        target_distance: Target segment distance in km
        tolerance: Distance tolerance in km
        
    Returns:
        ChargingStation object or None if no suitable stations found
    """
    # Calculate direction vector towards destination
    direction_vector = (
        end_position[0] - start_position[0],
        end_position[1] - start_position[1]
    )
    
    # Normalize direction vector
    vector_length = math.sqrt(direction_vector[0]**2 + direction_vector[1]**2)
    if vector_length > 0:
        direction_vector = (
            direction_vector[0] / vector_length,
            direction_vector[1] / vector_length
        )
    
    # Define distance range
    min_distance = target_distance - tolerance
    max_distance = target_distance + tolerance
    
    # Calculate total distance to destination
    total_distance_to_destination = calculate_distance(start_position, end_position)
    
    # Find all truck-suitable charging stations within the target distance range
    candidate_stations = []
    for station in charging_stations:
        # Only consider truck-suitable stations
        if station.truck_suitability != "yes":
            continue
            
        station_position = (station.latitude, station.longitude)
        distance_to_station = calculate_distance(start_position, station_position)
        
        # Skip stations that are too close or too far
        if not (min_distance <= distance_to_station <= max_distance):
            # If we're close to destination, consider stations closer than min_distance
            if total_distance_to_destination < target_distance and distance_to_station < min_distance:
                # Only consider stations that are in the direction of destination
                pass
            else:
                continue
        
        # Calculate remaining distance to destination after this station
        distance_from_station_to_destination = calculate_distance(station_position, end_position)
        
        # Calculate alignment with direction to destination
        station_vector = (
            station.latitude - start_position[0],
            station.longitude - start_position[1]
        )
        
        # Normalize station vector
        station_vector_length = math.sqrt(station_vector[0]**2 + station_vector[1]**2)
        if station_vector_length > 0:
            station_vector = (
                station_vector[0] / station_vector_length,
                station_vector[1] / station_vector_length
            )
            
        # Calculate dot product to measure alignment (1 = perfect alignment, -1 = opposite direction)
        alignment = direction_vector[0] * station_vector[0] + direction_vector[1] * station_vector[1]
        
        # Only consider stations with reasonable alignment (at least 0.5, which is about 60 degrees)
        if alignment > alignment_threshold:
            # Calculate progress ratio: how much closer we get to destination by visiting this station
            # Higher is better - means we're making more progress toward destination
            progress = (total_distance_to_destination - distance_from_station_to_destination) / distance_to_station
            
            candidate_stations.append((station, distance_to_station, alignment, progress))
    
    # If no candidates found with strict criteria, try with relaxed alignment
    if not candidate_stations:
        for station in charging_stations:
            if station.truck_suitability != "yes":
                continue
                
            station_position = (station.latitude, station.longitude)
            distance_to_station = calculate_distance(start_position, station_position)
            
            if min_distance <= distance_to_station <= max_distance:
                # Calculate remaining distance to destination after this station
                distance_from_station_to_destination = calculate_distance(station_position, end_position)
                
                # Calculate progress ratio
                progress = (total_distance_to_destination - distance_from_station_to_destination) / distance_to_station
                
                candidate_stations.append((station, distance_to_station, 0, progress))
    
    # Sort by distance to final destination (closest first)
    candidate_stations.sort(key=lambda x: calculate_distance((x[0].latitude, x[0].longitude), end_position))
    
    # Print the top 3 candidate stations and their metrics
    for station, distance, alignment, progress in candidate_stations[:3]:
        print(f"Station: {station.operator_name}, Progress: {progress:.2f}, Distance: {distance:.1f}, Station ID: {station.id}")
    
    # Return the station with best progress, or None if no suitable stations found
    if candidate_stations:
        return candidate_stations[0][0]
    
    return None

def save_optimization_results(results: Dict[str, Any], output_file: str = "optimization_results.json"):
    """Save optimization results to a JSON file"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

import random
# Example usage
if __name__ == "__main__":
    # Load charging stations
    stations = load_charging_stations("data/public_charge_points.csv")

    # Set a seed for random
    random.seed(42)

    # Randomly select 5 integers
    random_indices = random.sample(range(25), 6)
    print(random_indices)


    
    routes = [
        {
            "start_coord": {"latitude": stations[random_indices[0]].latitude, "longitude": stations[random_indices[0]].longitude},  
            "end_coord": {"latitude": stations[random_indices[1]].latitude, "longitude": stations[random_indices[1]].longitude}     
        },
        {
            "start_coord": {"latitude": stations[random_indices[2]].latitude, "longitude": stations[random_indices[2]].longitude},  
            "end_coord": {"latitude": stations[random_indices[3]].latitude, "longitude": stations[random_indices[3]].longitude}     
        },
        {
            "start_coord": {"latitude": stations[random_indices[4]].latitude, "longitude": stations[random_indices[4]].longitude},  
            "end_coord": {"latitude": stations[random_indices[5]].latitude, "longitude": stations[random_indices[5]].longitude}     
        }
    ]
    
    # Run optimization
    results = optimize_routes(routes, stations)
    
    # Save results
    save_optimization_results(results, "report.json")
    
    # Print summary
    print("\nOptimization Summary:")
    print(f"Total Routes: {len(results['routes'])}")
    print(f"Total Distance: {results['total_distance']:.1f} km")
    print(f"Total Iterations: {len(results['iterations'])}")
    
    from map_visualizer import visualize_report_json
    # Visualize the results
    visualize_report_json("report.json", "report_visualization.html")
