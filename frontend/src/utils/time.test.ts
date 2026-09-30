import { expect, test } from "vitest";
import { addDays, dayRange, hhmm, localParts, zonedToUtc } from "./time";

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
