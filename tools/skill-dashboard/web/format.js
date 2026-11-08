// Formatting helpers. Generic: no business knowledge, no copy of their own.

// Calendar units in seconds, largest first; months and years are averages,
// which is all a "3 months ago" label needs.
const MINUTE = 60;
const HOUR = MINUTE * MINUTE;
const DAY = HOUR * 24;
const WEEK = DAY * 7;
const YEAR = DAY * 365;
const MONTH = YEAR / 12;
const MS = 1000;
export const DAY_MS = DAY * MS;

/** True when `value` falls within the last `days` days. */
export const isRecent = (value, days) => Boolean(value) && Date.now() - new Date(value).getTime() < days * DAY_MS;

const SECONDS = [["year", YEAR], ["month", MONTH], ["week", WEEK], ["day", DAY], ["hour", HOUR], ["minute", MINUTE]];
const relativeFormat = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
const dayFormat = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
const fullFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const numberFormat = new Intl.NumberFormat();

const toDate = (value) => (value instanceof Date ? value : new Date(value));

export function relative(value, { justNow, never }) {
  if (!value) return never;
  const elapsed = (Date.now() - toDate(value).getTime()) / 1000;
  for (const [unit, size] of SECONDS) {
    if (Math.abs(elapsed) >= size) return relativeFormat.format(-Math.round(elapsed / size), unit);
  }
  return justNow;
}

export const day = (value) => (value ? dayFormat.format(toDate(value)) : "");
export const full = (value) => (value ? fullFormat.format(toDate(value)) : "");
export const number = (value) => numberFormat.format(value ?? 0);

// A calendar date from the server ("2026-11-08") is a local day, not UTC midnight.
export function localDay(isoDate) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function shortPath(path, keep = 2) {
  if (!path) return "";
  const parts = path.split("/").filter(Boolean);
  return parts.length > keep ? "…/" + parts.slice(-keep).join("/") : path;
}
