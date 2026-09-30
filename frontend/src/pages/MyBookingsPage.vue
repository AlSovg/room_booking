<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import { hhmm, localParts } from "@/utils/time";

type Scope = "upcoming" | "past" | "cancelled";
const scopes: [Scope, string][] = [["upcoming", "Предстоящие"], ["past", "Прошедшие"], ["cancelled", "Отменённые"]];
const scope = ref<Scope>("upcoming");
const rooms = ref(new Map<number, string>());
const bookings = ref<components["schemas"]["BookingOut"][]>([]);
const version = ref(0);
const error = ref<string | null>(null);

api.GET("/api/v1/rooms", { params: { query: {} } }).then(({ data }) => (rooms.value = new Map((data ?? []).map((r) => [r.id, r.name]))));

watchEffect(async (onCleanup) => {
  void version.value;
  let stale = false;
  onCleanup(() => (stale = true));
  const { data, error: e } = await api.GET("/api/v1/bookings/my", { params: { query: { scope: scope.value } } });
  if (stale) return;
  error.value = data ? null : errorMessage(e);
  bookings.value = data ?? [];
});

async function cancel(id: number) {
  if (!confirm("Отменить бронь?")) return;
  const { error: e } = await api.POST("/api/v1/bookings/{booking_id}/cancel", { params: { path: { booking_id: id } } });
  if (e) error.value = errorMessage(e);
  else version.value++;
}

const when = (b: components["schemas"]["BookingOut"]) => {
  const s = localParts(new Date(b.start_at)), e = localParts(new Date(b.end_at));
  return `${s.date}, ${hhmm(s.minutes)}–${hhmm(e.minutes || 1440)}`;
};
</script>

<template>
  <h1>Мои брони</h1>
  <div class="bar">
    <label v-for="[k, l] in scopes" :key="k"><input v-model="scope" type="radio" :value="k" /> {{ l }}</label>
  </div>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <p v-else-if="!bookings.length">Нет броней</p>
  <ul v-else class="list">
    <li v-for="b in bookings" :key="b.id">
      <strong>{{ b.title }}</strong>
      <span>{{ rooms.get(b.room_id) ?? `Комната №${b.room_id}` }} · {{ when(b) }}</span>
      <button v-if="scope === 'upcoming' && b.can_edit" @click="cancel(b.id)">Отменить</button>
    </li>
  </ul>
</template>
