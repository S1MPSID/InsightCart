import React from "react";
import KPICard from "./KPICard";

function formatMoney(value) {
  if (value >= 1000000) return `₹${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
  return `₹${value.toLocaleString()}`;
}

function formatNumber(value) {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toLocaleString();
}

export default function KPIGrid({ data }) {
  if (!data) return null;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <KPICard
          title="Total Revenue"
          value={formatMoney(data.revenue)}
          isLarge
        />
        <KPICard
          title="Total Profit"
          value={formatMoney(data.profit)}
          isLarge
        />
      </div>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Orders"
          value={formatNumber(data.orders)}
        />
        <KPICard
          title="Quantity"
          value={formatNumber(data.quantity)}
        />
        <KPICard
          title="Profit Margin"
          value={`${data.margin.toFixed(1)}%`}
        />
        <KPICard
          title="Avg Order Value"
          value={formatMoney(data.average_order_value)}
        />
      </div>
    </div>
  );
}