export interface DetailedRouteSegment {
  segment_number: number;
  start_point: [number, number];
  end_point: [number, number];
  distance_km: number;
  duration_minutes: number;
  energy_consumption_kwh: number;
  coordinates: Array<{
      lat: number;
      lng: number;latitude: number, longitude: number
}>;
  costs: {
    driver_cost_eur: number;
    energy_cost_eur: number;
    depreciation_cost_eur: number;
    tolls_cost_eur: number;
    total_cost_eur: number;
  };
}

export interface DetailedChargingStop {
  stop_number: number;
  charging_station: {
    id: number;
    country: string;
    latitude: number;
    longitude: number;
    truck_suitability: string;
    operator_name: string;
    max_power_kW: number;
    price_per_kWh: number;
  };
  arrival_battery_kwh: number;
  energy_to_charge_kwh: number;
  charging_time_hours: number;
  charging_cost_eur: number;
  departure_battery_kwh: number;
}

export interface RouteCosts {
  driver_cost_eur: number;
  energy_cost_eur: number;
  depreciation_cost_eur: number;
  tolls_cost_eur: number;
  charging_cost_eur: number;
  total_cost_eur: number;
}

export interface SingleRouteWithSegments {
  distance_km: number;
  route_name: string;
  duration_minutes: number;
  coordinates: Array<{
      lat: number;
      lng: number;latitude: number, longitude: number
}>;
  success: boolean;
  message?: string;
  route_segments: DetailedRouteSegment[];
  charging_stops: DetailedChargingStop[];
  total_costs: RouteCosts;
  truck_model: string;
  starting_battery_kwh: number;
  final_battery_kwh: number;
}
