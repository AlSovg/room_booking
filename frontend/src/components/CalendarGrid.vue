<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { DAY_END, DAY_START, STEP, hhmm, localParts, zonedToUtc } from "@/utils/time";

export interface Column { key: string; label: string; date: string }
export interface Item { id: number; col: string; start: string; end: string; title: string; own: boolean }
export interface Selection { col: string; start: Date; end: Date }

const props = defineProps<{ columns: Column[]; items: Item[]; selection: Selection | null }>();
const emit = defineEmits<{ select: [Selection] }>();

const ROW = 20; // px, совпадает с .cell в style.css
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

function selected(c: Column, i: number) {
  const d = drag.value;
  if (d) return d.col.key === c.key && i >= bounds(d)[0] && i <= bounds(d)[1];
  const s = props.selection;
  if (!s || s.col !== c.key) return false;
  const t = cellStart(c, i).getTime();
  return t >= s.start.getTime() && t < s.end.getTime();
}

const nowTop = (c: Column) => {
  const p = localParts(now.value);
  return p.date === c.date && p.minutes >= DAY_START && p.minutes < DAY_END
    ? `${((p.minutes - DAY_START) / STEP) * ROW}px` : null;
};

const place = (it: Item) => {
  const [a, b] = span(it);
  return { top: `${a * ROW}px`, height: `${(b - a) * ROW}px` };
};
</script>

<template>
  <div class="cal" :style="{ '--cols': columns.length }">
    <div />
    <div v-for="c in columns" :key="c.key" class="head">{{ c.label }}</div>

    <div>
      <div v-for="i in rows.filter((r) => r % 4 === 0)" :key="i" class="time" :style="{ height: 4 * ROW + 'px' }">
        {{ hhmm(DAY_START + i * STEP) }}
      </div>
    </div>

    <div v-for="c in columns" :key="c.key" class="col">
      <div
        v-for="i in rows" :key="i" class="cell"
        :class="{ past: isPast(c, i), busy: busy.get(c.key)![i], sel: selected(c, i), hour: i % 4 === 0 }"
        @mousedown.prevent="down(c, i)" @mouseenter="enter(c, i)"
      />
      <div
        v-for="it in items.filter((x) => x.col === c.key)" :key="it.id"
        class="booking" :class="{ own: it.own }" :style="place(it)" :title="it.title"
      >{{ it.title }}</div>
      <div v-if="nowTop(c)" class="now" :style="{ top: nowTop(c)! }" />
    </div>
  </div>
</template>
