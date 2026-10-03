<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import Icon from "@/components/Icon.vue";
import { useAuth } from "@/stores/auth";
import { useDismiss } from "@/utils/dismiss";

const auth = useAuth();
const router = useRouter();
const open = ref(false);
const root = ref<HTMLElement | null>(null);
useDismiss(root, open);

const user = computed(() => auth.user!);
const initials = computed(() =>
  user.value.full_name.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase(),
);

async function logout() {
  open.value = false;
  await auth.logout();
  router.push("/login");
}
</script>

<template>
  <div ref="root" class="user-menu">
    <button
      class="user-btn"
      aria-haspopup="menu"
      :aria-expanded="open"
      :aria-label="`${$t('user.menu')}: ${user.full_name}`"
      @click="open = !open"
    >
      <span class="avatar">{{ initials }}</span>
      <span class="user-name">{{ user.full_name }}</span>
      <Icon name="ChevronDown" :size="16" class="user-chevron" />
    </button>
    <div v-if="open" class="popover menu" role="menu" :aria-label="$t('user.menu')">
      <div class="menu-head">
        <b>{{ user.full_name }}</b>
        <small>{{ $t('user.role', { role: $t(user.role === 'admin' ? 'user.admin' : 'user.employee') }) }}</small>
      </div>
      <template v-if="user.role === 'admin'">
        <RouterLink role="menuitem" to="/admin" @click="open = false"><Icon name="Settings" :size="18" />{{ $t('user.adminPanel') }}</RouterLink>
        <RouterLink role="menuitem" to="/stats" @click="open = false"><Icon name="ChartColumn" :size="18" />{{ $t('user.stats') }}</RouterLink>
        <hr />
      </template>
      <button role="menuitem" @click="logout"><Icon name="LogOut" :size="18" />{{ $t('user.logout') }}</button>
    </div>
  </div>
</template>
