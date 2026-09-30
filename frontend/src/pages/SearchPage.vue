<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import BookingForm from "@/components/BookingForm.vue";
import RoomCard from "@/components/RoomCard.vue";
import { todayLocal, zonedToUtc } from "@/utils/time";

type Room = components["schemas"]["RoomOut"];
const toMin = (t: string) => +t.slice(0, 2) * 60 + +t.slice(3, 5);

const date = ref(todayLocal());
const from = ref("10:00");
const to = ref("11:00");
const minCapacity = ref(1);
const selected = ref<number[]>([]);
const equipment = ref<components["schemas"]["EquipmentOut"][]>([]);
const rooms = ref<Room[] | null>(null);
const chosen = ref<Room | null>(null);
const error = ref<string | null>(null);

api.GET("/api/v1/equipment").then(({ data }) => (equipment.value = data ?? []));

const interval = () => ({ start: zonedToUtc(date.value, toMin(from.value)), end: zonedToUtc(date.value, toMin(to.value)) });

async function search() {
  chosen.value = null;
  const { start, end } = interval();
  const { data, error: e } = await api.GET("/api/v1/rooms/available", {
    params: {
      query: {
        start: start.toISOString(), end: end.toISOString(),
        min_capacity: Math.max(1, minCapacity.value || 1), equipment_ids: selected.value,
      },
    },
  });
  error.value = data ? null : errorMessage(e);
  rooms.value = data ?? null;
}
</script>

<template>
  <h1>Поиск свободных комнат</h1>
  <form class="filters" @submit.prevent="search">
    <label>Дата <input v-model="date" type="date" required /></label>
    <label>С <input v-model="from" type="time" step="900" min="08:00" max="20:00" required /></label>
    <label>До <input v-model="to" type="time" step="900" min="08:00" max="20:00" required /></label>
    <label>Мин. вместимость <input v-model.number="minCapacity" type="number" min="1" /></label>
    <label v-for="e in equipment" :key="e.id">
      <input v-model="selected" type="checkbox" :value="e.id" /> {{ e.name }}
    </label>
    <button>Найти</button>
  </form>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <p v-else-if="rooms && !rooms.length">Свободных комнат нет</p>
  <div v-else-if="rooms" class="room-grid">
    <RoomCard v-for="r in rooms" :key="r.id" :room="r">
      <button @click="chosen = r">Забронировать</button>
    </RoomCard>
  </div>
  <BookingForm
    v-if="chosen" :key="chosen.id" :room="chosen" :start="interval().start" :end="interval().end"
    @created="chosen = null; search()" @close="chosen = null"
  />
</template>
