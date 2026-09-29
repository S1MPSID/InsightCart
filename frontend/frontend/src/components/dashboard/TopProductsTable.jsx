import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";

export default function TopProductsTable({ data, limit = 5, className = "col-span-1 lg:col-span-2" }) {
  if (!data || data.length === 0) return null;

  return (
    <AnalyticsCard title="Top Products" className={className} contentClassName="p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Product</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Category</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Revenue</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Profit</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Qty</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data.slice(0, limit).map((product, idx) => (
              <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-4 px-6">
                  <div className="font-semibold text-slate-800">{product.product_name}</div>
                  <div className="text-xs text-slate-500">{product.brand}</div>
                </td>
                <td className="py-4 px-6">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                    {product.category}
                  </span>
                </td>
                <td className="py-4 px-6 text-right font-medium text-slate-700">
                  ₹{product.revenue.toLocaleString()}
                </td>
                <td className="py-4 px-6 text-right font-medium text-emerald-600">
                  ₹{product.profit.toLocaleString()}
                </td>
                <td className="py-4 px-6 text-right font-medium text-slate-600">
                  {product.quantity.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AnalyticsCard>
  );
}
