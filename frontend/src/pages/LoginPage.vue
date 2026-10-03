<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import Icon from "@/components/Icon.vue";
import LangSwitch from "@/components/LangSwitch.vue";
import { useAuth } from "@/stores/auth";

const auth = useAuth();
const route = useRoute();
const router = useRouter();
const email = ref("");
const password = ref("");
const error = ref<string | null>(null);
const busy = ref(false);
const shown = ref(false);

async function submit() {
  busy.value = true;
  error.value = await auth.login(email.value, password.value);
  busy.value = false;
  if (!error.value) router.replace(String(route.query.next ?? "/"));
}
</script>

<template>
  <div class="login-page">
    <LangSwitch class="login-lang" />
    <div class="logo login-logo">
      <span class="logo-mark"><Icon name="Calendar" :size="22" :stroke-width="2.2" /></span>{{ $t("app.name") }}
    </div>
    <form class="login" :class="{ invalid: error }" @submit.prevent="submit">
      <div class="login-head">
        <h1>{{ $t("login.title") }}</h1>
        <span>{{ $t("login.subtitle") }}</span>
      </div>
      <div v-if="error" class="alert" role="alert"><Icon name="CircleAlert" :size="18" />{{ error }}</div>
      <label class="field">
        Email
        <span class="control">
          <Icon name="Mail" :size="18" :stroke-width="1.8" />
          <input v-model="email" type="email" autocomplete="username" required placeholder="name@example.com" />
        </span>
      </label>
      <label class="field">
        {{ $t("login.password") }}
        <span class="control">
          <Icon name="Lock" :size="18" :stroke-width="1.8" />
          <input v-model="password" :type="shown ? 'text' : 'password'" autocomplete="current-password" required />
          <button
            type="button"
            class="icon-btn reveal"
            :aria-label="shown ? $t('login.hide') : $t('login.show')"
            :aria-pressed="shown"
            @click="shown = !shown"
          >
            <Icon :name="shown ? 'EyeOff' : 'Eye'" :size="18" :stroke-width="1.8" />
          </button>
        </span>
      </label>
      <button class="btn btn-primary btn-lg" :disabled="busy"><Icon name="LogIn" :size="18" :stroke-width="2.2" />{{ $t("login.submit") }}</button>
      <p class="login-note">{{ $t("login.note") }}</p>
    </form>
  </div>
</template>
