const CURRENCY = "INR";
const LOCALE = "en-IN";

const moneyFormatter = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const moneyPreciseFormatter = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const numberFormatter = new Intl.NumberFormat(LOCALE);

function isNumeric(value) {
  return typeof value === "number" && Number.isFinite(value);
}

/** Full currency value, e.g. 1,21,89,606. Rounded to whole units for readability. */
export function formatMoney(value) {
  if (!isNumeric(value)) return "—";
  return moneyFormatter.format(value);
}

/** Full currency value with paise, for reconciliation figures that must tie out exactly. */
export function formatMoneyPrecise(value) {
  if (!isNumeric(value)) return "—";
  return moneyPreciseFormatter.format(value);
}

/** Compact currency for KPI tiles and axis ticks, e.g. Rs 12.2Cr. */
export function formatMoneyCompact(value) {
  if (!isNumeric(value)) return "—";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1e7) return `${sign}₹${trim(abs / 1e7)}Cr`;
  if (abs >= 1e5) return `${sign}₹${trim(abs / 1e5)}L`;
  if (abs >= 1e3) return `${sign}₹${trim(abs / 1e3)}K`;
  return `${sign}₹${numberFormatter.format(abs)}`;
}

/** Compact plain number for counts and axis ticks, e.g. 1.2Cr / 45.6K. */
export function formatNumberCompact(value) {
  if (!isNumeric(value)) return "—";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1e7) return `${sign}${trim(abs / 1e7)}Cr`;
  if (abs >= 1e5) return `${sign}${trim(abs / 1e5)}L`;
  if (abs >= 1e3) return `${sign}${trim(abs / 1e3)}K`;
  return `${sign}${numberFormatter.format(abs)}`;
}

export function formatNumber(value) {
  if (!isNumeric(value)) return "—";
  return numberFormatter.format(value);
}

export function formatPercent(value, digits = 1) {
  if (!isNumeric(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

/** Axis ticks stay symbol-free so the label column does not repeat the unit. */
export function formatAxisNumber(value) {
  if (!isNumeric(value)) return "";
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1e7) return `${sign}${trim(abs / 1e7)}Cr`;
  if (abs >= 1e5) return `${sign}${trim(abs / 1e5)}L`;
  if (abs >= 1e3) return `${sign}${trim(abs / 1e3)}K`;
  return `${sign}${numberFormatter.format(abs)}`;
}

function trim(value) {
  const fixed = value.toFixed(1);
  return fixed.endsWith(".0") ? fixed.slice(0, -2) : fixed;
}

const PERIOD_LABELS = {
  day: { short: "d MMM", long: "d MMM yyyy" },
  week: { short: "d MMM", long: "week of d MMM yyyy" },
  month: { short: "MMM yyyy", long: "MMMM yyyy" },
  quarter: { short: "MMM yyyy", long: "QQQ yyyy" },
  year: { short: "yyyy", long: "yyyy" },
};

/**
 * The API returns a truncated calendar date per period (e.g. 2022-01-01 for the
 * month of January), so every label is derived from that single value.
 */
export function formatPeriod(period, granularity = "day", variant = "short") {
  if (!period) return "—";
  const date = new Date(`${String(period).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(period);

  const format = PERIOD_LABELS[granularity] || PERIOD_LABELS.day;
  const month = date.toLocaleString(LOCALE, { month: "short" });
  const fullMonth = date.toLocaleString(LOCALE, { month: "long" });
  const day = date.getDate();
  const year = date.getFullYear();

  if (granularity === "year") return String(year);
  if (granularity === "quarter") {
    const quarter = Math.floor(date.getMonth() / 3) + 1;
    return variant === "long" ? `Q${quarter} ${year}` : `Q${quarter} ${year}`;
  }
  if (granularity === "month") {
    return variant === "long" ? `${fullMonth} ${year}` : `${month} ${year}`;
  }
  if (variant === "long") return `${format.long.replace("d MMM yyyy", `${day} ${month} ${year}`)}`;
  return `${day} ${month}`;
}

/** Full calendar date, e.g. 7 Dec 2025. */
export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.getDate()} ${date.toLocaleString(LOCALE, { month: "short" })} ${date.getFullYear()}`;
}

/** Timestamp with time, for "generated at" provenance lines. */
export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(LOCALE, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

const EXCEPTION_TYPE_LABELS = {
  unusually_high_sales_amount: "High sales amount",
  unusually_high_quantity: "High quantity",
  unusually_high_profit: "High profit",
  extreme_profit_margin: "Extreme margin",
  invalid_transaction_values: "Invalid values",
};

export function humaniseExceptionType(type) {
  if (!type) return "Unknown";
  return EXCEPTION_TYPE_LABELS[type] || type.replace(/_/g, " ");
}

export function humaniseKey(key) {
  if (!key) return "";
  return String(key).replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

export function initials(name) {
  if (!name) return "?";
  return String(name).trim().charAt(0).toUpperCase();
}
