import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Collection from "../views/Collection.vue";
import Packs from "../views/Packs.vue";
import Profile from "../views/Profile.vue";
import Players from "../views/Players.vue";
import PlayerProfile from "../views/PlayerProfile.vue";
import Binder from "../views/Binder.vue";
import { player } from "../services/api.js";
export default createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: "/", component: Home, meta: { title: "Accueil" } },
    {
      path: "/collection",
      redirect: () => `/collection/${player.data?.user.id || 5}`,
    },
    {
      path: "/collection/:id",
      name: "collection",
      component: Collection,
      meta: { title: "Collection" },
    },
    { path: "/packs", component: Packs, meta: { title: "Atelier de boosters" } },
    { path: "/profile", component: Profile, meta: { title: "Profil" } },
    { path: "/players", component: Players, meta: { title: "Collectionneurs" } },
    { path: "/binder", component: Binder, meta: { title: "Classeur d’échange" } },
    {
      path: "/players/:id",
      component: PlayerProfile,
      meta: { title: "Profil du collectionneur" },
    },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});
