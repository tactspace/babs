"use client";

import React, { useEffect, useMemo } from "react";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap, Marker } from "react-leaflet";
import type { LatLngExpression, LatLngBoundsExpression } from "leaflet";
import L from "leaflet";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faMapMarkerAlt, faChargingStation, faExchangeAlt, faBed, faMapPin } from "@fortawesome/free-solid-svg-icons";
import { renderToString } from "react-dom/server";

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
  startPoint?: [number, number];
  endPoint?: [number, number];
  startName?: string;
  endName?: string;
  mode?: "simulation" | "optimization"; // Add this line
};

type MapPoint = {
  position: [number, number];
  name: string;
};

// Predefined colors for location markers
const locationColors = [
  "#3b82f6", // blue
  "#ef4444", // red
  "#22c55e", // green
  "#a855f7", // purple
  "#f59e0b", // amber
  "#06b6d4", // cyan
  "#ec4899", // pink
  "#14b8a6", // teal
  "#f97316", // orange
  "#8b5cf6", // violet
  "#84cc16", // lime
  "#6366f1", // indigo
];

// Create custom icons using Font Awesome
const createIcon = (icon: any, color: string, size: number = 30) => {
  return L.divIcon({
    html: renderToString(
      <div style={{ color, fontSize: `${size}px`, textAlign: 'center' }}>
        <FontAwesomeIcon icon={icon} />
      </div>
    ),
    className: '',
    iconSize: [size, size],
    iconAnchor: [size/2, size],
    popupAnchor: [0, -size]
  });
};

function FitBounds({ layers, points }: { layers: RouteLayer[], points: MapPoint[] }) {
  const map = useMap();
  const bounds = useMemo<LatLngBoundsExpression | null>(() => {
    const all: LatLngExpression[] = [];
    layers.forEach((l) => {
      l.line.forEach((pt) => all.push(pt));
      (l.chargingStops || []).forEach((pt) => all.push(pt));
      if (l.swapPoint) all.push(l.swapPoint);
    });
    points.forEach(p => all.push(p.position));
    if (all.length === 0) return null;
    return all as unknown as LatLngBoundsExpression;
  }, [layers, points]);

  useEffect(() => {
    if (!bounds) return;
    try {
      map.fitBounds(bounds, { padding: [40, 40] });
    } catch {}
  }, [map, bounds]);

  return null;
}

export function SimMap({ layers, points = [] }: { layers: RouteLayer[], points?: MapPoint[] }) {
  // Default center Europe
  const center: LatLngExpression = [51.1657, 10.4515];
  
  // Create a map of point coordinates to colors
  const pointColorMap = useMemo(() => {
    const colorMap = new Map<string, string>();
    points.forEach((point, idx) => {
      const key = `${point.position[0]},${point.position[1]}`;
      colorMap.set(key, locationColors[idx % locationColors.length]);
    });
    return colorMap;
  }, [points]);
  
  // Function to get color for a point
  const getPointColor = (position: [number, number]): string => {
    const key = `${position[0]},${position[1]}`;
    return pointColorMap.get(key) || "#3b82f6"; // Default to blue if not found
  };

  return (
    <MapContainer center={center} zoom={5} style={{ width: "100%", height: "100%", borderRadius: "12px" }} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds layers={layers} points={points} />
      
      {/* Location markers */}
      {points.map((point, idx) => (
        <Marker key={`point-${idx}`} position={point.position} icon={createIcon(faMapMarkerAlt, locationColors[idx % locationColors.length], 35)}>
          <Popup>
            <div style={{ color: locationColors[idx % locationColors.length], fontWeight: 'bold' }}>{point.name}</div>
          </Popup>
        </Marker>
      ))}
      
      {layers.map((layer) => (
        <React.Fragment key={layer.id}>
          <Polyline positions={layer.line} pathOptions={{ color: layer.color, weight: layer.highlighted ? 6 : 4, opacity: layer.highlighted ? 0.9 : 0.7 }} />
          
          {/* Start and end markers with colors matching the location */}
          {layer.startPoint && (
            <Marker 
              position={layer.startPoint} 
              icon={createIcon(faMapPin, getPointColor(layer.startPoint), 35)}
            >
              <Popup>{layer.startName || 'Start'}</Popup>
            </Marker>
          )}
          
          {layer.endPoint && (
            <Marker 
              position={layer.endPoint} 
              icon={createIcon(faMapPin, getPointColor(layer.endPoint), 35)}
            >
              <Popup>{layer.endName || 'End'}</Popup>
            </Marker>
          )}
          
          {/* Only show charging stops for optimization mode */}
          {layer.mode === "optimization" && (layer.chargingStops || []).map((pt, idx) => (
            <CircleMarker key={`${layer.id}-cs-${idx}`} center={pt} radius={7} pathOptions={{ color: "#0ea5e9", fillColor: "#0ea5e9", fillOpacity: 0.95 }}>
              <Popup>Charging stop</Popup>
            </CircleMarker>
          ))}
          
          {/* Only show driver breaks for optimization mode */}
          {layer.mode === "optimization" && (layer.driverBreaks || []).map((brk, idx) => (
            <CircleMarker key={`${layer.id}-br-${idx}`} center={brk.location} radius={5} pathOptions={{ color: "#f59e0b", fillColor: "#f59e0b", fillOpacity: 0.9 }}>
              <Popup>{brk.break_type.replace("_", " ")}</Popup>
            </CircleMarker>
          ))}
          
          {/* Only show driver swaps for optimization mode */}
          {layer.mode === "optimization" && (layer.swapEvents || []).map((sw, idx) => (
            <CircleMarker key={`${layer.id}-sw-${idx}`} center={sw.location} radius={7} pathOptions={{ color: "#10b981", fillColor: "#10b981", fillOpacity: 1 }}>
              <Popup>{sw.reason || "Driver swap"}</Popup>
            </CircleMarker>
          ))}
          
          {/* Show nearby chargers for both modes */}
          {(layer.nearbyChargers || []).map((pt, idx) => (
            <CircleMarker key={`${layer.id}-nc-${idx}`} center={pt} radius={4} pathOptions={{ color: "#6366f1", fillColor: "#6366f1", fillOpacity: 0.8 }}>
              <Popup>Nearby charging</Popup>
            </CircleMarker>
          ))}
        </React.Fragment>
      ))}
    </MapContainer>
  );
}


