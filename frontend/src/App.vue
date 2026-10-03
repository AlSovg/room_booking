<script setup lang="ts">
import { useRoute } from "vue-router";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import Icon from "@/components/Icon.vue";
import LangSwitch from "@/components/LangSwitch.vue";
import NotificationBell from "@/components/NotificationBell.vue";
import UserMenu from "@/components/UserMenu.vue";
import type { IconName } from "@/icons-injection";
import { useAuth } from "@/stores/auth";

const auth = useAuth();
const route = useRoute();

const SECTIONS: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "nav.calendar", icon: "Calendar" },
  { to: "/rooms", label: "nav.rooms", icon: "DoorOpen" },
  { to: "/search", label: "nav.search", icon: "Search" },
  { to: "/my", label: "nav.my", icon: "Bookmark" },
];
// /rooms/5 подсвечивает «Комнаты»
const isActive = (to: string) => route.path === to || (to !== "/" && route.path.startsWith(`${to}/`));
</script>

<template>
  <header v-if="auth.user" class="topbar">
    <RouterLink to="/" class="logo">
      <span class="logo-mark"><Icon name="Calendar" :size="18" :stroke-width="2.2" /></span>{{ $t("app.name") }}
    </RouterLink>
    <nav class="nav" :aria-label="$t('nav.main')">
      <RouterLink v-for="s in SECTIONS" :key="s.to" :to="s.to" :aria-current="isActive(s.to) ? 'page' : undefined">
        {{ $t(s.label) }}
      </RouterLink>
    </nav>
    <LangSwitch />
    <NotificationBell />
    <UserMenu />
  </header>
  <main :class="auth.user ? 'with-tabbar' : 'bare'"><RouterView /></main>
  <nav v-if="auth.user" class="tabbar" :aria-label="$t('nav.sections')">
    <RouterLink v-for="s in SECTIONS" :key="s.to" :to="s.to" :aria-current="isActive(s.to) ? 'page' : undefined">
      <Icon :name="s.icon" :size="24" :stroke-width="isActive(s.to) ? 2.2 : 1.8" />{{ $t(s.label) }}
    </RouterLink>
  </nav>
  <ConfirmDialog />
</template>
