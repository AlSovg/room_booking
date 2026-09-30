import { expect, test } from "vitest";
import { addDays, ago, dayRange, hhmm, localParts, roomStatus, zonedToUtc } from "./time";

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
