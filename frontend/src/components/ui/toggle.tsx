import React from "react";

export interface ToggleProps {
  enabled: boolean;
  onChange: (next: boolean) => void;
  label?: string;
}

export function Toggle({ enabled, onChange, label }: ToggleProps) {
  return (
    <label className="flex items-center cursor-pointer select-none">
      {/* Visually hidden checkbox */}
      <input
        type="checkbox"
        className="sr-only"
        checked={enabled}
        onChange={(e) => onChange(e.target.checked)}
      />

      {/* The track */}
      <div
        className={`w-12 h-6 rounded-full transition-colors duration-300 ${
          enabled ? "bg-primary" : "bg-gray-300 dark:bg-gray-600"
        }`}
      >
        {/* The dot */}
        <div
          className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-300 ${
            enabled ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </div>

      {label && (
        <span className="ml-3 leading-none" style={{ fontSize: "2rem" }}>
          {label}
        </span>
      )}
    </label>
  );
}
