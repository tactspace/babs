export interface ChargingStation {
  id: number;
  country: string;
  latitude: number;
  longitude: number;
  truck_suitability: string; // "yes" or "limited"
  operator_name: string;
  max_power_kW: number;
  price_per_kWh: number;
}
