<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, Ban, BookOpen, LockKeyhole } from "lucide-vue-next";
import { api } from "../services/api";

const route = useRoute();
const profile = ref(null);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    profile.value = (await api(`/users/${route.params.id}`)).user;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => route.params.id, load);
</script>

<template>
  <div>
    <RouterLink to="/players" class="back-link">
      <ArrowLeft :size="15" /> Tous les collectionneurs
    </RouterLink>
    <div v-if="loading" class="loading-state" role="status">
      Ouverture du profil…
    </div>
    <div v-else-if="error" class="empty-state" role="alert">
      <h1>Profil indisponible.</h1>
      <p>{{ error }}</p>
    </div>
    <div v-else class="public-profile">
      <section class="public-profile-card">
        <span class="player-number">COLLECTIONNEUR {{ String(profile.id).padStart(2, "0") }}</span>
        <span class="avatar profile-avatar">{{ profile.name.charAt(0) }}</span>
        <p class="eyebrow">{{ profile.current ? "C’EST VOUS" : "COLLECTION PREMIÈRE LUEUR" }}</p>
        <h1>{{ profile.name }}<span class="accent">.</span></h1>
        <span class="account-status" :class="{ banned: profile.status === 'banned' }">
          <Ban v-if="profile.status === 'banned'" :size="13" />
          <BookOpen v-else :size="13" />
          {{ profile.status === "banned" ? `Compte banni · ${profile.banReason}` : "Compte actif" }}
        </span>
        <p>{{ profile.bio }}</p>
        <small>Collectionneur depuis le {{ new Date(profile.createdAt).toLocaleDateString("fr-FR") }}</small>
      </section>
      <section v-if="profile.status === 'banned'" class="private-album">
        <span class="lock-emblem"><LockKeyhole :size="27" /></span>
        <p class="eyebrow">ALBUM PERSONNEL</p>
        <h2>Cette collection est privée.</h2>
        <p>
          Cette collection a été rendue privée à la suite d’une mesure de
          modération.
        </p>
      </section>
      <section v-else class="private-album public-album">
        <span class="lock-emblem"><BookOpen :size="27" /></span>
        <p class="eyebrow">ALBUM PUBLIC</p>
        <h2>Cette collection est ouverte.</h2>
        <p>Parcourez les cartes réunies par {{ profile.name }}.</p>
        <RouterLink :to="`/collection/${profile.id}`" class="button primary">
          Ouvrir la collection
        </RouterLink>
      </section>
    </div>
  </div>
</template>
