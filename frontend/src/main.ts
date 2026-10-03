import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import { i18n, locale, setLocale } from "./i18n";
import { router } from "./router";
import "./style.css";

setLocale(locale.value); // <html lang> и заголовок вкладки
createApp(App).use(createPinia()).use(router).use(i18n).mount("#app");
