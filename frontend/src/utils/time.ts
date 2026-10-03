import { locale, t } from "@/i18n";

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

const fmts = new Map<string, Intl.DateTimeFormat>();
/** Форматтер дат под текущий язык интерфейса (кэш по языку и параметрам). */
export function dateFmt(opts: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const key = locale.value + JSON.stringify(opts);
  let f = fmts.get(key);
  if (!f) fmts.set(key, (f = new Intl.DateTimeFormat(locale.value, opts)));
  return f;
}

/** Подпись времени уведомления: «5 мин назад», «сегодня, 09:10», «вчера, 18:12», «28.09, 14:00». */
export function ago(iso: string, now = Date.now()): string {
  const min = Math.floor((now - Date.parse(iso)) / 60_000);
  if (min < 1) return t("time.justNow");
  if (min < 60) return t("time.minAgo", { n: min });
  const { date, minutes } = localParts(new Date(iso));
  const today = localParts(new Date(now)).date;
  const day =
    date === today ? t("time.today") : date === addDays(today, -1) ? t("time.yesterday")
    : dateFmt({ day: "2-digit", month: "2-digit", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`));
  return `${day}, ${hhmm(minutes)}`;
}

/**
 * Статус комнаты сейчас по сегодняшним броням (минуты от полуночи):
 * занята — до конца текущей брони с учётом стыкующихся, свободна — до начала следующей (null = до конца дня).
 */
export function roomStatus(busy: { start: number; end: number }[], now: number): { busy: boolean; until: number | null } {
  const sorted = [...busy].sort((a, b) => a.start - b.start);
  const i = sorted.findIndex((b) => b.start <= now && now < b.end);
  if (i < 0) return { busy: false, until: sorted.find((b) => b.start > now)?.start ?? null };
  let until = sorted[i].end;
  for (const b of sorted.slice(i + 1)) if (b.start <= until) until = Math.max(until, b.end);
  return { busy: true, until };
}

/** Ближайший час с начала следующего шага; если день кончился — завтра с начала дня. */
export function nextSlot(now = new Date()): { date: string; start: number; end: number } {
  const p = localParts(now);
  let date = p.date, start = Math.max(Math.ceil(p.minutes / STEP) * STEP, DAY_START);
  if (start + STEP > DAY_END) [date, start] = [addDays(date, 1), DAY_START];
  return { date, start, end: Math.min(start + 60, DAY_END) };
}

/** Свободное окно вокруг [start, end) в пределах рабочего дня: от конца предыдущей брони до начала следующей. */
export function freeWindow(busy: { start: number; end: number }[], start: number, end: number): { from: number; to: number } {
  return {
    from: Math.max(DAY_START, ...busy.filter((b) => b.end <= start).map((b) => b.end)),
    to: Math.min(DAY_END, ...busy.filter((b) => b.start >= end).map((b) => b.start)),
  };
}

/** plural(5, "plural.rooms") → «5 комнат»; формы слова лежат в локалях («{n} комната | {n} комнаты | {n} комнат») */
export const plural = (n: number, key: string) => t(key, { n }, n);

/** «Сегодня», «Завтра», «Вчера» или «Пятница, 2 октября» */
export function dayTitle(date: string, today = todayLocal()): string {
  const near = { [today]: "time.todayCap", [addDays(today, 1)]: "time.tomorrow", [addDays(today, -1)]: "time.yesterdayCap" }[date];
  if (near) return t(near);
  const s = dateFmt({ weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`));
  return s[0].toUpperCase() + s.slice(1);
}
