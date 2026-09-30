<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";

type Equipment = components["schemas"]["EquipmentOut"];
const items = ref<Equipment[]>([]);
const name = ref("");
const error = ref<string | null>(null);

const load = async () => (items.value = (await api.GET("/api/v1/equipment")).data ?? []);
load();

/** Показывает ошибку (например, 409 «используется») или перезагружает список. */
async function run(req: Promise<{ error?: unknown }>) {
  const { error: e } = await req;
  error.value = e ? errorMessage(e) : null;
  if (!e) await load();
  return !e;
}

async function add() {
  if (await run(api.POST("/api/v1/equipment", { body: { name: name.value.trim() } }))) name.value = "";
}

const rename = (e: Equipment) => {
  const n = prompt("Новое название", e.name)?.trim();
  if (n && n !== e.name) run(api.PATCH("/api/v1/equipment/{equipment_id}", { params: { path: { equipment_id: e.id } }, body: { name: n } }));
};

const remove = (e: Equipment) =>
  confirm(`Удалить «${e.name}»?`) && run(api.DELETE("/api/v1/equipment/{equipment_id}", { params: { path: { equipment_id: e.id } } }));
</script>

<template>
  <form class="bar" @submit.prevent="add">
    <input v-model="name" required maxlength="100" placeholder="Новое оборудование" />
    <button :disabled="!name.trim()">Добавить</button>
  </form>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <ul class="list">
    <li v-for="e in items" :key="e.id">
      {{ e.name }}
      <button @click="rename(e)">Переименовать</button>
      <button @click="remove(e)">Удалить</button>
    </li>
  </ul>
</template>
