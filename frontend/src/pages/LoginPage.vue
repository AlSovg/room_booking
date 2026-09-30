<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "@/stores/auth";

const auth = useAuth();
const route = useRoute();
const router = useRouter();
const email = ref("");
const password = ref("");
const error = ref<string | null>(null);
const busy = ref(false);

async function submit() {
  busy.value = true;
  error.value = await auth.login(email.value, password.value);
  busy.value = false;
  if (!error.value) router.replace(String(route.query.next ?? "/"));
}
</script>

<template>
  <form class="login" @submit.prevent="submit">
    <h1>Вход</h1>
    <label>Email <input v-model="email" type="email" autocomplete="username" required /></label>
    <label>Пароль <input v-model="password" type="password" autocomplete="current-password" required /></label>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <button :disabled="busy">Войти</button>
  </form>
</template>
