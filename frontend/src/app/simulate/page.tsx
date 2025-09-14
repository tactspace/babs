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

export default function SimulatePage() {
  const [trucks, setTrucks] = React.useState<TruckMap>({});
  const [entries, setEntries] = useState<RouteEntry[]>([
    { id: crypto.randomUUID(), startLat: "52.52", startLng: "13.405", endLat: "48.137", endLng: "11.575", truck: "", optimizeBy: "time", numDrivers: 1 },
  ]);
  const [drivers, setDrivers] = useState<Record<string, { id: string; name: string }>>({});
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, RouteResult | { error: string }>>({});
  const [tab, setTab] = useState<"time" | "cost">("time");

  React.useEffect(() => {
    fetch(`${apiBase}/trucks`).then(r => r.json()).then((data: TruckMap) => setTrucks(data)).catch(() => {});
    fetch(`${apiBase}/drivers`).then(r => r.json()).then((data: Record<string, { id: string; name: string }>) => setDrivers(data)).catch(() => {});
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

  async function runSimulations() {
    setLoading(true);
    const out: Record<string, RouteResult | { error: string }> = {};
    for (const e of entries) {
      try {
        const body: RouteRequest = {
          start_point: [Number(e.startLat), Number(e.startLng)],
          end_point: [Number(e.endLat), Number(e.endLng)],
          truck_model: e.truck || truckKeys[0],
          optimize_by: e.optimizeBy,
          num_drivers: e.numDrivers,
        };
        const res = await fetch(`${apiBase}/route`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        if (!res.ok) throw new Error(await res.text());
        out[e.id] = await res.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed";
        out[e.id] = { error: message };
      }
    }
    setResults(out);
    setLoading(false);
  }

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

      // naive driver swap: midpoint of polyline or between start/end
      let swapPoint: [number, number] | null = null;
      const poly = coords;
      if (poly.length >= 2) {
        const mid = Math.floor(poly.length / 2);
        swapPoint = poly[mid];
      }

      return {
        id: e.id,
        color: colors[idx % colors.length],
        line: coords,
        chargingStops,
        driverBreaks: (r?.driver_breaks || []) as DriverBreak[],
        nearbyChargers: nearby,
        swapEvents,
        swapPoint: swap ?? swapPoint,
      } satisfies RouteLayer;
    });
  }, [entries, results]);

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
        <div className="lg:col-span-2 space-y-4">
          {entries.map((e, idx) => (
            <div key={e.id} className="rounded-lg border p-4 space-y-3 bg-card">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium opacity-70">Route {idx + 1}</div>
                {entries.length > 1 && (
                  <button onClick={() => removeEntry(e.id)} className="text-sm text-red-600 hover:underline">Remove</button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input className="border rounded-md px-3 py-2 text-sm" placeholder="Start lat" value={e.startLat} onChange={ev => updateEntry(e.id, { startLat: ev.target.value })} />
                <input className="border rounded-md px-3 py-2 text-sm" placeholder="Start lng" value={e.startLng} onChange={ev => updateEntry(e.id, { startLng: ev.target.value })} />
                <input className="border rounded-md px-3 py-2 text-sm" placeholder="End lat" value={e.endLat} onChange={ev => updateEntry(e.id, { endLat: ev.target.value })} />
                <input className="border rounded-md px-3 py-2 text-sm" placeholder="End lng" value={e.endLng} onChange={ev => updateEntry(e.id, { endLng: ev.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <select className="border rounded-md px-3 py-2 w-full text-sm" value={e.truck} onChange={ev => updateEntry(e.id, { truck: ev.target.value })}>
                  <option value="" disabled>
                    {truckKeys.length ? "Select truck" : "Loading trucks..."}
                  </option>
                  {truckKeys.map(k => (
                    <option key={k} value={k}>{k}</option>
                  ))}
                </select>
                <select className="border rounded-md px-3 py-2 w-full text-sm" value={e.optimizeBy} onChange={ev => updateEntry(e.id, { optimizeBy: ev.target.value as "time" | "cost" })}>
                  <option value="time">Optimize by Time</option>
                  <option value="cost">Optimize by Cost</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3 items-center">
                <div className="text-xs text-muted-foreground">Drivers available</div>
                <input type="number" min={1} max={4} className="border rounded-md px-3 py-2 text-sm" value={e.numDrivers} onChange={ev => updateEntry(e.id, { numDrivers: Number(ev.target.value) })} />
              </div>
            </div>
          ))}
          <div className="flex gap-3">
            <button onClick={addEntry} className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-secondary text-secondary-foreground hover:opacity-90 h-9 px-4">Add route</button>
            <button onClick={runSimulations} disabled={loading || entries.length === 0} className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 disabled:opacity-50">
              {loading ? "Simulating..." : "Run simulation"}
            </button>
            <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
              <input type="file" accept=".csv" className="hidden" onChange={async (ev) => {
                const file = ev.target.files?.[0];
                if (!file) return;
                const text = await file.text();
                // Expected CSV headers: start_lat,start_lng,end_lat,end_lng,truck,optimize_by,num_drivers
                const lines = text.split(/\r?\n/).filter(Boolean);
                const [header, ...rows] = lines;
                const cols = header.split(",").map(s => s.trim());
                const idx = (name: string) => cols.indexOf(name);
                const iSlat = idx("start_lat"), iSlng = idx("start_lng"), iElat = idx("end_lat"), iElng = idx("end_lng");
                const iTruck = idx("truck"), iOpt = idx("optimize_by"), iN = idx("num_drivers");
                const added: RouteEntry[] = [];
                for (const row of rows) {
                  const parts = row.split(",");
                  if (parts.length < 4) continue;
                  const entry: RouteEntry = {
                    id: crypto.randomUUID(),
                    startLat: parts[iSlat]?.trim() || "",
                    startLng: parts[iSlng]?.trim() || "",
                    endLat: parts[iElat]?.trim() || "",
                    endLng: parts[iElng]?.trim() || "",
                    truck: parts[iTruck]?.trim() || (truckKeys[0] || ""),
                    optimizeBy: (parts[iOpt]?.trim() as any) === "cost" ? "cost" : "time",
                    numDrivers: Number(parts[iN] || 1) || 1,
                  };
                  added.push(entry);
                }
                if (added.length) setEntries(prev => [...prev, ...added]);
                ev.currentTarget.value = "";
              }} />
              <span className="underline">Upload CSV</span>
            </label>
          </div>
          <div className="text-xs text-muted-foreground">Tip: Enter coordinates like 52.52, 13.405 (Berlin) to 48.137, 11.575 (Munich)</div>
        </div>

        <div className="lg:col-span-3">
          <div className="h-[520px] rounded-lg overflow-hidden border bg-muted/30">
            <SimMap layers={layers} />
          </div>
          <div className="mt-4 grid gap-3">
            {sortedEntries.map((e) => {
              const r = results[e.id] as RouteResult | { error: string } | undefined;
              return (
                <div key={e.id} className="rounded-lg border p-4 bg-card text-sm">
                  <div className="font-medium">Route {entries.findIndex(x => x.id === e.id) + 1}</div>
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
                      <div>
                        <div className="font-medium mb-1">Charging decisions</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {(r.charging_stops || []).map((cs, idx) => (
                            <li key={idx}>
                              At {cs.charging_station.latitude.toFixed(3)},{cs.charging_station.longitude.toFixed(3)}: +{(cs.departure_battery_level - cs.arrival_battery_level).toFixed(1)} kWh, {(cs.charging_time/60).toFixed(0)} min, €{cs.charging_cost.toFixed(2)}{(cs as unknown as { reason?: string })?.reason ? ` — ${(cs as unknown as { reason?: string }).reason}` : ""}
                            </li>
                          ))}
                          {(!r.charging_stops || r.charging_stops.length === 0) && <li className="opacity-70">No charging required</li>}
                        </ul>
                      </div>
                      <div>
                        <div className="font-medium mb-1">Driver swaps</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {(r.driver_swaps || []).map((sw, idx) => (
                            <li key={idx}>At {(sw.time/3600).toFixed(1)}h near {sw.location[0].toFixed(3)},{sw.location[1].toFixed(3)}{(sw as unknown as { reason?: string })?.reason ? ` — ${(sw as unknown as { reason?: string }).reason}` : ""}</li>
                          ))}
                          {(!r.driver_swaps || r.driver_swaps.length === 0) && <li className="opacity-70">No swaps scheduled</li>}
                        </ul>
                      </div>
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


