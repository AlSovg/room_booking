<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import BookingForm from "@/components/BookingForm.vue";
import CalendarGrid, { type Column, type Item, type Selection } from "@/components/CalendarGrid.vue";
import Icon from "@/components/Icon.vue";
import { useAuth } from "@/stores/auth";
import { useMobile } from "@/utils/mobile";
import { addDays, dayRange, nextSlot, todayLocal, zonedToUtc } from "@/utils/time";

const auth = useAuth();
const date = ref(todayLocal());
const minCapacity = ref(1);
const rooms = ref<components["schemas"]["RoomOut"][]>([]);
const bookings = ref<components["schemas"]["BookingOut"][]>([]);
const selection = ref<Selection | null>(null);
const loading = ref(true);
const version = ref(0); // инкремент → перезагрузка броней
const error = ref<string | null>(null);

watchEffect(async (onCleanup) => {
  void version.value;
  let stale = false;
  onCleanup(() => (stale = true));
  const query = { min_capacity: Math.max(1, minCapacity.value || 1) };
  loading.value = true;
  const [r, b] = await Promise.all([
    api.GET("/api/v1/rooms", { params: { query } }),
    api.GET("/api/v1/bookings", { params: { query: dayRange(date.value) } }),
  ]);
  if (stale) return;
  error.value = r.data && b.data ? null : errorMessage(r.error ?? b.error);
  rooms.value = r.data ?? [];
  bookings.value = b.data ?? [];
  loading.value = false;
});

// на телефоне — одна комната, выбранная чипом
const mobile = useMobile();
const activeId = ref<number | null>(null);
const active = computed(() => rooms.value.find((r) => r.id === activeId.value) ?? rooms.value[0]);
const columns = computed<Column[]>(() =>
  rooms.value
    .filter((r) => !mobile.value || r === active.value)
    .map((r) => ({
      key: String(r.id), label: r.name, date: date.value,
      hint: [r.location, `до ${r.capacity} чел.`].filter(Boolean).join(" · "),
    })),
);

const dateTitle = computed(() => {
  const f = new Intl.DateTimeFormat("ru", { weekday: mobile.value ? "short" : "long", day: "numeric", month: "long", timeZone: "UTC" });
  const t = f.format(new Date(`${date.value}T00:00:00Z`));
  return t[0].toUpperCase() + t.slice(1);
});
const items = computed<Item[]>(() =>
  bookings.value.map((b) => ({
    id: b.id, col: String(b.room_id), start: b.start_at, end: b.end_at, title: b.title,
    own: b.organizer.id === auth.user?.id,
  })),
);

const move = (n: number) => {
  date.value = addDays(date.value, n);
  selection.value = null;
};

const selRoom = computed(() => rooms.value.find((r) => String(r.id) === selection.value?.col));

/** Кнопка «Новая бронь» — ближайший час в видимой комнате. */
function quickBook() {
  const s = nextSlot();
  date.value = s.date;
  if (active.value) selection.value = { col: String(active.value.id), start: zonedToUtc(s.date, s.start), end: zonedToUtc(s.date, s.end) };
}

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
  <div class="page cal-page">
    <div class="day-bar">
      <div class="week-nav">
        <button class="btn btn-sm btn-icon" aria-label="Предыдущий день" @click="move(-1)"><Icon name="ChevronLeft" :size="18" /></button>
        <button class="btn btn-sm" @click="date = todayLocal()">Сегодня</button>
        <button class="btn btn-sm btn-icon" aria-label="Следующий день" @click="move(1)"><Icon name="ChevronRight" :size="18" /></button>
      </div>
      <h1>{{ dateTitle }}</h1>
      <div class="legend" aria-hidden="true">
        <span><i class="own" />Мои</span><span><i />Чужие</span><span><i class="over" />Прошло</span>
      </div>
      <label class="cap-filter">
        от
        <input v-model.number="minCapacity" type="number" min="1" aria-label="Минимальная вместимость" />
        человек
      </label>
    </div>
    <div class="chips room-chips" role="group" aria-label="Комната">
      <button
        v-for="r in rooms" :key="r.id" type="button" class="chip"
        :aria-pressed="r === active" @click="activeId = r.id; selection = null"
      >{{ r.name }}<span>до {{ r.capacity }}</span></button>
    </div>
    <p v-if="active" class="cal-hint"><Icon name="MapPin" :size="16" />{{ [active.name, active.location].filter(Boolean).join(" · ") }} · нажмите на свободное время, чтобы забронировать</p>

    <p v-if="error" class="alert" role="alert">{{ error }}</p>
    <p v-else-if="loading && !rooms.length" class="empty">Загрузка…</p>
    <p v-else-if="!rooms.length" class="empty">Нет комнат под выбранные условия</p>
    <CalendarGrid v-else :columns="columns" :items="items" :selection="selection" :row="24" @select="selection = $event" />

    <button class="fab" aria-label="Новая бронь" @click="quickBook"><Icon name="Plus" :size="26" /></button>
    <BookingForm
      v-if="selection && selRoom" :key="selection.start.getTime() + selection.col" :rooms="rooms" :room-id="selRoom.id"
      :start="selection.start" :end="selection.end" @created="created" @close="selection = null" @show="show"
    />
  </div>
</template>
