import { defineStore } from "pinia";
import { ref } from "vue";
import { api, errorMessage, refreshSession, session, setToken, type User } from "@/api/client";

export const useAuth = defineStore("auth", () => {
  const user = ref<User | null>(null);
  let restored: Promise<void> | null = null;

  async function loadMe() {
    user.value = (await api.GET("/api/v1/me")).data ?? null;
  }

  /** Восстановление сессии по refresh-cookie при загрузке страницы (один раз). */
  const restore = () =>
    (restored ??= refreshSession().then((ok) => (ok ? loadMe() : undefined)));

  async function login(email: string, password: string): Promise<string | null> {
    const { data, error } = await api.POST("/api/v1/auth/login", { body: { email, password } });
    if (!data) return errorMessage(error);
    setToken(data.access_token);
    await loadMe();
    return null;
  }

  async function logout() {
    await api.POST("/api/v1/auth/logout");
    clear();
  }

  function clear() {
    setToken(null);
    user.value = null;
  }
  session.onExpired = clear;

  return { user, restore, login, logout };
});
