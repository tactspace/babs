"use client";

import { useState } from "react";

interface RouteComparison {
  route_name: string;
  route_index: number;
  base: {
    total_cost_eur: number;
    duration_minutes: number;
    distance_km: number;
    charging_cost_eur: number;
    driver_cost_eur: number;
  };
  optimized: {
    total_cost_eur: number;
    duration_minutes: number;
    distance_km: number;
    charging_cost_eur: number;
    driver_cost_eur: number;
  };
  savings: {
    total_cost_eur: number;
    duration_minutes: number;
    distance_km: number;
    charging_cost_eur: number;
    driver_cost_eur: number;
  };
  savings_percentage: {
    total_cost_eur: number;
    duration_minutes: number;
    distance_km: number;
    charging_cost_eur: number;
    driver_cost_eur: number;
  };
  swaps_applied: Array<{
    station_id: number;
    driver1_id: string;
    driver2_id: string;
    benefit_km: number;
    reason: string;
  }>;
}

interface TruckSwap {
  station_id: number;
  station_location: [number, number];
  driver1_id: string;
  driver2_id: string;
  benefit_km: number;
  alignment_dot: number;
  reason: string;
  detour_km_total: number;
  iteration: number;
  route_idx: number;
  global_iteration: number;
}

interface CostComparisonProps {
  optimizationResult: {
    routes: any[];
    total_distance_km: number;
    total_duration_minutes: number;
    total_cost_eur: number;
    total_charging_cost_eur: number;
    success: boolean;
    message: string;
    driver_assignments: any[];
    truck_swaps: TruckSwap[];
    drivers: any[];
    optimization_summary: any;
    base_cost_eur: number;
    optimized_cost_eur: number;
    cost_savings_eur: number;
    cost_savings_percentage: number;
    route_comparisons: RouteComparison[];
  } | null;
  onClose: () => void;
}

export default function CostComparison({ optimizationResult, onClose }: CostComparisonProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'routes' | 'swaps'>('overview');

  if (!optimizationResult) return null;

  const formatCurrency = (amount: number) => `€${amount.toFixed(2)}`;
  const formatPercentage = (percentage: number) => `${percentage.toFixed(1)}%`;
  const formatDistance = (distance: number) => `${distance.toFixed(1)} km`;
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[9999] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full h-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-green-50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Cost Optimization Results</h2>
              <p className="text-sm text-gray-600">Driver swap optimization analysis</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full p-2 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b bg-gray-50">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-8 py-4 font-medium text-sm transition-colors ${
              activeTab === 'overview'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Overview</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('routes')}
            className={`px-8 py-4 font-medium text-sm transition-colors ${
              activeTab === 'routes'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              <span>Route Details</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('swaps')}
            className={`px-8 py-4 font-medium text-sm transition-colors ${
              activeTab === 'swaps'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
              <span>Truck Swaps</span>
            </div>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Overall Summary */}
                <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-xl p-8 border border-blue-100">
                  <h3 className="text-2xl font-bold text-gray-900 mb-6">Overall Optimization Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-gray-900 mb-2">
                        {formatCurrency(optimizationResult.base_cost_eur)}
                      </div>
                      <div className="text-sm text-gray-600 font-medium">Base Cost</div>
                    </div>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-600 mb-2">
                        {formatCurrency(optimizationResult.optimized_cost_eur)}
                      </div>
                      <div className="text-sm text-gray-600 font-medium">Optimized Cost</div>
                    </div>
                    <div className="text-center">
                      <div className="text-4xl font-bold text-green-600 mb-2">
                        {formatCurrency(optimizationResult.cost_savings_eur)}
                      </div>
                      <div className="text-sm text-gray-600 font-medium">
                        Savings ({formatPercentage(optimizationResult.cost_savings_percentage)})
                      </div>
                    </div>
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {optimizationResult.routes.length}
                    </div>
                    <div className="text-sm text-gray-600 font-medium">Total Routes</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="text-3xl font-bold text-purple-600 mb-2">
                      {optimizationResult.truck_swaps.length}
                    </div>
                    <div className="text-sm text-gray-600 font-medium">Truck Swaps</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="text-3xl font-bold text-orange-600 mb-2">
                      {formatDistance(optimizationResult.total_distance_km)}
                    </div>
                    <div className="text-sm text-gray-600 font-medium">Total Distance</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="text-3xl font-bold text-indigo-600 mb-2">
                      {formatDuration(optimizationResult.total_duration_minutes)}
                    </div>
                    <div className="text-sm text-gray-600 font-medium">Total Duration</div>
                  </div>
                </div>

                {/* Cost Breakdown */}
                <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
                  <h3 className="text-xl font-bold text-gray-900 mb-6">Cost Breakdown</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center py-3 border-b border-gray-100">
                      <span className="text-gray-700 font-medium">Total Cost</span>
                      <div className="flex items-center space-x-4">
                        <span className="text-gray-500">{formatCurrency(optimizationResult.base_cost_eur)}</span>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-bold text-green-600 text-lg">{formatCurrency(optimizationResult.optimized_cost_eur)}</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center py-3 border-b border-gray-100">
                      <span className="text-gray-700 font-medium">Charging Costs</span>
                      <div className="flex items-center space-x-4">
                        <span className="text-gray-500">{formatCurrency(optimizationResult.base_cost_eur - optimizationResult.optimized_cost_eur + optimizationResult.total_charging_cost_eur)}</span>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-bold text-green-600 text-lg">{formatCurrency(optimizationResult.total_charging_cost_eur)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'routes' && (
              <div className="space-y-6">
                {optimizationResult.route_comparisons.map((comparison, index) => (
                  <div key={index} className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-xl font-bold text-gray-900">{comparison.route_name}</h3>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm text-gray-500 font-medium">Savings:</span>
                        <span className="font-bold text-green-600 text-lg">
                          {formatCurrency(comparison.savings.total_cost_eur)} ({formatPercentage(comparison.savings_percentage.total_cost_eur)})
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      {/* Base vs Optimized */}
                      <div>
                        <h4 className="font-bold text-gray-800 mb-4">Base vs Optimized</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center py-2">
                            <span className="text-sm text-gray-600 font-medium">Cost:</span>
                            <div className="flex items-center space-x-3">
                              <span className="text-sm text-gray-500">{formatCurrency(comparison.base.total_cost_eur)}</span>
                              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              <span className="text-sm font-bold text-green-600">{formatCurrency(comparison.optimized.total_cost_eur)}</span>
                            </div>
                          </div>
                          <div className="flex justify-between items-center py-2">
                            <span className="text-sm text-gray-600 font-medium">Duration:</span>
                            <div className="flex items-center space-x-3">
                              <span className="text-sm text-gray-500">{formatDuration(comparison.base.duration_minutes)}</span>
                              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              <span className="text-sm font-bold text-green-600">{formatDuration(comparison.optimized.duration_minutes)}</span>
                            </div>
                          </div>
                          <div className="flex justify-between items-center py-2">
                            <span className="text-sm text-gray-600 font-medium">Distance:</span>
                            <div className="flex items-center space-x-3">
                              <span className="text-sm text-gray-500">{formatDistance(comparison.base.distance_km)}</span>
                              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                              <span className="text-sm font-bold text-green-600">{formatDistance(comparison.optimized.distance_km)}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Swaps Applied */}
                      <div>
                        <h4 className="font-bold text-gray-800 mb-4">Swaps Applied</h4>
                        {comparison.swaps_applied.length > 0 ? (
                          <div className="space-y-3">
                            {comparison.swaps_applied.map((swap, swapIndex) => (
                              <div key={swapIndex} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <div className="font-medium text-blue-900">Driver {swap.driver1_id} ↔ Driver {swap.driver2_id}</div>
                                <div className="text-sm text-blue-700">Station {swap.station_id} • {swap.reason}</div>
                                <div className="text-sm text-green-600 font-medium">Benefit: {formatDistance(swap.benefit_km)}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-sm text-gray-500 italic bg-gray-50 rounded-lg p-4">No swaps applied to this route</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'swaps' && (
              <div className="space-y-6">
                {optimizationResult.truck_swaps.length > 0 ? (
                  optimizationResult.truck_swaps.map((swap, index) => (
                    <div key={index} className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
                      <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xl font-bold text-gray-900">Swap #{index + 1}</h3>
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-gray-500 font-medium">Benefit:</span>
                          <span className="font-bold text-green-600 text-lg">{formatDistance(swap.benefit_km)}</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div>
                          <h4 className="font-bold text-gray-800 mb-4">Driver Exchange</h4>
                          <div className="space-y-4">
                            <div className="flex items-center space-x-3">
                              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-lg font-bold text-blue-600">
                                {swap.driver1_id}
                              </div>
                              <span className="text-gray-700 font-medium">Driver {swap.driver1_id}</span>
                            </div>
                            <div className="flex items-center space-x-3">
                              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-lg font-bold text-green-600">
                                {swap.driver2_id}
                              </div>
                              <span className="text-gray-700 font-medium">Driver {swap.driver2_id}</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-bold text-gray-800 mb-4">Swap Details</h4>
                          <div className="space-y-3 text-sm">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                              <span className="text-gray-600 font-medium">Station:</span>
                              <span className="font-bold">#{swap.station_id}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                              <span className="text-gray-600 font-medium">Reason:</span>
                              <span className="font-bold capitalize">{swap.reason.replace('_', ' ')}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                              <span className="text-gray-600 font-medium">Detour:</span>
                              <span className="font-bold">{formatDistance(swap.detour_km_total)}</span>
                            </div>
                            <div className="flex justify-between items-center py-2">
                              <span className="text-gray-600 font-medium">Alignment:</span>
                              <span className="font-bold">{(swap.alignment_dot * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-16">
                    <div className="text-gray-400 text-8xl mb-6">🚛</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-4">No Truck Swaps Found</h3>
                    <p className="text-gray-500 text-lg">No beneficial driver swaps were identified for the current routes.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t bg-white">
          <button
            onClick={onClose}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
