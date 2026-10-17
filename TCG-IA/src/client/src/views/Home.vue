<script setup>
import { ref } from "vue";
import {
  ArrowUpRight,
  ArrowRight,
  BookOpen,
  Sparkles,
  ScanLine,
} from "lucide-vue-next";
import { player, rarityLabel } from "../services/api";
import TcgCard from "../components/TcgCard.vue";
import CardDetail from "../components/CardDetail.vue";
import BoosterPack from "../components/BoosterPack.vue";
const selected = ref(null);
</script>
<template>
  <div class="home-view">
    <div class="page-intro">
      <div>
        <p class="eyebrow">VOTRE CARNET DE COLLECTION</p>
        <h1>
          Ravi de vous revoir, {{ player.data.user.name
          }}<span class="accent">.</span>
        </h1>
      </div>
      <span class="small-note"
        ><BookOpen :size="14" /> Votre collection est publique</span
      >
    </div>
    <div class="home-grid">
      <section class="release-panel">
        <div class="release-copy">
          <p class="eyebrow"><span class="tiny-rule" /> SÉRIE 001 · DISPONIBLE</p>
          <h2>Petit booster.<br />Grandes possibilités.</h2>
          <p>
            Découvrez les créatures de Première Lueur.<br />Cinq cartes à
            collectionner.
          </p>
          <RouterLink class="button primary" to="/packs"
            >Ouvrir un booster <ArrowUpRight :size="19" /></RouterLink
          ><span class="release-note">Une carte rare ou mieux par booster.</span>
        </div>
        <div class="hero-pack">
          <div class="hero-orbit" />
          <span class="vertical-note">TUXEMON · PREMIÈRE ÉDITION</span
          ><BoosterPack /><span class="edition-tag">01 — PREMIÈRE LUEUR</span>
        </div>
      </section>
      <aside class="album-summary">
        <p class="eyebrow">VOTRE COLLECTION</p>
        <div class="big-number">
          {{ String(player.data.stats.total).padStart(2, "0")
          }}<span>cartes collectionnées</span>
        </div>
        <div class="summary-pair">
          <div>
            <strong
              >{{ player.data.stats.unique
              }}<small> / {{ player.data.stats.catalogSize }}</small></strong
            ><span>créatures découvertes</span>
          </div>
          <div>
            <strong>{{ player.data.stats.duplicates }}</strong
            ><span>exemplaires en double</span>
          </div>
        </div>
        <div class="album-progress">
          <span
            :style="{
              width: `${(100 * player.data.stats.unique) / player.data.stats.catalogSize}%`,
            }"
          />
        </div>
        <div class="highest">
          <Sparkles :size="18" />
          <div>
            <small>VOTRE PLUS BELLE TROUVAILLE</small
            ><b>{{ rarityLabel(player.data.stats.highestRarity) }}</b>
          </div>
        </div>
        <RouterLink to="/collection"
          >Explorer votre collection <ArrowRight :size="17"
        /></RouterLink>
      </aside>
    </div>
    <RouterLink to="/lab" class="lab-banner">
      <span class="lab-banner-icon"><ScanLine :size="22" /></span>
      <span>
        <small>NOUVEAU · LABORATOIRE D’ILLUSTRATION</small>
        <strong>Transformez votre créature en carte d’archive.</strong>
      </span>
      <ArrowRight :size="19" />
    </RouterLink>
    <section class="recent-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">NOUVEAUTÉS DANS VOTRE ALBUM</p>
          <h2>Dernières découvertes</h2>
        </div>
        <RouterLink to="/collection"
          >Voir la collection <ArrowRight :size="16"
        /></RouterLink>
      </div>
      <div v-if="!player.data.recent.length" class="empty-state">
        <h3>Votre album est prêt.</h3>
        <p>Votre première découverte vous attend dans un booster.</p>
        <RouterLink class="button primary" to="/packs">
          Ouvrir un booster <ArrowUpRight :size="17" />
        </RouterLink>
      </div>
      <div v-else class="card-grid recent-grid">
        <div
          v-for="(card, i) in player.data.recent"
          :key="card.id"
          class="card-cell"
          :style="{ '--i': i }"
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
        </div>
      </div>
    </section>
    <CardDetail v-if="selected" :card="selected" @close="selected = null" />
  </div>
</template>
