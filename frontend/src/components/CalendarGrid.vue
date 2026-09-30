<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { DAY_END, DAY_START, STEP, hhmm, localParts, zonedToUtc } from "@/utils/time";

export interface Column { key: string; label: string; date: string; sub?: string } // sub — число дня в шапке недели
export interface Item { id: number; col: string; start: string; end: string; title: string; own: boolean }
export interface Selection { col: string; start: Date; end: Date }

const props = defineProps<{ columns: Column[]; items: Item[]; selection: Selection | null }>();
const emit = defineEmits<{ select: [Selection] }>();

const ROW = 18; // px, совпадает с .cell в style.css
const ROWS = (DAY_END - DAY_START) / STEP;
const rows = Array.from({ length: ROWS }, (_, i) => i);
const now = ref(new Date());
let timer: number;
onMounted(() => (timer = window.setInterval(() => (now.value = new Date()), 30_000)));
onBeforeUnmount(() => clearInterval(timer));

const cellStart = (c: Column, i: number) => zonedToUtc(c.date, DAY_START + i * STEP);

/** Диапазон строк брони [from, to). */
function span(it: Item): [number, number] {
  const s = localParts(new Date(it.start)).minutes;
  const e = localParts(new Date(it.end)).minutes || 24 * 60; // конец ровно в полночь
  return [(s - DAY_START) / STEP, (e - DAY_START) / STEP];
}

/** Клетка занята бронью: [колонка][строка]. */
const busy = computed(() => {
  const m = new Map<string, boolean[]>();
  for (const c of props.columns) m.set(c.key, Array(ROWS).fill(false));
  for (const it of props.items) {
    const cells = m.get(it.col);
    if (!cells) continue;
    const [a, b] = span(it);
    for (let i = Math.max(a, 0); i < Math.min(b, ROWS); i++) cells[i] = true;
  }
  return m;
});

const isPast = (c: Column, i: number) => cellStart(c, i).getTime() + STEP * 60_000 <= now.value.getTime();
const isFree = (c: Column, i: number) => i >= 0 && i < ROWS && !busy.value.get(c.key)![i] && !isPast(c, i);

// перетаскивание: якорь и текущая клетка в одной колонке
const drag = ref<{ col: Column; anchor: number; cur: number } | null>(null);
const bounds = (d: { anchor: number; cur: number }) => [Math.min(d.anchor, d.cur), Math.max(d.anchor, d.cur)] as const;

function down(c: Column, i: number) {
  if (isFree(c, i)) drag.value = { col: c, anchor: i, cur: i };
}

function enter(c: Column, i: number) {
  const d = drag.value;
  if (!d || c.key !== d.col.key) return;
  const dir = i > d.anchor ? 1 : -1;
  let cur = d.anchor;
  while (cur !== i && isFree(c, cur + dir)) cur += dir; // не проходим через занятое и прошедшее
  d.cur = cur;
}

function up() {
  const d = drag.value;
  drag.value = null;
  if (!d) return;
  const [a, b] = bounds(d);
  emit("select", { col: d.col.key, start: cellStart(d.col, a), end: new Date(cellStart(d.col, b).getTime() + STEP * 60_000) });
}
onMounted(() => window.addEventListener("mouseup", up));
onBeforeUnmount(() => window.removeEventListener("mouseup", up));

/** Выделение в колонке: строки [from, to). */
function selRows(c: Column): [number, number] | null {
  const d = drag.value;
  if (d) return d.col.key === c.key ? [bounds(d)[0], bounds(d)[1] + 1] : null;
  const s = props.selection;
  if (!s || s.col !== c.key) return null;
  const row = (t: Date) => (localParts(t).minutes - DAY_START) / STEP;
  return [row(s.start), row(s.end) || ROWS];
}
const rowTime = (i: number) => hhmm(DAY_START + i * STEP);

const nowRow = computed(() => {
  const p = localParts(now.value);
  return p.minutes >= DAY_START && p.minutes < DAY_END ? { date: p.date, top: ((p.minutes - DAY_START) / STEP) * ROW } : null;
});
const nowLabel = computed(() => hhmm(localParts(now.value).minutes));
const isToday = (c: Column) => localParts(now.value).date === c.date;
const isWeekend = (c: Column) => [0, 6].includes(new Date(`${c.date}T00:00:00Z`).getUTCDay());

/** Высота заштрихованной прошедшей части колонки. */
function pastHeight(c: Column) {
  const today = localParts(now.value).date;
  if (c.date < today) return ROWS * ROW;
  if (c.date > today) return 0;
  const top = ((localParts(now.value).minutes - DAY_START) / STEP) * ROW;
  return Math.min(Math.max(top, 0), ROWS * ROW);
}

const place = (it: Item) => {
  const [a, b] = span(it);
  return { top: `${a * ROW + 1}px`, height: `${(b - a) * ROW - 2}px` };
};
const range = (it: Item) => `${hhmm(localParts(new Date(it.start)).minutes)}–${hhmm(localParts(new Date(it.end)).minutes || 1440)}`;
const isOver = (it: Item) => new Date(it.end).getTime() <= now.value.getTime();
</script>

<template>
  <div class="cal" :style="{ '--cols': columns.length, '--row': ROW + 'px' }">
    <div class="corner" />
    <div v-for="c in columns" :key="c.key" class="head" :class="{ today: c.sub && isToday(c) }">
      <span class="head-label">{{ c.label }}</span><span v-if="c.sub" class="head-num">{{ c.sub }}</span>
    </div>

    <div class="times">
      <div v-for="i in rows.filter((r) => r % 4 === 0)" :key="i" class="time" :style="{ height: 4 * ROW + 'px' }">
        {{ rowTime(i) }}
      </div>
      <div v-if="nowRow && columns.some((c) => c.date === nowRow!.date)" class="now-label" :style="{ top: nowRow.top + 'px' }">{{ nowLabel }}</div>
    </div>

    <div v-for="c in columns" :key="c.key" class="col" :class="{ weekend: isWeekend(c) }">
      <div v-if="pastHeight(c)" class="past" :style="{ height: pastHeight(c) + 'px' }" />
      <div
        v-for="i in rows" :key="i" class="cell"
        :class="{ past: isPast(c, i), busy: busy.get(c.key)![i] }"
        @mousedown.prevent="down(c, i)" @mouseenter="enter(c, i)"
      />
      <div
        v-for="it in items.filter((x) => x.col === c.key)" :key="it.id"
        class="booking" :class="{ own: it.own, over: isOver(it) }" :style="place(it)" :title="`${it.title}, ${range(it)}`"
      >
        <b>{{ it.title }}</b><span class="mono">{{ range(it) }}</span>
      </div>
      <div
        v-if="selRows(c)" class="sel"
        :style="{ top: selRows(c)![0] * ROW + 'px', height: (selRows(c)![1] - selRows(c)![0]) * ROW + 'px' }"
      >
        <span class="mono">{{ rowTime(selRows(c)![0]) }}–{{ rowTime(selRows(c)![1]) }}</span>
      </div>
      <div v-if="nowRow?.date === c.date" class="now" :style="{ top: nowRow.top + 'px' }" />
    </div>
  </div>
</template>
