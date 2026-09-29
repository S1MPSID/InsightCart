/**
 * Shared Recharts axis and grid styling. Kept out of the tooltip component so
 * each chart file exports only components, which keeps React Fast Refresh
 * working during development.
 */
export const axisTick = { fill: "#94a3b8", fontSize: 12, fontWeight: 500 };

export const axisLineProps = { axisLine: false, tickLine: false };

export const gridProps = { strokeDasharray: "3 3", stroke: "#f1f5f9" };

export const cursorStroke = { stroke: "#cbd5e1", strokeWidth: 1, strokeDasharray: "4 4" };
