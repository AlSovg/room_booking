<script setup lang="ts">
import { ref } from "vue";
import Icon from "@/components/Icon.vue";
import AdminEquipment from "@/components/admin/AdminEquipment.vue";
import AdminRooms from "@/components/admin/AdminRooms.vue";
import AdminUsers from "@/components/admin/AdminUsers.vue";
import type { IconName } from "@/icons-injection";

const tabs = {
  rooms: ["Комнаты", "DoorOpen", AdminRooms],
  equipment: ["Оборудование", "Projector", AdminEquipment],
  users: ["Пользователи", "Users", AdminUsers],
} as const satisfies Record<string, readonly [string, IconName, unknown]>;
const tab = ref<keyof typeof tabs>("rooms");
const rooms = ref<InstanceType<typeof AdminRooms> | null>(null);
</script>

<template>
  <div class="page admin-page">
    <div class="my-head">
      <h1 class="title-icon"><Icon name="Wrench" :size="26" />Администрирование</h1>
      <button v-if="tab === 'rooms'" class="btn btn-primary" @click="rooms?.create()"><Icon name="Plus" :size="18" />Добавить комнату</button>
    </div>
    <div role="tablist" aria-label="Разделы администрирования" class="segmented admin-tabs">
      <button v-for="(t, k) in tabs" :key="k" role="tab" :aria-selected="tab === k" @click="tab = k">
        <Icon :name="t[1]" :size="17" />{{ t[0] }}
      </button>
    </div>
    <AdminRooms v-if="tab === 'rooms'" ref="rooms" />
    <component :is="tabs[tab][2]" v-else :key="tab" />
  </div>
</template>
