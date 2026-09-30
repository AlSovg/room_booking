<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import RoomCard from "@/components/RoomCard.vue";

type Room = components["schemas"]["RoomOut"];

const equipment = ref<components["schemas"]["EquipmentOut"][]>([]);
const rooms = ref<Room[]>([]);
const minCapacity = ref(1);
const selected = ref<number[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

api.GET("/api/v1/equipment").then(({ data }) => (equipment.value = data ?? []));

watchEffect(async (onCleanup) => {
  let stale = false;
  onCleanup(() => (stale = true));
  const query = { min_capacity: Math.max(1, minCapacity.value || 1), equipment_ids: selected.value };
  loading.value = true;
  const { data, error: e } = await api.GET("/api/v1/rooms", { params: { query } });
  if (stale) return; // ответ устаревшего запроса не затирает свежий
  error.value = data ? null : errorMessage(e);
  rooms.value = data ?? [];
  loading.value = false;
});
</script>

<template>
  <h1>Комнаты</h1>
  <form class="filters" @submit.prevent>
    <label>Мин. вместимость <input v-model.number="minCapacity" type="number" min="1" /></label>
    <label v-for="e in equipment" :key="e.id">
      <input v-model="selected" type="checkbox" :value="e.id" /> {{ e.name }}
    </label>
  </form>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <p v-else-if="loading">Загрузка…</p>
  <p v-else-if="!rooms.length">Нет комнат под выбранные условия</p>
  <div v-else class="grid">
    <RoomCard v-for="r in rooms" :key="r.id" :room="r" />
  </div>
</template>
