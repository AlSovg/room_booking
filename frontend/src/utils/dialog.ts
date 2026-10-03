import { ref } from "vue";

export interface DialogOptions {
  title: string;
  text?: string;
  confirm: string;
  danger?: boolean;
  /** Если задано — диалог со строкой ввода, начальное значение — это поле. */
  input?: string;
}

/** Текущий диалог; `done` получает `true`/строку при подтверждении и `null` при отмене. */
export const dialog = ref<(DialogOptions & { done: (v: string | boolean | null) => void }) | null>(null);

const ask = (o: DialogOptions) => new Promise<string | boolean | null>((done) => (dialog.value = { ...o, done }));

export const confirmAction = async (o: DialogOptions) => (await ask(o)) === true;
export const promptText = async (o: DialogOptions & { input: string }) => (await ask(o)) as string | null;
