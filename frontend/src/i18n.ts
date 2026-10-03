import { createI18n } from "vue-i18n";
import en from "./locales/en";
import ru from "./locales/ru";

export const LOCALES = ["ru", "en"] as const;
export type Locale = (typeof LOCALES)[number];

const KEY = "locale";

function initial(): Locale {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "ru" || saved === "en") return saved;
    return navigator.language.startsWith("ru") ? "ru" : "en";
  } catch {
    return "ru"; // нет localStorage/navigator (тесты, приватный режим)
  }
}

// «1 комната | 2 комнаты | 5 комнат»: 1, 21 → one; 2–4, 22–24 → few; остальное, включая 0, → many
const ruPlural = (n: number) => {
  const teen = n % 100 > 10 && n % 100 < 20;
  if (!teen && n % 10 === 1) return 0;
  if (!teen && n % 10 >= 2 && n % 10 <= 4) return 1;
  return 2;
};

export const i18n = createI18n({
  legacy: false,
  locale: initial(),
  fallbackLocale: "ru",
  messages: { ru, en },
  pluralRules: { ru: ruPlural },
});

export const t = i18n.global.t;
export const locale = i18n.global.locale; // ref<Locale>, реактивен

export function setLocale(l: Locale) {
  locale.value = l;
  document.documentElement.lang = l;
  document.title = t("app.title");
  try {
    localStorage.setItem(KEY, l);
  } catch {
    /* не критично */
  }
}
