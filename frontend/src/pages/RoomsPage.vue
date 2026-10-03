<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import RoomCard from "@/components/RoomCard.vue";
import { equipmentIcon } from "@/icons-injection";
import { dayRange, hhmm, localParts, roomStatus, todayLocal } from "@/utils/time";

type Room = components["schemas"]["RoomOut"];

const equipment = ref<components["schemas"]["EquipmentOut"][]>([]);
const rooms = ref<Room[]>([]);
const total = ref<number | null>(null);
const today = ref<components["schemas"]["BookingOut"][]>([]);
const minCapacity = ref(1);
const selected = ref<number[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

api.GET("/api/v1/equipment").then(({ data }) => (equipment.value = data ?? []));
api.GET("/api/v1/rooms", { params: { query: {} } }).then(({ data }) => (total.value = data?.length ?? null));
api.GET("/api/v1/bookings", { params: { query: dayRange(todayLocal()) } }).then(({ data }) => (today.value = data ?? []));

watchEffect(async (onCleanup) => {
  let stale = false;
  onCleanup(() => (stale = true));
  const query = { min_capacity: Math.max(1, minCapacity.value || 1), equipment_ids: selected.value };
  loading.value = true;
  const { data, error: e } = await api.GET("/api/v1/rooms", { params: { query } });
  if (stale) return; // ответ устаревшего запроса не затирает свежий
  error.value = data ? null : errorMessage(e);
  rooms.value = data ?? [];
  loading.value = false;
});

const toggle = (id: number) => {
  selected.value = selected.value.includes(id) ? selected.value.filter((x) => x !== id) : [...selected.value, id];
};

const minutes = (iso: string) => localParts(new Date(iso)).minutes;
const status = computed(() => {
  const now = localParts(new Date()).minutes;
  return Object.fromEntries(
    rooms.value.map((r) => [
      r.id,
      roomStatus(today.value.filter((b) => b.room_id === r.id).map((b) => ({ start: minutes(b.start_at), end: minutes(b.end_at) })), now),
    ]),
  );
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>{{ $t("nav.rooms") }}</h1>
      <span v-if="!loading && total !== null" class="page-sub">{{ $t("rooms.found", { n: rooms.length, total }) }}</span>
    </div>
    <form class="filter-bar" @submit.prevent>
      <label class="cap-filter">
        {{ $t("common.from") }}
        <input v-model.number="minCapacity" type="number" min="1" :aria-label="$t('common.minCapacity')" />
        {{ $t("common.people") }}
      </label>
      <div class="chips">
        <button
          v-for="e in equipment" :key="e.id" type="button" class="chip"
          :aria-pressed="selected.includes(e.id)" @click="toggle(e.id)"
        >
          <Icon :name="equipmentIcon(e.name)" :size="16" />{{ e.name }}
        </button>
      </div>
    </form>
    <p v-if="error" class="alert" role="alert">{{ error }}</p>
    <p v-else-if="loading && !rooms.length" class="empty">{{ $t("common.loading") }}</p>
    <p v-else-if="!rooms.length" class="empty">{{ $t("common.noRooms") }}</p>
    <div v-else class="room-grid">
      <RoomCard v-for="r in rooms" :key="r.id" :room="r">
        <span class="status">
          <span class="status-dot" :class="{ busy: status[r.id]?.busy }" />
          <template v-if="status[r.id]?.until != null">
            {{ $t(status[r.id].busy ? "rooms.busyUntil" : "rooms.freeUntil") }} <b class="mono">{{ hhmm(status[r.id].until!) }}</b>
          </template>
          <template v-else>{{ $t("rooms.freeAllDay") }}</template>
        </span>
        <RouterLink :to="`/rooms/${r.id}`" class="room-link"><Icon name="Calendar" :size="18" />{{ $t("rooms.schedule") }}</RouterLink>
      </RoomCard>
    </div>
  </div>
</template>
