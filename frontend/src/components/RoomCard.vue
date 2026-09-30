<script setup lang="ts">
import type { components } from "@/api/schema";

defineProps<{ room: components["schemas"]["RoomOut"] }>();
</script>

<template>
  <article class="card">
    <h3><RouterLink :to="`/rooms/${room.id}`">{{ room.name }}</RouterLink></h3>
    <p class="meta">{{ room.location ?? "—" }} · до {{ room.capacity }} чел.</p>
    <p v-if="room.description">{{ room.description }}</p>
    <ul class="tags">
      <li v-for="e in room.equipment" :key="e.id">{{ e.name }}</li>
    </ul>
    <slot />
  </article>
</template>
