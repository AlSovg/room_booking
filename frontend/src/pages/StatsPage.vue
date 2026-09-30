<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import { DAY_END, DAY_START, addDays, todayLocal } from "@/utils/time";

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
  rooms.value = r.data ?? [];
  users.value = u.data ?? [];
  peak.value = p.data ?? [];
});

const pct = (x: number) => `${(x * 100).toFixed(1)}%`;

// тепловая карта: день недели (1–7) × час рабочего дня
const days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const hours = Array.from({ length: (DAY_END - DAY_START) / 60 }, (_, i) => DAY_START / 60 + i);
const cell = computed(() => new Map(peak.value.map((c) => [`${c.weekday}-${c.hour}`, c])));
const maxMinutes = computed(() => Math.max(1, ...peak.value.map((c) => c.booked_minutes)));
const shade = (wd: number, h: number) => {
  const c = cell.value.get(`${wd}-${h}`);
  return c ? { background: `rgba(74, 144, 217, ${0.15 + 0.85 * (c.booked_minutes / maxMinutes.value)})` } : undefined;
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
  <h1>Статистика</h1>
  <div class="bar">
    <label>С <input v-model="from" type="date" :max="to" /></label>
    <label>По <input v-model="to" type="date" :min="from" /></label>
  </div>
  <p v-if="error" class="error" role="alert">{{ error }}</p>

  <template v-if="summary">
    <h2>Сводка <button @click="download('summary')">CSV</button></h2>
    <p>
      Броней: {{ summary.total }} · отменено: {{ summary.cancelled }} ({{ pct(summary.cancel_rate) }}) ·
      средняя длительность: {{ summary.avg_duration_minutes }} мин
    </p>
  </template>

  <h2>Загрузка комнат <button @click="download('rooms')">CSV</button></h2>
  <table class="stats">
    <thead><tr><th>Комната</th><th>Броней</th><th>Часов</th><th>Загрузка</th></tr></thead>
    <tbody>
      <tr v-for="r in rooms" :key="r.room_id">
        <td>{{ r.name }}</td><td>{{ r.bookings }}</td><td>{{ (r.booked_minutes / 60).toFixed(1) }}</td><td>{{ pct(r.utilization) }}</td>
      </tr>
    </tbody>
  </table>

  <h2>Пиковые часы <button @click="download('peak-hours')">CSV</button></h2>
  <table class="stats heat">
    <thead><tr><th /><th v-for="h in hours" :key="h">{{ h }}</th></tr></thead>
    <tbody>
      <tr v-for="(d, i) in days" :key="d">
        <th>{{ d }}</th>
        <td
          v-for="h in hours" :key="h" :style="shade(i + 1, h)"
          :title="cell.get(`${i + 1}-${h}`) ? `${cell.get(`${i + 1}-${h}`)!.bookings} броней, ${cell.get(`${i + 1}-${h}`)!.booked_minutes} мин` : ''"
        />
      </tr>
    </tbody>
  </table>

  <h2>Пользователи <button @click="download('users')">CSV</button></h2>
  <table class="stats">
    <thead><tr><th>Пользователь</th><th>Всего</th><th>Активных</th><th>Отменено</th><th>Часов</th><th>Доля отмен</th></tr></thead>
    <tbody>
      <tr v-for="u in users" :key="u.user_id">
        <td>{{ u.full_name }}</td><td>{{ u.total }}</td><td>{{ u.active }}</td><td>{{ u.cancelled }}</td><td>{{ u.hours }}</td><td>{{ pct(u.cancel_rate) }}</td>
      </tr>
    </tbody>
  </table>
</template>
