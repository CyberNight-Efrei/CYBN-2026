<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { onBeforeRouteLeave } from "vue-router";
import { ArrowRight, RotateCcw, Sparkles } from "lucide-vue-next";
import { api, player, refreshPlayer, rarityLabel } from "../services/api";
import BoosterPack from "../components/BoosterPack.vue";
import TcgCard from "../components/TcgCard.vue";
import CardDetail from "../components/CardDetail.vue";
const phase = ref("sealed"),
  result = ref(null),
  index = ref(0),
  error = ref(""),
  rules = ref(null),
  selected = ref(null),
  busy = ref(false);
// Persist the request ID before POST, so retrying a lost response is idempotent.
const storageKey = `cybermon-pending-${player.data.user.id}`;
let timer;
onMounted(async () => {
  try {
    rules.value = await api("/packs/rules");
  } catch (e) {
    error.value = e.message;
  }
  if (sessionStorage.getItem(storageKey))
    error.value =
      "Une ouverture est en attente. Cliquez sur Ouvrir un booster pour récupérer vos cartes.";
});
onUnmounted(() => clearTimeout(timer));
onBeforeRouteLeave(() => !busy.value);
function requestUuid() {
  // getRandomValues also works on plain-HTTP LAN instances.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const h = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}
async function open() {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  try {
    let requestId = sessionStorage.getItem(storageKey);
    if (!requestId) {
      requestId = requestUuid();
      sessionStorage.setItem(storageKey, requestId);
    }
    result.value = await api("/packs/open", {
      method: "POST",
      body: JSON.stringify({ requestId }),
    });
    sessionStorage.removeItem(storageKey);
    index.value = 0;
    phase.value = "opening";
    timer = setTimeout(
      () => {
        phase.value = "reveal";
        busy.value = false;
      },
      1050,
    );
    refreshPlayer().catch(() => {});
  } catch (e) {
    busy.value = false;
    error.value = e.message;
  }
}
function next() {
  if (index.value < result.value.cards.length - 1) index.value++;
  else phase.value = "summary";
}
function reset() {
  phase.value = "sealed";
  result.value = null;
  index.value = 0;
}
</script>
<template>
  <div class="packs-view">
    <div class="page-intro">
      <div>
        <p class="eyebrow">UN INSTANT DE DÉCOUVERTE</p>
        <h1>Atelier de boosters<span class="accent">.</span></h1>
      </div>
      <span class="small-note">PREMIÈRE LUEUR · SÉRIE 001</span>
    </div>
    <div v-if="phase === 'sealed' || phase === 'opening'" class="pack-studio">
      <section
        class="pack-stage"
        :class="{ 'is-opening': phase === 'opening' }"
      >
        <div class="stage-lines" />
        <div class="stage-halo" />
        <BoosterPack :opening="phase === 'opening'" /><span class="stage-label"
          >PREMIÈRE ÉDITION / 40 CRÉATURES À DÉCOUVRIR</span
        >
      </section>
      <section class="pack-description">
        <p class="eyebrow">LA COLLECTION ORIGINALE</p>
        <h2>Première Lueur</h2>
        <p class="pack-lead">
          Toute grande collection<br />commence par un peu de curiosité.
        </p>
        <p class="muted">
          Découvrez le monde sauvage de Tuxemon, un booster à la fois. Votre
          prochaine créature préférée se cache peut-être ici.
        </p>
        <div class="pack-facts">
          <span><b>05</b> cartes par booster</span
          ><span><Sparkles :size="18" /> Une rare ou mieux garantie</span>
        </div>
        <button
          class="button primary wide"
          :disabled="busy || !rules"
          @click="open"
        >
          {{ busy ? "Ouverture du booster…" : "Ouvrir un booster"
          }}<ArrowRight :size="18" />
        </button>
        <p class="pack-free">
          Aucun jeton. Aucun paiement. Juste le plaisir de collectionner.
        </p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <details v-if="rules" class="odds">
          <summary>Que contient-il ? Probabilités</summary>
          <p>2 cartes communes + 2 peu communes. La dernière carte est :</p>
          <div v-for="(weight, rarity) in rules.finalSlot" :key="rarity">
            <span>{{ rarityLabel(rarity) }}</span
            ><b>{{ weight }}%</b>
          </div>
          <p>Chaque carte est tirée indépendamment ; les doublons sont possibles.</p>
        </details>
        <button
          v-if="!rules"
          class="button"
          @click="
            api('/packs/rules')
              .then((r) => (rules = r))
              .catch((e) => (error = e.message))
          "
        >
          Réessayer
        </button>
      </section>
    </div>
    <section
      v-else-if="phase === 'reveal'"
      class="reveal-studio"
      :class="`reveal-${result.cards[index].rarity}`"
    >
      <p class="eyebrow">VOTRE PROCHAINE DÉCOUVERTE</p>
      <div class="reveal-slot">
        <Transition name="reveal"
          ><div :key="index" class="revealed-card">
            <TcgCard :card="result.cards[index]" /></div
        ></Transition>
      </div>
      <div class="reveal-caption" aria-live="polite">
        <span>{{ rarityLabel(result.cards[index].rarity) }}</span>
        <h2>{{ result.cards[index].name }}</h2>
      </div>
      <div class="reveal-dots" aria-hidden="true">
        <span v-for="n in 5" :key="n" :class="{ filled: n <= index + 1 }" />
      </div>
      <button class="button primary" @click="next">
        {{ index === 4 ? "Voir le récapitulatif" : "Révéler la carte suivante"
        }}<ArrowRight :size="18" />
      </button>
      <p class="small-note">
        {{ index + 1 }} / 5 · Déjà ajoutée à votre collection
      </p>
    </section>
    <section v-else class="pack-results">
      <p class="eyebrow">CINQ NOUVELLES RAISONS DE COLLECTIONNER</p>
      <h2>Un booster bien ouvert.</h2>
      <p class="muted">Les cinq cartes sont maintenant dans votre collection.</p>
      <div class="card-grid">
        <div
          v-for="(card, i) in result.cards"
          :key="i"
          class="card-cell"
          :style="{ '--i': i }"
        >
          <TcgCard :card="card" interactive @select="selected = $event" />
          <div class="card-caption">
            <span>{{ card.name }}</span
            ><small>{{ rarityLabel(card.rarity) }}</small>
          </div>
        </div>
      </div>
      <div class="result-actions">
        <button class="button primary" @click="reset">
          <RotateCcw :size="17" /> En ouvrir un autre</button
        ><RouterLink class="button" to="/collection"
          >Voir la collection <ArrowRight :size="17"
        /></RouterLink>
      </div>
    </section>
    <CardDetail v-if="selected" :card="selected" @close="selected = null" />
  </div>
</template>
