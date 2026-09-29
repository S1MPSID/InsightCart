import React, { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import api from "../services/api";
import DataQualityCard from "../components/dashboard/DataQualityCard";
import ReconciliationCard from "../components/dashboard/ReconciliationCard";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";

export default function DataQuality() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({ quality: null, reconciliation: null });

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [qRes, rRes] = await Promise.all([
          api.get("/data-quality"),
          api.get("/reconciliation")
        ]);
        setData({ quality: qRes.data, reconciliation: rRes.data });
      } catch (err) {
        console.error("Failed to fetch data quality:", err);
        setError("Unable to load data quality metrics.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><LoadingState message="Loading quality metrics..." /></div></Layout>;
  if (error) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><ErrorState message={error} /></div></Layout>;

  return (
    <Layout>
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-800">Data Governance & Quality</h1>
        <p className="text-slate-500">Automated integrity checks and system reconciliation.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <DataQualityCard data={data.quality} className="col-span-1 lg:col-span-1" />
        <ReconciliationCard data={data.reconciliation} className="col-span-1 lg:col-span-2" />
      </div>
    </Layout>
  );
}
