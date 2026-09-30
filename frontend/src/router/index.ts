import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "@/stores/auth";

declare module "vue-router" {
  interface RouteMeta {
    public?: boolean;
    admin?: boolean;
  }
}

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("@/pages/LoginPage.vue"), meta: { public: true } },
    { path: "/", component: () => import("@/pages/HomePage.vue") },
    { path: "/rooms", component: () => import("@/pages/RoomsPage.vue") },
    { path: "/my", component: () => import("@/pages/MyBookingsPage.vue") },
    { path: "/rooms/:id(\\d+)", component: () => import("@/pages/RoomPage.vue") },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuth();
  await auth.restore();
  if (!auth.user) return to.meta.public ? true : { path: "/login", query: { next: to.fullPath } };
  if (to.meta.public) return "/";
  if (to.meta.admin && auth.user.role !== "admin") return "/";
});
