<script setup lang="ts">
import { locale, setLocale } from "@/i18n";
</script>

<template>
  <button
    class="btn lang-switch"
    type="button"
    :title="$t('lang.switch')"
    :aria-label="$t('lang.switch')"
    @click="setLocale(locale === 'ru' ? 'en' : 'ru')"
  >
    {{ locale === "ru" ? "EN" : "RU" }}
  </button>
</template>
