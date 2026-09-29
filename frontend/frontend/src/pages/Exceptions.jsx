import React, { useState, useEffect } from "react";
import Layout from "../components/layout/Layout";
import api from "../services/api";
import ExceptionAnalysis from "../components/dashboard/ExceptionAnalysis";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";

export default function Exceptions() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exceptions, setExceptions] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const res = await api.get("/exceptions");
        setExceptions(res.data);
      } catch (err) {
        console.error("Failed to fetch exceptions:", err);
        setError("Unable to load exceptions data.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><LoadingState message="Loading exceptions..." /></div></Layout>;
  if (error) return <Layout><div className="h-full flex items-center justify-center min-h-[60vh]"><ErrorState message={error} /></div></Layout>;

  return (
    <Layout>
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-slate-800">Statistical Exception Analysis</h1>
        <p className="text-slate-500">Exceptions indicate statistical unusualness and are not evidence of fraud, error, or misconduct.</p>
      </div>
      <div className="grid grid-cols-1 gap-8">
        <ExceptionAnalysis data={exceptions} className="col-span-1" />
      </div>
    </Layout>
  );
}
