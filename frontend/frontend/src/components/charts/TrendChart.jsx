import React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ChartTooltip from "./ChartTooltip";
import { axisLineProps, axisTick, cursorStroke, gridProps } from "./chartTheme";
import { formatAxisNumber, formatMoney, formatNumber, formatPercent, formatPeriod } from "../../utils/format";

const FORMATTERS = {
  money: formatMoney,
  count: formatNumber,
  percent: (value) => formatPercent(value),
};

/**
 * Time-series chart driven by a declarative series list, so the same component
 * renders revenue vs profit, orders vs units, or margin without duplication.
 * X labels follow the granularity returned by the trends endpoint.
 */
export default function TrendChart({
  data,
  series,
  granularity = "month",
  height = 320,
  yAxisWidth = 64,
  compact = false,
}) {
  if (!data || data.length === 0) return null;

  const tooltipFormatters = series.reduce((acc, s) => {
    acc[s.name] = FORMATTERS[s.format] || formatNumber;
    return acc;
  }, {});

  const renderTooltip = (props) => (
    <ChartTooltip
      {...props}
      title={formatPeriod(props?.label, granularity, "long")}
      formatters={tooltipFormatters}
    />
  );

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
          <defs>
            {series.map((s) => (
              <linearGradient key={s.key} id={`fill-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={s.color} stopOpacity={0.18} />
                <stop offset="95%" stopColor={s.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid {...gridProps} vertical={false} />
          <XAxis
            dataKey="period"
            {...axisLineProps}
            tick={axisTick}
            minTickGap={compact ? 24 : 16}
            tickFormatter={(value) => formatPeriod(value, granularity)}
            dy={12}
          />
          <YAxis
            {...axisLineProps}
            tick={axisTick}
            tickFormatter={formatAxisNumber}
            tickCount={5}
            width={yAxisWidth}
          />
          <Tooltip
            cursor={cursorStroke}
            content={renderTooltip}
          />
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={3}
              fill={`url(#fill-${s.key})`}
              fillOpacity={1}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: s.color }}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Line variant for a single series, where a filled area would imply accumulation. */
export function TrendLine({ data, dataKey, name, color, granularity = "month", height = 220, format = "money" }) {
  if (!data || data.length === 0) return null;

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`fill-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.18} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...gridProps} vertical={false} />
          <XAxis
            dataKey="period"
            {...axisLineProps}
            tick={axisTick}
            minTickGap={24}
            tickFormatter={(value) => formatPeriod(value, granularity)}
            dy={12}
          />
          <YAxis {...axisLineProps} tick={axisTick} tickFormatter={formatAxisNumber} tickCount={4} width={64} />
          <Tooltip
            cursor={cursorStroke}
            content={(props) => (
              <ChartTooltip
                {...props}
                title={formatPeriod(props?.label, granularity, "long")}
                formatters={{ [name]: FORMATTERS[format] || formatNumber }}
              />
            )}
          />
          <Area
            type="monotone"
            dataKey={dataKey}
            name={name}
            stroke={color}
            strokeWidth={2.5}
            fill={`url(#fill-${dataKey})`}
            fillOpacity={1}
            dot={false}
            activeDot={{ r: 5, strokeWidth: 0, fill: color }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
