<script setup>
import { ref } from "vue";
import { player, api, refreshPlayer, rarityLabel } from "../services/api";
const name = ref(player.data.user.name),
  bio = ref(player.data.user.bio),
  message = ref(""),
  saving = ref(false),
  error = ref("");
async function save() {
  saving.value = true;
  error.value = "";
  message.value = "";
  try {
    await api("/me", {
      method: "PATCH",
      body: JSON.stringify({ name: name.value, bio: bio.value }),
    });
    await refreshPlayer();
    message.value = "Profil enregistré.";
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}
</script>
<template>
  <div>
    <div class="page-intro">
      <div>
        <p class="eyebrow">LA PERSONNE DERRIÈRE L’ALBUM</p>
        <h1>Votre profil<span class="accent">.</span></h1>
      </div>
    </div>
    <div class="profile-layout">
      <section class="collector-card">
        <span class="avatar large">{{ player.data.user.name.charAt(0) }}</span>
        <p class="eyebrow">COLLECTION PREMIÈRE LUEUR</p>
        <h2>{{ player.data.user.name }}</h2>
        <p>{{ player.data.user.bio }}</p>
        <div>
          <span>Cartes collectionnées</span><b>{{ player.data.stats.total }}</b>
        </div>
        <div>
          <span>Boosters ouverts</span><b>{{ player.data.stats.packsOpened }}</b>
        </div>
        <div>
          <span>Meilleure découverte</span
          ><b>{{ rarityLabel(player.data.stats.highestRarity) }}</b>
        </div>
      </section>
      <form class="profile-form" @submit.prevent="save">
        <h2>À votre image.</h2>
        <label
          >Nom de collectionneur<input
            v-model="name"
            required
            maxlength="32"
            autocomplete="nickname" /></label
        ><label
          >Quelques mots<textarea v-model="bio" maxlength="160" rows="3" />
        </label>
        <p class="muted">Votre profil et votre collection sont visibles par les autres joueurs.</p>
        <button class="button primary" :disabled="saving || !name.trim()">
          {{ saving ? "Enregistrement…" : "Enregistrer le profil" }}
        </button>
        <p v-if="message" role="status" class="success">{{ message }}</p>
        <p v-if="error" role="alert" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>
