<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

const POLL = 30_000; // решение 8: опрос раз в 30 с
const count = ref(0);
const open = ref(false);
const items = ref<components["schemas"]["NotificationOut"][]>([]);
let timer: number;

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
  <div class="bell">
    <button aria-label="Уведомления" @click="toggle">🔔<b v-if="count" class="badge">{{ count }}</b></button>
    <div v-if="open" class="panel">
      <button v-if="count" @click="readAll">Прочитать все</button>
      <p v-if="!items.length">Уведомлений нет</p>
      <ul v-else>
        <li v-for="n in items" :key="n.id" :class="{ unread: !n.is_read }" @click="read(n)">
          {{ n.message }}<small>{{ new Date(n.created_at).toLocaleString("ru") }}</small>
        </li>
      </ul>
    </div>
  </div>
</template>
