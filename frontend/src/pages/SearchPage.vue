<script setup lang="ts">
import { computed, ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import BookingForm from "@/components/BookingForm.vue";
import Icon from "@/components/Icon.vue";
import { equipmentIcon } from "@/icons-injection";
import {
  DAY_END, DAY_START, dayRange, dayTitle, freeWindow, hhmm, localParts, nextSlot, plural, todayLocal, zonedToUtc,
} from "@/utils/time";

type Room = components["schemas"]["RoomOut"];
const toMin = (t: string) => +t.slice(0, 2) * 60 + +t.slice(3, 5);

const slot = nextSlot();
const date = ref(slot.date);
const from = ref(hhmm(slot.start));
const to = ref(hhmm(slot.end));
const minCapacity = ref(1);
const selected = ref<number[]>([]);
const equipment = ref<components["schemas"]["EquipmentOut"][]>([]);
const rooms = ref<Room[] | null>(null);
const busy = ref<components["schemas"]["BookingOut"][]>([]);
const chosen = ref<Room | null>(null);
const error = ref<string | null>(null);
// параметры последнего поиска: результаты не меняются, пока форму правят
const last = ref({ date: date.value, start: 0, end: 0, capacity: 1, equipment: [] as string[] });

api.GET("/api/v1/equipment").then(({ data }) => (equipment.value = data ?? []));

const toggle = (id: number) => {
  selected.value = selected.value.includes(id) ? selected.value.filter((x) => x !== id) : [...selected.value, id];
};

async function search() {
  chosen.value = null;
  const q = {
    date: date.value, start: toMin(from.value), end: toMin(to.value), capacity: Math.max(1, minCapacity.value || 1),
    equipment: equipment.value.filter((e) => selected.value.includes(e.id)).map((e) => e.name.toLowerCase()),
  };
  const [r, b] = await Promise.all([
    api.GET("/api/v1/rooms/available", {
      params: {
        query: {
          start: zonedToUtc(q.date, q.start).toISOString(), end: zonedToUtc(q.date, q.end).toISOString(),
          min_capacity: q.capacity, equipment_ids: selected.value,
        },
      },
    }),
    api.GET("/api/v1/bookings", { params: { query: dayRange(q.date) } }),
  ]);
  error.value = r.data ? null : errorMessage(r.error);
  rooms.value = r.data ?? null;
  busy.value = b.data ?? [];
  last.value = q;
}
search();

const SPAN = DAY_END - DAY_START;
const pct = (m: number) => `${((Math.min(Math.max(m, DAY_START), DAY_END) - DAY_START) / SPAN) * 100}%`;
const width = (s: number, e: number) => `${((Math.min(e, DAY_END) - Math.max(s, DAY_START)) / SPAN) * 100}%`;
const ticks = Array.from({ length: SPAN / 120 + 1 }, (_, i) => DAY_START + i * 120);
const minutes = (iso: string) => localParts(new Date(iso)).minutes || 1440;

const now = computed(() => (last.value.date === todayLocal() ? localParts(new Date()).minutes : null));
const roomBusy = (id: number) =>
  busy.value.filter((b) => b.room_id === id).map((b) => ({ start: localParts(new Date(b.start_at)).minutes, end: minutes(b.end_at) }));
const free = (id: number) => freeWindow(roomBusy(id), last.value.start, last.value.end);

const summary = computed(() => {
  const l = last.value;
  const day = dayTitle(l.date).toLowerCase();
  return [day, `от ${plural(l.capacity, ["человека", "человек", "человек"])}`, ...l.equipment];
});
const interval = () => ({ start: zonedToUtc(last.value.date, last.value.start), end: zonedToUtc(last.value.date, last.value.end) });
</script>

<template>
  <div class="page search-page">
    <h1 class="search-title">Поиск свободной комнаты</h1>
    <form class="card search-form" @submit.prevent="search">
      <div class="search-fields">
        <label class="field search-date">
          <span class="field-label"><Icon name="Calendar" :size="15" />Дата</span>
          <input v-model="date" type="date" class="input" :min="todayLocal()" required />
        </label>
        <label class="field">
          <span class="field-label"><Icon name="Clock" :size="15" />С</span>
          <input v-model="from" type="time" class="input mono" step="900" min="08:00" max="20:00" required />
        </label>
        <label class="field">
          <span class="field-label"><Icon name="Clock" :size="15" />До</span>
          <input v-model="to" type="time" class="input mono" step="900" min="08:00" max="20:00" required />
        </label>
        <label class="field">
          <span class="field-label"><Icon name="Users" :size="15" />Участников</span>
          <input v-model.number="minCapacity" type="number" class="input mono" min="1" />
        </label>
        <button class="btn btn-primary search-submit"><Icon name="Search" :size="18" />Найти</button>
      </div>
      <div class="search-equipment">
        <span>Нужно оборудование</span>
        <div class="chips">
          <button
            v-for="e in equipment" :key="e.id" type="button" class="chip"
            :aria-pressed="selected.includes(e.id)" @click="toggle(e.id)"
          >
            <Icon :name="equipmentIcon(e.name)" :size="16" />{{ e.name }}
          </button>
        </div>
      </div>
    </form>

    <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>
    <template v-else-if="rooms">
      <div class="results-head">
        <h2>{{ rooms.length ? `${rooms.length === 1 ? "Свободна" : "Свободны"} ${plural(rooms.length, ["комната", "комнаты", "комнат"])}` : "Свободных комнат нет" }}</h2>
        <span class="results-sub">
          {{ summary[0] }} · <span class="mono">{{ hhmm(last.start) }}–{{ hhmm(last.end) }}</span>
          <template v-for="s in summary.slice(1)" :key="s"> · {{ s }}</template>
        </span>
        <span class="legend">
          <span><i class="mine" />Ваш интервал</span>
          <span><i />Занято</span>
        </span>
      </div>
      <ul v-if="rooms.length" class="card results">
        <li v-for="r in rooms" :key="r.id">
          <div class="result-info">
            <div class="result-name">
              <RouterLink :to="`/rooms/${r.id}`">{{ r.name }}</RouterLink>
              <span>
                <span v-if="r.location"><Icon name="MapPin" :size="14" :stroke-width="1.8" />{{ r.location }}</span>
                <span><Icon name="Users" :size="14" :stroke-width="1.8" />до {{ r.capacity }}</span>
              </span>
            </div>
            <ul v-if="r.equipment.length" class="tags">
              <li v-for="e in r.equipment" :key="e.id"><Icon :name="equipmentIcon(e.name)" :size="14" />{{ e.name }}</li>
            </ul>
          </div>
          <div class="timeline" :aria-label="`Занятость ${r.name} на день`">
            <div class="timeline-bar">
              <div v-if="now !== null" class="timeline-past" :style="{ width: pct(now) }" />
              <div
                v-for="(b, i) in roomBusy(r.id)" :key="i" class="timeline-busy" :title="`Занято ${hhmm(b.start)}–${hhmm(b.end)}`"
                :style="{ left: pct(b.start), width: width(b.start, b.end) }"
              />
              <div class="timeline-mine" :style="{ left: pct(last.start), width: width(last.start, last.end) }" />
              <div v-if="now !== null && now > DAY_START && now < DAY_END" class="timeline-now" :style="{ left: pct(now) }" />
            </div>
            <div class="timeline-ticks mono">
              <span v-for="t in ticks" :key="t" :style="{ left: pct(t) }">{{ hhmm(t).slice(0, 2) }}</span>
            </div>
          </div>
          <span class="result-free">Свободна <span class="mono">{{ hhmm(free(r.id).from) }}–{{ hhmm(free(r.id).to) }}</span></span>
          <button class="btn btn-primary" @click="chosen = r"><Icon name="Plus" :size="18" />Забронировать</button>
        </li>
      </ul>
    </template>
    <BookingForm
      v-if="chosen && rooms" :key="chosen.id" :rooms="rooms" :room-id="chosen.id" :start="interval().start" :end="interval().end"
      @created="search()" @close="chosen = null" @show="chosen = null"
    />
  </div>
</template>
