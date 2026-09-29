import React from "react";

export default function StatusBadge({ status, text, className = "" }) {
  let styles = "bg-slate-100 text-slate-600";
  
  const s = (status || "").toUpperCase();
  if (s === "PASS" || s === "SUCCESS" || s === "LOW") {
    styles = "bg-emerald-100 text-emerald-700";
  } else if (s === "FAIL" || s === "ERROR" || s === "CRITICAL" || s === "HIGH") {
    styles = "bg-rose-100 text-rose-700";
  } else if (s === "INFO" || s === "MEDIUM" || s === "WARNING") {
    styles = "bg-amber-100 text-amber-700";
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${styles} ${className}`}>
      {text || status}
    </span>
  );
}
