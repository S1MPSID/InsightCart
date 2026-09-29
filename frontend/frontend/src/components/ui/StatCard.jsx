import React from "react";

/** Compact stat tile for the sub-pages, where a full KPICard grid would overpower the content. */
export default function StatCard({ title, value, note, icon: Icon, tone = "default", progress }) {
  const tones = {
    default: "bg-slate-50 text-slate-500",
    indigo: "bg-indigo-50 text-indigo-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600",
    sky: "bg-sky-50 text-sky-600",
    violet: "bg-violet-50 text-violet-600",
  };

  return (
    <div className="bg-white rounded-[24px] shadow-[0_4px_24px_rgb(0,0,0,0.03)] px-6 py-5 flex flex-col justify-between gap-4 h-full">
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        {Icon && (
          <span className={`shrink-0 p-2 rounded-xl ${tones[tone] || tones.default}`}>
            <Icon className="w-4 h-4" />
          </span>
        )}
      </div>
      <div>
        <div className="text-2xl font-extrabold tracking-tight text-slate-900 tabular-nums">{value}</div>
        {note && <div className="text-xs font-medium text-slate-400 mt-1.5">{note}</div>}
        {typeof progress === "number" && Number.isFinite(progress) && (
          <div className="mt-3 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-indigo-500 transition-all"
              style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
