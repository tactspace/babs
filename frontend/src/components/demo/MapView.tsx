"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { createCustomMarker, COLORS } from "./LocationMarkerIcon";

interface MapViewProps {
  coordinates: {
    lat: number;
    lng: number;
  };
}

export default function MapView({ coordinates }: MapViewProps) {
  const [isMounted, setIsMounted] = useState(false);

  const customRedMarker = createCustomMarker(COLORS.BLUE);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return <div className="w-full h-screen bg-gray-100 flex items-center justify-center">Loading map...</div>;
  }

  return (
    <MapContainer 
      center={[coordinates.lat, coordinates.lng]} 
      zoom={13} 
      style={{ height: "100%", width: "100%" }}
      key={`${coordinates.lat}-${coordinates.lng}`}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.optily.eu">optily.eu</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker position={[coordinates.lat, coordinates.lng]} icon={customRedMarker}>
        <Popup>
          <div className="font-medium p-1">
            <div className="font-bold mb-1">Selected Point</div>
            <div>Latitude: {coordinates.lat.toFixed(5)}</div>
            <div>Longitude: {coordinates.lng.toFixed(5)}</div>
          </div>
        </Popup>
      </Marker>
    </MapContainer>
  );
}
