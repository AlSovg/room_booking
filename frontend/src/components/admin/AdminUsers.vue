<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";

type User = components["schemas"]["UserOut"];
const users = ref<User[]>([]);
const form = ref({ full_name: "", email: "", role: "employee" as User["role"] });
const error = ref<string | null>(null);
const password = ref<string | null>(null); // показывается один раз

const load = async () => (users.value = (await api.GET("/api/v1/users")).data ?? []);
load();

async function done(e: unknown) {
  error.value = e ? errorMessage(e) : null;
  if (!e) await load();
  return !e;
}

async function create() {
  const { data, error: e } = await api.POST("/api/v1/users", { body: { ...form.value, full_name: form.value.full_name.trim() } });
  if (await done(e)) {
    password.value = `${data!.user.email}: ${data!.temporary_password}`;
    form.value = { full_name: "", email: "", role: "employee" };
  }
}

const patch = async (u: User, body: components["schemas"]["UserUpdate"]) =>
  done((await api.PATCH("/api/v1/users/{user_id}", { params: { path: { user_id: u.id } }, body })).error);

async function reset(u: User) {
  if (!confirm(`Сбросить пароль ${u.email}?`)) return;
  const { data, error: e } = await api.POST("/api/v1/users/{user_id}/reset-password", { params: { path: { user_id: u.id } } });
  if (await done(e)) password.value = `${u.email}: ${data!.temporary_password}`;
}
</script>

<template>
  <form class="booking-form" @submit.prevent="create">
    <label>ФИО <input v-model="form.full_name" required /></label>
    <label>Email <input v-model="form.email" type="email" required /></label>
    <label>Роль
      <select v-model="form.role"><option value="employee">Сотрудник</option><option value="admin">Администратор</option></select>
    </label>
    <button>Создать</button>
  </form>
  <p v-if="password">Временный пароль (показан один раз) — <code>{{ password }}</code></p>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <ul class="list">
    <li v-for="u in users" :key="u.id">
      <strong>{{ u.full_name }}</strong>
      <span>{{ u.email }} · {{ u.role === "admin" ? "админ" : "сотрудник" }}<template v-if="!u.is_active"> · заблокирован</template></span>
      <button @click="patch(u, { is_active: !u.is_active })">{{ u.is_active ? "Заблокировать" : "Разблокировать" }}</button>
      <button @click="patch(u, { role: u.role === 'admin' ? 'employee' : 'admin' })">{{ u.role === "admin" ? "Сделать сотрудником" : "Сделать админом" }}</button>
      <button @click="reset(u)">Сбросить пароль</button>
    </li>
  </ul>
</template>
