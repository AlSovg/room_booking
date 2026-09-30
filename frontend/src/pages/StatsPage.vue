<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { DAY_END, DAY_START, addDays, plural, todayLocal } from "@/utils/time";

type S = components["schemas"];
const to = ref(todayLocal());
const from = ref(addDays(todayLocal(), -29));
const summary = ref<S["StatsSummary"] | null>(null);
const rooms = ref<S["RoomStat"][]>([]);
const users = ref<S["UserStat"][]>([]);
const peak = ref<S["PeakCell"][]>([]);
const error = ref<string | null>(null);

watchEffect(async (onCleanup) => {
  let stale = false;
  onCleanup(() => (stale = true));
  const params = { params: { query: { from: from.value, to: to.value } } };
  const [s, r, u, p] = await Promise.all([
    api.GET("/api/v1/stats/summary", params),
    api.GET("/api/v1/stats/rooms", params),
    api.GET("/api/v1/stats/users", params),
    api.GET("/api/v1/stats/peak-hours", params),
  ]);
  if (stale) return;
  error.value = s.data && r.data && u.data && p.data ? null : errorMessage(s.error ?? r.error ?? u.error ?? p.error);
  summary.value = s.data ?? null;
  rooms.value = [...(r.data ?? [])].sort((a, b) => b.utilization - a.utilization);
  users.value = [...(u.data ?? [])].sort((a, b) => b.hours - a.hours);
  peak.value = p.data ?? [];
});

const presets: [string, number][] = [["7 дней", 7], ["30 дней", 30], ["Квартал", 90]];
const setPreset = (n: number) => {
  to.value = todayLocal();
  from.value = addDays(to.value, 1 - n);
};
const isPreset = (n: number) => to.value === todayLocal() && from.value === addDays(to.value, 1 - n);
const days = computed(() => Math.round((Date.parse(to.value) - Date.parse(from.value)) / 86_400_000) + 1);
const dmy = (d: string) => d.split("-").reverse().join(".");

const pct = (x: number) => `${(x * 100).toFixed(1).replace(".", ",")}%`;
const bookedHours = computed(() => Math.round(rooms.value.reduce((a, r) => a + r.booked_minutes, 0) / 60));

// тепловая карта: день недели (1–7) × час рабочего дня
const weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const hours = Array.from({ length: (DAY_END - DAY_START) / 60 }, (_, i) => DAY_START / 60 + i);
const cell = computed(() => new Map(peak.value.map((c) => [`${c.weekday}-${c.hour}`, c])));
const maxMinutes = computed(() => Math.max(1, ...peak.value.map((c) => c.booked_minutes)));
const heat = (wd: number, h: number) => {
  const c = cell.value.get(`${wd}-${h}`);
  return c
    ? { style: { background: `rgba(0, 119, 255, ${(0.08 + 0.87 * (c.booked_minutes / maxMinutes.value)).toFixed(2)})` }, title: `${plural(c.bookings, ["бронь", "брони", "броней"])}, ${c.booked_minutes} мин` }
    : { style: undefined, title: undefined };
};

/** CSV отдаёт бэкенд (`;` и BOM для Excel); качаем с токеном и сохраняем как файл. */
async function download(kind: "summary" | "rooms" | "users" | "peak-hours") {
  const { data, error: e } = await api.GET(`/api/v1/stats/${kind}`, {
    params: { query: { from: from.value, to: to.value, format: "csv" } },
    parseAs: "blob",
  });
  if (!data) return (error.value = errorMessage(e));
  const a = document.createElement("a");
  a.href = URL.createObjectURL(data as Blob);
  a.download = `${kind}_${from.value}_${to.value}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
</script>

<template>
  <div class="page stats-page">
    <div class="my-head">
      <h1 class="title-icon"><Icon name="ChartColumn" :size="26" />Статистика</h1>
      <div class="period">
        <button v-for="[l, n] in presets" :key="n" type="button" class="chip" :aria-pressed="isPreset(n)" @click="setPreset(n)">{{ l }}</button>
        <span class="divider" />
        <label>С<input v-model="from" type="date" class="input mono" :max="to" required /></label>
        <label>По<input v-model="to" type="date" class="input mono" :min="from" required /></label>
      </div>
    </div>
    <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>

    <template v-if="summary">
      <div class="stats-sub">
        <span>Сводка за {{ dmy(from).slice(0, 5) }} – {{ dmy(to) }}</span>
        <button class="btn btn-sm csv" aria-label="Скачать CSV: сводка" @click="download('summary')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <div class="metrics">
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon brand"><Icon name="Calendar" :size="17" /></span>Броней</span>
          <b>{{ summary.total }}</b>
          <small>за {{ plural(days, ["день", "дня", "дней"]) }}</small>
        </div>
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon danger"><Icon name="CircleX" :size="17" /></span>Отменено</span>
          <b>{{ summary.cancelled }}</b>
          <small><em>{{ pct(summary.cancel_rate) }}</em> от всех броней</small>
        </div>
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon accent"><Icon name="Timer" :size="17" /></span>Средняя длительность</span>
          <b>{{ summary.avg_duration_minutes }} <span>мин</span></b>
          <small>по состоявшимся</small>
        </div>
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon ok"><Icon name="Clock" :size="17" /></span>Забронировано</span>
          <b>{{ bookedHours }} <span>ч</span></b>
          <small>сумма по комнатам</small>
        </div>
      </div>
    </template>

    <section class="card stats-section">
      <div class="section-head">
        <h2>Загрузка комнат</h2>
        <button class="btn btn-sm csv" aria-label="Скачать CSV: загрузка комнат" @click="download('rooms')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <ul class="util-bars">
        <li v-for="r in rooms" :key="r.room_id">
          <b>{{ r.name }}</b>
          <span class="util-track"><span :class="{ low: r.utilization < 0.4 }" :style="{ width: `${r.utilization * 100}%` }" /></span>
          <span class="mono">{{ pct(r.utilization) }}</span>
          <small>{{ plural(r.bookings, ["бронь", "брони", "броней"]) }} · {{ (r.booked_minutes / 60).toFixed(1).replace(".", ",") }} ч</small>
        </li>
      </ul>
    </section>

    <section class="card stats-section">
      <div class="section-head">
        <h2>Пиковые часы</h2>
        <span class="heat-legend">меньше<i v-for="a in [0.12, 0.35, 0.6, 0.95]" :key="a" :style="{ background: `rgba(0, 119, 255, ${a})` }" />больше</span>
        <button class="btn btn-sm csv" aria-label="Скачать CSV: пиковые часы" @click="download('peak-hours')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <div class="heat-wrap">
        <table class="heat">
          <thead><tr><th /><th v-for="h in hours" :key="h" class="mono">{{ h }}</th></tr></thead>
          <tbody>
            <tr v-for="(d, i) in weekdays" :key="d">
              <th>{{ d }}</th>
              <td v-for="h in hours" :key="h"><span v-bind="heat(i + 1, h)" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card stats-section">
      <div class="section-head">
        <h2>Пользователи</h2>
        <button class="btn btn-sm csv" aria-label="Скачать CSV: пользователи" @click="download('users')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <div class="table-wrap">
        <table class="table num">
          <thead>
            <tr><th>Пользователь</th><th>Всего</th><th>Активных</th><th>Отменено</th><th>Часов</th><th>Доля отмен</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.user_id">
              <td><strong>{{ u.full_name }}</strong></td>
              <td class="mono">{{ u.total }}</td>
              <td class="mono">{{ u.active }}</td>
              <td class="mono">{{ u.cancelled }}</td>
              <td class="mono">{{ u.hours.toFixed(1) }}</td>
              <td class="mono" :class="{ high: u.cancel_rate > 0.2 }">{{ pct(u.cancel_rate) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
