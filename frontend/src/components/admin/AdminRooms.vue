<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";

type Room = components["schemas"]["RoomOut"];
const rooms = ref<Room[]>([]);
const equipment = ref<components["schemas"]["EquipmentOut"][]>([]);
const error = ref<string | null>(null);

const blank = () => ({ name: "", location: "", capacity: 4, description: "", is_active: true, equipment_ids: [] as number[] });
const form = ref(blank());
const editing = ref<number | null>(null);

const load = async () => (rooms.value = (await api.GET("/api/v1/rooms", { params: { query: { include_inactive: true } } })).data ?? []);
load();
api.GET("/api/v1/equipment").then(({ data }) => (equipment.value = data ?? []));

function edit(r: Room) {
  editing.value = r.id;
  form.value = {
    name: r.name, location: r.location ?? "", capacity: r.capacity, description: r.description ?? "",
    is_active: r.is_active, equipment_ids: r.equipment.map((e) => e.id),
  };
}

function reset() {
  editing.value = null;
  form.value = blank();
}

async function save() {
  const f = form.value;
  const body = { ...f, name: f.name.trim(), location: f.location.trim() || null, description: f.description.trim() || null };
  const { error: e } = editing.value
    ? await api.PATCH("/api/v1/rooms/{room_id}", { params: { path: { room_id: editing.value } }, body })
    : await api.POST("/api/v1/rooms", { body });
  error.value = e ? errorMessage(e) : null;
  if (e) return;
  reset();
  await load();
}
</script>

<template>
  <form class="booking-form" @submit.prevent="save">
    <label>Название <input v-model="form.name" required maxlength="100" /></label>
    <label>Местоположение <input v-model="form.location" /></label>
    <label>Вместимость <input v-model.number="form.capacity" type="number" min="1" required /></label>
    <label>Описание <input v-model="form.description" /></label>
    <label><input v-model="form.is_active" type="checkbox" /> Активна</label>
    <label v-for="e in equipment" :key="e.id"><input v-model="form.equipment_ids" type="checkbox" :value="e.id" /> {{ e.name }}</label>
    <button :disabled="!form.name.trim()">{{ editing ? "Сохранить" : "Добавить комнату" }}</button>
    <button v-if="editing" type="button" @click="reset">Отмена</button>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </form>
  <ul class="list">
    <li v-for="r in rooms" :key="r.id">
      <strong>{{ r.name }}</strong>
      <span>{{ r.location ?? "—" }} · до {{ r.capacity }} чел.<template v-if="!r.is_active"> · неактивна</template></span>
      <button @click="edit(r)">Изменить</button>
    </li>
  </ul>
</template>
