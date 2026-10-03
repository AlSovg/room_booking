import createClient, { type Middleware } from "openapi-fetch";
import { i18n } from "@/i18n";
import type { components, paths } from "./schema";

export type User = components["schemas"]["UserOut"];

let token: string | null = null;
export const session = { onExpired: () => {} }; // стор подписывается: refresh не удался → выход

export const setToken = (t: string | null) => (token = t);

export const api = createClient<paths>({ baseUrl: "", credentials: "include" });

let refreshing: Promise<boolean> | null = null;

/** Обновляет access по refresh-cookie; параллельные вызовы делят один запрос (ротация не терпит гонки). */
export function refreshSession(): Promise<boolean> {
  refreshing ??= api
    .POST("/api/v1/auth/refresh")
    .then(({ data }) => {
      setToken(data?.access_token ?? null);
      return !!data;
    })
    .finally(() => (refreshing = null));
  return refreshing;
}

const clones = new Map<string, Request>();
const isAuthCall = (url: string) => url.includes("/api/v1/auth/");

const authMiddleware: Middleware = {
  onRequest({ request, id }) {
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    if (!isAuthCall(request.url)) clones.set(id, request.clone());
    return request;
  },
  async onResponse({ response, id }) {
    const retry = clones.get(id);
    clones.delete(id);
    if (response.status !== 401 || !retry) return response;
    if (!(await refreshSession())) {
      session.onExpired();
      return response;
    }
    retry.headers.set("Authorization", `Bearer ${token}`);
    return fetch(retry);
  },
};
api.use(authMiddleware);

/** Текст ошибки: перевод по коду с параметрами из details, иначе сообщение сервера (оно на русском). */
export function errorMessage(e: unknown): string {
  const err = (e as { error?: { code?: string; message?: string; details?: Record<string, unknown> } } | undefined)?.error;
  const { t, te } = i18n.global;
  if (err?.code && te(`errors.${err.code}`)) return t(`errors.${err.code}`, err.details ?? {});
  return err?.message ?? t("errors.request");
}
