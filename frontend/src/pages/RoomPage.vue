<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useRoute } from "vue-router";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import BookingForm from "@/components/BookingForm.vue";
import CalendarGrid, { type Column, type Item, type Selection } from "@/components/CalendarGrid.vue";
import Icon from "@/components/Icon.vue";
import { equipmentIcon } from "@/icons-injection";
import { useAuth } from "@/stores/auth";
import { useMobile } from "@/utils/mobile";
import { addDays, hhmm, localParts, nextSlot, roomStatus, todayLocal, zonedToUtc } from "@/utils/time";

const auth = useAuth();
const route = useRoute();
const roomId = computed(() => Number(route.params.id));
const date = ref(todayLocal());
const room = ref<components["schemas"]["RoomOut"] | null>(null);
const bookings = ref<components["schemas"]["BookingOut"][]>([]);
const selection = ref<Selection | null>(null);
const loading = ref(true);
const version = ref(0); // инкремент → перезагрузка броней
const error = ref<string | null>(null);

/** Понедельник недели, в которую попадает date. */
const monday = computed(() => addDays(date.value, -((new Date(`${date.value}T00:00:00Z`).getUTCDay() + 6) % 7)));

watchEffect(async (onCleanup) => {
  void version.value;
  let stale = false;
  onCleanup(() => (stale = true));
  const query = {
    from: zonedToUtc(monday.value, 0).toISOString(),
    to: zonedToUtc(addDays(monday.value, 7), 0).toISOString(),
    room_id: roomId.value,
  };
  loading.value = true;
  const [r, b] = await Promise.all([
    api.GET("/api/v1/rooms/{room_id}", { params: { path: { room_id: roomId.value } } }),
    api.GET("/api/v1/bookings", { params: { query } }),
  ]);
  if (stale) return;
  error.value = r.data && b.data ? null : errorMessage(r.error ?? b.error);
  room.value = r.data ?? null;
  bookings.value = b.data ?? [];
  loading.value = false;
});

// на телефоне сетка показывает один день, выбранный в полоске дней
const mobile = useMobile();

const utc = (d: string) => new Date(`${d}T00:00:00Z`);
const weekday = new Intl.DateTimeFormat("ru", { weekday: "short", timeZone: "UTC" });
const dayMonth = new Intl.DateTimeFormat("ru", { day: "numeric", month: "long", timeZone: "UTC" });
const week = computed<Column[]>(() =>
  Array.from({ length: 7 }, (_, i) => {
    const d = addDays(monday.value, i);
    return { key: d, label: weekday.format(utc(d)).toUpperCase(), date: d, sub: String(utc(d).getUTCDate()) };
  }),
);
const columns = computed(() => (mobile.value ? week.value.filter((c) => c.date === date.value) : week.value));
const weekTitle = computed(() => `${dayMonth.format(utc(monday.value))} – ${dayMonth.format(utc(addDays(monday.value, 6)))}`);

const status = computed(() => {
  const now = localParts(new Date());
  const busy = bookings.value
    .filter((b) => localParts(new Date(b.start_at)).date === now.date)
    .map((b) => ({ start: localParts(new Date(b.start_at)).minutes, end: localParts(new Date(b.end_at)).minutes || 1440 }));
  return roomStatus(busy, now.minutes);
});

/** «Забронировать» без выделения — ближайший час. */
function quickBook() {
  const s = nextSlot();
  date.value = s.date;
  selection.value = { col: s.date, start: zonedToUtc(s.date, s.start), end: zonedToUtc(s.date, s.end) };
}
const items = computed<Item[]>(() =>
  bookings.value.map((b) => ({
    id: b.id, col: localParts(new Date(b.start_at)).date, start: b.start_at, end: b.end_at, title: b.title,
    own: b.organizer.id === auth.user?.id,
  })),
);

const move = (n: number) => {
  date.value = addDays(date.value, n * (mobile.value ? 1 : 7));
  selection.value = null;
};

const show = (d: string) => {
  selection.value = null;
  date.value = d;
};

const created = () => {
  selection.value = null;
  version.value++;
};
</script>

<template>
  <div class="page room-page">
    <RouterLink to="/rooms" class="back-link"><Icon name="ChevronLeft" :size="18" />Все комнаты</RouterLink>
    <section v-if="room" class="card room-hero">
      <div class="room-hero-info">
        <div class="room-hero-title">
          <h1>{{ room.name }}</h1>
          <span class="status">
            <span class="status-dot" :class="{ busy: status.busy }" />
            <template v-if="status.until != null">
              {{ status.busy ? "Занята до" : "Свободна до" }} <b class="mono">{{ hhmm(status.until) }}</b>
            </template>
            <template v-else>Свободна до конца дня</template>
          </span>
        </div>
        <div class="room-hero-meta">
          <span v-if="room.location"><Icon name="MapPin" :size="18" :stroke-width="1.8" />{{ room.location }}</span>
          <span><Icon name="Users" :size="18" :stroke-width="1.8" />до {{ room.capacity }} человек</span>
          <ul v-if="room.equipment.length" class="tags">
            <li v-for="e in room.equipment" :key="e.id"><Icon :name="equipmentIcon(e.name)" :size="14" />{{ e.name }}</li>
          </ul>
        </div>
      </div>
      <button class="btn btn-primary" @click="quickBook"><Icon name="Plus" :size="18" />Забронировать</button>
    </section>

    <div class="week-bar">
      <div class="week-nav">
        <button class="btn btn-sm btn-icon" :aria-label="mobile ? 'Предыдущий день' : 'Предыдущая неделя'" @click="move(-1)"><Icon name="ChevronLeft" :size="18" /></button>
        <button class="btn btn-sm" @click="date = todayLocal()">Сегодня</button>
        <button class="btn btn-sm btn-icon" :aria-label="mobile ? 'Следующий день' : 'Следующая неделя'" @click="move(1)"><Icon name="ChevronRight" :size="18" /></button>
      </div>
      <h2>{{ weekTitle }}</h2>
      <span class="week-hint">Выделите время в сетке, чтобы забронировать</span>
      <input v-model="date" type="date" class="date-input" aria-label="Перейти к дате" />
    </div>
    <div class="day-strip" role="group" aria-label="День недели">
      <button v-for="c in week" :key="c.key" :aria-pressed="c.date === date" @click="date = c.date">
        <span>{{ c.label }}</span><b>{{ c.sub }}</b>
      </button>
    </div>

    <BookingForm
      v-if="selection && room" :key="selection.start.getTime()" :rooms="[room]" :room-id="room.id"
      :start="selection.start" :end="selection.end" @created="created" @close="selection = null" @show="show"
    />
    <p v-if="error" class="alert" role="alert">{{ error }}</p>
    <p v-else-if="loading && !room" class="empty">Загрузка…</p>
    <CalendarGrid v-else :columns="columns" :items="items" :selection="selection" @select="selection = $event" />
  </div>
</template>
