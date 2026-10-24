<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  Search,
  SlidersHorizontal,
  LockKeyhole,
  BookOpen,
  ArrowUpRight,
} from "lucide-vue-next";
import {
  api,
  player,
  rarityLabel,
  rarityRank,
  typeLabel,
} from "../services/api";
import TcgCard from "../components/TcgCard.vue";
import CardDetail from "../components/CardDetail.vue";
const route = useRoute();
const cards = ref([]),
  owner = ref(null),
  query = ref(""),
  type = ref(""),
  rarity = ref(""),
  sort = ref("recent"),
  selected = ref(null),
  loading = ref(true),
  accessDenied = ref(false),
  error = ref("");
const types = computed(() =>
  [...new Set(cards.value.map((c) => c.type))].sort(),
);
const filtered = computed(() =>
  cards.value
    .filter(
      (c) =>
        c.name.toLowerCase().includes(query.value.toLowerCase()) &&
        (!type.value || c.type === type.value) &&
        (!rarity.value || c.rarity === rarity.value),
    )
    .sort(
      (a, b) =>
        Number(b.special) - Number(a.special) ||
        (sort.value === "name"
          ? a.name.localeCompare(b.name)
          : sort.value === "rarity"
            ? rarityRank.indexOf(b.rarity) - rarityRank.indexOf(a.rarity) ||
              a.number - b.number
            : sort.value === "quantity"
              ? b.quantity - a.quantity || a.number - b.number
              : sort.value === "number"
                ? a.number - b.number
                : new Date(b.acquiredAt) - new Date(a.acquiredAt)),
    ),
);
const total = computed(() =>
  cards.value.reduce((sum, c) => sum + c.quantity, 0),
);
const isOwn = computed(
  () => Number(route.params.id) === player.data.user.id,
);
async function load() {
  loading.value = true;
  accessDenied.value = false;
  error.value = "";
  cards.value = [];
  owner.value = null;
  selected.value = null;
  try {
    const id = route.params.id;
    owner.value = (await api(`/users/${id}`)).user;
    cards.value = (await api(`/users/${id}/collection`)).cards;
  } catch (e) {
    accessDenied.value = e.status === 403;
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
function clear() {
  query.value = "";
  type.value = "";
  rarity.value = "";
}
onMounted(load);
watch(() => route.params.id, load);
</script>
<template>
  <div>
    <div class="page-intro">
      <div>
        <p class="eyebrow">CHAQUE CARTE A SON HISTOIRE</p>
        <h1>
          {{ isOwn ? "Votre collection" : `Collection de ${owner?.name || "…"}`
          }}<span class="accent">.</span>
        </h1>
        <p v-if="!loading && !error" class="muted">
          {{ total }} cartes · {{ cards.length }} différentes ·
          {{ total - cards.length }} en double
        </p>
      </div>
      <RouterLink v-if="isOwn" to="/packs" class="button primary"
        >Ouvrir un booster <ArrowUpRight :size="17"
      /></RouterLink>
    </div>
    <div v-if="!loading && !error && cards.length" class="collection-toolbar">
      <label class="search-field"
        ><Search :size="18" /><input
          v-model="query"
          maxlength="64"
          placeholder="Trouver une créature…"
          aria-label="Rechercher par nom" /></label
      ><label
        ><span class="sr-only">Filtrer par type</span
        ><select v-model="type">
          <option value="">Tous les types</option>
          <option v-for="t in types" :key="t" :value="t">{{ typeLabel(t) }}</option>
        </select></label
      ><label
        ><span class="sr-only">Filtrer par rareté</span
        ><select v-model="rarity">
          <option value="">Toutes les raretés</option>
          <option v-for="r in rarityRank" :key="r" :value="r">
            {{ rarityLabel(r) }}
          </option>
        </select></label
      ><label class="sort-field"
        ><SlidersHorizontal :size="15" /><select
          v-model="sort"
          aria-label="Trier les cartes"
        >
          <option value="recent">Plus récentes</option>
          <option value="number">Numéro de carte</option>
          <option value="name">Nom de A à Z</option>
          <option value="rarity">Plus rares</option>
          <option value="quantity">Plus d’exemplaires</option>
        </select></label
      >
    </div>
    <div v-if="!loading && !error && cards.length" class="collection-meta">
      <span
        >PREMIÈRE LUEUR <b>{{ filtered.length }} découvertes</b></span
      ><span v-if="owner?.status === 'banned'"><LockKeyhole :size="13" /> Album privé</span>
      <span v-else><BookOpen :size="13" /> Album public</span>
    </div>
    <div v-if="loading" class="loading-state" role="status">
      Ouverture de l’album…
    </div>
    <section
      v-else-if="accessDenied"
      class="private-album collection-denied"
      role="alert"
    >
      <span class="lock-emblem"><LockKeyhole :size="27" /></span>
      <p class="eyebrow">ALBUM PERSONNEL</p>
      <h2>Cet album est verrouillé.</h2>
      <p>{{ error }}</p>
      <RouterLink to="/players" class="button">Retour aux collectionneurs</RouterLink>
    </section>
    <div v-else-if="error" class="empty-state" role="alert">
      <h2>Impossible d’ouvrir cette collection.</h2>
      <p>{{ error }}</p>
      <button class="button" @click="load">Réessayer</button>
    </div>
    <div v-else-if="!cards.length" class="empty-state">
      <h2>Votre album attend sa première carte.</h2>
      <p>Utilisez le bouton ci-dessus pour commencer votre collection.</p>
    </div>
    <div v-else-if="!filtered.length" class="empty-state">
      <h2>Aucune créature ici. Pour l’instant.</h2>
      <p>Essayez un autre nom ou réinitialisez les filtres.</p>
      <button class="button" @click="clear">Effacer les filtres</button>
    </div>
    <TransitionGroup
      v-else
      name="cards"
      tag="div"
      class="card-grid collection-grid"
      ><div
        v-for="(card, i) in filtered"
        :key="card.id"
        class="card-cell"
        :style="{ '--i': Math.min(i, 8) }"
      >
        <TcgCard
          :card="card"
          interactive
          show-quantity
          @select="selected = $event"
        />
        <div class="card-caption">
          <span>{{ card.name }}</span
          ><small>{{ rarityLabel(card.rarity) }}</small>
        </div>
      </div></TransitionGroup
    >
    <CardDetail v-if="selected" :card="selected" :foreign="!isOwn" @close="selected = null" />
  </div>
</template>
