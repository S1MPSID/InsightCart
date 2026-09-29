import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";
import StatusBadge from "../ui/StatusBadge";
import { CheckCircle2, AlertCircle, Info as InfoIcon } from "lucide-react";

export default function DataQualityCard({ data }) {
  if (!data) return null;

  return (
    <AnalyticsCard title="Data Quality" subtitle="Automated integrity checks" className="col-span-1 lg:col-span-1">
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-6 p-4 rounded-2xl bg-slate-50/50 border border-slate-100">
          <div className="flex flex-col">
            <span className="text-sm font-medium text-slate-500 mb-1">Status</span>
            <StatusBadge status={data.overall_status} text={data.overall_status === 'PASS' ? 'Healthy' : 'Issues Found'} className="w-fit text-sm px-3 py-1" />
          </div>
          
          <div className="w-px h-10 bg-slate-200"></div>
          
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              <div>
                <div className="font-bold text-slate-800">{data.passed}</div>
                <div className="text-xs text-slate-500">Passed</div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <AlertCircle className={`w-5 h-5 ${data.failed > 0 ? "text-rose-500" : "text-slate-300"}`} />
              <div>
                <div className={`font-bold ${data.failed > 0 ? "text-rose-600" : "text-slate-800"}`}>{data.failed}</div>
                <div className="text-xs text-slate-500">Failed</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <InfoIcon className="w-5 h-5 text-amber-500" />
              <div>
                <div className="font-bold text-slate-800">{data.informational}</div>
                <div className="text-xs text-slate-500">Info</div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {data.checks.map((check, idx) => (
            <div key={idx} className="flex flex-col gap-1.5 pb-4 border-b border-slate-50 last:border-0 last:pb-0">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-800">{check.name}</span>
                <StatusBadge status={check.status} />
              </div>
              <p className="text-sm text-slate-500">{check.description}</p>
              {check.status !== 'PASS' && (
                <p className="text-sm text-rose-600 bg-rose-50 px-3 py-2 rounded-lg mt-1">{check.explanation}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </AnalyticsCard>
  );
}
