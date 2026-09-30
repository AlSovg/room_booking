<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useRoute } from "vue-router";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import CalendarGrid, { type Column, type Item, type Selection } from "@/components/CalendarGrid.vue";
import { useAuth } from "@/stores/auth";
import { addDays, hhmm, localParts, todayLocal, zonedToUtc } from "@/utils/time";

const auth = useAuth();
const route = useRoute();
const roomId = computed(() => Number(route.params.id));
const date = ref(todayLocal());
const room = ref<components["schemas"]["RoomOut"] | null>(null);
const bookings = ref<components["schemas"]["BookingOut"][]>([]);
const selection = ref<Selection | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

/** Понедельник недели, в которую попадает date. */
const monday = computed(() => addDays(date.value, -((new Date(`${date.value}T00:00:00Z`).getUTCDay() + 6) % 7)));

watchEffect(async (onCleanup) => {
  let stale = false;
  onCleanup(() => (stale = true));
  const query = {
    from: zonedToUtc(monday.value, 0).toISOString(),
    to: zonedToUtc(addDays(monday.value, 7), 0).toISOString(),
    room_id: roomId.value,
  };
  loading.value = true;
  const [r, b] = await Promise.all([
    api.GET("/api/v1/rooms/{room_id}", { params: { path: { room_id: roomId.value } } }),
    api.GET("/api/v1/bookings", { params: { query } }),
  ]);
  if (stale) return;
  error.value = r.data && b.data ? null : errorMessage(r.error ?? b.error);
  room.value = r.data ?? null;
  bookings.value = b.data ?? [];
  loading.value = false;
});

const dayLabel = new Intl.DateTimeFormat("ru", { weekday: "short", day: "numeric", month: "numeric", timeZone: "UTC" });
const columns = computed<Column[]>(() =>
  Array.from({ length: 7 }, (_, i) => {
    const d = addDays(monday.value, i);
    return { key: d, label: dayLabel.format(new Date(`${d}T00:00:00Z`)), date: d };
  }),
);
const items = computed<Item[]>(() =>
  bookings.value.map((b) => ({
    id: b.id, col: localParts(new Date(b.start_at)).date, start: b.start_at, end: b.end_at, title: b.title,
    own: b.organizer.id === auth.user?.id,
  })),
);

const move = (n: number) => {
  date.value = addDays(date.value, n * 7);
  selection.value = null;
};

const label = computed(() => {
  const s = selection.value;
  if (!s) return null;
  const from = localParts(s.start).minutes, to = localParts(s.end).minutes || 1440;
  return `${s.col}, ${hhmm(from)}–${hhmm(to)}`;
});
</script>

<template>
  <RouterLink to="/rooms">← Комнаты</RouterLink>
  <h1>{{ room?.name ?? "Комната" }}</h1>
  <div class="bar">
    <button @click="move(-1)" aria-label="Предыдущая неделя">◀</button>
    <button @click="date = todayLocal()">Сегодня</button>
    <button @click="move(1)" aria-label="Следующая неделя">▶</button>
    <input v-model="date" type="date" />
    <span v-if="label">Выбрано: {{ label }}</span>
  </div>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <p v-else-if="loading && !room">Загрузка…</p>
  <CalendarGrid v-else :columns="columns" :items="items" :selection="selection" @select="selection = $event" />
</template>
