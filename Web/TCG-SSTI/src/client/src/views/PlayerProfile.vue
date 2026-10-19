<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ArrowLeft, ArrowRight, Ban, BookOpen, BookOpenCheck } from "lucide-vue-next";
import { api, player } from "../services/api";
import TcgCard from "../components/TcgCard.vue";

const route = useRoute();
const profile = ref(null);
const binder = ref(null);
const collection = ref([]);
const requested = ref(null);
const offeredCardId = ref("");
const messageTemplate = ref(
  "Bonjour {{ to }}, échangerais-tu {{ requested }} contre mon {{ offered }} ?",
);
const preview = ref("");
const notice = ref("");
const loading = ref(true);
const busy = ref(false);
const error = ref("");
const canTrade = computed(() =>
  Boolean(collection.value.length && requested.value && offeredCardId.value),
);

async function load() {
  loading.value = true;
  error.value = "";
  requested.value = null;
  preview.value = "";
  try {
    const id = route.params.id;
    const [profileResult, binderResult] = await Promise.all([
      api(`/users/${id}`),
      api(`/users/${id}/binder`),
    ]);
    profile.value = profileResult.user;
    binder.value = binderResult.binder;
    if (!profile.value.current) {
      collection.value = (
        await api(`/users/${player.data.user.id}/collection`)
      ).cards;
      offeredCardId.value = collection.value[0]?.id || "";
    }
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function tradeValues() {
  return {
    toUserId: profile.value.id,
    offeredCardId: Number(offeredCardId.value),
    requestedCardId: requested.value.id,
    messageTemplate: messageTemplate.value,
  };
}

async function previewMessage() {
  if (!canTrade.value) return;
  busy.value = true;
  error.value = "";
  notice.value = "";
  try {
    const result = await api("/trades/preview", {
        method: "POST",
        body: JSON.stringify(tradeValues()),
      });
    preview.value = result.renderedMessage;
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

async function sendTrade() {
  if (!canTrade.value) return;
  busy.value = true;
  error.value = "";
  try {
    const result = await api("/trades", {
      method: "POST",
      body: JSON.stringify(tradeValues()),
    });
    preview.value = result.renderedMessage;
    notice.value = `Proposition d’échange nº ${result.id} envoyée.`;
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
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
    <div v-else-if="error && !profile" class="empty-state" role="alert">
      <h1>Profil indisponible.</h1>
      <p>{{ error }}</p>
    </div>
    <template v-else>
      <div class="public-profile compact-profile">
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
        <section class="binder-intro">
          <BookOpenCheck :size="30" />
          <p class="eyebrow">CLASSEUR D’ÉCHANGE PUBLIC</p>
          <h2>{{ binder.title }}</h2>
          <p>
            Une petite sélection proposée à l’échange.
            {{ profile.status === "banned" ? "La collection complète est verrouillée par la modération." : "La collection complète est publique." }}
          </p>
          <RouterLink v-if="profile.current" to="/binder" class="button primary">
            Gérer votre classeur <ArrowRight :size="16" />
          </RouterLink>
          <RouterLink
            v-else-if="profile.status !== 'banned'"
            :to="`/collection/${profile.id}`"
            class="button"
          >
            Voir la collection <ArrowRight :size="16" />
          </RouterLink>
        </section>
      </div>

      <section class="binder-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">DISPONIBLES À L’ÉCHANGE</p>
            <h2>{{ binder.cards.length }} cartes proposées</h2>
          </div>
          <span v-if="!profile.current" class="small-note">Choisissez-en une pour proposer un échange</span>
        </div>
        <div v-if="!binder.cards.length" class="empty-state">
          <p>Ce classeur est vide pour le moment.</p>
        </div>
        <div v-else class="card-grid binder-card-grid">
          <div
            v-for="card in binder.cards"
            :key="card.id"
            class="card-cell binder-choice"
            :class="{ selected: requested?.id === card.id }"
          >
            <TcgCard
              :card="card"
              :interactive="!profile.current && profile.status !== 'banned'"
              @select="requested = $event"
            />
            <div class="card-caption"><span>{{ card.name }}</span></div>
          </div>
        </div>
      </section>

      <form
        v-if="!profile.current && profile.status !== 'banned' && requested"
        class="trade-composer"
        @submit.prevent="sendTrade"
      >
        <div>
          <p class="eyebrow">PROPOSER UN ÉCHANGE</p>
          <h2>Votre demande pour {{ requested.name }}.</h2>
          <p class="muted">
            Personnalisez le message avec des variables comme
            <code v-pre>{{ to }}</code>, <code v-pre>{{ offered }}</code> et
            <code v-pre>{{ requested }}</code>.
          </p>
        </div>
        <label v-if="collection.length">
          Votre offre
          <select v-model="offeredCardId" required>
            <option v-for="card in collection" :key="card.id" :value="card.id">
              {{ card.name }} · {{ card.quantity }} en collection
            </option>
          </select>
        </label>
        <div v-else class="trade-requirement" role="status">
          <div>
            <strong>Vous n'avez aucune carte à proposer.</strong>
            <p>
              Ouvrez un booster pour obtenir votre première carte, puis revenez
              préparer cet échange.
            </p>
          </div>
          <RouterLink to="/packs" class="button">Ouvrir un booster</RouterLink>
        </div>
        <label>
          Message
          <textarea v-model="messageTemplate" required maxlength="500" rows="4" />
        </label>
        <div v-if="preview" class="trade-preview">
          <span>APERÇU DU MESSAGE</span>
          <p>{{ preview }}</p>
        </div>
        <p v-if="notice" class="success" role="status">{{ notice }}</p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <div class="trade-actions">
          <button
            type="button"
            class="button"
            :disabled="busy || !canTrade"
            @click="previewMessage"
          >
            Prévisualiser le message
          </button>
          <button type="submit" class="button primary" :disabled="busy || !canTrade">
            Envoyer la proposition <ArrowRight :size="16" />
          </button>
        </div>
      </form>
    </template>
  </div>
</template>
