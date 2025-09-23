from typing import List, Optional, Dict, Any
from models import (
    SingleRouteRequest, SingleRouteWithSegments, MultiRouteWithSegments,
    Driver, TruckSwap, ChargingStation, RouteComparison
)
from optily import plan_route
from optimizer import optimize_routes
from charging_stations import load_charging_stations
import logging
from trucks import load_truck_specs
logger = logging.getLogger(__name__)

def calculate_multi_route_with_swaps(
    route_requests: List[SingleRouteRequest],
    starting_battery_kwh: float = None
) -> MultiRouteWithSegments:
    """
    Wrapper function similar to /calculate-costs but for multiple routes with swapping optimization.
    
    Args:
        route_requests: List of SingleRouteRequest objects
        starting_battery_kwh: Starting battery level (optional)
        
    Returns:
        MultiRouteWithSegments with detailed segments, costs, and optimization results
    """
    try:
        # Load charging stations
        charging_stations = load_charging_stations("data/public_charge_points.csv")
        trucks = load_truck_specs("data/truck_specs.csv") 

        truck_model = list(trucks.keys())[0]
        
        # Step 1: Calculate base routes using the existing plan_route function
        base_routes = []
        total_base_cost = 0.0
        total_base_distance = 0.0
        total_base_duration = 0.0
        total_base_charging_cost = 0.0
        
        for i, request in enumerate(route_requests):
            try:
                # Calculate individual route using existing function
                route_result = plan_route(request, truck_model, starting_battery_kwh)
                
                if not route_result.success:
                    logger.warning(f"Failed to calculate route {i+1}: {route_result.message}")
                    continue
                    
                base_routes.append(route_result)
                total_base_cost += route_result.total_costs.total_cost_eur if route_result.total_costs else 0
                total_base_distance += route_result.distance_km
                total_base_duration += route_result.duration_minutes
                total_base_charging_cost += route_result.total_costs.charging_cost_eur if route_result.total_costs else 0
                
            except Exception as e:
                logger.error(f"Error calculating route {i+1}: {str(e)}")
                continue
        with open(f"simple_routes.json", "w") as f:
            f.write(f"{base_routes}")
            f.write("\n")
            f.write(f"Total Cost: {total_base_cost}"+ "\n")
            f.write(f"Total Distance: {total_base_distance}"+ "\n")
            f.write(f"Total Duration: {total_base_duration}"+ "\n")
            f.write(f"Total Charging Cost: {total_base_charging_cost}"+ "\n")
        
        if not base_routes:
            return MultiRouteWithSegments(
                routes=[],
                total_distance_km=0,
                total_duration_minutes=0,
                total_cost_eur=0,
                total_charging_cost_eur=0,
                success=False,
                message="Failed to calculate any routes"
            )
        
        # Step 2: Prepare data for optimization
        optimizer_routes = []
        drivers = []
        
        for i, (request, route_result) in enumerate(zip(route_requests, base_routes)):
            # Convert to optimizer format
            optimizer_routes.append({
                "start_coord": {"latitude": request.start_lat, "longitude": request.start_lng},
                "end_coord": {"latitude": request.end_lat, "longitude": request.end_lng}
            })
            
            # Create driver for each route starting at their route's origin
            driver = Driver(
                id=str(i+1),
                name=f"Driver {i+1}",
                current_location=(request.start_lat, request.start_lng),
                home_location=(request.start_lat, request.start_lng)
            )
            drivers.append(driver)
        
        # Step 3: Run optimization to find beneficial swaps
        optimization_result = optimize_routes(optimizer_routes, charging_stations, drivers)

        with open(f"simple_routes.json", "w") as f:
            f.write(f"*"*120 + "\n")
            f.write(f"Step 3: Optimization Result: {optimization_result}"+ "\n")
            f.write(f"*"*120 + "\n")
            
        
        # Step 4: Apply swaps to route segments and update costs
        optimized_routes = _apply_swaps_to_routes(
            base_routes, optimization_result, route_requests, truck_model, starting_battery_kwh
        )

        with open(f"simple_routes.json", "w") as f:
            f.write(f"*"*120 + "\n")
            f.write(f"Step 4: Optimization swaps Result: {optimization_result}"+ "\n")
            f.write(f"*"*120 + "\n")
            
        
        # Step 5: Calculate optimized totals
        total_optimized_cost = sum(route.total_costs.total_cost_eur if route.total_costs else 0 
                                 for route in optimized_routes)
        total_optimized_distance = sum(route.distance_km for route in optimized_routes)
        total_optimized_duration = sum(route.duration_minutes for route in optimized_routes)
        total_optimized_charging_cost = sum(route.total_costs.charging_cost_eur if route.total_costs else 0 
                                          for route in optimized_routes)
        
        # Step 6: Convert truck swaps to our model format
        truck_swaps = []
        for swap in optimization_result.get("truck_swaps", []):
            truck_swaps.append(TruckSwap(
                station_id=swap["station_id"],
                station_location=swap["station_location"],
                driver1_id=swap["driver1_id"],
                driver2_id=swap["driver2_id"],
                benefit_km=swap.get("benefit_km", 0.0),
                alignment_dot=swap.get("alignment_dot", 0.0),
                reason=swap.get("reason", "unknown"),
                detour_km_total=swap.get("detour_km_total", 0.0),
                iteration=swap["iteration"],
                route_idx=swap["route_idx"],
                global_iteration=swap["global_iteration"]
            ))
        
        # Step 7: Calculate per-route comparisons
        route_comparisons = _calculate_route_comparisons(
            base_routes, optimized_routes, truck_swaps, route_requests
        )

        with open(f"simple_routes.json", "w") as f:
            f.write(f"*"*120 + "\n")
            f.write(f"Step 7: Route Comparisons Result: {route_comparisons}"+ "\n")
            f.write(f"*"*120 + "\n")
        
        # Step 8: Calculate overall savings
        cost_savings = total_base_cost - total_optimized_cost
        cost_savings_percentage = (cost_savings / total_base_cost * 100) if total_base_cost > 0 else 0
        
        # Step 9: Build optimization summary
        optimization_summary = {
            "total_routes": len(optimized_routes),
            "total_swaps_found": len(truck_swaps),
            "optimization_iterations": len(optimization_result.get("iterations", [])),
            "base_vs_optimized": {
                "base_cost": total_base_cost,
                "optimized_cost": total_optimized_cost,
                "savings": cost_savings,
                "savings_percentage": cost_savings_percentage
            },
            "route_comparisons": route_comparisons
        }

        with open(f"simple_routes.json", "w") as f:
            f.write(f"*"*120 + "\n")
            f.write(f"Step 9: Optimization Summary Result: {optimization_summary}"+ "\n")
            f.write(f"*"*120 + "\n")
        
        response = MultiRouteWithSegments(
            routes=optimized_routes,
            total_distance_km=total_optimized_distance,
            total_duration_minutes=total_optimized_duration,
            total_cost_eur=total_optimized_cost,
            total_charging_cost_eur=total_optimized_charging_cost,
            success=True,
            message=f"Successfully optimized {len(optimized_routes)} routes with {len(truck_swaps)} swaps",
            driver_assignments=optimization_result.get("driver_assignments", []),
            truck_swaps=truck_swaps,
            drivers=drivers,
            optimization_summary=optimization_summary,
            base_cost_eur=total_base_cost,
            optimized_cost_eur=total_optimized_cost,
            cost_savings_eur=cost_savings,
            cost_savings_percentage=cost_savings_percentage,
            route_comparisons=route_comparisons
        )

        with open(f"simple_routes.json", "w") as f:
            f.write(f"*"*120 + "\n")
            f.write(f"Step 10: Response Result: {response}"+ "\n")
            f.write(f"*"*120 + "\n")
        
        return response
    except Exception as e:
        logger.error(f"Error in calculate_multi_route_with_swaps: {str(e)}")
        return MultiRouteWithSegments(
            routes=[],
            total_distance_km=0,
            total_duration_minutes=0,
            total_cost_eur=0,
            total_charging_cost_eur=0,
            success=False,
            message=f"Error calculating multi-route with swaps: {str(e)}"
        )

def _calculate_route_comparisons(
    base_routes: List[SingleRouteWithSegments],
    optimized_routes: List[SingleRouteWithSegments],
    truck_swaps: List[TruckSwap],
    route_requests: List[SingleRouteRequest]
) -> List[RouteComparison]:
    """
    Calculate detailed comparison for each route between base and optimized versions.
    """
    route_comparisons = []
    
    for i, (base_route, optimized_route, request) in enumerate(zip(base_routes, optimized_routes, route_requests)):
        # Get swaps that affected this route
        route_swaps = [swap for swap in truck_swaps if swap.route_idx == i]
        
        # Calculate base metrics
        base_cost = base_route.total_costs.total_cost_eur if base_route.total_costs else 0
        base_duration = base_route.duration_minutes
        base_distance = base_route.distance_km
        base_charging_cost = base_route.total_costs.charging_cost_eur if base_route.total_costs else 0
        base_driver_cost = base_route.total_costs.driver_cost_eur if base_route.total_costs else 0
        
        # Calculate optimized metrics
        optimized_cost = optimized_route.total_costs.total_cost_eur if optimized_route.total_costs else 0
        optimized_duration = optimized_route.duration_minutes
        optimized_distance = optimized_route.distance_km
        optimized_charging_cost = optimized_route.total_costs.charging_cost_eur if optimized_route.total_costs else 0
        optimized_driver_cost = optimized_route.total_costs.driver_cost_eur if optimized_route.total_costs else 0
        
        # Calculate savings
        cost_savings = base_cost - optimized_cost
        duration_savings = base_duration - optimized_duration
        distance_savings = base_distance - optimized_distance
        charging_cost_savings = base_charging_cost - optimized_charging_cost
        driver_cost_savings = base_driver_cost - optimized_driver_cost
        
        # Calculate percentage savings
        cost_savings_pct = (cost_savings / base_cost * 100) if base_cost > 0 else 0
        duration_savings_pct = (duration_savings / base_duration * 100) if base_duration > 0 else 0
        distance_savings_pct = (distance_savings / base_distance * 100) if base_distance > 0 else 0
        charging_cost_savings_pct = (charging_cost_savings / base_charging_cost * 100) if base_charging_cost > 0 else 0
        driver_cost_savings_pct = (driver_cost_savings / base_driver_cost * 100) if base_driver_cost > 0 else 0
        
        comparison = RouteComparison(
            route_name=request.route_name or f"Route {i+1}",
            route_index=i,
            base={
                "total_cost_eur": base_cost,
                "duration_minutes": base_duration,
                "distance_km": base_distance,
                "charging_cost_eur": base_charging_cost,
                "driver_cost_eur": base_driver_cost
            },
            optimized={
                "total_cost_eur": optimized_cost,
                "duration_minutes": optimized_duration,
                "distance_km": optimized_distance,
                "charging_cost_eur": optimized_charging_cost,
                "driver_cost_eur": optimized_driver_cost
            },
            savings={
                "total_cost_eur": cost_savings,
                "duration_minutes": duration_savings,
                "distance_km": distance_savings,
                "charging_cost_eur": charging_cost_savings,
                "driver_cost_eur": driver_cost_savings
            },
            savings_percentage={
                "total_cost_eur": cost_savings_pct,
                "duration_minutes": duration_savings_pct,
                "distance_km": distance_savings_pct,
                "charging_cost_eur": charging_cost_savings_pct,
                "driver_cost_eur": driver_cost_savings_pct
            },
            swaps_applied=route_swaps
        )
        
        route_comparisons.append(comparison)
    
    return route_comparisons

def _apply_swaps_to_routes(
    base_routes: List[SingleRouteWithSegments],
    optimization_result: Dict[str, Any],
    route_requests: List[SingleRouteRequest],
    truck_model: str = None,
    starting_battery_kwh: float = None
) -> List[SingleRouteWithSegments]:
    """
    Apply optimization swaps by recalculating costs based on actual route changes.
    
    Key insight: Driver swaps don't change costs directly - only route changes (detours) do.
    Cost = (Distance × Time × Driver_Wage) + (Energy × Charging_Price)
    """
    optimized_routes = []
    
    # Get optimization data
    swaps = optimization_result.get("truck_swaps", [])
    driver_assignments = optimization_result.get("driver_assignments", [])
    iterations = optimization_result.get("iterations", [])
    
    # Create a mapping of route_idx to current driver
    route_to_driver = {}
    for assignment in driver_assignments:
        route_to_driver[assignment["route_id"]] = assignment["driver_id"]
    
    # Group iterations by route
    route_iterations = {}
    for iteration in iterations:
        route_idx = iteration.get("route_idx", 0)
        if route_idx not in route_iterations:
            route_iterations[route_idx] = []
        route_iterations[route_idx].append(iteration)
    
    for i, route in enumerate(base_routes):
        # Deep copy the route
        optimized_route = route.copy(deep=True)
        
        # Get current driver assignment
        current_driver_id = route_to_driver.get(i, str(i+1))
        
        # Get optimization iterations for this route
        route_opt_iterations = route_iterations.get(i, [])
        
        if route_opt_iterations:
            # Recalculate costs based on actual optimization results
            optimized_route = _recalculate_route_costs_from_iterations(
                optimized_route, 
                route_opt_iterations, 
                current_driver_id
            )
        else:
            # No optimization applied, just update driver ID
            for segment in optimized_route.route_segments:
                segment.driver_id = current_driver_id
            
            if optimized_route.driver:
                optimized_route.driver.id = current_driver_id
                optimized_route.driver.name = f"Driver {current_driver_id}"
        
        optimized_routes.append(optimized_route)
    
    return optimized_routes

def _recalculate_route_costs_from_iterations(
    route: SingleRouteWithSegments,
    route_iterations: List[Dict],
    current_driver_id: str
) -> SingleRouteWithSegments:
    """
    Recalculate route costs based on actual optimization iterations.
    
    This is the correct approach because:
    1. Each iteration contains the actual distance, time, and charging costs
    2. Driver wage is constant (€35/hour)
    3. Charging costs are based on actual station prices
    4. No arbitrary cost reductions - use real data
    """
    # Calculate totals from optimization iterations
    total_distance = sum(iter.get("distance", 0) for iter in route_iterations)
    total_duration = sum(iter.get("time_elapsed_minutes", 0) for iter in route_iterations)
    total_driver_cost = sum(iter.get("cost_to_company", 0) for iter in route_iterations)
    total_charging_cost = sum(iter.get("charging_cost", 0) for iter in route_iterations)
    total_cost = sum(iter.get("sum_cost", 0) for iter in route_iterations)
    
    # Update route with actual optimization results
    route.distance_km = total_distance
    route.duration_minutes = total_duration
    
    # Update costs with actual values from optimization
    if route.total_costs:
        route.total_costs.total_cost_eur = total_cost
        route.total_costs.driver_cost_eur = total_driver_cost
        route.total_costs.charging_cost_eur = total_charging_cost
        # Keep other costs proportional (depreciation, tolls)
        if route.total_costs.total_cost_eur > 0:
            cost_ratio = total_cost / route.total_costs.total_cost_eur
            route.total_costs.depreciation_cost_eur *= cost_ratio
            route.total_costs.tolls_cost_eur *= cost_ratio
    
    # Update driver assignments
    for segment in route.route_segments:
        segment.driver_id = current_driver_id
    
    if route.driver:
        route.driver.id = current_driver_id
        route.driver.name = f"Driver {current_driver_id}"
    
    return route

# Example usage
if __name__ == "__main__":
    # Example route requests
    route_requests = [
        # SingleRouteRequest(
        #     start_lat=53.5511, start_lng=9.9937,   # Hamburg
        #     end_lat=50.1109, end_lng=8.6821,      # Frankfurt
        #     route_name="Hamburg-Frankfurt"
        # ),
        # SingleRouteRequest(
        #     start_lat=48.1351, start_lng=11.5820,  # Munich
        #     end_lat=52.5200, end_lng=13.4050,     # Berlin
        #     route_name="Munich-Berlin"
        # ),
        # SingleRouteRequest(
        #     start_lat=51.2277, start_lng=6.7735,   # Düsseldorf
        #     end_lat=51.0504, end_lng=13.7373,     # Dresden
        #     route_name="Düsseldorf-Dresden"
        # ),
        # SingleRouteRequest(start_lat=53.5511, start_lng=9.9937, end_lat=50.1109, end_lng=8.6821, route_name="Hamburg-Frankfurt"),
    # SingleRouteRequest(start_lat=48.1351, start_lng=11.5820, end_lat=52.5200, end_lng=13.4050, route_name="Munich-Berlin"),
    SingleRouteRequest(start_lat=54.78431, start_lng=9.43961, end_lat=48.37154, end_lng=10.89851, route_name="Augsburg-Kiel"),
    # SingleRouteRequest(start_lat=51.2277, start_lng=6.7735, end_lat=51.0504, end_lng=13.7373, route_name="Düsseldorf-Dresden"),
    # SingleRouteRequest(start_lat=51.3397, start_lng=12.3731, end_lat=52.3759, end_lng=9.7320, route_name="Leipzig-Hanover"),
    SingleRouteRequest(start_lat=54.78333, start_lng=9.43333, end_lat=48.40108, end_lng=9.98761, route_name="Ulm-Flensburg")
    ]

    
    # Call the wrapper function
    result = calculate_multi_route_with_swaps(route_requests)
    
    if result.success:
        print(f"✅ Optimized {len(result.routes)} routes successfully!")
        print(f"Total Cost: €{result.total_cost_eur:.2f}")
        print(f"Cost Savings: €{result.cost_savings_eur:.2f} ({result.cost_savings_percentage:.1f}%)")
        print(f"Truck Swaps Found: {len(result.truck_swaps)}")
        
        # Print detailed per-route comparisons
        print("\n" + "="*80)
        print("PER-ROUTE COMPARISON ANALYSIS")
        print("="*80)
        
        for comparison in result.route_comparisons:
            print(f"\n {comparison.route_name} (Route {comparison.route_index + 1})")
            print("-" * 60)
            
            # Base vs Optimized
            print(f" COST COMPARISON:")
            print(f"   Base Cost:      €{comparison.base['total_cost_eur']:.2f}")
            print(f"   Optimized Cost: €{comparison.optimized['total_cost_eur']:.2f}")
            print(f"   Savings:        €{comparison.savings['total_cost_eur']:.2f} ({comparison.savings_percentage['total_cost_eur']:.1f}%)")
            
            print(f"\n⏱️  TIME COMPARISON:")
            print(f"   Base Duration:      {comparison.base['duration_minutes']:.0f} minutes")
            print(f"   Optimized Duration: {comparison.optimized['duration_minutes']:.0f} minutes")
            print(f"   Time Change:        {comparison.savings['duration_minutes']:+.0f} minutes ({comparison.savings_percentage['duration_minutes']:+.1f}%)")
            
            print(f"\n🛣️  DISTANCE COMPARISON:")
            print(f"   Base Distance:      {comparison.base['distance_km']:.1f} km")
            print(f"   Optimized Distance: {comparison.optimized['distance_km']:.1f} km")
            print(f"   Distance Change:    {comparison.savings['distance_km']:+.1f} km ({comparison.savings_percentage['distance_km']:+.1f}%)")
            
            print(f"\n🔋 CHARGING COST COMPARISON:")
            print(f"   Base Charging:      €{comparison.base['charging_cost_eur']:.2f}")
            print(f"   Optimized Charging: €{comparison.optimized['charging_cost_eur']:.2f}")
            print(f"   Charging Savings:   €{comparison.savings['charging_cost_eur']:.2f} ({comparison.savings_percentage['charging_cost_eur']:.1f}%)")
            
            print(f"\n👨‍ DRIVER COST COMPARISON:")
            print(f"   Base Driver Cost:      €{comparison.base['driver_cost_eur']:.2f}")
            print(f"   Optimized Driver Cost: €{comparison.optimized['driver_cost_eur']:.2f}")
            print(f"   Driver Cost Savings:   €{comparison.savings['driver_cost_eur']:.2f} ({comparison.savings_percentage['driver_cost_eur']:.1f}%)")
            
            # Show swaps applied to this route
            if comparison.swaps_applied:
                print(f"\n🔄 SWAPS APPLIED TO THIS ROUTE:")
                for swap in comparison.swaps_applied:
                    print(f"   • Driver {swap.driver1_id} ↔ Driver {swap.driver2_id} at Station {swap.station_id}")
                    print(f"     Reason: {swap.reason}, Benefit: {swap.benefit_km:.1f} km")
            else:
                print(f"\n NO SWAPS APPLIED TO THIS ROUTE")
        
        print("\n" + "="*80)
        print("OVERALL SUMMARY")
        print("="*80)
        print(f"Total Routes: {len(result.routes)}")
        print(f"Total Swaps: {len(result.truck_swaps)}")
        print(f"Overall Cost Savings: €{result.cost_savings_eur:.2f} ({result.cost_savings_percentage:.1f}%)")
        
    else:
        print(f"Error: {result.message}")