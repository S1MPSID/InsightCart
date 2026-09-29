import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format, parseISO } from "date-fns";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-slate-100 p-5 min-w-[180px]">
        <p className="text-sm font-semibold text-slate-800 mb-3 border-b border-slate-50 pb-2">
          {format(parseISO(label), "MMM d, yyyy")}
        </p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between text-sm mt-2">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-slate-500 font-medium">{entry.name}</span>
            </div>
            <span className="font-bold text-slate-900">
              {entry.name === "Revenue" || entry.name === "Profit" 
                ? `₹${entry.value.toLocaleString()}` 
                : entry.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function RevenueChart({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <AnalyticsCard 
      title="Revenue & Profit Trend" 
      className="col-span-1 lg:col-span-2"
      contentClassName="p-6 pt-0"
    >
      <div className="h-[320px] w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" opacity={0.6} />
            <XAxis 
              dataKey="period" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#94a3b8', fontSize: 13, fontWeight: 500 }}
              tickFormatter={(val) => {
                try { return format(parseISO(val), "MMM d"); } catch { return val; }
              }}
              dy={15}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#94a3b8', fontSize: 13, fontWeight: 500 }}
              tickFormatter={(val) => val >= 1000 ? `₹${(val / 1000).toFixed(0)}k` : `₹${val}`}
              tickCount={5}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }} />
            <Area 
              type="monotone" 
              dataKey="revenue" 
              name="Revenue" 
              stroke="#6366f1" 
              strokeWidth={4}
              fillOpacity={1} 
              fill="url(#colorRevenue)" 
              activeDot={{ r: 6, strokeWidth: 0, fill: '#6366f1' }}
            />
            <Area 
              type="monotone" 
              dataKey="profit" 
              name="Profit" 
              stroke="#10b981" 
              strokeWidth={4}
              fillOpacity={1} 
              fill="url(#colorProfit)" 
              activeDot={{ r: 6, strokeWidth: 0, fill: '#10b981' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </AnalyticsCard>
  );
}
