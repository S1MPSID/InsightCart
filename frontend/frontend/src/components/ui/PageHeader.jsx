import React from "react";

/**
 * The single page header used by every route. Layout renders it through Header
 * so the title, description and action slot stay in the same place on all pages.
 */
export default function PageHeader({ title, description, actions, meta }) {
  return (
    <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
          {title}
        </h1>
        {description && (
          <p className="text-slate-500 font-medium mt-1 max-w-3xl">{description}</p>
        )}
        {meta && <div className="text-xs text-slate-400 font-medium mt-2">{meta}</div>}
      </div>
      {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
    </div>
  );
}
