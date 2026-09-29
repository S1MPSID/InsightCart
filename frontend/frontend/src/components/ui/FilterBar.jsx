import React from "react";

/**
 * Pill-style control for switching between a small set of mutually exclusive
 * options, such as the ranking metric on Products/Customers or the trend
 * granularity on Analytics. Keeps filter state in the URL-less page component.
 */
export default function SegmentedControl({ label, options, value, onChange, className = "" }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {label && <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</span>}
      <div
        role="group"
        aria-label={label}
        className="inline-flex items-center gap-1 p-1 rounded-full bg-white shadow-[0_2px_10px_rgb(0,0,0,0.04)]"
      >
        {options.map((option) => {
          const active = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onChange(option.value)}
              aria-pressed={active}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-full transition-colors ${
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** Native select styled to match the pill controls, for longer option lists. */
export function SelectControl({ label, value, onChange, options, className = "" }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {label && <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</span>}
      <div className="relative">
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="appearance-none pl-4 pr-9 py-2 text-xs font-semibold rounded-full bg-white text-slate-700 shadow-[0_2px_10px_rgb(0,0,0,0.04)] focus:outline-none focus:ring-2 focus:ring-indigo-100 cursor-pointer"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <svg
          className="w-3 h-3 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
}
