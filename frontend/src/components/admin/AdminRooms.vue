<script setup lang="ts">
import { nextTick, ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { equipmentIcon } from "@/icons-injection";

type Room = components["schemas"]["RoomOut"];
const rooms = ref<Room[]>([]);
const equipment = ref<components["schemas"]["EquipmentOut"][]>([]);
const error = ref<string | null>(null);

const blank = () => ({ name: "", location: "", capacity: 4, description: "", is_active: true, equipment_ids: [] as number[] });
const form = ref(blank());
const editing = ref<Room | null>(null);
const dialog = ref<HTMLDialogElement | null>(null);

const load = async () => (rooms.value = (await api.GET("/api/v1/rooms", { params: { query: { include_inactive: true } } })).data ?? []);
load();
api.GET("/api/v1/equipment").then(({ data }) => (equipment.value = data ?? []));

async function open(r: Room | null) {
  editing.value = r;
  error.value = null;
  form.value = r
    ? {
        name: r.name, location: r.location ?? "", capacity: r.capacity, description: r.description ?? "",
        is_active: r.is_active, equipment_ids: r.equipment.map((e) => e.id),
      }
    : blank();
  await nextTick();
  dialog.value!.showModal();
}
defineExpose({ create: () => open(null) });

async function save() {
  const f = form.value;
  const body = { ...f, name: f.name.trim(), location: f.location.trim() || null, description: f.description.trim() || null };
  const { error: e } = editing.value
    ? await api.PATCH("/api/v1/rooms/{room_id}", { params: { path: { room_id: editing.value.id } }, body })
    : await api.POST("/api/v1/rooms", { body });
  error.value = e ? errorMessage(e) : null;
  if (e) return;
  dialog.value!.close();
  await load();
}
</script>

<template>
  <div class="table-wrap card">
    <table class="table">
      <thead>
        <tr>
          <th style="width: 200px">Комната</th>
          <th style="width: 140px">Вместимость</th>
          <th>Оборудование</th>
          <th style="width: 130px">Статус</th>
          <th style="width: 72px"><span class="sr-only">Действия</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rooms" :key="r.id" :class="{ dim: !r.is_active }">
          <td>
            <span class="cell-title">
              <strong>{{ r.name }}</strong>
              <span v-if="r.location"><Icon name="MapPin" :size="13" />{{ r.location }}</span>
            </span>
          </td>
          <td><span class="cell-icon"><Icon name="Users" :size="16" :stroke-width="1.8" />до {{ r.capacity }}</span></td>
          <td>
            <ul v-if="r.equipment.length" class="tags">
              <li v-for="e in r.equipment" :key="e.id"><Icon :name="equipmentIcon(e.name)" :size="14" />{{ e.name }}</li>
            </ul>
            <span v-else class="none">—</span>
          </td>
          <td><span class="badge" :class="r.is_active ? 'ok' : 'off'"><i />{{ r.is_active ? "Активна" : "Неактивна" }}</span></td>
          <td class="actions">
            <button class="btn btn-sm btn-icon" :aria-label="`Изменить комнату ${r.name}`" :title="`Изменить комнату ${r.name}`" @click="open(r)">
              <Icon name="Pencil" :size="18" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <p class="note"><Icon name="CircleAlert" :size="16" />Комнаты не удаляются — неактивная скрыта из поиска и календаря, история броней сохраняется.</p>

  <dialog ref="dialog" class="modal room-modal" aria-labelledby="room-title" @click.self="dialog!.close()">
    <form class="modal-body" @submit.prevent="save">
      <div class="modal-head">
        <div>
          <h2 id="room-title">{{ editing ? "Изменить комнату" : "Новая комната" }}</h2>
          <span v-if="editing">{{ editing.name }}<template v-if="editing.location"> · {{ editing.location }}</template></span>
        </div>
        <button type="button" class="icon-btn modal-close" aria-label="Закрыть" @click="dialog!.close()"><Icon name="X" /></button>
      </div>
      <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>
      <div class="room-fields">
        <label class="field wide">
          <span class="field-label"><Icon name="Type" :size="15" />Название</span>
          <input v-model="form.name" class="input" required maxlength="100" />
        </label>
        <label class="field">
          <span class="field-label"><Icon name="MapPin" :size="15" />Местоположение</span>
          <input v-model="form.location" class="input" />
        </label>
        <label class="field">
          <span class="field-label"><Icon name="Users" :size="15" />Вместимость</span>
          <input v-model.number="form.capacity" type="number" min="1" class="input mono" required />
        </label>
        <label class="field wide">
          Описание
          <textarea v-model="form.description" rows="2" class="input textarea" />
        </label>
      </div>
      <fieldset class="check-group">
        <legend>Оборудование</legend>
        <label v-for="e in equipment" :key="e.id" class="check">
          <input v-model="form.equipment_ids" type="checkbox" :value="e.id" />
          <Icon :name="equipmentIcon(e.name)" :size="16" />{{ e.name }}
        </label>
      </fieldset>
      <label class="switch-row">
        <span><b>Активна</b><small>Неактивную комнату нельзя забронировать</small></span>
        <input v-model="form.is_active" type="checkbox" role="switch" class="switch" />
      </label>
      <div class="modal-actions">
        <button type="button" class="btn" @click="dialog!.close()">Отмена</button>
        <button class="btn btn-primary" :disabled="!form.name.trim()"><Icon name="Check" :size="18" />{{ editing ? "Сохранить" : "Добавить" }}</button>
      </div>
    </form>
  </dialog>
</template>
