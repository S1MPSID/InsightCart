import React from "react";
import AnalyticsCard from "../ui/AnalyticsCard";

export default function TopCustomersTable({ data, limit = 5, className = "col-span-1 lg:col-span-1" }) {
  if (!data || data.length === 0) return null;

  return (
    <AnalyticsCard title="Top Customers" className={className} contentClassName="p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">Customer</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Revenue</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Profit</th>
              <th className="py-4 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Orders</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {data.slice(0, limit).map((customer, idx) => (
              <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                <td className="py-4 px-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-xs shrink-0">
                      {customer.customer_name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800">{customer.customer_name}</div>
                      <div className="text-xs text-slate-500">{customer.state}</div>
                    </div>
                  </div>
                </td>
                <td className="py-4 px-6 text-right font-medium text-slate-700">
                  ₹{customer.revenue.toLocaleString()}
                </td>
                <td className="py-4 px-6 text-right font-medium text-emerald-600">
                  ₹{customer.profit.toLocaleString()}
                </td>
                <td className="py-4 px-6 text-right font-medium text-slate-600">
                  {customer.orders.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AnalyticsCard>
  );
}
