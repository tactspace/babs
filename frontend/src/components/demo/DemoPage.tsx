"use client";

import { useState } from "react";
import CoordinateForm from "./CoordinateForm";
import "./MapStyles.css";
import dynamic from "next/dynamic";

const MapView = dynamic(() => import("./MapView"), { ssr: false });

export default function DemoPage() {
  const [coordinates, setCoordinates] = useState({ lat: 52.52, lng: 13.405 }); // Default to Berlin

  const handleCoordinateSubmit = (lat: number, lng: number) => {
    setCoordinates({ lat, lng });
  };

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      {/* Left side - Form (2/5 width) */}
      <div className="w-full md:w-2/5 p-6 border-r border-gray-200 overflow-y-auto">
        <h1 className="text-2xl font-bold mb-6">Route Planner</h1>
        <CoordinateForm onSubmit={handleCoordinateSubmit} />
      </div>
      
      {/* Right side - Map (3/5 width) */}
      <div className="w-full md:w-3/5 h-[50vh] md:h-screen">
        <MapView coordinates={coordinates} />
      </div>
    </div>
  );
}