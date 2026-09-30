<script setup lang="ts">
import { ref } from "vue";
import AdminEquipment from "@/components/admin/AdminEquipment.vue";
import AdminRooms from "@/components/admin/AdminRooms.vue";
import AdminUsers from "@/components/admin/AdminUsers.vue";

const tabs = { rooms: ["Комнаты", AdminRooms], equipment: ["Оборудование", AdminEquipment], users: ["Пользователи", AdminUsers] } as const;
const tab = ref<keyof typeof tabs>("rooms");
</script>

<template>
  <h1>Администрирование</h1>
  <div class="bar">
    <label v-for="(t, k) in tabs" :key="k"><input v-model="tab" type="radio" :value="k" /> {{ t[0] }}</label>
  </div>
  <component :is="tabs[tab][1]" :key="tab" />
</template>
