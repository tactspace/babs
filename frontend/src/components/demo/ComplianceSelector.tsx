"use client";

import { useState } from "react";

export type ComplianceType = "EU" | "US";

interface ComplianceSelectorProps {
  onComplianceSelect: (compliance: ComplianceType | null) => void;
  selectedCompliance?: ComplianceType | null;
}

export default function ComplianceSelector({ onComplianceSelect, selectedCompliance }: ComplianceSelectorProps) {
  const complianceOptions: ComplianceType[] = ["EU", "US"];

  const isEnabled = (compliance: ComplianceType) => {
    return compliance === "EU"; // Only EU is enabled
  };

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Compliance Type
      </label>
      
      <div className="flex gap-2">
        {complianceOptions.map((compliance) => {
          const enabled = isEnabled(compliance);
          return (
            <button
              key={compliance}
              type="button"
              onClick={() => enabled ? onComplianceSelect(compliance === selectedCompliance ? null : compliance) : null}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-150 border ${
                enabled
                  ? selectedCompliance === compliance
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                  : 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed opacity-60'
              }`}
            >
              {compliance}
              {!enabled && (
                <span className="text-xs italic ml-1">
                  (coming soon)
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
