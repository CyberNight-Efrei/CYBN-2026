<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  ImagePlus,
  ScanLine,
} from "lucide-vue-next";
import { api, refreshPlayer } from "../services/api";
import TcgCard from "../components/TcgCard.vue";

const info = ref(null);
const file = ref(null);
const previewUrl = ref("");
const result = ref(null);
const error = ref("");
const busy = ref(false);
const cooldown = ref(0);
let timer;
let cooldownUntil = 0;

function choose(event) {
  error.value = "";
  result.value = null;
  const selected = event.target.files?.[0] || null;
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = "";
  file.value = null;
  if (!selected) return;
  if (!info.value.acceptedTypes.includes(selected.type)) {
    error.value = "Choisissez une illustration PNG, JPEG ou WebP.";
    return;
  }
  if (selected.size > info.value.maxBytes) {
    error.value = "Cette illustration dépasse 2 Mo.";
    return;
  }
  file.value = selected;
  previewUrl.value = URL.createObjectURL(selected);
}

function startCooldown(seconds) {
  clearInterval(timer);
  cooldownUntil = Date.now() + Math.max(0, seconds) * 1000;
  const update = () => {
    cooldown.value = Math.max(
      0,
      Math.ceil((cooldownUntil - Date.now()) / 1000),
    );
    if (!cooldown.value) clearInterval(timer);
  };
  update();
  if (cooldown.value) timer = setInterval(update, 1000);
}

async function scan() {
  if (!file.value || busy.value || cooldown.value) return;
  busy.value = true;
  error.value = "";
  try {
    result.value = await api("/imports", {
      method: "POST",
      headers: { "Content-Type": file.value.type },
      body: file.value,
    });
    startCooldown(result.value.cooldownSeconds);
    await refreshPlayer();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

onMounted(async () => {
  try {
    info.value = await api("/imports/model");
    startCooldown(info.value.cooldownRemainingSeconds);
  } catch (e) {
    error.value = e.message;
  }
});

onUnmounted(() => {
  clearInterval(timer);
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
});
</script>

<template>
  <div class="lab-view">
    <div class="page-intro">
      <div>
        <p class="eyebrow">NOUVEAU DANS LES ARCHIVES</p>
        <h1>Laboratoire d’illustration<span class="accent">.</span></h1>
        <p class="muted">Transformez une illustration de créature en carte d’archive jouable.</p>
      </div>
      <span class="small-note"><BrainCircuit :size="15" /> Propulsé par BLIP</span>
    </div>

    <div class="lab-layout">
      <section class="scanner-panel">
        <div class="scanner-heading">
          <div>
            <p class="eyebrow">SCANNER IMAGE-VERS-CARTE</p>
            <h2>Montrez-nous une créature.</h2>
          </div>
          <ScanLine :size="29" />
        </div>
        <label class="upload-zone" :class="{ ready: previewUrl }">
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            :disabled="busy || !info"
            @change="choose"
          />
          <img v-if="previewUrl" :src="previewUrl" alt="Aperçu de l’illustration choisie" />
          <template v-else>
            <span class="upload-icon"><ImagePlus :size="28" /></span>
            <strong>Choisir une illustration</strong>
            <small>PNG, JPEG ou WebP · 2 Mo maximum</small>
          </template>
        </label>
        <p class="scanner-note">
          Pour cette version, utilisez l’illustration de la créature elle-même,
          et non une photo de la carte imprimée entière.
        </p>
        <button
          class="button primary wide"
          :disabled="!file || busy || cooldown"
          @click="scan"
        >
          <span>{{ busy ? "Analyse de l’illustration…" : cooldown ? `Scanner disponible dans ${cooldown} s` : "Créer la carte d’archive" }}</span>
          <ArrowRight :size="18" />
        </button>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
      </section>

      <aside v-if="info" class="model-card">
        <Cpu :size="25" />
        <p class="eyebrow">TRANSPARENCE DU MODÈLE</p>
        <h2>{{ info.model }}</h2>
        <p>
          Le scanner est déterministe et sa recette exacte est publique afin
          que chaque carte d’archive puisse être reproduite.
        </p>
        <dl>
          <div><dt>Révision</dt><dd>{{ info.revision }}</dd></div>
          <div><dt>Processeur</dt><dd>{{ info.processor }}</dd></div>
          <div><dt>Génération</dt><dd>{{ info.generation.numBeams }} faisceaux · {{ info.generation.maxNewTokens }} jetons</dd></div>
          <div><dt>Échantillonnage</dt><dd>{{ info.generation.doSample ? "activé" : "désactivé" }}</dd></div>
          <div><dt>Cartes connues</dt><dd>{{ info.catalogMatching }}</dd></div>
        </dl>
      </aside>
    </div>

    <section v-if="result" class="scan-result">
      <div class="scan-result-card"><TcgCard :card="result.card" /></div>
      <div class="scan-result-copy">
        <span class="result-check"><CheckCircle2 :size="22" /></span>
        <p class="eyebrow">ANALYSE TERMINÉE</p>
        <h2>{{ result.card.name }}</h2>
        <p class="caption-quote">“{{ result.caption }}”</p>
        <p class="muted">
          {{
            result.matched
              ? `Correspondance trouvée avec l’illustration ${result.matched.slug} du catalogue.`
              : "Une nouvelle carte d’archive a été créée à partir de la légende du modèle."
          }}
        </p>
        <RouterLink to="/collection" class="button">Voir dans la collection</RouterLink>
      </div>
    </section>
  </div>
</template>
