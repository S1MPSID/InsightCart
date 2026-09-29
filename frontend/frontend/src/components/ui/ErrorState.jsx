import React from "react";
import { AlertCircle } from "lucide-react";

export default function ErrorState({ message = "Failed to load data." }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px] w-full text-rose-500 bg-rose-50/50 rounded-3xl p-6 border border-rose-100">
      <AlertCircle className="w-8 h-8 mb-4 opacity-80" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
