import React, { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import api from "../services/api";
import RevenueChart from "../components/dashboard/RevenueChart";
import CategoryPerformance from "../components/dashboard/CategoryPerformance";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [data, setData] = useState({
    trends: null,
    categories: null
  });

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [trendsRes, categoriesRes] = await Promise.all([
          api.get("/trends?granularity=month"),
          api.get("/categories")
        ]);
        setData({
          trends: trendsRes.data.data,
          categories: categoriesRes.data.data
        });
      } catch (err) {
        console.error("Failed to fetch analytics data:", err);
        setError("Unable to load analytics data.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><LoadingState message="Loading analytics..." /></div></Layout>;
  if (error) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><ErrorState message={error} /></div></Layout>;

  return (
    <Layout>
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-800">Business Analytics</h1>
        <p className="text-slate-500">Deep dive into your sales and category performance.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <RevenueChart data={data.trends} />
        <CategoryPerformance data={data.categories} />
      </div>
    </Layout>
  );
}
