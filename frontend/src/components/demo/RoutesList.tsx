"use client";

import { Route } from "./DemoPage";

interface RoutesListProps {
  routes: Route[];
  activeRouteId: string;
  onRouteSelect: (routeId: string) => void;
  onRouteDelete: (routeId: string) => void;
  onClearAll?: () => void;
}

export default function RoutesList({ routes, activeRouteId, onRouteSelect, onRouteDelete, onClearAll }: RoutesListProps) {
  return (
    <div className="flex-1 px-10 pb-8 overflow-hidden">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Routes</h2>
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
      
      <div className="space-y-3 overflow-y-auto h-full">
        {routes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            <p className="text-sm font-medium mb-1">No routes yet</p>
            <p className="text-xs text-gray-400">Add your first route using the form above</p>
          </div>
        ) : (
          routes.map(route => (
            <div 
              key={route.id} 
              className={`p-4 rounded-md flex justify-between items-center cursor-pointer ${
                route.id === activeRouteId ? 'bg-primary/10 border border-primary/30' : 'bg-gray-100 hover:bg-gray-200'
              }`}
              onClick={() => onRouteSelect(route.id)}
            >
              <div>
                <div className="font-medium">{route.name}</div>
                <div className="text-xs text-gray-500">
                  {route.start.lat.toFixed(2)}, {route.start.lng.toFixed(2)} → {route.end.lat.toFixed(2)}, {route.end.lng.toFixed(2)}
                </div>
              </div>
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
          ))
        )}
      </div>
    </div>
  );
}
