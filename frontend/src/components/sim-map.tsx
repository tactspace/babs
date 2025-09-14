"use client";

import React, { useEffect, useMemo } from "react";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from "react-leaflet";
import type { LatLngExpression, LatLngBoundsExpression } from "leaflet";

export type DriverBreak = {
  break_type: "short_break" | "long_rest" | string;
  location: [number, number];
  start_time?: number;
  duration?: number;
};
export type DriverSwap = { location: [number, number]; time: number; reason?: string };

export type RouteLayer = {
  id: string;
  color: string;
  line: LatLngExpression[];
  chargingStops?: [number, number][];
  driverBreaks?: DriverBreak[];
  swapPoint?: [number, number] | null;
  highlighted?: boolean;
  nearbyChargers?: [number, number][];
  swapEvents?: DriverSwap[];
};

function FitBounds({ layers }: { layers: RouteLayer[] }) {
  const map = useMap();
  const bounds = useMemo<LatLngBoundsExpression | null>(() => {
    const all: LatLngExpression[] = [];
    layers.forEach((l) => {
      l.line.forEach((pt) => all.push(pt));
      (l.chargingStops || []).forEach((pt) => all.push(pt));
      if (l.swapPoint) all.push(l.swapPoint);
    });
    if (all.length === 0) return null;
    return all as unknown as LatLngBoundsExpression;
  }, [layers]);

  useEffect(() => {
    if (!bounds) return;
    try {
      map.fitBounds(bounds, { padding: [40, 40] });
    } catch {}
  }, [map, bounds]);

  return null;
}

export function SimMap({ layers }: { layers: RouteLayer[] }) {
  // Default center Europe
  const center: LatLngExpression = [51.1657, 10.4515];

  return (
    <MapContainer center={center} zoom={5} style={{ width: "100%", height: "100%", borderRadius: "12px" }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds layers={layers} />
      {layers.map((layer) => (
        <React.Fragment key={layer.id}>
          <Polyline positions={layer.line} pathOptions={{ color: layer.color, weight: layer.highlighted ? 6 : 4, opacity: layer.highlighted ? 0.9 : 0.7 }} />
          {(layer.nearbyChargers || []).map((pt, idx) => (
            <CircleMarker key={`${layer.id}-nc-${idx}`} center={pt} radius={4} pathOptions={{ color: "#6366f1", fillColor: "#6366f1", fillOpacity: 0.8 }}>
              <Popup>Nearby charging</Popup>
            </CircleMarker>
          ))}
          {(layer.chargingStops || []).map((pt, idx) => (
            <CircleMarker key={`${layer.id}-cs-${idx}`} center={pt} radius={7} pathOptions={{ color: "#0ea5e9", fillColor: "#0ea5e9", fillOpacity: 0.95 }}>
              <Popup>Charging stop</Popup>
            </CircleMarker>
          ))}
          {(layer.driverBreaks || []).map((brk, idx) => (
            <CircleMarker key={`${layer.id}-br-${idx}`} center={brk.location} radius={5} pathOptions={{ color: "#f59e0b", fillColor: "#f59e0b", fillOpacity: 0.9 }}>
              <Popup>{brk.break_type.replace("_", " ")}</Popup>
            </CircleMarker>
          ))}
          {(layer.swapEvents || []).map((sw, idx) => (
            <CircleMarker key={`${layer.id}-sw-${idx}`} center={sw.location} radius={7} pathOptions={{ color: "#10b981", fillColor: "#10b981", fillOpacity: 1 }}>
              <Popup>{sw.reason || "Driver swap"}</Popup>
            </CircleMarker>
          ))}
        </React.Fragment>
      ))}
    </MapContainer>
  );
}


