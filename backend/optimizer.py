import json
import networkx as nx
from typing import List, Dict, Tuple, Any, Optional
import math
from models import ChargingStation, Driver
from charging_stations import load_charging_stations, calculate_distance
from tomtom import get_route

# Constants
TARGET_SEGMENT_DISTANCE = 300  # km
DISTANCE_TOLERANCE = 50  # km
AVERAGE_TRUCK_SPEED = 70  # km/h
INTERVAL_TIME = 45  # minutes
DRIVER_HOURLY_WAGE = 35  # euros per hour
ALIGNMENT_THRESHOLD = 0.3
# Require drivers' onward directions at a station to be sufficiently opposite (crossing paths)
INVERSE_ALIGNMENT_THRESHOLD = 0.8
# Maximum detour radius (km) to consider a rendezvous swap near a station
NEAR_RENDEZVOUS_RADIUS_KM = 300

def get_distance_between_stations(station1_coords: Tuple[float, float], station2_coords: Tuple[float, float], charging_stations: List[ChargingStation]) -> float:
    """Get the distance between two stations"""
    with open('graph_computation.json', 'r') as f:
        distance_cache = json.load(f)

    # find station ids from coords
    station1_id = next((station.id for station in charging_stations if station.latitude == station1_coords[0] and station.longitude == station1_coords[1]), None)
    station2_id = next((station.id for station in charging_stations if station.latitude == station2_coords[0] and station.longitude == station2_coords[1]), None)

    print(station1_id, station2_id)
    try:
        res =  distance_cache[f"{station1_id}_{station2_id}"]["api_response"]["routes"][0]["summary"]["lengthInMeters"] / 1000
    except Exception as e:
        print(f"Error getting distance between {station1_coords} and {station2_coords}: {e}")
    dist = get_route(station1_coords, station2_coords)
    res = dist["distance"] / 1000
    print(f"Distance between {station1_coords} and {station2_coords} is {res} km")
    return res

def optimize_routes(
    routes: List[Dict], 
    charging_stations: List[ChargingStation],
    drivers: List[Driver]
) -> Dict[str, Any]:
    """
    Optimize routes with driver-truck assignments and potential swaps
    
    Args:
        routes: List of route dictionaries
        charging_stations: List of charging stations
        drivers: List of drivers
        
    Returns:
        Dictionary with optimized route details and driver assignments
    """
    # Initialize results
    results = {
        "routes": [],
        "total_distance": 0,
        "iterations": [],
        "driver_assignments": [],
        "truck_swaps": []
    }
    
    # Initialize driver-truck assignments
    driver_assignments = []
    for i, (driver, route) in enumerate(zip(drivers, routes)):
        driver.current_location = (route["start_coord"]["latitude"], route["start_coord"]["longitude"])
        driver.current_truck_id = i
        driver_assignments.append({
            "driver_id": driver.id,
            "truck_id": i,
            "route_id": i
        })
    
    results["driver_assignments"] = driver_assignments
    
    # Initialize route processing state
    route_states = []
    for route_idx, route in enumerate(routes):
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
        
        # Initialize route state
        route_states.append({
            "route_idx": route_idx,
            "start_coord": start_coord,
            "end_coord": end_coord,
            "total_distance_km": total_distance_km,
            "current_position": start_coord,
            "remaining_distance": total_distance_km,
            "iterations": [],
            "iteration_count": 0,
            "completed": False
        })
    
    # Process routes in iterations until all are complete
    all_completed = False
    global_iteration = 0
    
    while not all_completed:
        global_iteration += 1
        print(f"Global iteration {global_iteration}")
        current_iterations = []
        
        # Process one iteration for each route
        for route_state in route_states:
            if route_state["completed"]:
                continue
                
            route_idx = route_state["route_idx"]
            current_position = route_state["current_position"]
            end_coord = route_state["end_coord"]
            remaining_distance = route_state["remaining_distance"]
            iteration_count = route_state["iteration_count"] + 1
            route_state["iteration_count"] = iteration_count
            
            print(f"Route {route_idx+1}, Iteration {iteration_count}, remaining distance: {remaining_distance:.1f} km")
            
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
                route_state["completed"] = True
                continue
                
            next_position = (next_station.latitude, next_station.longitude)
            segment_distance = get_distance_between_stations(current_position, next_position, charging_stations)
            
            # Update remaining distance
            remaining_distance -= segment_distance
            route_state["remaining_distance"] = remaining_distance
            
            total_time_elapsed = ((segment_distance / AVERAGE_TRUCK_SPEED) * 3600) / 60
            total_time_elapsed += INTERVAL_TIME
            
            # Cost to company is only the time driver was on the road and not the time spent charging
            cost_to_company = DRIVER_HOURLY_WAGE * (segment_distance / AVERAGE_TRUCK_SPEED)
            
            # Estimate charging cost (assuming average charging session of 80% battery at 350 kWh)
            estimated_charging_cost = next_station.price_per_kWh * 280  # 80% of 350 kWh
            
            # Record this iteration
            iteration_data = {
                "iteration": iteration_count,
                "route_idx": route_idx,
                "start_position": current_position,
                "end_position": next_position,
                "distance": segment_distance,
                "charging_station": {
                    "id": next_station.id,
                    "name": next_station.operator_name,
                    "location": next_position
                },
                "time_elapsed_minutes": total_time_elapsed,
                "cost_to_company": cost_to_company,
                "charging_cost": estimated_charging_cost,
                "sum_cost": cost_to_company + estimated_charging_cost
            }
            
            route_state["iterations"].append(iteration_data)
            current_iterations.append(iteration_data)
            
            # Update current position for next iteration
            route_state["current_position"] = next_position
            
            # Update driver locations
            for driver in drivers:
                if driver.current_truck_id == route_idx:
                    driver.current_location = next_position
            
            # If we're close enough to destination, finish
            if remaining_distance < TARGET_SEGMENT_DISTANCE + DISTANCE_TOLERANCE:
                # Final segment to destination
                final_segment = get_route(next_position, end_coord)
                if final_segment:
                    final_distance = final_segment["distance"] / 1000
                    final_time_elapsed = ((final_distance / AVERAGE_TRUCK_SPEED) * 3600) / 60 
                    final_cost_to_company = DRIVER_HOURLY_WAGE * (final_distance / AVERAGE_TRUCK_SPEED)
                    
                    final_iteration = {
                        "iteration": iteration_count + 1,
                        "route_idx": route_idx,
                        "start_position": next_position,
                        "end_position": end_coord,
                        "distance": final_distance,
                        "is_final": True,
                        "cost_to_company": final_cost_to_company,
                        "time_elapsed_minutes": final_time_elapsed,
                        "charging_cost": 0,
                        "sum_cost": final_cost_to_company
                    }
                    
                    route_state["iterations"].append(final_iteration)
                    route_state["remaining_distance"] = 0
                    route_state["completed"] = True
                    route_state["current_position"] = end_coord
                    
                    # Update driver locations for completed route
                    for driver in drivers:
                        if driver.current_truck_id == route_idx:
                            driver.current_location = end_coord
        
        # After processing one iteration for each route, check for potential truck swaps
        if current_iterations:
            # Map route index to its end coordinate for alignment checks
            route_end_coords = {rs["route_idx"]: rs["end_coord"] for rs in route_states}
            potential_swaps = find_potential_truck_swaps(
                current_iterations, 
                drivers,
                charging_stations,
                route_end_coords
            )
            
            # Apply the best swap
            if potential_swaps:
                swap = potential_swaps[0]  # Take the best swap
                
                # Update driver assignments
                driver1_id = swap["driver1_id"]
                driver2_id = swap["driver2_id"]
                
                # Find the drivers
                driver1 = next(d for d in drivers if d.id == driver1_id)
                driver2 = next(d for d in drivers if d.id == driver2_id)
                
                # Swap truck assignments
                temp_truck = driver1.current_truck_id
                driver1.current_truck_id = driver2.current_truck_id
                driver2.current_truck_id = temp_truck
                
                # Record the swap for both involved iterations so the visualizer can match per route
                results["truck_swaps"].append({
                    "station_id": swap["station_id"],
                    "driver1_id": driver1_id,
                    "driver2_id": driver2_id,
                    "benefit_km": swap.get("benefit_km", 0.0),
                    "alignment_dot": swap.get("alignment_dot"),
                    "reason": swap.get("reason", "same_station"),
                    "station_location": swap.get("station_location"),
                    "detour_km_total": swap.get("detour_km_total", 0.0),
                    "iteration": swap["iteration1"]["iteration"],
                    "global_iteration": global_iteration
                })
                results["truck_swaps"].append({
                    "station_id": swap["station_id"],
                    "driver1_id": driver1_id,
                    "driver2_id": driver2_id,
                    "benefit_km": swap.get("benefit_km", 0.0),
                    "alignment_dot": swap.get("alignment_dot"),
                    "reason": swap.get("reason", "same_station"),
                    "station_location": swap.get("station_location"),
                    "detour_km_total": swap.get("detour_km_total", 0.0),
                    "iteration": swap["iteration2"]["iteration"],
                    "global_iteration": global_iteration
                })
        
        # Check if all routes are completed
        all_completed = all(route_state["completed"] for route_state in route_states)
    
    # Compile final results
    for route_state in route_states:
        route_result = {
            "start_coord": route_state["start_coord"],
            "end_coord": route_state["end_coord"],
            "total_distance": route_state["total_distance_km"],
            "iterations": route_state["iterations"]
        }
        
        results["routes"].append(route_result)
        results["total_distance"] += route_state["total_distance_km"]
        results["iterations"].extend(route_state["iterations"])
    
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
    4. Having lower charging costs
    
    The algorithm:
    - First checks if destination itself is within target distance range
    - Filters for truck-suitable charging stations
    - Checks if stations are within target distance range
    - Verifies stations are reasonably aligned with the direction to destination
    - Sorts candidates by a combined score of distance to destination and charging cost
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
    
    # First check if the destination is within the target distance range
    if total_distance_to_destination <= max_distance:
        print(f"Destination is within range ({total_distance_to_destination:.1f} km). Going directly to destination.")
        # Create a temporary ChargingStation object for the destination
        destination_station = ChargingStation(
            id=-1,  # Use a special ID to indicate this is the destination
            country="",
            latitude=end_position[0],
            longitude=end_position[1],
            truck_suitability="yes",
            operator_name="Destination",
            max_power_kW=0,
            price_per_kWh=0
        )
        return destination_station
    
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
            
            # Estimate charging cost (assuming average charging session of 80% battery at 350 kWh)
            # This is a simplified model - in a real implementation you'd use the actual truck model
            estimated_charging_cost = station.price_per_kWh * 280  # 80% of 350 kWh
            
            candidate_stations.append((station, distance_to_station, alignment, progress, estimated_charging_cost))
    
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
                
                # Estimate charging cost
                estimated_charging_cost = station.price_per_kWh * 280  # 80% of 350 kWh
                
                candidate_stations.append((station, distance_to_station, 0, progress, estimated_charging_cost))
    
    # Sort by combined score: distance to destination + charging cost
    # Normalize both factors to have comparable weights
    if candidate_stations:
        # Find max distance and max cost for normalization
        max_distance = max(calculate_distance((s[0].latitude, s[0].longitude), end_position) for s in candidate_stations)
        max_cost = max(s[4] for s in candidate_stations) if max(s[4] for s in candidate_stations) > 0 else 1
        
        # Calculate combined score for each station
        for i, (station, distance, alignment, progress, cost) in enumerate(candidate_stations):
            distance_to_dest = calculate_distance((station.latitude, station.longitude), end_position)
            # Normalize both factors (0-1 range) and combine them
            normalized_distance = distance_to_dest / max_distance if max_distance > 0 else 0
            normalized_cost = cost / max_cost if max_cost > 0 else 0
            # Combined score (lower is better)
            combined_score = normalized_distance + normalized_cost
            # Replace the tuple with updated one including the score
            candidate_stations[i] = (station, distance, alignment, progress, cost, combined_score)
        
        # Sort by combined score (lower is better)
        candidate_stations.sort(key=lambda x: x[5])
    
    # Print the top 3 candidate stations and their metrics
    for station, distance, alignment, progress, cost, score in candidate_stations[:3]:
        print(f"Station: {station.operator_name}, Score: {score:.2f}, Distance: {distance:.1f}, "
              f"Cost: {cost:.2f}, Station ID: {station.id}")
    
    # Return the station with best combined score, or None if no suitable stations found
    if candidate_stations:
        return candidate_stations[0][0]
    
    return None

def save_optimization_results(results: Dict[str, Any], output_file: str = "optimization_results.json"):
    """Save optimization results to a JSON file"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def find_potential_truck_swaps(
    current_iterations: List[Dict], 
    drivers: List[Driver],
    charging_stations: List[ChargingStation],
    route_end_coords: Dict[int, Tuple[float, float]]
) -> List[Dict]:
    """
    Find potential truck swaps between drivers at charging stations.
    Only consider pairs whose onward directions from the station are inversely aligned
    (i.e., crossing paths) according to INVERSE_ALIGNMENT_THRESHOLD.
    
    Args:
        current_iterations: List of current route iterations
        drivers: List of drivers with their home locations
        charging_stations: List of charging stations
        route_end_coords: Mapping from route_idx to final destination coordinates
        
    Returns:
        List of potential truck swaps (sorted by most inverse alignment)
    """
    potential_swaps = []
    
    # Build iteration -> driver pairs for this global step
    iteration_driver_pairs: List[Tuple[Driver, Dict]] = []
    for iteration in current_iterations:
        if "is_final" in iteration and iteration["is_final"]:
            continue
        driver_for_route = next((d for d in drivers if d.current_truck_id == iteration["route_idx"]), None)
        if driver_for_route:
            iteration_driver_pairs.append((driver_for_route, iteration))

    # Helper: compute normalized direction vector
    def _normalize(vec: Tuple[float, float]) -> Tuple[float, float]:
        length = math.sqrt(vec[0]**2 + vec[1]**2)
        if length == 0:
            return (0.0, 0.0)
        return (vec[0]/length, vec[1]/length)

    # Evaluate all pairs for same-station and near-station rendezvous
    for i in range(len(iteration_driver_pairs)):
        for j in range(i+1, len(iteration_driver_pairs)):
            driver1, iteration1 = iteration_driver_pairs[i]
            driver2, iteration2 = iteration_driver_pairs[j]
            if driver1.id == driver2.id:
                continue

            # Onward direction vectors from current end positions toward their destinations
            pos1 = iteration1["end_position"]
            pos2 = iteration2["end_position"]
            route1_end = route_end_coords.get(iteration1["route_idx"])
            route2_end = route_end_coords.get(iteration2["route_idx"])
            if not route1_end or not route2_end:
                continue
            nv1 = _normalize((route1_end[0] - pos1[0], route1_end[1] - pos1[1]))
            nv2 = _normalize((route2_end[0] - pos2[0], route2_end[1] - pos2[1]))
            dot = nv1[0] * nv2[0] + nv1[1] * nv2[1]
            if dot > INVERSE_ALIGNMENT_THRESHOLD:
                continue

            # Case A: same station
            station1_id = iteration1["charging_station"]["id"]
            station2_id = iteration2["charging_station"]["id"]
            if station1_id == station2_id:
                potential_swaps.append({
                    "station_id": station1_id,
                    "station_location": iteration1["charging_station"].get("location", pos1),
                    "driver1_id": driver1.id,
                    "driver2_id": driver2.id,
                    "benefit_km": 0.0,
                    "alignment_dot": dot,
                    "reason": "same_station",
                    "detour_km_total": 0.0,
                    "iteration1": iteration1,
                    "iteration2": iteration2
                })
                continue

            # Case B: near-station rendezvous within radius for both
            best_station = None
            best_detour_sum = float('inf')
            for st in charging_stations:
                if st.truck_suitability != "yes":
                    continue
                st_pos = (st.latitude, st.longitude)
                d1 = calculate_distance(pos1, st_pos)
                d2 = calculate_distance(pos2, st_pos)
                if d1 <= NEAR_RENDEZVOUS_RADIUS_KM and d2 <= NEAR_RENDEZVOUS_RADIUS_KM:
                    detour_sum = d1 + d2
                    if detour_sum < best_detour_sum:
                        best_detour_sum = detour_sum
                        best_station = (st.id, st_pos)

            if best_station is not None:
                potential_swaps.append({
                    "station_id": best_station[0],
                    "station_location": best_station[1],
                    "driver1_id": driver1.id,
                    "driver2_id": driver2.id,
                    "benefit_km": 0.0,
                    "alignment_dot": dot,
                    "reason": "rendezvous_within_radius",
                    "detour_km_total": best_detour_sum,
                    "iteration1": iteration1,
                    "iteration2": iteration2
                })

    # Sort by most inverse alignment first, then by smallest detour if available
    potential_swaps.sort(key=lambda x: (x.get("alignment_dot", 0.0), x.get("detour_km_total", 0.0)))
    return potential_swaps

import random
# Example usage
if __name__ == "__main__":
    # Load charging stations
    stations = load_charging_stations("data/public_charge_points.csv")

    stations_idx = [11, 0, 10, 18, 21, 3, 16, 6]
    for idx in stations_idx:
        print(stations[idx].latitude, stations[idx].longitude)

    print(stations[9], stations[17])
    print(stations[3], stations[4]  )
    print(stations[12], stations[13])
    
    print(f"stations[11] {stations[11]} stations[10] {stations[10]} stations[21] {stations[21]} stations[16] {stations[16]} \nStations {stations[0]} {stations[18]} {stations[3]} {stations[6]}")
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

    # Example drivers (replace with actual driver data)
    drivers = [
        Driver(id=1, name="Driver Lubeck", home_location=(stations[11].latitude, stations[11].longitude)),
        Driver(id=2, name="Driver Ulm", home_location=(stations[10].latitude, stations[10].longitude)),
    ]

    # Run optimization
    results = optimize_routes(routes, stations, drivers)
    
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


