import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";
import { TrendingUp, TrendingDown } from "lucide-react";

export default function KPICard({ title, value, change, positive, isLarge = false }) {
  return (
    <AnalyticsCard className={isLarge ? "bg-gradient-to-br from-white to-slate-50 border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)]" : "shadow-[0_2px_10px_rgb(0,0,0,0.02)] border-none"}>
      <div className={`flex flex-col h-full justify-between gap-4 ${isLarge ? 'p-2' : ''}`}>
        <h3 className={`font-medium ${isLarge ? 'text-slate-500 text-lg' : 'text-slate-400 text-sm'}`}>{title}</h3>
        
        <div className="flex items-end justify-between">
          <div className={`font-extrabold tracking-tight text-slate-900 ${isLarge ? "text-5xl lg:text-6xl" : "text-3xl"}`}>
            {value}
          </div>
          
          {change && (
            <div className={`flex items-center gap-1 font-semibold mb-1 ${isLarge ? 'text-base' : 'text-xs'} ${positive ? "text-emerald-500" : "text-rose-500"}`}>
              {positive ? <TrendingUp size={isLarge ? 20 : 14} /> : <TrendingDown size={isLarge ? 20 : 14} />}
              <span>{change}</span>
            </div>
          )}
        </div>
      </div>
    </AnalyticsCard>
  );
}