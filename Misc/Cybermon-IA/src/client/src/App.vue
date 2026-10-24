<script setup>
import { computed, onMounted, ref } from "vue";
import {
  Layers3,
  PackageOpen,
  House,
  UsersRound,
  ScanLine,
  ArrowUpRight,
} from "lucide-vue-next";
import { player, refreshPlayer } from "./services/api";
const error = ref("");
const collectionPath = computed(
  () => `/collection/${player.data?.user.id || 5}`,
);
async function load() {
  error.value = "";
  try {
    await refreshPlayer();
  } catch (e) {
    error.value = e.message;
  }
}
onMounted(load);
</script>
<template>
  <header class="site-header">
    <RouterLink to="/" class="brand" aria-label="Accueil Cybermon">
      <span class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 40 40" focusable="false">
          <path d="m12 11-4-5 7 2.5M28 11l4-5-7 2.5" />
          <path d="M8 20c0-7.2 4.6-11 12-11s12 3.8 12 11v3c0 6-4.8 10-12 10S8 29 8 23z" />
          <circle cx="15" cy="21" r="1.8" />
          <circle cx="25" cy="21" r="1.8" />
          <path d="M16 27c2.7 1.5 5.3 1.5 8 0" />
        </svg>
      </span>
      <span>Cybermon</span>
    </RouterLink>
    <nav aria-label="Navigation principale">
      <RouterLink to="/" exact-active-class="active"
        ><House :size="17" /> <span>Accueil</span></RouterLink
      >
      <RouterLink :to="collectionPath" active-class="active"
        ><Layers3 :size="17" /> <span>Collection</span></RouterLink
      >
      <RouterLink to="/packs" active-class="active"
        ><PackageOpen :size="17" /> <span>Boosters</span></RouterLink
      >
      <RouterLink to="/players" active-class="active"
        ><UsersRound :size="17" /> <span>Collectionneurs</span></RouterLink
      >
      <RouterLink to="/lab" active-class="active"
        ><ScanLine :size="17" /> <span>Labo</span></RouterLink
      >
    </nav>
    <RouterLink to="/profile" class="profile-link"
      ><span class="avatar">{{ player.data?.user.name.charAt(0) || "·" }}</span
      ><span class="profile-name">{{
        player.data?.user.name || "Collectionneur"
      }}</span
      ><ArrowUpRight :size="15"
    /></RouterLink>
  </header>
  <main id="main-content">
    <div v-if="error" class="empty-state" role="alert">
      <h1>Connexion interrompue.</h1>
      <p>{{ error }}</p>
      <button class="button" @click="load">Réessayer</button>
    </div>
    <template v-else-if="player.data"
      ><RouterView v-slot="{ Component }"
        ><Transition name="page" mode="out-in"
          ><component :is="Component" /></Transition></RouterView
    ></template>
    <div v-else class="loading-state" role="status">
      <span class="spinner" />Ouverture de votre album…
    </div>
  </main>
  <footer>
    <span><b>Cybermon</b> · Un monde à collectionner.</span
    ><a href="/credits.txt" target="_blank" rel="noopener"
      >Illustrations Tuxemon et crédits <ArrowUpRight :size="13" /></a
    ><span>PREMIÈRE LUEUR · SÉRIE 001</span>
  </footer>
</template>
