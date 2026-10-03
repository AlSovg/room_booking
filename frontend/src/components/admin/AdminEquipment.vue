<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { confirmAction, promptText } from "@/utils/dialog";
import { equipmentIcon } from "@/icons-injection";
import { t } from "@/i18n";
import { plural } from "@/utils/time";

type Equipment = components["schemas"]["EquipmentOut"];
const items = ref<Equipment[]>([]);
const usage = ref(new Map<number, number>());
const name = ref("");
const error = ref<string | null>(null);

async function load() {
  const [e, r] = await Promise.all([
    api.GET("/api/v1/equipment"),
    api.GET("/api/v1/rooms", { params: { query: { include_inactive: true } } }),
  ]);
  items.value = e.data ?? [];
  usage.value = new Map();
  for (const x of (r.data ?? []).flatMap((room) => room.equipment)) usage.value.set(x.id, (usage.value.get(x.id) ?? 0) + 1);
}
load();

/** Показывает ошибку (например, 409 «используется») или перезагружает список. */
async function run(req: Promise<{ error?: unknown }>) {
  const { error: e } = await req;
  error.value = e ? errorMessage(e) : null;
  if (!e) await load();
  return !e;
}

async function add() {
  if (await run(api.POST("/api/v1/equipment", { body: { name: name.value.trim() } }))) name.value = "";
}

const rename = async (e: Equipment) => {
  const n = await promptText({ title: t("equip.renameTitle"), confirm: t("common.save"), input: e.name });
  if (n && n !== e.name) run(api.PATCH("/api/v1/equipment/{equipment_id}", { params: { path: { equipment_id: e.id } }, body: { name: n } }));
};

const remove = async (e: Equipment) =>
  (await confirmAction({ title: t("equip.deleteTitle"), text: t("equip.deleteText", { name: e.name }), confirm: t("common.delete"), danger: true })) &&
  run(api.DELETE("/api/v1/equipment/{equipment_id}", { params: { path: { equipment_id: e.id } } }));

const used = (e: Equipment) => {
  const n = usage.value.get(e.id);
  return n ? plural(n, "plural.inRooms") : t("equip.unused");
};
</script>

<template>
  <div class="equip-layout">
    <ul class="card equip-list">
      <li v-for="e in items" :key="e.id">
        <span class="equip-icon"><Icon :name="equipmentIcon(e.name)" :size="20" /></span>
        <span class="cell-title"><strong>{{ e.name }}</strong><span>{{ used(e) }}</span></span>
        <button class="btn btn-sm btn-icon" :aria-label="$t('equip.renameAria', { name: e.name })" :title="$t('equip.renameAria', { name: e.name })" @click="rename(e)">
          <Icon name="Pencil" :size="18" />
        </button>
        <button class="btn btn-sm btn-icon btn-danger" :aria-label="$t('equip.deleteAria', { name: e.name })" :title="$t('equip.deleteAria', { name: e.name })" @click="remove(e)">
          <Icon name="Trash2" :size="18" />
        </button>
      </li>
    </ul>
    <form class="card side-form" @submit.prevent="add">
      <h2>{{ $t("equip.new") }}</h2>
      <label class="field">
        {{ $t("equip.name") }}
        <input v-model="name" class="input" required maxlength="100" :placeholder="$t('equip.namePh')" />
      </label>
      <button class="btn btn-primary" :disabled="!name.trim()"><Icon name="Plus" :size="18" />{{ $t("common.add") }}</button>
      <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>
    </form>
  </div>
</template>
