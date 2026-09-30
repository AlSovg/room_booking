<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import { hhmm, localParts } from "@/utils/time";

const props = defineProps<{ room: components["schemas"]["RoomOut"]; start: Date; end: Date }>();
const emit = defineEmits<{ created: []; close: [] }>();

const title = ref("");
const attendees = ref(1);
const busy = ref(false);
const error = ref<string | null>(null);

const when = () => {
  const s = localParts(props.start), e = localParts(props.end);
  return `${s.date}, ${hhmm(s.minutes)}–${hhmm(e.minutes || 1440)}`;
};

async function submit() {
  busy.value = true;
  error.value = null;
  const { data, error: e } = await api.POST("/api/v1/bookings", {
    body: {
      room_id: props.room.id, title: title.value.trim(), attendees: attendees.value,
      start_at: props.start.toISOString(), end_at: props.end.toISOString(),
    },
  });
  busy.value = false;
  if (data) return emit("created");
  const c = (e as { error?: { code?: string; details?: { conflicting_booking?: { title: string; start_at: string; end_at: string; organizer: string } } } })?.error;
  const o = c?.code === "BOOKING_CONFLICT" ? c.details?.conflicting_booking : undefined;
  error.value = o
    ? `${errorMessage(e)}: «${o.title}» (${o.organizer}), ${hhmm(localParts(new Date(o.start_at)).minutes)}–${hhmm(localParts(new Date(o.end_at)).minutes || 1440)}`
    : errorMessage(e);
}
</script>

<template>
  <form class="booking-form" @submit.prevent="submit">
    <strong>{{ room.name }} · {{ when() }}</strong>
    <label>Название <input v-model="title" required maxlength="200" /></label>
    <label>Участников <input v-model.number="attendees" type="number" min="1" :max="room.capacity" required /></label>
    <button :disabled="busy || !title.trim()">Забронировать</button>
    <button type="button" @click="emit('close')">Отмена</button>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </form>
</template>
