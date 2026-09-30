import { onBeforeUnmount, ref } from "vue";

/** true на ширине телефона — совпадает с @media (max-width: 767px) в style.css. */
export function useMobile() {
  const mq = window.matchMedia("(max-width: 767px)");
  const mobile = ref(mq.matches);
  const onChange = () => (mobile.value = mq.matches);
  mq.addEventListener("change", onChange);
  onBeforeUnmount(() => mq.removeEventListener("change", onChange));
  return mobile;
}
