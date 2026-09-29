import React, { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import api from "../services/api";

import KPIGrid from "../components/dashboard/KPIGrid";
import RevenueChart from "../components/dashboard/RevenueChart";
import CategoryPerformance from "../components/dashboard/CategoryPerformance";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [data, setData] = useState({
    summary: null,
    trends: null,
    categories: null
  });

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [summaryRes, trendsRes, categoriesRes] = await Promise.all([
          api.get("/dashboard-summary"),
          api.get("/trends?granularity=month"),
          api.get("/categories")
        ]);

        setData({
          summary: summaryRes.data,
          trends: trendsRes.data.data,
          categories: categoriesRes.data.data
        });
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Unable to load analytics data. Please ensure the backend is running.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center min-h-[60vh]">
          <LoadingState message="Loading your workspace..." />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center min-h-[60vh]">
          <ErrorState message={error} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <KPIGrid data={data.summary} />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <RevenueChart data={data.trends} />
        <CategoryPerformance data={data.categories} />
      </div>
    </Layout>
  );
}