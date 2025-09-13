from typing import List, Tuple
from models import RouteRequest, RouteResult, RouteSegment, DriverBreak, DriverBreakType, ChargingStop, ChargingStation
from charging_stations import calculate_distance
from trucks import load_truck_specs, calculate_energy_consumption


AVG_TRUCK_SPEED_KMH = 70.0  # simplified average speed


def _build_straight_route_points(start: Tuple[float, float], end: Tuple[float, float], steps: int = 20) -> List[Tuple[float, float]]:
    lat1, lon1 = start
    lat2, lon2 = end
    points: List[Tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        points.append((lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t))
    return points


def _estimate_breaks(total_duration_s: float, points: List[Tuple[float, float]]) -> List[DriverBreak]:
    # very simple: add a short break every 4.5h, long rest every 9h
    breaks: List[DriverBreak] = []
    time = 0.0
    next_short = 4.5 * 3600
    next_long = 9.0 * 3600
    while next_short < total_duration_s or next_long < total_duration_s:
        idx = min(int((time / total_duration_s) * (len(points) - 1)), len(points) - 1) if total_duration_s > 0 else 0
        location = points[idx]
        if next_long <= time + 1e-6:
            breaks.append(DriverBreak(break_type=DriverBreakType.LONG_REST, location=location, start_time=time, duration=11 * 3600))
            next_long += 9.0 * 3600
        elif next_short <= time + 1e-6:
            breaks.append(DriverBreak(break_type=DriverBreakType.SHORT_BREAK, location=location, start_time=time, duration=45 * 60))
            next_short += 4.5 * 3600
        time += 3600  # advance by 1h chunk to place markers roughly
        if time > total_duration_s:
            break
    return breaks


def find_optimal_route(request: RouteRequest) -> RouteResult:
    start = request.start_point
    end = request.end_point

    # Straight-line distance (km)
    distance_km = calculate_distance(start, end)
    total_distance_m = distance_km * 1000.0

    # Duration in seconds (average speed)
    duration_hours = distance_km / max(AVG_TRUCK_SPEED_KMH, 1e-3)
    driving_duration_s = duration_hours * 3600.0

    # Simple energy estimate using selected truck
    trucks = load_truck_specs("data/truck_specs.csv")
    truck = trucks.get(request.truck_model)
    if truck is None:
        # fallback: pick any truck
        truck = next(iter(trucks.values()))
    energy_kwh = calculate_energy_consumption(distance_km, truck)

    # Build straight polyline into segments
    points = _build_straight_route_points(start, end)
    segments: List[RouteSegment] = []
    if len(points) >= 2:
        seg_dist_total = 0.0
        for i in range(len(points) - 1):
            sp = points[i]
            ep = points[i + 1]
            seg_km = calculate_distance(sp, ep)
            seg_dist_total += seg_km
            seg_hours = seg_km / max(AVG_TRUCK_SPEED_KMH, 1e-3)
            segments.append(
                RouteSegment(
                    start_point=sp,
                    end_point=ep,
                    distance=seg_km * 1000.0,
                    duration=seg_hours * 3600.0,
                    energy_consumption=calculate_energy_consumption(seg_km, truck),
                )
            )

    # Breaks (rough visualization only)
    driver_breaks = _estimate_breaks(driving_duration_s, points)

    # No charging logic implemented; return empty list and zero cost for now
    charging_stops: List[ChargingStop] = []
    total_cost_eur = 0.0

    result = RouteResult(
        total_distance=total_distance_m,
        total_duration=driving_duration_s + sum(b.duration for b in driver_breaks),
        driving_duration=driving_duration_s,
        total_energy_consumption=energy_kwh,
        total_cost=total_cost_eur,
        route_segments=segments,
        driver_breaks=driver_breaks,
        charging_stops=charging_stops,
        feasible=True,
    )
    return result


