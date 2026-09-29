import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-slate-100 p-5 min-w-[180px]">
        <p className="text-sm font-semibold text-slate-800 mb-3 border-b border-slate-50 pb-2">{label}</p>
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

export default function CategoryPerformance({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <AnalyticsCard title="Category Performance" className="col-span-1 lg:col-span-1" contentClassName="p-6 pt-0">
      <div className="h-[320px] w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" opacity={0.6} />
            <XAxis 
              type="number"
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#94a3b8', fontSize: 13, fontWeight: 500 }}
              tickFormatter={(val) => val >= 1000 ? `₹${(val / 1000).toFixed(0)}k` : `₹${val}`}
            />
            <YAxis 
              dataKey="category" 
              type="category" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#475569', fontSize: 13, fontWeight: 500 }}
              width={100}
            />
            <Tooltip content={<CustomTooltip />} cursor={{fill: '#f8fafc'}} />
            <Bar dataKey="revenue" name="Revenue" fill="#3b82f6" radius={[0, 6, 6, 0]} barSize={16} />
            <Bar dataKey="profit" name="Profit" fill="#8b5cf6" radius={[0, 6, 6, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </AnalyticsCard>
  );
}
