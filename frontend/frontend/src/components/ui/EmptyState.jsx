import React from "react";
import { Info } from "lucide-react";

export default function EmptyState({ message = "No data available." }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px] w-full text-slate-400 bg-slate-50/50 rounded-3xl p-6 border border-slate-100 border-dashed">
      <Info className="w-8 h-8 mb-4 opacity-50" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
