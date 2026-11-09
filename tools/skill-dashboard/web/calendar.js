// Page layer: day and month arithmetic on "YYYY-MM-DD" / "YYYY-MM" strings,
// done in UTC so a time zone or daylight-saving change never shifts a day.

const DAY_MS = 864e5;
const MONTHS_IN_YEAR = 12;

export const addDays = (day, n) => new Date(Date.parse(`${day}T00:00:00Z`) + n * DAY_MS).toISOString().slice(0, 10);

const nextMonth = (month) => {
  const [year, number] = month.split("-").map(Number);
  return number === MONTHS_IN_YEAR ? `${year + 1}-01` : `${year}-${String(number + 1).padStart(2, "0")}`;
};

/** Every day of `month`, from `firstDay` at the earliest to `today` at the latest. */
export function monthDays(month, firstDay, today) {
  const last = addDays(`${nextMonth(month)}-01`, -1);
  const days = [];
  for (let day = `${month}-01` < firstDay ? firstDay : `${month}-01`; day <= (last < today ? last : today); day = addDays(day, 1)) days.push(day);
  return days;
}

/** Month ids from `first` to `last`, inclusive. */
export function monthsBetween(first, last) {
  const out = [];
  for (let m = first; m <= last; m = nextMonth(m)) out.push(m);
  return out;
}
