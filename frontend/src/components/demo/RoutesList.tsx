"use client";

import { Route } from "./DemoPage";
import { Eye, EyeOff, Loader2, ChevronDown, ChevronRight, Zap, Clock, DollarSign, MapPin, Coffee, Moon, AlertCircle } from "lucide-react";
import { useState } from "react";

interface RoutesListProps {
  routes: Route[];
  activeRouteId: string;
  onRouteSelect: (routeId: string) => void;
  onRouteDelete: (routeId: string) => void;
  onClearAll?: () => void;
  showChargingStations: boolean;
  onChargingStationsToggle: () => void;
  loadingChargingStations: boolean;
}

export default function RoutesList({ 
  routes, 
  activeRouteId, 
  onRouteSelect, 
  onRouteDelete, 
  onClearAll,
  showChargingStations,
  onChargingStationsToggle,
  loadingChargingStations
}: RoutesListProps) {
  const [expandedRoutes, setExpandedRoutes] = useState<Set<string>>(new Set());

  const toggleExpanded = (routeId: string) => {
    const newExpanded = new Set(expandedRoutes);
    if (newExpanded.has(routeId)) {
      newExpanded.delete(routeId);
    } else {
      newExpanded.add(routeId);
    }
    setExpandedRoutes(newExpanded);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatBreakDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getBreakIcon = (breakType: string) => {
    switch (breakType) {
      case 'short_break':
        return <Coffee className="w-3 h-3" />;
      case 'long_rest':
        return <Moon className="w-3 h-3" />;
      default:
        return <AlertCircle className="w-3 h-3" />;
    }
  };

  const getBreakColor = (breakType: string) => {
    switch (breakType) {
      case 'short_break':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'long_rest':
        return 'bg-purple-50 border-purple-200 text-purple-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  return (
    <div className="flex-1 px-10 pb-12 overflow-hidden">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Routes</h2>
        <div className="flex items-center gap-3">
          {/* Charging Stations Toggle */}
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Charging Stations</span>
            <button
              onClick={onChargingStationsToggle}
              className="p-1 text-gray-500 hover:text-primary transition-colors"
              title={showChargingStations ? "Hide charging stations" : "Show charging stations"}
              disabled={loadingChargingStations}
            >
              {loadingChargingStations ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : showChargingStations ? (
                <Eye className="w-5 h-5" />
              ) : (
                <EyeOff className="w-5 h-5" />
              )}
            </button>
          </div>
          
          {/* Clear All Button */}
          {routes.length > 0 && (
            <button
              onClick={onClearAll}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 hover:bg-red-200 hover:text-red-800 rounded-md transition-colors border border-red-200"
              title="Clear all routes"
            >
              Clear All
            </button>
          )}
        </div>
      </div>
      
      <div className="space-y-3 overflow-y-auto h-full pb-4">
        {routes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            <p className="text-sm font-medium mb-1">No routes yet</p>
            <p className="text-xs text-gray-400">Add your first route using the form above</p>
          </div>
        ) : (
          routes.map(route => {
            const isExpanded = expandedRoutes.has(route.id);
            const hasRouteData = route.routeData && route.routeData.success;
            
            return (
              <div 
                key={route.id} 
                className={`rounded-md border transition-colors ${
                  route.id === activeRouteId ? 'bg-primary/10 border-primary/30' : 'bg-gray-100 hover:bg-gray-200 border-gray-200'
                }`}
              >
                {/* Main Route Card */}
                <div 
                  className="p-4 cursor-pointer"
                  onClick={() => onRouteSelect(route.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-medium">{route.name}</div>
                      <div className="text-xs text-gray-500 mb-2">
                        {route.start.lat.toFixed(2)}, {route.start.lng.toFixed(2)} → {route.end.lat.toFixed(2)}, {route.end.lng.toFixed(2)}
                      </div>
                      
                      {/* Route Summary */}
                      {hasRouteData && (
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            <span>{route.distance_km?.toFixed(1)} km</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            <span>{formatDuration(route.duration_minutes || 0)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <DollarSign className="w-3 h-3" />
                            <span className="font-medium text-green-600">
                              {formatCurrency(route.routeData?.total_costs?.total_cost_eur || 0)}
                            </span>
                          </div>
                          {route.routeData?.charging_stops && route.routeData.charging_stops.length > 0 && (
                            <div className="flex items-center gap-1">
                              <Zap className="w-3 h-3" />
                              <span>{route.routeData.charging_stops.length} stops</span>
                            </div>
                          )}
                          {route.routeData?.driver_breaks && route.routeData.driver_breaks.length > 0 && (
                            <div className="flex items-center gap-1">
                              <Coffee className="w-3 h-3" />
                              <span>{route.routeData.driver_breaks.length} breaks</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {/* Expand/Collapse Button */}
                      {hasRouteData && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleExpanded(route.id);
                          }}
                          className="p-1 text-gray-500 hover:text-primary transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                      )}
                      
                      {/* Delete Button */}
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          onRouteDelete(route.id);
                        }}
                        className="p-1 text-gray-500 hover:text-red-500 transition-colors"
                        title="Delete route"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && hasRouteData && (
                  <div className="px-4 pb-4 border-t border-gray-200 bg-white/50">
                    <div className="pt-3 space-y-3">
                      {/* EU Compliance Status */}
                      <div className="flex items-center gap-2 text-sm">
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          route.routeData?.eu_compliant 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {route.routeData?.eu_compliant ? 'EU Compliant' : 'Non-Compliant'}
                        </div>
                        {route.routeData?.driver && (
                          <div className="text-xs text-gray-600">
                            Driver: {route.routeData.driver.name || route.routeData.driver.id}
                          </div>
                        )}
                      </div>

                      {/* Truck Info */}
                      <div className="text-sm">
                        <div className="font-medium text-gray-700 mb-1">Truck Model</div>
                        <div className="text-gray-600">{route.routeData?.truck_model}</div>
                        <div className="text-xs text-gray-500">
                          Battery: {route.routeData?.starting_battery_kwh.toFixed(0)}kWh → {route.routeData?.final_battery_kwh.toFixed(0)}kWh
                        </div>
                      </div>

                      {/* Driver Information */}
                      {route.routeData?.driver && (
                        <div className="text-sm">
                          <div className="font-medium text-gray-700 mb-1">Driver Status</div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="flex justify-between">
                              <span>Total Driving:</span>
                              <span>{formatDuration(route.routeData.driver.mins_driven)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Continuous:</span>
                              <span>{formatDuration(route.routeData.driver.continuous_driving_minutes)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Break Time:</span>
                              <span>{formatDuration(route.routeData.driver.breaks_taken_min)}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Cost Breakdown */}
                      <div className="text-sm">
                        <div className="font-medium text-gray-700 mb-2">Cost Breakdown</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex justify-between">
                            <span>Driver:</span>
                            <span>{formatCurrency(route.routeData?.total_costs.driver_cost_eur || 0)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Depreciation:</span>
                            <span>{formatCurrency(route.routeData?.total_costs.depreciation_cost_eur || 0)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Tolls:</span>
                            <span>{formatCurrency(route.routeData?.total_costs.tolls_cost_eur || 0)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Charging:</span>
                            <span>{formatCurrency(route.routeData?.total_costs.charging_cost_eur || 0)}</span>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-200 flex justify-between font-medium">
                          <span>Total:</span>
                          <span className="text-green-600">{formatCurrency(route.routeData?.total_costs.total_cost_eur || 0)}</span>
                        </div>
                      </div>

                      {/* Driver Breaks */}
                      {route.routeData?.driver_breaks && route.routeData.driver_breaks.length > 0 && (
                        <div className="text-sm">
                          <div className="font-medium text-gray-700 mb-2">Driver Breaks</div>
                          <div className="space-y-2">
                            {route.routeData.driver_breaks.map((breakItem, index) => (
                              <div key={index} className={`p-2 rounded border text-xs ${getBreakColor(breakItem.break_type)}`}>
                                <div className="flex items-center gap-2 mb-1">
                                  {getBreakIcon(breakItem.break_type)}
                                  <span className="font-medium capitalize">
                                    {breakItem.break_type.replace('_', ' ')} #{breakItem.break_number}
                                  </span>
                                </div>
                                <div className="text-gray-600 mb-1">{breakItem.reason}</div>
                                <div className="flex justify-between items-center">
                                  <span>Duration: {formatBreakDuration(breakItem.duration_minutes)}</span>
                                  <span>Start: {formatDuration(breakItem.start_time_minutes)}</span>
                                </div>
                                {breakItem.charging_station && (
                                  <div className="mt-1 text-xs opacity-75">
                                    At: {breakItem.charging_station.operator_name}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Route Segments */}
                      {route.routeData?.route_segments && route.routeData.route_segments.length > 0 && (
                        <div className="text-sm">
                          <div className="font-medium text-gray-700 mb-2">Route Segments</div>
                          <div className="space-y-2">
                            {route.routeData.route_segments.map((segment, index) => (
                              <div key={index} className="bg-gray-50 p-2 rounded text-xs">
                                <div className="font-medium">Segment {segment.segment_number}</div>
                                <div className="flex justify-between mt-1">
                                  <span>{segment.distance_km.toFixed(1)} km</span>
                                  <span>{formatDuration(segment.duration_minutes)}</span>
                                  <span>{formatCurrency(segment.costs.total_cost_eur)}</span>
                                </div>
                                {segment.driver_id && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    Driver: {segment.driver_id}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Charging Stops */}
                      {route.routeData?.charging_stops && route.routeData.charging_stops.length > 0 && (
                        <div className="text-sm">
                          <div className="font-medium text-gray-700 mb-2">Charging Stops</div>
                          <div className="space-y-2">
                            {route.routeData.charging_stops.map((stop, index) => (
                              <div key={index} className="bg-blue-50 p-2 rounded text-xs">
                                <div className="font-medium">{stop.charging_station.operator_name}</div>
                                <div className="text-gray-600">{stop.charging_station.max_power_kW}kW</div>
                                <div className="flex justify-between mt-1">
                                  <span>{stop.charging_time_hours.toFixed(1)}h</span>
                                  <span>{formatCurrency(stop.charging_cost_eur)}</span>
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                  Battery: {stop.arrival_battery_kwh.toFixed(0)}kWh → {stop.departure_battery_kwh.toFixed(0)}kWh
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
