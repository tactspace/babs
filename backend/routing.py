from typing import List, Tuple
from models import RouteRequest, RouteResult, RouteSegment, DriverBreak, DriverBreakType, ChargingStop, DriverSwap, ChargingStation
from charging_stations import calculate_distance, find_nearest_charging_stations
from tomtom import get_route
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


def _assign_swaps(points: List[Tuple[float, float]], duration_s: float, num_drivers: int, nearby_chargers: List[ChargingStation]) -> List[DriverSwap]:
    if num_drivers <= 1 or duration_s <= 0:
        return []
    swaps: List[DriverSwap] = []
    interval = 4.5 * 3600
    t = interval
    while t < duration_s:
        idx = min(int((t / duration_s) * (len(points) - 1)), len(points) - 1)
        target = points[idx]
        # snap to closest nearby charger
        best_loc = target
        if nearby_chargers:
            best = None
            best_d = 1e9
            for st in nearby_chargers:
                d = calculate_distance(target, (st.latitude, st.longitude))
                if d < best_d:
                    best_d = d
                    best = st
            if best is not None:
                best_loc = (best.latitude, best.longitude)
        swaps.append(DriverSwap(location=best_loc, time=t))
        t += interval
    return swaps


def find_optimal_route(request: RouteRequest) -> RouteResult:
    start = request.start_point
    end = request.end_point

    # Fetch route from TomTom
    route_type = "fastest" if request.optimize_by != "cost" else "shortest"
    tt = get_route(start, end, vehicle_type="truck", route_type=route_type)
    if not tt or "coordinates" not in tt:
        # Fallback to straight line
        distance_km = calculate_distance(start, end)
        total_distance_m = distance_km * 1000.0
        duration_hours = distance_km / max(AVG_TRUCK_SPEED_KMH, 1e-3)
        driving_duration_s = duration_hours * 3600.0
        points = _build_straight_route_points(start, end)
    else:
        total_distance_m = float(tt["distance"]) or 0.0
        driving_duration_s = float(tt["duration"]) or 0.0
        # TomTom points are dicts with latitude/longitude
        points = [(p["latitude"], p["longitude"]) for p in tt["coordinates"]]

    # Simple energy estimate using selected truck
    trucks = load_truck_specs("data/truck_specs.csv")
    truck = trucks.get(request.truck_model)
    if truck is None:
        # fallback: pick any truck
        truck = next(iter(trucks.values()))
    # Use total_distance_m from TomTom (or fallback) to compute energy
    distance_km_for_energy = (total_distance_m or 0.0) / 1000.0
    energy_kwh = calculate_energy_consumption(distance_km_for_energy, truck)

    segments: List[RouteSegment] = []
    if len(points) >= 2:
        for i in range(len(points) - 1):
            sp = points[i]
            ep = points[i + 1]
            seg_km = calculate_distance(sp, ep)
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

    # Simple charging visualization: find few chargers near the path (sample every ~50km)
    # For now we do not simulate battery state; we just propose nearby chargers and pick swap at first charger after 4.5h
    charging_stops: List[ChargingStop] = []
    nearby_chargers: List[ChargingStation] = []
    try:
        from main import charging_stations as ALL_STATIONS  # loaded at startup
        if points:
            sample_indices = [0]
            step = max(1, int(len(points) / 10))
            sample_indices += list(range(step, len(points), step))
            for idx in sample_indices:
                pt = points[min(idx, len(points) - 1)]
                near = find_nearest_charging_stations(pt, ALL_STATIONS, max_distance=30.0, truck_suitable_only=True, limit=2)
                for st in near:
                    if all(x.id != st.id for x in nearby_chargers):
                        nearby_chargers.append(st)
    except Exception:
        pass

    # EV charging planning: simulate battery and charge when needed
    battery_capacity = truck.battery_capacity
    reserve_kwh = 0.1 * battery_capacity
    current_battery = request.initial_battery_level if (request.initial_battery_level is not None) else battery_capacity
    optimize_by = (request.optimize_by or "time").lower()
    max_power_kW = 250.0  # vehicle max charge power cap
    total_charging_time_s = 0.0
    elapsed_time_s = 0.0
    time_since_last_swap_s = 0.0
    battery_trace: list[dict] = []

    def pick_station(location: Tuple[float, float], energy_to_add: float) -> ChargingStation | None:
        try:
            from main import charging_stations as ALL_STATIONS
        except Exception:
            return None
        candidates = find_nearest_charging_stations(location, ALL_STATIONS, max_distance=50.0, truck_suitable_only=True, limit=5)
        if not candidates:
            candidates = find_nearest_charging_stations(location, ALL_STATIONS, max_distance=80.0, truck_suitable_only=True, limit=5)
        if not candidates:
            # As a fallback, include stations with limited suitability
            candidates = find_nearest_charging_stations(location, ALL_STATIONS, max_distance=80.0, truck_suitable_only=False, limit=5)
        best = None
        best_score = 1e18
        for st in candidates:
            power = max(1.0, min(max_power_kW, st.max_power_kW))
            time_h = (energy_to_add / power) if energy_to_add > 0 else 0.0
            cost = max(0.0, energy_to_add) * st.price_per_kWh
            score = time_h if optimize_by == "time" else cost
            if score < best_score:
                best_score = score
                best = st
        return best

    for seg in segments:
        seg_energy = seg.energy_consumption
        # Charge before segment if needed to keep reserve
        if current_battery - seg_energy < reserve_kwh:
            target_soc = 0.6 if optimize_by == "time" else 0.9
            target_level = max(current_battery, target_soc * battery_capacity)
            min_needed = reserve_kwh + seg_energy
            if target_level < min_needed:
                target_level = min(battery_capacity, min_needed + 0.05 * battery_capacity)
            energy_to_add = max(0.0, min(target_level - current_battery, battery_capacity - current_battery))
            if energy_to_add > 0.0:
                st = pick_station(seg.start_point, energy_to_add)
                if st is not None:
                    power = max(1.0, min(max_power_kW, st.max_power_kW))
                    charge_time_s = (energy_to_add / power) * 3600.0
                    charge_cost = energy_to_add * st.price_per_kWh
                    charging_stops.append(ChargingStop(
                        charging_station=st,
                        arrival_battery_level=current_battery,
                        departure_battery_level=current_battery + energy_to_add,
                        charging_time=charge_time_s,
                        charging_cost=charge_cost,
                        reason=f"Charge {energy_to_add:.1f} kWh to reach target SOC for next segment (strategy: {optimize_by}).",
                    ))
                    # Swap at charging if >4.5h driving elapsed and have multiple drivers
                    if int(request.num_drivers or 1) > 1 and time_since_last_swap_s >= 4.5 * 3600:
                        driver_swaps.append(DriverSwap(location=(st.latitude, st.longitude), time=elapsed_time_s, reason="Driver swap during charging after 4.5h driving."))
                        time_since_last_swap_s = 0.0
                    current_battery += energy_to_add
                    total_charging_time_s += charge_time_s
                    elapsed_time_s += charge_time_s
                    battery_trace.append({
                        "location": (st.latitude, st.longitude),
                        "time": elapsed_time_s,
                        "battery_kwh": current_battery,
                        "soc_percent": (current_battery / battery_capacity) * 100.0,
                        "event": "charge"
                    })
        # Drive segment
        current_battery -= seg_energy
        elapsed_time_s += seg.duration
        time_since_last_swap_s += seg.duration
        # record end-of-segment battery
        battery_trace.append({
            "location": seg.end_point,
            "time": elapsed_time_s,
            "battery_kwh": current_battery,
            "soc_percent": (current_battery / battery_capacity) * 100.0,
            "event": "drive"
        })

    # If arriving below reserve, top-up near destination to maintain reserve buffer
    if current_battery < reserve_kwh:
        need = reserve_kwh - current_battery
        st = pick_station(points[-1], need)
        if st is not None and need > 0:
            power = max(1.0, min(max_power_kW, st.max_power_kW))
            charge_time_s = (need / power) * 3600.0
            charge_cost = need * st.price_per_kWh
            charging_stops.append(ChargingStop(
                charging_station=st,
                arrival_battery_level=current_battery,
                departure_battery_level=current_battery + need,
                charging_time=charge_time_s,
                charging_cost=charge_cost,
                reason="Top-up near destination to keep reserve buffer."
            ))
            current_battery += need
            total_charging_time_s += charge_time_s
            elapsed_time_s += charge_time_s
            battery_trace.append({
                "location": (st.latitude, st.longitude),
                "time": elapsed_time_s,
                "battery_kwh": current_battery,
                "soc_percent": (current_battery / battery_capacity) * 100.0,
                "event": "charge"
            })

    # Total energy cost equals sum of charging costs
    total_cost_eur = sum(cs.charging_cost for cs in charging_stops) if charging_stops else 0.0

    # If no swaps scheduled via charging, snap to nearby chargers at 4.5h cadence
    if 'driver_swaps' not in locals() or len(driver_swaps) == 0:
        driver_swaps = _assign_swaps(points, driving_duration_s, int(request.num_drivers or 1), nearby_chargers)

    result = RouteResult(
        total_distance=total_distance_m,
        total_duration=driving_duration_s + sum(b.duration for b in driver_breaks) + total_charging_time_s,
        driving_duration=driving_duration_s,
        total_energy_consumption=energy_kwh,
        total_cost=total_cost_eur,
        route_segments=segments,
        driver_breaks=driver_breaks,
        charging_stops=charging_stops,
        driver_swaps=driver_swaps,
        nearby_charging_stations=nearby_chargers,
        battery_capacity_kwh=battery_capacity,
        battery_trace=battery_trace,
        feasible=True,
    )
    return result


