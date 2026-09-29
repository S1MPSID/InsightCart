import React from "react";

export default function AnalyticsCard({ title, subtitle, action, children, className = "", contentClassName = "p-6" }) {
  return (
    <div className={`bg-white rounded-[28px] shadow-[0_4px_24px_rgb(0,0,0,0.03)] overflow-hidden flex flex-col h-full ${className}`}>
      {(title || subtitle || action) && (
        <div className="px-7 pt-7 pb-4 flex items-center justify-between">
          <div>
            {title && <h3 className="text-lg font-bold text-slate-800">{title}</h3>}
            {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={`flex-1 flex flex-col ${contentClassName}`}>
        {children}
      </div>
    </div>
  );
}
