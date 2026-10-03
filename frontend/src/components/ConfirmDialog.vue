<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import Icon from "@/components/Icon.vue";
import { dialog } from "@/utils/dialog";

const el = ref<HTMLDialogElement>();
const value = ref("");
let result: string | boolean | null = null;

watch(dialog, async (d) => {
  if (!d) return;
  result = null;
  value.value = d.input ?? "";
  await nextTick();
  el.value!.showModal();
});

const accept = () => {
  result = dialog.value!.input === undefined ? true : value.value.trim() || null;
  el.value!.close();
};
// close срабатывает и по Esc, и по клику на фон — result остаётся null
const closed = () => {
  dialog.value?.done(result);
  dialog.value = null;
};
</script>

<template>
  <dialog ref="el" class="modal confirm-modal" aria-labelledby="confirm-title" @close="closed" @click.self="el!.close()">
    <form v-if="dialog" class="modal-body" @submit.prevent="accept">
      <div class="modal-head">
        <div>
          <h2 id="confirm-title">{{ dialog.title }}</h2>
          <span v-if="dialog.text">{{ dialog.text }}</span>
        </div>
        <button type="button" class="icon-btn modal-close" :aria-label="$t('common.close')" @click="el!.close()"><Icon name="X" /></button>
      </div>
      <input v-if="dialog.input !== undefined" v-model="value" class="input" autofocus required maxlength="100" aria-labelledby="confirm-title" />
      <div class="modal-actions">
        <button type="button" class="btn" @click="el!.close()">{{ $t("common.cancel") }}</button>
        <button class="btn" :class="dialog.danger ? 'btn-danger' : 'btn-primary'">{{ dialog.confirm }}</button>
      </div>
    </form>
  </dialog>
</template>
