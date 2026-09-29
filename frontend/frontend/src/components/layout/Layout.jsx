import React from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function Layout({ children }) {
    return (
        <div className="flex h-screen bg-[#EEF2F6] font-sans text-slate-800 overflow-hidden relative">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto px-6 md:px-10 pb-10">
                    <div className="max-w-[1600px] mx-auto h-full flex flex-col gap-8">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}