"use client";

import React, { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { RouteLayer, DriverBreak } from "@/components/sim-map";

const SimMap = dynamic(() => import("@/components/sim-map").then(m => m.SimMap), { ssr: false });

type TruckMap = Record<string, {
  manufacturer: string;
  model: string;
  battery_capacity: number;
  consumption: number;
  range: number;
}>;

type RouteRequest = {
  start_point: [number, number];
  end_point: [number, number];
  truck_model: string;
  initial_battery_level?: number | null;
  optimize_by?: "time" | "cost";
  num_drivers?: number;
  optimize_swaps?: boolean;  // Add this line
  driver_ids?: string[];     // Add this line
};

type RouteSegment = { start_point: [number, number]; end_point: [number, number]; distance: number; duration: number; energy_consumption: number };
type ChargingStationLite = { latitude: number; longitude: number };
type ChargingStop = { charging_station: ChargingStationLite; arrival_battery_level: number; departure_battery_level: number; charging_time: number; charging_cost: number };
type DriverSwap = { location: [number, number]; time: number; reason?: string };
type RouteResult = {
  total_distance: number;
  total_duration: number;
  driving_duration: number;
  total_energy_consumption: number;
  total_cost: number;
  route_segments: RouteSegment[];
  driver_breaks: DriverBreak[];
  charging_stops: ChargingStop[];
  nearby_charging_stations?: { latitude: number; longitude: number }[];
  feasible: boolean;
  driver_swaps?: DriverSwap[];
};

type RouteEntry = {
  id: string;
  startLat: string;
  startLng: string;
  endLat: string;
  endLng: string;
  truck: string;
  optimizeBy: "time" | "cost";
  numDrivers: number;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

// Predefined locations (just lat/lng points)
const predefinedLocations = [
  { lat: "53.83249", lng: "10.65118" },
  { lat: "48.1411754", lng: "11.7367876" },
  { lat: "48.04249", lng: "10.6203" },
  { lat: "53.84584", lng: "9.93593" },
  { lat: "49.92372", lng: "7.82567" },
  { lat: "52.17403", lng: "11.49524" },
  { lat: "50.86574", lng: "11.7726" },
  { lat: "49.84", lng: "8.14348" },
];

export default function SimulatePage() {
  const [trucks, setTrucks] = React.useState<TruckMap>({});
  const [entries, setEntries] = useState<RouteEntry[]>([]);
  const [drivers, setDrivers] = useState<Record<string, { id: string; name: string }>>({});
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, RouteResult | { error: string }>>({});
  const [tab, setTab] = useState<"time" | "cost">("time");
  const [isOptimizing, setIsOptimizing] = useState(false);

  // Add these state variables to the SimulatePage component
  const [simulationResults, setSimulationResults] = useState<Record<string, RouteResult | { error: string }>>({});
  const [optimizationResults, setOptimizationResults] = useState<Record<string, RouteResult | { error: string }>>({});
  const [activeMode, setActiveMode] = useState<"none" | "simulation" | "optimization">("none");

  React.useEffect(() => {
    fetch(`${apiBase}/trucks`).then(r => r.json()).then((data: TruckMap) => setTrucks(data)).catch(() => {});
    fetch(`${apiBase}/drivers`).then(r => r.json()).then((data: Record<string, { id: string; name: string }>) => setDrivers(data)).catch(() => {});
    
    // Create 5 initial routes from predefined locations
    const initialRoutes: RouteEntry[] = [
      // Route 1: Location 0 to Location 1
      {
        id: crypto.randomUUID(),
        startLat: predefinedLocations[0].lat,
        startLng: predefinedLocations[0].lng,
        endLat: predefinedLocations[1].lat,
        endLng: predefinedLocations[1].lng,
        truck: "",
        optimizeBy: "time",
        numDrivers: 1
      },
      // Route 2: Location 1 to Location 2
      {
        id: crypto.randomUUID(),
        startLat: predefinedLocations[1].lat,
        startLng: predefinedLocations[1].lng,
        endLat: predefinedLocations[2].lat,
        endLng: predefinedLocations[2].lng,
        truck: "",
        optimizeBy: "cost",
        numDrivers: 1
      },
      // Route 3: Location 2 to Location 3
      {
        id: crypto.randomUUID(),
        startLat: predefinedLocations[2].lat,
        startLng: predefinedLocations[2].lng,
        endLat: predefinedLocations[3].lat,
        endLng: predefinedLocations[3].lng,
        truck: "",
        optimizeBy: "time",
        numDrivers: 2
      },
      // Route 4: Location 3 to Location 4
      {
        id: crypto.randomUUID(),
        startLat: predefinedLocations[3].lat,
        startLng: predefinedLocations[3].lng,
        endLat: predefinedLocations[4].lat,
        endLng: predefinedLocations[4].lng,
        truck: "",
        optimizeBy: "cost",
        numDrivers: 1
      },
      // Route 5: Location 4 to Location 5
      {
        id: crypto.randomUUID(),
        startLat: predefinedLocations[4].lat,
        startLng: predefinedLocations[4].lng,
        endLat: predefinedLocations[5].lat,
        endLng: predefinedLocations[5].lng,
        truck: "",
        optimizeBy: "time",
        numDrivers: 2
      }
    ];
    
    setEntries(initialRoutes);
  }, []);

  const truckKeys = useMemo(() => Object.keys(trucks), [trucks]);

  function updateEntry(id: string, patch: Partial<RouteEntry>) {
    setEntries(prev => prev.map(e => e.id === id ? { ...e, ...patch } : e));
  }

  function addEntry() {
    setEntries(prev => [...prev, { id: crypto.randomUUID(), startLat: "", startLng: "", endLat: "", endLng: "", truck: truckKeys[0] || "", optimizeBy: tab, numDrivers: 1 }]);
  }

  function removeEntry(id: string) {
    setEntries(prev => prev.filter(e => e.id !== id));
  }

  // Separate functions for each button
  async function runOptimization() {
    if (loading || activeMode === "simulation") return;
    
    setLoading(true);
    setActiveMode("optimization");
    setIsOptimizing(true);
    
    const out: Record<string, RouteResult | { error: string }> = {};
    
    // Optimization logic
    for (const e of entries) {
      try {
        const body: RouteRequest = {
          start_point: [Number(e.startLat), Number(e.startLng)],
          end_point: [Number(e.endLat), Number(e.endLng)],
          truck_model: e.truck || truckKeys[0],
          optimize_by: e.optimizeBy,
          num_drivers: e.numDrivers,
          optimize_swaps: true,
        };
        
        const res = await fetch(`${apiBase}/optimize`, { 
          method: "POST", 
          headers: { "Content-Type": "application/json" }, 
          body: JSON.stringify(body) 
        });
        
        if (!res.ok) throw new Error(await res.text());
        out[e.id] = await res.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed";
        out[e.id] = { error: message };
      }
    }
    
    setOptimizationResults(out);
    setResults(out);
    setLoading(false);
  }

  async function runSimulation() {
    if (loading || activeMode === "optimization") return;
    
    setLoading(true);
    setActiveMode("simulation");
    setIsOptimizing(false);
    
    const out: Record<string, RouteResult | { error: string }> = {};
    
    // Simulation logic
    try {
      const routes = entries.map(e => ({
        start_point: [Number(e.startLat), Number(e.startLng)],
        end_point: [Number(e.endLat), Number(e.endLng)],
        truck_type: "electric"
      }));
      
      const res = await fetch(`${apiBase}/multi-route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ routes })
      });
      
      if (!res.ok) throw new Error(await res.text());
      const multiResult = await res.json();
      
      entries.forEach((e, idx) => {
        if (idx < multiResult.routes.length) {
          out[e.id] = multiResult.routes[idx];
        }
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed";
      entries.forEach(e => {
        out[e.id] = { error: message };
      });
    }
    
    setSimulationResults(out);
    setResults(out);
    setLoading(false);
  }

  const sortedEntries = useMemo(() => {
    const copy = [...entries];
    copy.sort((a, b) => {
      const ra = results[a.id] as RouteResult | undefined;
      const rb = results[b.id] as RouteResult | undefined;
      if (!ra || !rb) return 0;
      return tab === "time" ? (ra.total_duration - rb.total_duration) : (ra.total_cost - rb.total_cost);
    });
    return copy;
  }, [entries, results, tab]);

  // Helper function to find location name by coordinates
  const getLocationName = (lat: string, lng: string) => {
    const location = predefinedLocations.find(loc => loc.lat === lat && loc.lng === lng);
    return location?.name || `${lat}, ${lng}`;
  };

  const mapPoints = useMemo(() => {
    // Extract all unique points from entries
    const points = new Set<string>();
    entries.forEach(entry => {
      points.add(`${entry.startLat},${entry.startLng}`);
      points.add(`${entry.endLat},${entry.endLng}`);
    });
    
    // Convert to array of point objects
    return Array.from(points).map(pointStr => {
      const [lat, lng] = pointStr.split(',');
      return {
        position: [Number(lat), Number(lng)] as [number, number],
        name: getLocationName(lat, lng)
      };
    });
  }, [entries]);

  const layers: RouteLayer[] = useMemo(() => {
    const colors = ["#3b82f6", "#ef4444", "#22c55e", "#a855f7", "#f59e0b"];
    return entries.map((e, idx) => {
      const r = results[e.id] as RouteResult | undefined;
      const coords: [number, number][] = [];
      if (r?.route_segments?.length) {
        r.route_segments.forEach(seg => {
          coords.push(seg.start_point);
          coords.push(seg.end_point);
        });
      } else {
        // fallback to straight line if no segments
        if (e.startLat && e.startLng && e.endLat && e.endLng) {
          coords.push([Number(e.startLat), Number(e.startLng)]);
          coords.push([Number(e.endLat), Number(e.endLng)]);
        }
      }
      const chargingStops = (r?.charging_stops || []).map(s => [s.charging_station.latitude, s.charging_station.longitude]) as [number, number][];
      const swapEvents = (r?.driver_swaps || []).map(sw => ({ location: sw.location as [number, number], time: sw.time, reason: sw.reason })) as DriverSwap[];
      const swap = swapEvents?.[0]?.location as [number, number] | undefined;
      const nearby = (r?.nearby_charging_stations || []).map(s => [s.latitude, s.longitude]) as [number, number][];

      return {
        id: e.id,
        color: colors[idx % colors.length],
        line: coords,
        chargingStops,
        driverBreaks: (r?.driver_breaks || []) as DriverBreak[],
        nearbyChargers: nearby,
        swapEvents,
        swapPoint: swap,
        startPoint: [Number(e.startLat), Number(e.startLng)] as [number, number],
        endPoint: [Number(e.endLat), Number(e.endLng)] as [number, number],
        startName: getLocationName(e.startLat, e.startLng),
        endName: getLocationName(e.endLat, e.endLng),
        mode: activeMode as "simulation" | "optimization", // Add this line
      } satisfies RouteLayer;
    });
  }, [entries, results, activeMode]); // Add activeMode to the dependency array

  return (
    <div className="min-h-screen container mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Route Simulation</h1>
        <div className="inline-flex rounded-md border overflow-hidden">
          <button onClick={() => setTab("time")} className={`px-3 py-1 text-sm ${tab === "time" ? "bg-primary text-primary-foreground" : "bg-background"}`}>Optimize by Time</button>
          <button onClick={() => setTab("cost")} className={`px-3 py-1 text-sm ${tab === "cost" ? "bg-primary text-primary-foreground" : "bg-background"}`}>Optimize by Cost</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2">
          <div className="rounded-lg border p-4 space-y-4 bg-card mb-4">
            <h2 className="text-lg font-medium">Predefined Routes</h2>
            <div className="space-y-3">
              {entries.map((e, idx) => (
                <div key={e.id} className="p-3 border rounded-md bg-background">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium">Route {idx + 1}</div>
                    <div className="text-xs px-2 py-1 rounded bg-muted">
                      {e.optimizeBy === "time" ? "Fastest" : "Cheapest"}
                    </div>
                  </div>
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    <div className="flex items-center">
                      <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white text-xs mr-2">A</div>
                      <div>{getLocationName(e.startLat, e.startLng)}</div>
                    </div>
                    <div className="flex items-center">
                      <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center text-white text-xs mr-2">B</div>
                      <div>{getLocationName(e.endLat, e.endLng)}</div>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    {e.numDrivers} driver{e.numDrivers > 1 ? 's' : ''}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-3 mt-4">
              <button 
                onClick={runOptimization} 
                disabled={loading || entries.length === 0 || activeMode === "simulation"} 
                className={`inline-flex items-center justify-center rounded-md text-sm font-medium ${activeMode === "optimization" ? "bg-green-600" : "bg-primary"} text-primary-foreground hover:opacity-90 h-9 px-4 disabled:opacity-50 flex-1`}
              >
                {loading && isOptimizing ? "Optimizing..." : "Optimize"}
              </button>
              <button 
                onClick={runSimulation} 
                disabled={loading || entries.length === 0 || activeMode === "optimization"} 
                className={`inline-flex items-center justify-center rounded-md text-sm font-medium ${activeMode === "simulation" ? "bg-green-600" : "bg-primary"} text-primary-foreground hover:opacity-90 h-9 px-4 disabled:opacity-50 flex-1`}
              >
                {loading && !isOptimizing ? "Simulating..." : "Run Simulation"}
              </button>
            </div>
            {activeMode !== "none" && (
              <button
                onClick={() => {
                  setActiveMode("none");
                  setResults({});
                }}
                className="mt-2 text-xs text-blue-600 hover:underline"
              >
                Reset and compare again
              </button>
            )}
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="h-[520px] rounded-lg overflow-hidden border bg-muted/30">
            <SimMap layers={layers} points={mapPoints} />
          </div>
          <div className="mt-4 grid gap-3">
            {sortedEntries.map((e) => {
              const simResult = simulationResults[e.id] as RouteResult | { error: string } | undefined;
              const optResult = optimizationResults[e.id] as RouteResult | { error: string } | undefined;
              const r = results[e.id] as RouteResult | { error: string } | undefined;
              
              return (
                <div key={e.id} className="rounded-lg border p-4 bg-card text-sm">
                  <div className="font-medium">Route {entries.findIndex(x => x.id === e.id) + 1}: {getLocationName(e.startLat, e.startLng)} to {getLocationName(e.endLat, e.endLng)}</div>
                  
                  {r && "error" in r ? (
                    <div className="text-red-600">{String(r.error)}</div>
                  ) : r ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-2">
                        <div>Duration: {(r.total_duration / 3600).toFixed(2)} h</div>
                        <div>Cost: € {r.total_cost?.toFixed?.(2) ?? r.total_cost}</div>
                        <div>Distance: {(r.total_distance / 1000).toFixed(1)} km</div>
                        <div>Energy: {r.total_energy_consumption?.toFixed?.(1) ?? r.total_energy_consumption} kWh</div>
                      </div>
                      
                      {/* Show comparison if both results are available */}
                      {simResult && !("error" in simResult) && optResult && !("error" in optResult) && (
                        <div className="mt-3 p-2 bg-muted/30 rounded-md">
                          <div className="font-medium mb-1">Comparison</div>
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <div></div>
                            <div className="font-medium">Simulation</div>
                            <div className="font-medium">Optimization</div>
                            
                            <div>Duration:</div>
                            <div>{(simResult.total_duration / 3600).toFixed(2)} h</div>
                            <div className={optResult.total_duration < simResult.total_duration ? "text-green-600 font-medium" : ""}>
                              {(optResult.total_duration / 3600).toFixed(2)} h
                              {optResult.total_duration < simResult.total_duration && 
                                ` (${(100 - (optResult.total_duration / simResult.total_duration) * 100).toFixed(1)}% faster)`}
                            </div>
                            
                            <div>Cost:</div>
                            <div>€ {simResult.total_cost?.toFixed?.(2) ?? simResult.total_cost}</div>
                            <div className={optResult.total_cost < simResult.total_cost ? "text-green-600 font-medium" : ""}>
                              € {optResult.total_cost?.toFixed?.(2) ?? optResult.total_cost}
                              {optResult.total_cost < simResult.total_cost && 
                                ` (${(100 - (optResult.total_cost / simResult.total_cost) * 100).toFixed(1)}% cheaper)`}
                            </div>
                            
                            <div>Energy:</div>
                            <div>{simResult.total_energy_consumption?.toFixed?.(1) ?? simResult.total_energy_consumption} kWh</div>
                            <div>{optResult.total_energy_consumption?.toFixed?.(1) ?? optResult.total_energy_consumption} kWh</div>
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <div className="font-medium mb-1">Charging decisions</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {(r.charging_stops || []).map((cs, idx) => (
                            <li key={idx}>
                              At {cs.charging_station.name || `Station #${cs.charging_station.id}`}: +{(cs.departure_battery_level - cs.arrival_battery_level).toFixed(1)} kWh, {(cs.charging_time/60).toFixed(0)} min, €{cs.charging_cost.toFixed(2)}
                            </li>
                          ))}
                          {(!r.charging_stops || r.charging_stops.length === 0) && <li className="opacity-70">No charging required</li>}
                        </ul>
                      </div>
                      
                      <div>
                        <div className="font-medium mb-1">Driver breaks</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {(r.driver_breaks || []).map((brk, idx) => (
                            <li key={idx}>
                              {brk.break_type === "short_break" ? "Short break" : "Long rest"} at {(brk.start_time/3600).toFixed(1)}h 
                              {activeMode === "simulation" && " near "}
                              {activeMode === "simulation" && 
                                getNearestStationName(brk.location, r.nearby_charging_stations || [])}
                              {activeMode === "simulation" ? "" : ` (${(brk.duration/60).toFixed(0)} min)`}
                            </li>
                          ))}
                          {(!r.driver_breaks || r.driver_breaks.length === 0) && <li className="opacity-70">No breaks required</li>}
                        </ul>
                      </div>
                      
                      {/* Only show driver swaps for optimization mode */}
                      {activeMode === "optimization" && (
                        <div>
                          <div className="font-medium mb-1">Driver swaps</div>
                          <ul className="list-disc pl-5 space-y-1">
                            {(r.driver_swaps || []).map((sw, idx) => (
                              <li key={idx}>At {(sw.time/3600).toFixed(1)}h near {sw.location[0].toFixed(3)},{sw.location[1].toFixed(3)}{sw.reason ? ` — ${sw.reason}` : ""}</li>
                            ))}
                            {(!r.driver_swaps || r.driver_swaps.length === 0) && <li className="opacity-70">No swaps scheduled</li>}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="opacity-60">No result yet</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// Add this helper function to find the nearest station name
function getNearestStationName(location: [number, number], stations: any[]): string {
  if (!stations || stations.length === 0) return `${location[0].toFixed(3)},${location[1].toFixed(3)}`;
  
  let nearestStation = stations[0];
  let minDistance = calculateDistance(location, [stations[0].latitude, stations[0].longitude]);
  
  for (const station of stations) {
    const distance = calculateDistance(location, [station.latitude, station.longitude]);
    if (distance < minDistance) {
      minDistance = distance;
      nearestStation = station;
    }
  }
  
  return nearestStation.name || `Station #${nearestStation.id}`;
}

// Add this helper function to calculate distance between two points
function calculateDistance(point1: [number, number], point2: [number, number]): number {
  const R = 6371; // Earth's radius in km
  const dLat = (point2[0] - point1[0]) * Math.PI / 180;
  const dLon = (point2[1] - point1[1]) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(point1[0] * Math.PI / 180) * Math.cos(point2[0] * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}


