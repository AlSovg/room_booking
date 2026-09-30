<script setup lang="ts">
import NotificationBell from "@/components/NotificationBell.vue";
import { useRouter } from "vue-router";
import { useAuth } from "@/stores/auth";

const auth = useAuth();
const router = useRouter();

async function logout() {
  await auth.logout();
  router.push("/login");
}
</script>

<template>
  <header v-if="auth.user">
    <nav>
      <RouterLink to="/">Календарь</RouterLink>
      <RouterLink to="/rooms">Комнаты</RouterLink>
      <RouterLink to="/search">Поиск</RouterLink>
      <RouterLink to="/my">Мои брони</RouterLink>
      <RouterLink v-if="auth.user.role === 'admin'" to="/admin">Админка</RouterLink>
    </nav>
    <NotificationBell />
    <span>{{ auth.user.full_name }}</span>
    <button @click="logout">Выйти</button>
  </header>
  <main><RouterView /></main>
</template>
