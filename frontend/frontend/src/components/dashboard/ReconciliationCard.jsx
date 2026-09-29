import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";
import StatusBadge from "../ui/StatusBadge";

export default function ReconciliationCard({ data }) {
  if (!data) return null;

  return (
    <AnalyticsCard title="System Reconciliation" subtitle="Source vs Database matching" className="col-span-1 lg:col-span-2">
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-50/50 border border-slate-100">
          <div>
            <div className="text-sm font-medium text-slate-500">Overall Match</div>
            <div className="font-bold text-lg mt-1 text-slate-800">
              {data.passed} / {data.total_metrics} Metrics
            </div>
          </div>
          <StatusBadge status={data.overall_status} text={data.overall_status === 'PASS' ? 'Verified' : 'Mismatch'} className="text-sm px-3 py-1" />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="py-3 text-xs font-semibold text-slate-500 uppercase">Metric</th>
                <th className="py-3 text-xs font-semibold text-slate-500 uppercase text-right">Source Value</th>
                <th className="py-3 text-xs font-semibold text-slate-500 uppercase text-right">DB Value</th>
                <th className="py-3 text-xs font-semibold text-slate-500 uppercase text-right">Diff</th>
                <th className="py-3 text-xs font-semibold text-slate-500 uppercase text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {data.metrics.map((metric, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-3 font-medium text-slate-800 text-sm">{metric.metric}</td>
                  <td className="py-3 text-right text-sm text-slate-600">
                    {metric.metric.toLowerCase().includes('revenue') || metric.metric.toLowerCase().includes('profit') 
                      ? `₹${metric.source_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` 
                      : metric.source_value.toLocaleString()}
                  </td>
                  <td className="py-3 text-right text-sm text-slate-600">
                    {metric.metric.toLowerCase().includes('revenue') || metric.metric.toLowerCase().includes('profit') 
                      ? `₹${metric.database_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` 
                      : metric.database_value.toLocaleString()}
                  </td>
                  <td className={`py-3 text-right text-sm font-medium ${Math.abs(metric.difference) > 0 ? "text-amber-600" : "text-slate-400"}`}>
                    {metric.difference.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </td>
                  <td className="py-3 text-right">
                    <StatusBadge status={metric.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AnalyticsCard>
  );
}
