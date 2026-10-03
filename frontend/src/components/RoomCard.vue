<script setup lang="ts">
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { equipmentIcon } from "@/icons-injection";

defineProps<{ room: components["schemas"]["RoomOut"] }>();
</script>

<template>
  <article class="card room-card">
    <div class="room-head">
      <div class="room-title">
        <h2>{{ room.name }}</h2>
        <span v-if="room.location" class="room-loc"><Icon name="MapPin" :size="16" :stroke-width="1.8" />{{ room.location }}</span>
      </div>
      <span class="cap" :aria-label="$t('room.capacityAria', { n: room.capacity })"><Icon name="Users" :size="16" />{{ $t("common.upTo", { n: room.capacity }) }}</span>
    </div>
    <p v-if="room.description" class="room-desc">{{ room.description }}</p>
    <ul v-if="room.equipment.length" class="tags">
      <li v-for="e in room.equipment" :key="e.id"><Icon :name="equipmentIcon(e.name)" :size="14" />{{ e.name }}</li>
    </ul>
    <div v-if="$slots.default" class="room-foot"><slot /></div>
  </article>
</template>
