import React from "react";
import {
    LayoutDashboard,
    BarChart3,
    Package,
    Users,
    ShieldAlert,
    AlertTriangle,
    Settings,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const menuItems = [
    { name: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
    { name: "Analytics", icon: BarChart3, path: "/analytics" },
    { name: "Products", icon: Package, path: "/products" },
    { name: "Customers", icon: Users, path: "/customers" },
    { name: "Data Quality", icon: ShieldAlert, path: "/data-quality" },
    { name: "Exceptions", icon: AlertTriangle, path: "/exceptions" },
];

export default function Sidebar() {
    const location = useLocation();

    return (
        <aside className="w-20 lg:w-24 bg-white h-[calc(100vh-48px)] my-6 ml-6 rounded-[24px] shadow-[0_4px_24px_rgb(0,0,0,0.03)] shrink-0 flex flex-col items-center py-8">
            <div className="w-12 h-12 bg-black rounded-xl flex items-center justify-center text-white mb-8">
                {/* Minimal Logo */}
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 3v18h18" />
                    <path d="m19 9-5 5-4-4-3 3" />
                </svg>
            </div>

            <nav className="flex-1 w-full flex flex-col items-center gap-4">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path || (item.path !== "/" && location.pathname.startsWith(item.path));

                    return (
                        <Link
                            key={item.name}
                            to={item.path}
                            title={item.name}
                            className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all ${
                                isActive 
                                    ? "bg-slate-900 text-white shadow-lg" 
                                    : "text-slate-500 hover:bg-slate-200 hover:text-slate-800"
                            }`}
                        >
                            <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
                        </Link>
                    );
                })}
            </nav>

            <div className="mt-auto">
                <button 
                    className="w-12 h-12 rounded-2xl flex items-center justify-center text-slate-500 hover:bg-slate-200 hover:text-slate-800 transition-all"
                    title="Settings"
                >
                    <Settings size={22} strokeWidth={2} />
                </button>
            </div>
        </aside>
    );
}