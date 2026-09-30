<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { api } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import type { IconName } from "@/icons-injection";
import { useDismiss } from "@/utils/dismiss";
import { ago } from "@/utils/time";

type Kind = components["schemas"]["NotificationType"];
const KINDS: Record<Kind, { title: string; icon: IconName }> = {
  reminder: { title: "Скоро начнётся", icon: "Clock" },
  changed: { title: "Бронь изменена", icon: "Pencil" },
  cancelled: { title: "Бронь отменена", icon: "CircleX" },
};

const POLL = 30_000; // решение 8: опрос раз в 30 с
const count = ref(0);
const open = ref(false);
const items = ref<components["schemas"]["NotificationOut"][]>([]);
let timer: number;
const root = ref<HTMLElement | null>(null);
useDismiss(root, open);

async function refreshCount() {
  count.value = (await api.GET("/api/v1/notifications/unread-count")).data?.count ?? count.value;
}

async function loadList() {
  items.value = (await api.GET("/api/v1/notifications", { params: { query: {} } })).data ?? items.value;
}

async function toggle() {
  open.value = !open.value;
  if (open.value) await Promise.all([loadList(), refreshCount()]);
}

async function read(n: components["schemas"]["NotificationOut"]) {
  if (n.is_read) return;
  await api.POST("/api/v1/notifications/{notification_id}/read", { params: { path: { notification_id: n.id } } });
  await Promise.all([loadList(), refreshCount()]);
}

async function readAll() {
  await api.POST("/api/v1/notifications/read-all");
  await Promise.all([loadList(), refreshCount()]);
}

onMounted(() => {
  refreshCount();
  timer = window.setInterval(() => {
    refreshCount();
    if (open.value) loadList();
  }, POLL);
});
onBeforeUnmount(() => clearInterval(timer));
</script>

<template>
  <div ref="root" class="bell">
    <button
      class="icon-btn"
      :class="{ active: open }"
      :aria-label="count ? `Уведомления, ${count} непрочитанных` : 'Уведомления'"
      :aria-expanded="open"
      @click="toggle"
    >
      <Icon name="Bell" :size="22" :stroke-width="1.8" />
      <b v-if="count" class="count">{{ count }}</b>
    </button>
    <div v-if="open" class="popover panel" role="dialog" aria-label="Уведомления">
      <div class="panel-head">
        <h2>Уведомления<span v-if="count" class="pill">{{ count }} новых</span></h2>
        <button v-if="count" class="link-btn" @click="readAll"><Icon name="CheckCheck" :size="16" />Прочитать все</button>
      </div>
      <p v-if="!items.length" class="empty">Уведомлений нет</p>
      <ul v-else>
        <li v-for="n in items" :key="n.id">
          <button :class="{ unread: !n.is_read }" @click="read(n)">
            <span class="kind" :class="n.type"><Icon :name="KINDS[n.type].icon" :size="18" /></span>
            <span class="body">
              <span class="row"><b>{{ KINDS[n.type].title }}</b><small>{{ ago(n.created_at) }}</small></span>
              <span class="text">{{ n.message }}</span>
            </span>
            <span v-if="!n.is_read" class="dot" aria-label="Не прочитано" />
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
