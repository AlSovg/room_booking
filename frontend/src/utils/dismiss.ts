import { onBeforeUnmount, onMounted, type Ref } from "vue";

/** Закрывает всплывающее окно по клику вне `root` и по Escape. */
export function useDismiss(root: Ref<HTMLElement | null>, open: Ref<boolean>) {
  const onPointer = (e: PointerEvent) => {
    if (open.value && !root.value?.contains(e.target as Node)) open.value = false;
  };
  const onKey = (e: KeyboardEvent) => {
    if (open.value && e.key === "Escape") open.value = false;
  };
  onMounted(() => {
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
  });
  onBeforeUnmount(() => {
    document.removeEventListener("pointerdown", onPointer);
    document.removeEventListener("keydown", onKey);
  });
}
