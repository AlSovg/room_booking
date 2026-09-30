<script setup lang="ts">
import { useRoute } from "vue-router";
import Icon from "@/components/Icon.vue";
import NotificationBell from "@/components/NotificationBell.vue";
import UserMenu from "@/components/UserMenu.vue";
import type { IconName } from "@/icons-injection";
import { useAuth } from "@/stores/auth";

const auth = useAuth();
const route = useRoute();

const SECTIONS: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "Календарь", icon: "Calendar" },
  { to: "/rooms", label: "Комнаты", icon: "DoorOpen" },
  { to: "/search", label: "Поиск", icon: "Search" },
  { to: "/my", label: "Мои брони", icon: "Bookmark" },
];
// /rooms/5 подсвечивает «Комнаты»
const isActive = (to: string) => route.path === to || (to !== "/" && route.path.startsWith(`${to}/`));
</script>

<template>
  <header v-if="auth.user" class="topbar">
    <RouterLink to="/" class="logo">
      <span class="logo-mark"><Icon name="Calendar" :size="18" :stroke-width="2.2" /></span>Переговорные
    </RouterLink>
    <nav class="nav" aria-label="Основная навигация">
      <RouterLink v-for="s in SECTIONS" :key="s.to" :to="s.to" :aria-current="isActive(s.to) ? 'page' : undefined">
        {{ s.label }}
      </RouterLink>
    </nav>
    <NotificationBell />
    <UserMenu />
  </header>
  <main :class="auth.user ? 'with-tabbar' : 'bare'"><RouterView /></main>
  <nav v-if="auth.user" class="tabbar" aria-label="Разделы">
    <RouterLink v-for="s in SECTIONS" :key="s.to" :to="s.to" :aria-current="isActive(s.to) ? 'page' : undefined">
      <Icon :name="s.icon" :size="24" :stroke-width="isActive(s.to) ? 2.2 : 1.8" />{{ s.label }}
    </RouterLink>
  </nav>
</template>
