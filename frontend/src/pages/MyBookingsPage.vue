<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import BookingForm from "@/components/BookingForm.vue";
import Icon from "@/components/Icon.vue";
import { t } from "@/i18n";
import { confirmAction } from "@/utils/dialog";
import { dateFmt, dayTitle, hhmm, localParts, plural, todayLocal } from "@/utils/time";

type Booking = components["schemas"]["BookingOut"];
type Scope = "upcoming" | "past" | "cancelled";
const scopes: Scope[] = ["upcoming", "past", "cancelled"];
const scope = ref<Scope>("upcoming");
const rooms = ref<components["schemas"]["RoomOut"][]>([]);
const bookings = ref<Booking[]>([]);
const editing = ref<Booking | null>(null);
const loading = ref(true);
const version = ref(0);
const error = ref<string | null>(null);

api.GET("/api/v1/rooms", { params: { query: {} } }).then(({ data }) => (rooms.value = data ?? []));

watchEffect(async (onCleanup) => {
  void version.value;
  let stale = false;
  onCleanup(() => (stale = true));
  loading.value = true;
  const { data, error: e } = await api.GET("/api/v1/bookings/my", { params: { query: { scope: scope.value } } });
  if (stale) return;
  error.value = data ? null : errorMessage(e);
  bookings.value = data ?? [];
  loading.value = false;
});

async function cancel(b: Booking) {
  if (!(await confirmAction({ title: t("my.cancelTitle"), text: t("my.cancelText", { title: b.title }), confirm: t("my.cancelConfirm"), danger: true }))) return;
  const { error: e } = await api.POST("/api/v1/bookings/{booking_id}/cancel", { params: { path: { booking_id: b.id } } });
  if (e) error.value = errorMessage(e);
  else version.value++;
}

const saved = () => {
  editing.value = null;
  version.value++;
};

const today = todayLocal();

const now = Date.now();

// брони по дням в порядке API
const groups = computed(() => {
  const map = new Map<string, Booking[]>();
  for (const b of bookings.value) {
    const d = localParts(new Date(b.start_at)).date;
    map.set(d, [...(map.get(d) ?? []), b]);
  }
  return [...map].map(([date, list]) => ({
    date, list, title: dayTitle(date, today),
    wd: dateFmt({ weekday: "short", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`)).toUpperCase(), day: +date.slice(8),
  }));
});

const roomName = (id: number) => rooms.value.find((r) => r.id === id)?.name ?? t("my.roomN", { id });
const time = (b: Booking) => `${hhmm(localParts(new Date(b.start_at)).minutes)}–${hhmm(localParts(new Date(b.end_at)).minutes || 1440)}`;
// «через N мин» — если начало в ближайший час
const soon = (b: Booking) => {
  const min = Math.ceil((Date.parse(b.start_at) - now) / 60_000);
  return min > 0 && min <= 60 ? min : null;
};
</script>

<template>
  <div class="page my-page">
    <div class="my-head">
      <h1>{{ $t("nav.my") }}</h1>
      <div role="tablist" :aria-label="$t('my.period')" class="segmented">
        <button v-for="k in scopes" :key="k" role="tab" :aria-selected="scope === k" @click="scope = k">{{ $t(`my.scope.${k}`) }}</button>
      </div>
    </div>
    <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>
    <p v-else-if="loading && !bookings.length" class="empty">{{ $t("common.loading") }}</p>
    <p v-else-if="!bookings.length" class="empty">{{ $t("my.none") }}</p>
    <section v-for="g in groups" :key="g.date" class="day-group">
      <h2>{{ g.title }}</h2>
      <ul class="card booking-list">
        <li v-for="b in g.list" :key="b.id" :class="{ cancelled: b.status === 'cancelled' }">
          <div class="date-badge" :class="{ today: g.date === today }"><span>{{ g.wd }}</span><b>{{ g.day }}</b></div>
          <span class="mono booking-time">{{ time(b) }}</span>
          <div class="booking-info">
            <b>{{ b.title }}</b>
            <span>
              <span><Icon name="DoorOpen" :size="14" />{{ roomName(b.room_id) }}</span>
              <span><Icon name="Users" :size="14" />{{ plural(b.attendees, "plural.attendees") }}</span>
            </span>
          </div>
          <span v-if="scope === 'upcoming' && soon(b)" class="soon"><Icon name="Clock" :size="14" />{{ $t("my.soon", { n: soon(b) }) }}</span>
          <div v-if="scope === 'upcoming' && b.can_edit" class="booking-actions">
            <button class="btn btn-sm" @click="editing = b"><Icon name="Pencil" :size="16" />{{ $t("common.edit") }}</button>
            <button class="btn btn-sm btn-icon btn-danger" :aria-label="$t('my.cancelAria', { title: b.title })" :title="$t('my.cancelAria', { title: b.title })" @click="cancel(b)">
              <Icon name="Trash2" :size="18" />
            </button>
          </div>
        </li>
      </ul>
    </section>
    <BookingForm
      v-if="editing && rooms.length" :key="editing.id" :booking="editing" :rooms="rooms" :room-id="editing.room_id"
      :start="new Date(editing.start_at)" :end="new Date(editing.end_at)"
      @created="saved" @close="editing = null" @show="editing = null"
    />
  </div>
</template>
