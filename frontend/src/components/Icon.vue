<script setup lang="ts">
import { computed } from "vue";
import { ICONS, type IconName } from "@/icons-injection";

const props = withDefaults(
  defineProps<{ name: IconName; size?: number; color?: string; fill?: string; strokeWidth?: number }>(),
  { size: 20, color: "currentColor", fill: "none", strokeWidth: 2 },
);

const icon = computed(() => ICONS[props.name]);
</script>

<template>
  <component :is="icon" class="icon" aria-hidden="true" :color :fill :size :stroke-width="strokeWidth" />
</template>
