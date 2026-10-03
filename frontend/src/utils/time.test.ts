import { beforeAll, expect, test } from "vitest";
import { locale } from "@/i18n";
import { addDays, ago, dayRange, dayTitle, freeWindow, hhmm, localParts, nextSlot, plural, roomStatus, zonedToUtc } from "./time";

beforeAll(() => (locale.value = "ru"));

test("локальное время организации (UTC+3) ↔ UTC", () => {
  expect(zonedToUtc("2030-01-15", 10 * 60).toISOString()).toBe("2030-01-15T07:00:00.000Z");
  expect(localParts(new Date("2030-01-15T21:30:00Z"))).toEqual({ date: "2030-01-16", minutes: 30 }); // через полночь
  expect(dayRange("2030-01-15")).toEqual({ from: "2030-01-14T21:00:00.000Z", to: "2030-01-15T21:00:00.000Z" });
});

test("addDays и hhmm", () => {
  expect(addDays("2030-02-28", 1)).toBe("2030-03-01");
  expect(addDays("2030-01-01", -1)).toBe("2029-12-31");
  expect(hhmm(8 * 60 + 5)).toBe("08:05");
});

test("ago: подпись времени уведомления", () => {
  const now = Date.parse("2030-01-15T07:35:00Z"); // 10:35 по Москве
  expect(ago("2030-01-15T07:34:30Z", now)).toBe("только что");
  expect(ago("2030-01-15T07:33:00Z", now)).toBe("2 мин назад");
  expect(ago("2030-01-15T06:10:00Z", now)).toBe("сегодня, 09:10");
  expect(ago("2030-01-14T15:12:00Z", now)).toBe("вчера, 18:12");
  expect(ago("2030-01-12T11:00:00Z", now)).toBe("12.01, 14:00");
});

test("roomStatus: занята до конца цепочки броней, свободна до следующей", () => {
  const b = [{ start: 600, end: 660 }, { start: 660, end: 690 }, { start: 840, end: 900 }];
  expect(roomStatus(b, 620)).toEqual({ busy: true, until: 690 }); // 10:00–11:00 + встык 11:00–11:30
  expect(roomStatus(b, 690)).toEqual({ busy: false, until: 840 }); // полуоткрытый интервал
  expect(roomStatus(b, 910)).toEqual({ busy: false, until: null });
  expect(roomStatus([], 600)).toEqual({ busy: false, until: null });
});

test("nextSlot: округление вверх до шага, утро → начало дня, вечер → завтра", () => {
  expect(nextSlot(zonedToUtc("2030-01-15", 10 * 60 + 5))).toEqual({ date: "2030-01-15", start: 615, end: 675 });
  expect(nextSlot(zonedToUtc("2030-01-15", 6 * 60))).toEqual({ date: "2030-01-15", start: 480, end: 540 });
  expect(nextSlot(zonedToUtc("2030-01-15", 19 * 60 + 30))).toEqual({ date: "2030-01-15", start: 1170, end: 1200 });
  expect(nextSlot(zonedToUtc("2030-01-15", 19 * 60 + 50))).toEqual({ date: "2030-01-16", start: 480, end: 540 });
});

test("freeWindow, plural, dayTitle", () => {
  const busy = [{ start: 600, end: 690 }, { start: 960, end: 1020 }, { start: 700, end: 720 }];
  expect(freeWindow(busy, 840, 900)).toEqual({ from: 720, to: 960 });
  expect(freeWindow([], 840, 900)).toEqual({ from: 480, to: 1200 });
  expect([1, 3, 5, 21].map((n) => plural(n, "plural.freeRooms"))).toEqual(["Свободна 1 комната", "Свободны 3 комнаты", "Свободны 5 комнат", "Свободна 21 комната"]);
  expect(dayTitle("2030-01-16", "2030-01-15")).toBe("Завтра");
  expect(dayTitle("2030-01-18", "2030-01-15")).toBe("Пятница, 18 января");
});

test("английская локаль: подписи и plural", () => {
  locale.value = "en";
  try {
    const now = Date.parse("2030-01-15T07:35:00Z");
    expect(ago("2030-01-15T07:33:00Z", now)).toBe("2 min ago");
    expect(ago("2030-01-14T15:12:00Z", now)).toBe("yesterday, 18:12");
    expect(dayTitle("2030-01-18", "2030-01-15")).toBe("Friday, January 18");
    expect([1, 3].map((n) => plural(n, "plural.bookings"))).toEqual(["1 booking", "3 bookings"]);
  } finally {
    locale.value = "ru";
  }
});
