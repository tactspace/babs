"use client";

import { useState, FormEvent, useRef } from "react";
import TruckSelector, { Truck } from "./TruckSelector";
import ComplianceSelector, { ComplianceType } from "./ComplianceSelector";

interface CoordinateFormProps {
  onSubmit: (startLat: number, startLng: number, endLat: number, endLng: number, name?: string, driverSalary?: number) => void;
  onImportCSV?: (routes: Array<{name: string, startLat: number, startLng: number, endLat: number, endLng: number}>) => void;
  onFindRoute?: () => void; // Simplified - no parameters needed
  isFindRouteEnabled?: boolean; // Add enabled state
  isFindingRoutes?: boolean; // Add loading state
}

export default function CoordinateForm({ onSubmit, onImportCSV, onFindRoute, isFindRouteEnabled, isFindingRoutes }: CoordinateFormProps) {
  const [startLatitude, setStartLatitude] = useState("");
  const [startLongitude, setStartLongitude] = useState("");
  const [endLatitude, setEndLatitude] = useState("");
  const [endLongitude, setEndLongitude] = useState("");
  const [routeName, setRouteName] = useState("");
  const [driverSalary, setDriverSalary] = useState("");
  const [error, setError] = useState("");
  const [selectedTruck, setSelectedTruck] = useState<Truck | null>(null);
  const [selectedCompliance, setSelectedCompliance] = useState<ComplianceType | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");

    const startLat = parseFloat(startLatitude);
    const startLng = parseFloat(startLongitude);
    const endLat = parseFloat(endLatitude);
    const endLng = parseFloat(endLongitude);
    const salary = driverSalary ? parseInt(driverSalary) : undefined;
    console.log("CoordinateForm - driverSalary input:", driverSalary);
    console.log("CoordinateForm - parsed salary:", salary);

    if (isNaN(startLat) || isNaN(startLng) || isNaN(endLat) || isNaN(endLng)) {
      setError("Please enter valid numeric coordinates");
      return;
    }

    if (startLat < -90 || startLat > 90 || endLat < -90 || endLat > 90) {
      setError("Latitude must be between -90 and 90 degrees");
      return;
    }

    if (startLng < -180 || startLng > 180 || endLng < -180 || endLng > 180) {
      setError("Longitude must be between -180 and 180 degrees");
      return;
    }

    if (driverSalary && (isNaN(salary!) || salary! <= 0)) {
      setError("Driver salary must be a positive number");
      return;
    }

    onSubmit(startLat, startLng, endLat, endLng, routeName, salary);
    console.log("CoordinateForm - calling onSubmit with salary:", salary);
    
    // Clear the form after successful submission
    clearForm();
  };

  const clearForm = () => {
    setRouteName("");
    setStartLatitude("");
    setStartLongitude("");
    setEndLatitude("");
    setEndLongitude("");
    setDriverSalary("");
    setSelectedTruck(null);
    setSelectedCompliance(null);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError("Please select a CSV file");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csvText = e.target?.result as string;
        const routes = parseCSV(csvText);
        
        if (routes.length === 0) {
          setError("No valid routes found in CSV file");
          return;
        }

        if (onImportCSV) {
          onImportCSV(routes);
          setError("");
        }
      } catch (error) {
        setError(`Error reading CSV file. Please check the format. ${error}`);
      }
    };

    reader.readAsText(file);
    
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const parseCSV = (csvText: string): Array<{name: string, startLat: number, startLng: number, endLat: number, endLng: number, driverSalary?: number}> => {
    const lines = csvText.trim().split('\n');
    const routes: Array<{name: string, startLat: number, startLng: number, endLat: number, endLng: number, driverSalary?: number}> = [];

    // Skip header row if it exists
    const startIndex = lines[0].toLowerCase().includes('route_name') ? 1 : 0;

    for (let i = startIndex; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Split by comma and handle quoted values
      const columns = line.split(',').map(col => col.trim().replace(/^"|"$/g, ''));
      
      if (columns.length < 5) {
        console.warn(`Skipping line ${i + 1}: insufficient columns`);
        continue;
      }

      const [name, startLatStr, startLngStr, endLatStr, endLngStr, driverSalaryStr] = columns;
      
      const startLat = parseFloat(startLatStr);
      const startLng = parseFloat(startLngStr);
      const endLat = parseFloat(endLatStr);
      const endLng = parseFloat(endLngStr);
      const driverSalary = driverSalaryStr ? parseFloat(driverSalaryStr) : undefined;

      // Validate coordinates
      if (isNaN(startLat) || isNaN(startLng) || isNaN(endLat) || isNaN(endLng)) {
        console.warn(`Skipping line ${i + 1}: invalid coordinates`);
        continue;
      }

      if (startLat < -90 || startLat > 90 || endLat < -90 || endLat > 90) {
        console.warn(`Skipping line ${i + 1}: latitude out of range`);
        continue;
      }

      if (startLng < -180 || startLng > 180 || endLng < -180 || endLng > 180) {
        console.warn(`Skipping line ${i + 1}: longitude out of range`);
        continue;
      }

      routes.push({
        name: name || `Route ${routes.length + 1}`,
        startLat,
        startLng,
        endLat,
        endLng,
        driverSalary
      });
    }

    return routes;
  };

  const handleFindRoute = () => {
    if (onFindRoute) {
      onFindRoute();
    }
  };

  return (
    <div className="bg-white rounded-lg p-4">
      <h2 className="text-xl font-bold mb-4">Add New Route</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="routeName" className="block text-sm font-medium text-gray-700 mb-1">
            Route Name
          </label>
          <input
            id="routeName"
            type="text"
            value={routeName}
            onChange={(e) => setRouteName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., Berlin Route"
          />
        </div>

        <TruckSelector 
          onTruckSelect={setSelectedTruck}
          selectedTruck={selectedTruck}
        />

        <ComplianceSelector 
          onComplianceSelect={setSelectedCompliance}
          selectedCompliance={selectedCompliance}
        />
{/* 
        <div className="mb-4">
          <label htmlFor="driverSalary" className="block text-sm font-medium text-gray-700 mb-1">
            Driver Salary (€/hour)
          </label>
          <input
            id="driverSalary"
            type="number"
            value={driverSalary}
            onChange={(e) => setDriverSalary(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="e.g., 35"
            min="1"
          />
        </div> */}

        <div className="mb-4">
          <h3 className="font-medium text-gray-700 mb-2">Starting Point</h3>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label htmlFor="startLatitude" className="block text-sm font-medium text-gray-700 mb-1">
                Latitude
              </label>
              <input
                id="startLatitude"
                type="text"
                value={startLatitude}
                onChange={(e) => setStartLatitude(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., 52.52"
                required
              />
            </div>
            <div>
              <label htmlFor="startLongitude" className="block text-sm font-medium text-gray-700 mb-1">
                Longitude
              </label>
              <input
                id="startLongitude"
                type="text"
                value={startLongitude}
                onChange={(e) => setStartLongitude(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., 13.405"
                required
              />
            </div>
          </div>
        </div>
        
        <div className="mb-6">
          <h3 className="font-medium text-gray-700 mb-2">Destination</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="endLatitude" className="block text-sm font-medium text-gray-700 mb-1">
                Latitude
              </label>
              <input
                id="endLatitude"
                type="text"
                value={endLatitude}
                onChange={(e) => setEndLatitude(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., 52.52"
                required
              />
            </div>
            <div>
              <label htmlFor="endLongitude" className="block text-sm font-medium text-gray-700 mb-1">
                Longitude
              </label>
              <input
                id="endLongitude"
                type="text"
                value={endLongitude}
                onChange={(e) => setEndLongitude(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., 13.405"
                required
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-2 bg-red-50 text-red-600 rounded-md text-sm">
            {error}
          </div>
        )}
        
        <div className="flex gap-2">
          <button
            type="submit"
            className="flex-1 inline-flex justify-center items-center rounded-md bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 text-sm font-medium transition-colors"
          >
            Add Route
          </button>
          
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 inline-flex justify-center items-center rounded-md bg-black text-white hover:bg-primary/90 h-10 px-4 py-2 text-sm font-medium transition-colors"
          >
            Import CSV
          </button>

          <button
            type="button"
            onClick={handleFindRoute}
            disabled={!isFindRouteEnabled}
            className="flex-1 inline-flex justify-center items-center rounded-md bg-primary text-white hover:bg-primary/90 h-10 px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isFindingRoutes ? "Finding Routes..." : "Find Routes"}
          </button>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          className="hidden"
        />
      </form>
    </div>
  );
}
