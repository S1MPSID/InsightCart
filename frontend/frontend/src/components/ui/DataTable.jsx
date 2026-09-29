import React from "react";

/**
 * Reusable table shell so every table in the app shares header styling, scroll
 * behaviour and the loading / error / empty contract. Columns are declarative:
 *
 *   { key, header, align, width, render(row), className, headerClassName }
 */
export default function DataTable({
  columns,
  rows,
  rowKey,
  isLoading,
  error,
  onRetry,
  emptyTitle = "Nothing to show yet",
  emptyMessage = "No records matched the current filters.",
  loadingMessage = "Loading records...",
  errorMessage = "Could not load these records.",
  footer,
  maxHeight,
}) {
  if (isLoading) return <TableMessage tone="loading" message={loadingMessage} />;
  if (error) {
    return (
      <TableMessage
        tone="error"
        message={errorMessage}
        hint={typeof error === "string" ? error : undefined}
        onRetry={onRetry}
      />
    );
  }
  if (!rows || rows.length === 0) {
    return <TableMessage tone="empty" title={emptyTitle} message={emptyMessage} />;
  }

  return (
    <div className="flex flex-col min-h-0">
      <div className="overflow-auto flex-1" style={maxHeight ? { maxHeight } : undefined}>
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-slate-100 bg-slate-50/80 backdrop-blur">
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  style={col.width ? { width: col.width } : undefined}
                  className={`py-3.5 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap ${
                    col.align === "right" ? "text-right" : "text-left"
                  } ${col.headerClassName || ""}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {rows.map((row, index) => (
              <tr key={rowKey ? rowKey(row, index) : index} className="hover:bg-slate-50/60 transition-colors">
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`py-3.5 px-6 text-sm ${
                      col.align === "right" ? "text-right tabular-nums" : "text-left"
                    } ${col.className || "text-slate-600"}`}
                  >
                    {col.render ? col.render(row, index) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {footer && <div className="px-6 py-3.5 border-t border-slate-100 text-xs font-medium text-slate-400">{footer}</div>}
    </div>
  );
}

function TableMessage({ tone, message, title, hint, onRetry }) {
  const styles = {
    loading: "text-slate-400",
    empty: "text-slate-400",
    error: "text-rose-500",
  }[tone];

  return (
    <div className="flex flex-col items-center justify-center text-center px-6 py-16 gap-2">
      {tone === "loading" && (
        <div className="w-6 h-6 border-2 border-slate-200 border-t-indigo-500 rounded-full animate-spin mb-2" />
      )}
      {title && <p className="text-sm font-semibold text-slate-600">{title}</p>}
      <p className={`text-sm font-medium ${styles}`}>{message}</p>
      {hint && <p className="text-xs text-slate-400 max-w-md">{hint}</p>}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 px-4 py-2 text-xs font-semibold rounded-full bg-slate-900 text-white hover:bg-slate-700 transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  );
}
