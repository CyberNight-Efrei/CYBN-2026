<script setup>
import { onMounted, ref } from "vue";
import { ArrowRight, Ban, BookOpen, UsersRound } from "lucide-vue-next";
import { api } from "../services/api";

const users = ref([]);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    users.value = (await api("/users")).users;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div class="page-intro">
      <div>
        <p class="eyebrow">LA COMMUNAUTÉ PREMIÈRE LUEUR</p>
        <h1>Collectionneurs<span class="accent">.</span></h1>
        <p class="muted">Rencontrez celles et ceux qui composent leur album à vos côtés.</p>
      </div>
      <span class="small-note"><UsersRound :size="15" /> 12 collectionneurs</span>
    </div>

    <div v-if="loading" class="loading-state" role="status">
      Recherche des collectionneurs…
    </div>
    <div v-else-if="error" class="empty-state" role="alert">
      <p>{{ error }}</p>
      <button class="button" @click="load">Réessayer</button>
    </div>
    <div v-else class="player-grid">
      <RouterLink
        v-for="user in users"
        :key="user.id"
        :to="`/players/${user.id}`"
        class="player-tile"
      >
        <span class="player-number">{{ String(user.id).padStart(2, "0") }}</span>
        <span class="avatar large">{{ user.name.charAt(0) }}</span>
        <span class="player-copy">
          <small>{{ user.status === "banned" ? "COMPTE BANNI" : user.current ? "VOTRE PROFIL" : "COLLECTION PREMIÈRE LUEUR" }}</small>
          <strong>{{ user.name }}</strong>
          <span class="account-status" :class="{ banned: user.status === 'banned' }">
            <Ban v-if="user.status === 'banned'" :size="12" />
            <BookOpen v-else :size="12" />
            {{ user.status === "banned" ? "Banni · Collection privée" : "Collection publique" }}
          </span>
        </span>
        <ArrowRight :size="18" />
      </RouterLink>
    </div>
  </div>
</template>
