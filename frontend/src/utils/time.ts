// Единственное место работы с часовыми поясами: API в UTC, интерфейс — в зоне организации.
export const ORG_TZ = "Europe/Moscow";
export const DAY_START = 8 * 60; // рабочий день, минуты от полуночи
export const DAY_END = 20 * 60;
export const STEP = 15;

const fmt = new Intl.DateTimeFormat("en-CA", {
  timeZone: ORG_TZ, hourCycle: "h23",
  year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
});

/** Локальная дата организации (YYYY-MM-DD) и минуты от её полуночи. */
export function localParts(d: Date): { date: string; minutes: number } {
  const p = Object.fromEntries(fmt.formatToParts(d).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, minutes: +p.hour * 60 + +p.minute };
}

const asUtc = (date: string, minutes: number) => Date.parse(`${date}T00:00:00Z`) + minutes * 60_000;

/** Момент времени по локальной дате организации и минутам от полуночи. */
export function zonedToUtc(date: string, minutes: number): Date {
  const guess = asUtc(date, minutes);
  const p = localParts(new Date(guess));
  return new Date(guess - (asUtc(p.date, p.minutes) - guess)); // поправка на смещение зоны
}

export const addDays = (date: string, n: number) => new Date(asUtc(date, 0) + n * 86_400_000).toISOString().slice(0, 10);

export const todayLocal = () => localParts(new Date()).date;

/** Границы локальных суток для запроса к API. */
export const dayRange = (date: string) => ({
  from: zonedToUtc(date, 0).toISOString(),
  to: zonedToUtc(addDays(date, 1), 0).toISOString(),
});

export const hhmm = (minutes: number) =>
  `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
