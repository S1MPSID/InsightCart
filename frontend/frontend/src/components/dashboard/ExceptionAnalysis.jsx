import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";
import StatusBadge from "../ui/StatusBadge";
import { AlertTriangle } from "lucide-react";
import { format, parseISO } from "date-fns";

export default function ExceptionAnalysis({ data }) {
  if (!data) return null;

  return (
    <AnalyticsCard title="Exception Analysis" className="col-span-1 lg:col-span-3" contentClassName="p-0">
      <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50/30">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-100 text-amber-600 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-slate-800">Statistical exceptions for review — not evidence of fraud.</h4>
            <p className="text-sm text-slate-500 mt-1">
              {data.total_exceptions_detected} exceptions detected across {data.total_flagged_transactions} flagged transactions.
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {Object.entries(data.count_by_type).map(([type, count]) => (
            <div key={type} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg shadow-sm text-sm">
              <span className="text-slate-500 mr-2">{type}:</span>
              <span className="font-bold text-slate-800">{count}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Exception Type</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Metric</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Value</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Threshold</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data.data.slice(0, 10).map((item, idx) => (
              <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-4 px-6 text-sm text-slate-600 whitespace-nowrap">
                  {item.date ? format(parseISO(item.date), "MMM d, yyyy") : "N/A"}
                </td>
                <td className="py-4 px-6">
                  <div className="font-medium text-slate-800">{item.exception_type}</div>
                  <div className="text-xs text-slate-500 mt-1 truncate max-w-xs" title={item.reason}>{item.reason}</div>
                </td>
                <td className="py-4 px-6 text-sm text-slate-600 font-medium">
                  {item.metric}
                </td>
                <td className="py-4 px-6 text-sm text-slate-900 font-bold text-right">
                  {item.value?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td className="py-4 px-6 text-sm text-slate-500 text-right">
                  {item.threshold?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td className="py-4 px-6">
                  <StatusBadge 
                    status={item.severity} 
                    text={item.severity} 
                    className={
                      item.severity === 'critical' ? 'bg-rose-100 text-rose-700' :
                      item.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                      'bg-amber-100 text-amber-700'
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AnalyticsCard>
  );
}
