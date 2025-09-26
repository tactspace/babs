"use client";

import { useState, useEffect } from "react";
import { Battery, BatteryFull, Route } from "lucide-react";
import { BASE_URL } from "../../lib/utils";

export interface Truck {
  manufacturer: string;
  model: string;
  battery_capacity: number;
  consumption: number;
  range: number;
}

interface TruckSelectorProps {
  onTruckSelect: (truck: Truck | null) => void;
  selectedTruck?: Truck | null;
}

export default function TruckSelector({ onTruckSelect, selectedTruck }: TruckSelectorProps) {
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchTrucks = async () => {
      try {
        const response = await fetch(`${BASE_URL}/trucks`);
        if (response.ok) {
          const data = await response.json();
          setTrucks(data.trucks || []);
        }
      } catch (error) {
        console.error('Error fetching trucks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrucks();
  }, []);

  const isSelected = (truck: Truck) => {
    return selectedTruck && 
           selectedTruck.manufacturer === truck.manufacturer && 
           selectedTruck.model === truck.model;
  };

  const isEnabled = (index: number) => {
    return index === 0; // Only first truck is enabled
  };

  if (loading) {
    return (
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Truck Type
        </label>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex-shrink-0 w-40 h-24 bg-gray-100 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Truck Type
      </label>
      
      <div className="flex gap-2 overflow-x-auto pb-1">
        {trucks.map((truck, index) => {
          const enabled = isEnabled(index);
          return (
            <div
              key={index}
              onClick={() => enabled ? onTruckSelect(truck) : null}
              className={`relative flex-shrink-0 w-40 h-24 p-3 rounded border transition-all duration-150 group ${
                enabled
                  ? isSelected(truck)
                    ? 'border-blue-500 bg-blue-50 cursor-pointer'
                    : 'border-gray-200 bg-white hover:border-gray-300 cursor-pointer'
                  : 'border-gray-200 bg-gray-100 opacity-50 cursor-not-allowed'
              }`}
            >
              <div className="h-full flex flex-col justify-between">
                <div>
                  <h3 className="font-medium text-sm text-primary truncate">
                    {truck.manufacturer}
                  </h3>
                  <p className="text-xs text-gray-600 truncate">
                    {truck.model}
                  </p>
                </div>
                
                <div className="text-xs text-gray-500 mt-2">
                  <div className="flex items-center gap-1">
                    <BatteryFull className="w-3 h-3" />
                    <span>{truck.battery_capacity}kWh</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Route className="w-3 h-3" />
                    <span>{truck.range}km</span>
                  </div>
                </div>
              </div>
              
              {/* Simple "Coming soon" text for disabled trucks */}
              {!enabled && (
                <div className="absolute top-1 right-1">
                  <span className="text-xs text-gray-400 font-medium">Coming soon</span>
                </div>
              )}
              
              {/* Hover overlay for disabled trucks */}
              {!enabled && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-80 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <span className="text-sm font-medium text-white">Coming soon</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {trucks.length === 0 && !loading && (
        <div className="text-center py-4 text-gray-500 text-sm">
          No trucks available
        </div>
      )}
    </div>
  );
}
