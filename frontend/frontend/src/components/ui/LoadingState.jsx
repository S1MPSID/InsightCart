import React from "react";
import { Loader2 } from "lucide-react";

export default function LoadingState({ message = "Loading data..." }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px] w-full text-slate-400">
      <Loader2 className="w-8 h-8 animate-spin mb-4 text-indigo-400" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
