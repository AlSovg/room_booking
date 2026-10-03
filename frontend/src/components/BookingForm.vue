<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { t } from "@/i18n";
import { DAY_END, DAY_START, STEP, hhmm, localParts, todayLocal, zonedToUtc } from "@/utils/time";

type Room = components["schemas"]["RoomOut"];
type Booking = components["schemas"]["BookingOut"];
type Conflict = { title: string; start_at: string; end_at: string; organizer: string };

// booking — режим изменения существующей брони
const props = defineProps<{ rooms: Room[]; roomId: number; start: Date; end: Date; booking?: Booking }>();
const emit = defineEmits<{ created: []; close: []; show: [date: string] }>();

const date = ref(localParts(props.start).date);
const from = ref(localParts(props.start).minutes);
const to = ref(localParts(props.end).minutes || 24 * 60);
const roomId = ref(props.roomId);
const title = ref(props.booking?.title ?? "");
const attendees = ref(props.booking?.attendees ?? 1);
const busy = ref(false);
const error = ref<string | null>(null);
const conflict = ref<Conflict | null>(null);

const room = computed(() => props.rooms.find((r) => r.id === roomId.value) ?? props.rooms[0]);
const meta = computed(() => [room.value.name, room.value.location, t("cal.upToShort", { n: room.value.capacity })].filter(Boolean).join(" · "));
const slots = Array.from({ length: (DAY_END - DAY_START) / STEP + 1 }, (_, i) => DAY_START + i * STEP);
const time = (iso: string) => hhmm(localParts(new Date(iso)).minutes || 24 * 60);

watch(from, (v) => {
  if (to.value <= v) to.value = Math.min(v + 60, DAY_END);
});
watch([date, from, to, roomId], () => (conflict.value = null));

const dialog = ref<HTMLDialogElement | null>(null);
onMounted(() => dialog.value!.showModal());
const close = () => dialog.value!.close(); // → событие close → emit("close")

async function submit() {
  busy.value = true;
  error.value = null;
  conflict.value = null;
  const body = {
    room_id: roomId.value, title: title.value.trim(), attendees: attendees.value,
    start_at: zonedToUtc(date.value, from.value).toISOString(), end_at: zonedToUtc(date.value, to.value).toISOString(),
  };
  const { data, error: e } = props.booking
    ? await api.PATCH("/api/v1/bookings/{booking_id}", { params: { path: { booking_id: props.booking.id } }, body })
    : await api.POST("/api/v1/bookings", { body });
  busy.value = false;
  if (data) return emit("created");
  const c = (e as { error?: { code?: string; details?: { conflicting_booking?: Conflict } } })?.error;
  conflict.value = (c?.code === "BOOKING_CONFLICT" && c.details?.conflicting_booking) || null;
  if (!conflict.value) error.value = errorMessage(e);
}
</script>

<template>
  <dialog ref="dialog" class="modal" aria-labelledby="booking-title" @close="emit('close')" @click.self="close">
    <form class="modal-body" @submit.prevent="submit">
      <div class="modal-head">
        <div>
          <h2 id="booking-title">{{ $t(booking ? "booking.edit" : "cal.newBooking") }}</h2>
          <span>{{ meta }}</span>
        </div>
        <button type="button" class="icon-btn modal-close" :aria-label="$t('common.close')" @click="close"><Icon name="X" /></button>
      </div>

      <div v-if="conflict" class="alert alert-block" role="alert">
        <Icon name="CircleAlert" />
        <div>
          <strong>{{ $t("booking.taken") }}</strong>
          <span>{{ conflict.title }} · <span class="mono">{{ time(conflict.start_at) }}–{{ time(conflict.end_at) }}</span> · {{ conflict.organizer }}</span>
          <a href="#" @click.prevent="emit('show', localParts(new Date(conflict.start_at)).date)">{{ $t("booking.showInCalendar") }}</a>
        </div>
      </div>
      <p v-else-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>

      <div class="modal-when">
        <label class="field">
          <span class="field-label"><Icon name="Calendar" :size="16" />{{ $t("booking.date") }}</span>
          <input v-model="date" type="date" class="input" :min="todayLocal()" required />
        </label>
        <label class="field">
          <span class="field-label"><Icon name="Clock" :size="16" />{{ $t("booking.start") }}</span>
          <select v-model.number="from" class="input mono" :class="{ invalid: conflict }">
            <option v-for="m in slots.slice(0, -1)" :key="m" :value="m">{{ hhmm(m) }}</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label"><Icon name="Timer" :size="16" />{{ $t("booking.end") }}</span>
          <select v-model.number="to" class="input mono" :class="{ invalid: conflict }">
            <option v-for="m in slots.filter((x) => x > from)" :key="m" :value="m">{{ hhmm(m) }}</option>
          </select>
        </label>
      </div>
      <label v-if="rooms.length > 1" class="field">
        <span class="field-label"><Icon name="DoorOpen" :size="16" />{{ $t("common.room") }}</span>
        <select v-model.number="roomId" class="input">
          <option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.name }}</option>
        </select>
      </label>
      <label class="field">
        <span class="field-label"><Icon name="Pencil" :size="16" />{{ $t("booking.topic") }}</span>
        <input v-model="title" class="input" :placeholder="$t('booking.topicPh')" maxlength="200" required />
      </label>
      <label class="field">
        <span class="field-label"><Icon name="Users" :size="16" />{{ $t("booking.attendees") }}</span>
        <span class="attendees">
          <input v-model.number="attendees" type="number" class="input mono" min="1" :max="room.capacity" required />
          {{ $t("booking.outOf", { n: room.capacity }) }}
        </span>
      </label>

      <div class="modal-actions">
        <button type="button" class="btn" @click="close">{{ $t("common.cancel") }}</button>
        <button class="btn btn-primary" :disabled="busy || !title.trim()"><Icon name="Check" :size="18" />{{ $t(booking ? "common.save" : "booking.book") }}</button>
      </div>
    </form>
  </dialog>
</template>
