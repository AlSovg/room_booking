<script setup lang="ts">
import { ref } from "vue";
import { api, errorMessage } from "@/api/client";
import type { components } from "@/api/schema";
import Icon from "@/components/Icon.vue";
import { confirmAction } from "@/utils/dialog";
import { t } from "@/i18n";
import { useAuth } from "@/stores/auth";

type User = components["schemas"]["UserOut"];
const me = useAuth().user?.id;
const users = ref<User[]>([]);
const form = ref({ full_name: "", email: "", role: "employee" as User["role"] });
const error = ref<string | null>(null);
const password = ref<{ email: string; value: string } | null>(null); // показывается один раз

const load = async () => (users.value = (await api.GET("/api/v1/users")).data ?? []);
load();

async function done(e: unknown) {
  error.value = e ? errorMessage(e) : null;
  if (!e) await load();
  return !e;
}

async function create() {
  const { data, error: e } = await api.POST("/api/v1/users", { body: { ...form.value, full_name: form.value.full_name.trim() } });
  if (await done(e)) {
    password.value = { email: data!.user.email, value: data!.temporary_password };
    form.value = { full_name: "", email: "", role: "employee" };
  }
}

const patch = async (u: User, body: components["schemas"]["UserUpdate"]) =>
  done((await api.PATCH("/api/v1/users/{user_id}", { params: { path: { user_id: u.id } }, body })).error);

async function reset(u: User) {
  if (!(await confirmAction({ title: t("users.resetTitle"), text: t("users.resetText", { email: u.email }), confirm: t("users.resetConfirm") }))) return;
  const { data, error: e } = await api.POST("/api/v1/users/{user_id}/reset-password", { params: { path: { user_id: u.id } } });
  if (await done(e)) password.value = { email: u.email, value: data!.temporary_password };
}

const copy = () => navigator.clipboard.writeText(password.value!.value);
const initials = (n: string) => n.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
</script>

<template>
  <form class="card user-form" @submit.prevent="create">
    <label class="field">{{ $t("users.fullName") }}<input v-model="form.full_name" class="input" required :placeholder="$t('users.fullNamePh')" /></label>
    <label class="field">
      <span class="field-label"><Icon name="Mail" :size="15" />Email</span>
      <input v-model="form.email" type="email" class="input" required placeholder="name@example.com" />
    </label>
    <label class="field role-field">
      {{ $t("users.role") }}
      <select v-model="form.role" class="input"><option value="employee">{{ $t("user.employee") }}</option><option value="admin">{{ $t("user.admin") }}</option></select>
    </label>
    <button class="btn btn-primary"><Icon name="UserPlus" :size="18" />{{ $t("users.create") }}</button>
  </form>
  <div v-if="password" class="password-note" role="status">
    <span class="password-icon"><Icon name="KeyRound" :size="18" /></span>
    <span class="cell-title">
      <b>{{ $t("users.tempPassword", { email: password.email }) }}</b>
      <code class="mono">{{ password.value }}</code>
    </span>
    <button class="btn btn-sm" @click="copy"><Icon name="Copy" :size="16" />{{ $t("users.copy") }}</button>
    <button class="icon-btn" :aria-label="$t('users.hide')" @click="password = null"><Icon name="X" :size="18" /></button>
  </div>
  <p v-if="error" class="alert" role="alert"><Icon name="CircleAlert" />{{ error }}</p>
  <div class="table-wrap card">
    <table class="table">
      <thead>
        <tr>
          <th>{{ $t("users.user") }}</th>
          <th style="width: 190px">{{ $t("users.role") }}</th>
          <th style="width: 170px">{{ $t("common.status") }}</th>
          <th style="width: 160px"><span class="sr-only">{{ $t("common.actions") }}</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>
            <span class="user-cell" :class="{ dim: !u.is_active }">
              <span class="avatar">{{ initials(u.full_name) }}</span>
              <span class="cell-title"><strong>{{ u.full_name }}</strong><span>{{ u.email }}</span></span>
            </span>
          </td>
          <td>
            <span v-if="u.role === 'admin'" class="badge brand"><Icon name="Shield" :size="13" :stroke-width="2.4" />{{ $t("user.admin") }}</span>
            <span v-else class="badge off"><Icon name="Users" :size="13" :stroke-width="2.4" />{{ $t("user.employee") }}</span>
          </td>
          <td><span class="badge" :class="u.is_active ? 'ok' : 'bad'"><i />{{ $t(u.is_active ? "users.active" : "users.blocked") }}</span></td>
          <td class="actions">
            <span v-if="u.id === me" class="none">{{ $t("users.you") }}</span>
            <span v-else>
              <button
                class="btn btn-sm btn-icon" :aria-label="$t(u.role === 'admin' ? 'users.makeEmployee' : 'users.makeAdmin')"
                :title="$t(u.role === 'admin' ? 'users.makeEmployee' : 'users.makeAdmin')"
                @click="patch(u, { role: u.role === 'admin' ? 'employee' : 'admin' })"
              >
                <Icon name="Shield" :size="18" />
              </button>
              <button class="btn btn-sm btn-icon" :aria-label="$t('users.resetAria', { email: u.email })" :title="$t('users.resetAria', { email: u.email })" @click="reset(u)">
                <Icon name="KeyRound" :size="18" />
              </button>
              <button
                v-if="u.is_active" class="btn btn-sm btn-icon btn-danger" :aria-label="$t('users.blockAria', { name: u.full_name })"
                :title="$t('users.blockAria', { name: u.full_name })" @click="patch(u, { is_active: false })"
              >
                <Icon name="Ban" :size="18" />
              </button>
              <button
                v-else class="btn btn-sm btn-icon" :aria-label="$t('users.unblockAria', { name: u.full_name })"
                :title="$t('users.unblockAria', { name: u.full_name })" @click="patch(u, { is_active: true })"
              >
                <Icon name="LockOpen" :size="18" />
              </button>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
