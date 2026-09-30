<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import BookingForm from "@/components/BookingForm.vue";
import CalendarGrid, { type Column, type Item, type Selection } from "@/components/CalendarGrid.vue";
import { useAuth } from "@/stores/auth";
import { addDays, dayRange, todayLocal } from "@/utils/time";

const auth = useAuth();
const date = ref(todayLocal());
const minCapacity = ref(1);
const rooms = ref<components["schemas"]["RoomOut"][]>([]);
const bookings = ref<components["schemas"]["BookingOut"][]>([]);
const selection = ref<Selection | null>(null);
const loading = ref(true);
const version = ref(0); // инкремент → перезагрузка броней
const error = ref<string | null>(null);

watchEffect(async (onCleanup) => {
  void version.value;
  let stale = false;
  onCleanup(() => (stale = true));
  const query = { min_capacity: Math.max(1, minCapacity.value || 1) };
  loading.value = true;
  const [r, b] = await Promise.all([
    api.GET("/api/v1/rooms", { params: { query } }),
    api.GET("/api/v1/bookings", { params: { query: dayRange(date.value) } }),
  ]);
  if (stale) return;
  error.value = r.data && b.data ? null : errorMessage(r.error ?? b.error);
  rooms.value = r.data ?? [];
  bookings.value = b.data ?? [];
  loading.value = false;
});

const columns = computed<Column[]>(() => rooms.value.map((r) => ({ key: String(r.id), label: r.name, date: date.value })));
const items = computed<Item[]>(() =>
  bookings.value.map((b) => ({
    id: b.id, col: String(b.room_id), start: b.start_at, end: b.end_at, title: b.title,
    own: b.organizer.id === auth.user?.id,
  })),
);

const move = (n: number) => {
  date.value = addDays(date.value, n);
  selection.value = null;
};

const selRoom = computed(() => rooms.value.find((r) => String(r.id) === selection.value?.col));

const created = () => {
  selection.value = null;
  version.value++;
};
</script>

<template>
  <div class="bar">
    <button @click="move(-1)" aria-label="Предыдущий день">◀</button>
    <button @click="date = todayLocal()">Сегодня</button>
    <button @click="move(1)" aria-label="Следующий день">▶</button>
    <input v-model="date" type="date" />
    <label>Мин. вместимость <input v-model.number="minCapacity" type="number" min="1" /></label>
  </div>
  <BookingForm
    v-if="selection && selRoom" :key="selection.start.getTime() + selection.col" :room="selRoom"
    :start="selection.start" :end="selection.end" @created="created" @close="selection = null"
  />
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <p v-else-if="loading && !rooms.length">Загрузка…</p>
  <p v-else-if="!rooms.length">Нет комнат под выбранные условия</p>
  <CalendarGrid v-else :columns="columns" :items="items" :selection="selection" @select="selection = $event" />
</template>
