import React from "react";
import { formatNumber } from "../../utils/format";

/**
 * One tooltip for every Recharts surface in the app. Previously each chart
 * carried its own copy that formatted the same numbers differently.
 *
 * `formatters` maps a Recharts series name (Area/Bar `name`) to a value
 * formatter, so money series and count series can share this component.
 * `title` is the period label, so time-series callers do not repeat the
 * date formatting the chart axis already performs.
 */
export default function ChartTooltip({ active, payload, title, formatters, onViewAll }) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-slate-100 p-4 min-w-[190px]">
      {title && <p className="text-sm font-semibold text-slate-800 mb-3 border-b border-slate-50 pb-2">{title}</p>}
      <div className="flex flex-col gap-2">
        {payload.map((entry, index) => (
          <div key={`${entry.dataKey}-${index}`} className="flex items-center justify-between gap-6 text-sm">
            <span className="flex items-center gap-2 text-slate-500 font-medium">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: entry.color || entry.fill }}
              />
              {entry.name}
            </span>
            <span className="font-bold text-slate-900 tabular-nums">
              {formatValue(entry, formatters)}
            </span>
          </div>
        ))}
      </div>
      {onViewAll && (
        <button
          type="button"
          onClick={onViewAll}
          className="mt-3 pt-2.5 border-t border-slate-50 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
        >
          View all
        </button>
      )}
    </div>
  );
}

function formatValue(entry, formatters) {
  const formatter = formatters?.[entry.name];
  if (formatter) return formatter(entry.value);

  const value = Array.isArray(entry.value) ? entry.value[1] : entry.value;
  const magnitude = Math.abs(Number(value) || 0);
  return magnitude >= 1000 ? formatNumber(value) : String(value);
}
