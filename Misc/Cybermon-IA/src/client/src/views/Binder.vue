<script setup>
import { computed, onMounted, ref } from "vue";
import { Check, Save } from "lucide-vue-next";
import { api, player } from "../services/api";
import TcgCard from "../components/TcgCard.vue";

const cards = ref([]);
const selected = ref([]);
const loading = ref(true);
const saving = ref(false);
const message = ref("");
const error = ref("");
const selectedSet = computed(() => new Set(selected.value));

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [collection, binder] = await Promise.all([
      api(`/users/${player.data.user.id}/collection`),
      api("/me/binder"),
    ]);
    cards.value = collection.cards;
    selected.value = binder.binder.cards.map((card) => card.id);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function toggle(id) {
  if (selectedSet.value.has(id))
    selected.value = selected.value.filter((cardId) => cardId !== id);
  else if (selected.value.length < 6) selected.value = [...selected.value, id];
}

async function save() {
  saving.value = true;
  error.value = "";
  message.value = "";
  try {
    await api("/me/binder", {
      method: "PUT",
      body: JSON.stringify({ cardIds: selected.value }),
    });
    message.value = "Votre classeur public est à jour.";
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div class="page-intro">
      <div>
        <p class="eyebrow">UNE FENÊTRE SUR VOTRE ALBUM</p>
        <h1>Classeur d’échange<span class="accent">.</span></h1>
        <p class="muted">Choisissez jusqu’à six cartes à montrer aux autres collectionneurs.</p>
      </div>
      <div class="binder-counter">
        <strong>{{ selected.length }}</strong><span>/ 6 visibles</span>
      </div>
    </div>
    <div v-if="loading" class="loading-state" role="status">Ouverture de votre classeur…</div>
    <div v-else-if="error && !cards.length" class="empty-state" role="alert">
      <p>{{ error }}</p>
      <button class="button" @click="load">Réessayer</button>
    </div>
    <div v-else-if="!cards.length" class="empty-state">
      <h2>Votre classeur attend vos premières cartes.</h2>
      <p>Commencez votre collection avant de choisir des cartes à échanger.</p>
      <RouterLink to="/packs" class="button primary">Ouvrir un booster</RouterLink>
    </div>
    <template v-else>
      <div class="card-grid collection-grid binder-editor-grid">
        <button
          v-for="card in cards"
          :key="card.id"
          type="button"
          class="binder-select-card"
          :class="{ selected: selectedSet.has(card.id) }"
          :aria-pressed="selectedSet.has(card.id)"
          @click="toggle(card.id)"
        >
          <TcgCard :card="card" />
          <span class="binder-check"><Check :size="15" /></span>
          <span>{{ card.name }}</span>
        </button>
      </div>
      <div class="binder-savebar">
        <span>{{ selected.length }} cartes seront proposées à l’échange. Votre collection complète reste publique.</span>
        <p v-if="message" class="success" role="status">{{ message }}</p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button class="button primary" :disabled="saving" @click="save">
          <Save :size="16" /> {{ saving ? "Enregistrement…" : "Enregistrer le classeur" }}
        </button>
      </div>
    </template>
  </div>
</template>
