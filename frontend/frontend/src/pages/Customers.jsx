import React, { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import api from "../services/api";
import TopCustomersTable from "../components/dashboard/TopCustomersTable";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import AnalyticsCard from "../components/ui/AnalyticsCard";

export default function Customers() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [customers, setCustomers] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const res = await api.get("/customers");
        setCustomers(res.data.data);
      } catch (err) {
        console.error("Failed to fetch customers:", err);
        setError("Unable to load customers data.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><LoadingState message="Loading customers..." /></div></Layout>;
  if (error) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><ErrorState message={error} /></div></Layout>;

  return (
    <Layout>
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-800">Customer Analytics</h1>
        <p className="text-slate-500">Analyze top customers and purchasing behavior.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <TopCustomersTable data={customers} limit={20} className="col-span-1 lg:col-span-2" />
        <AnalyticsCard title="Customer Summary" className="col-span-1 lg:col-span-1" contentClassName="p-6">
          <div className="flex flex-col gap-4">
            <div>
              <div className="text-sm text-slate-500">Total Key Customers</div>
              <div className="text-4xl font-extrabold text-slate-800 mt-2">{customers?.length || 0}</div>
            </div>
            <div className="w-full h-px bg-slate-100 my-2"></div>
            <div>
              <div className="text-sm text-slate-500">Top Customer by Revenue</div>
              <div className="text-lg font-semibold text-slate-800 mt-1">{customers?.[0]?.customer_name || 'N/A'}</div>
              <div className="text-sm text-slate-500">{customers?.[0] ? `₹${customers[0].revenue.toLocaleString()}` : ''}</div>
            </div>
          </div>
        </AnalyticsCard>
      </div>
    </Layout>
  );
}
