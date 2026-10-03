<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { locale, t } from "@/i18n";
import { DAY_END, DAY_START, addDays, dateFmt, plural, todayLocal } from "@/utils/time";

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

const presets: [string, number][] = [["stats.d7", 7], ["stats.d30", 30], ["stats.d90", 90]];
const setPreset = (n: number) => {
  to.value = todayLocal();
  from.value = addDays(to.value, 1 - n);
};
const isPreset = (n: number) => to.value === todayLocal() && from.value === addDays(to.value, 1 - n);
const days = computed(() => Math.round((Date.parse(to.value) - Date.parse(from.value)) / 86_400_000) + 1);
const dmy = (d: string, year = true) =>
  dateFmt({ day: "2-digit", month: "2-digit", ...(year && { year: "numeric" }), timeZone: "UTC" }).format(new Date(`${d}T00:00:00Z`));

const num = (x: number, digits = 1) => x.toLocaleString(locale.value, { minimumFractionDigits: digits, maximumFractionDigits: digits });
const pct = (x: number) => `${num(x * 100)}%`;
const bookedHours = computed(() => Math.round(rooms.value.reduce((a, r) => a + r.booked_minutes, 0) / 60));

// тепловая карта: день недели (1–7) × час рабочего дня
const weekdays = () => Array.from({ length: 7 }, (_, i) => dateFmt({ weekday: "short", timeZone: "UTC" }).format(new Date(`${addDays("2030-01-07", i)}T00:00:00Z`))); // с понедельника
const hours = Array.from({ length: (DAY_END - DAY_START) / 60 }, (_, i) => DAY_START / 60 + i);
const cell = computed(() => new Map(peak.value.map((c) => [`${c.weekday}-${c.hour}`, c])));
const maxMinutes = computed(() => Math.max(1, ...peak.value.map((c) => c.booked_minutes)));
const heat = (wd: number, h: number) => {
  const c = cell.value.get(`${wd}-${h}`);
  return c
    ? { style: { background: `rgba(0, 119, 255, ${(0.08 + 0.87 * (c.booked_minutes / maxMinutes.value)).toFixed(2)})` }, title: `${plural(c.bookings, "plural.bookings")}, ${c.booked_minutes} ${t("stats.min")}` }
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
      <h1 class="title-icon"><Icon name="ChartColumn" :size="26" />{{ $t("user.stats") }}</h1>
      <div class="period">
        <button v-for="[l, n] in presets" :key="n" type="button" class="chip" :aria-pressed="isPreset(n)" @click="setPreset(n)">{{ $t(l) }}</button>
        <span class="divider" />
        <label>{{ $t("stats.from") }}<input v-model="from" type="date" class="input mono" :max="to" required /></label>
        <label>{{ $t("stats.to") }}<input v-model="to" type="date" class="input mono" :min="from" required /></label>
      </div>
    </div>
    <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>

    <template v-if="summary">
      <div class="stats-sub">
        <span>{{ $t("stats.summaryFor", { from: dmy(from, false), to: dmy(to) }) }}</span>
        <button class="btn btn-sm csv" :aria-label="$t('stats.csv', { what: $t('stats.summary') })" @click="download('summary')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <div class="metrics">
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon brand"><Icon name="Calendar" :size="17" /></span>{{ $t("stats.bookings") }}</span>
          <b>{{ summary.total }}</b>
          <small>{{ $t("stats.forDays", { days: plural(days, "plural.days") }) }}</small>
        </div>
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon danger"><Icon name="CircleX" :size="17" /></span>{{ $t("stats.cancelled") }}</span>
          <b>{{ summary.cancelled }}</b>
          <small><em>{{ pct(summary.cancel_rate) }}</em> {{ $t("stats.ofAll") }}</small>
        </div>
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon accent"><Icon name="Timer" :size="17" /></span>{{ $t("stats.avgDuration") }}</span>
          <b>{{ summary.avg_duration_minutes }} <span>{{ $t("stats.min") }}</span></b>
          <small>{{ $t("stats.ofCompleted") }}</small>
        </div>
        <div class="card metric">
          <span class="metric-label"><span class="metric-icon ok"><Icon name="Clock" :size="17" /></span>{{ $t("stats.booked") }}</span>
          <b>{{ bookedHours }} <span>{{ $t("stats.h") }}</span></b>
          <small>{{ $t("stats.sumRooms") }}</small>
        </div>
      </div>
    </template>

    <section class="card stats-section">
      <div class="section-head">
        <h2>{{ $t("stats.utilization") }}</h2>
        <button class="btn btn-sm csv" :aria-label="$t('stats.csv', { what: $t('stats.utilization') })" @click="download('rooms')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <ul class="util-bars">
        <li v-for="r in rooms" :key="r.room_id">
          <b>{{ r.name }}</b>
          <span class="util-track"><span :class="{ low: r.utilization < 0.4 }" :style="{ width: `${r.utilization * 100}%` }" /></span>
          <span class="mono">{{ pct(r.utilization) }}</span>
          <small>{{ plural(r.bookings, "plural.bookings") }} · {{ num(r.booked_minutes / 60) }} {{ $t("stats.h") }}</small>
        </li>
      </ul>
    </section>

    <section class="card stats-section">
      <div class="section-head">
        <h2>{{ $t("stats.peak") }}</h2>
        <span class="heat-legend">{{ $t("stats.less") }}<i v-for="a in [0.12, 0.35, 0.6, 0.95]" :key="a" :style="{ background: `rgba(0, 119, 255, ${a})` }" />{{ $t("stats.more") }}</span>
        <button class="btn btn-sm csv" :aria-label="$t('stats.csv', { what: $t('stats.peak') })" @click="download('peak-hours')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <div class="heat-wrap">
        <table class="heat">
          <thead><tr><th /><th v-for="h in hours" :key="h" class="mono">{{ h }}</th></tr></thead>
          <tbody>
            <tr v-for="(d, i) in weekdays()" :key="d">
              <th>{{ d }}</th>
              <td v-for="h in hours" :key="h"><span v-bind="heat(i + 1, h)" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card stats-section">
      <div class="section-head">
        <h2>{{ $t("admin.users") }}</h2>
        <button class="btn btn-sm csv" :aria-label="$t('stats.csv', { what: $t('admin.users') })" @click="download('users')"><Icon name="Download" :size="16" />CSV</button>
      </div>
      <div class="table-wrap">
        <table class="table num">
          <thead>
            <tr><th>{{ $t("users.user") }}</th><th>{{ $t("stats.total") }}</th><th>{{ $t("stats.activeCol") }}</th><th>{{ $t("stats.cancelled") }}</th><th>{{ $t("stats.hours") }}</th><th>{{ $t("stats.cancelRate") }}</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.user_id">
              <td><strong>{{ u.full_name }}</strong></td>
              <td class="mono">{{ u.total }}</td>
              <td class="mono">{{ u.active }}</td>
              <td class="mono">{{ u.cancelled }}</td>
              <td class="mono">{{ num(u.hours) }}</td>
              <td class="mono" :class="{ high: u.cancel_rate > 0.2 }">{{ pct(u.cancel_rate) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
