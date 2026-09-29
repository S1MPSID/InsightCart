import React from "react";
import { Search, Settings, User } from "lucide-react";

export default function Header() {
  return (
    <header className="px-8 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
          Welcome back.
        </h1>
        <p className="text-slate-500 font-medium mt-1">
          Your Retail Analytics Overview
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search analytics..."
            className="pl-10 pr-4 py-2.5 bg-white border-none rounded-full text-sm shadow-[0_2px_10px_rgb(0,0,0,0.03)] focus:outline-none focus:ring-2 focus:ring-indigo-100 w-64 transition-all"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <button className="p-2.5 rounded-full bg-white text-slate-500 hover:bg-slate-50 shadow-[0_2px_10px_rgb(0,0,0,0.03)] transition-colors">
            <Settings className="w-5 h-5" />
          </button>
          <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold ml-2 shadow-[0_2px_10px_rgb(0,0,0,0.03)] overflow-hidden">
            <User className="w-5 h-5" />
          </div>
        </div>
      </div>
    </header>
  );
}
