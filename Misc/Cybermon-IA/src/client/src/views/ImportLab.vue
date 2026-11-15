<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
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
const scanState = ref(null);
const displayedProgress = ref(0);
const clock = ref(Date.now());
const connectionNotice = ref("");
const controller = new AbortController();
let pollTimer, clockTimer, animation;
let mounted = true;
const pending = (status) => ["uploading", "queued", "processing"].includes(status);
const elapsed = computed(() => scanState.value
  ? Math.max(0, Math.floor(((scanState.value.finishedAt || clock.value) - scanState.value.startedAt) / 1000))
  : 0);
const stageLabel = computed(() => {
  const task = scanState.value;
  if (!task) return "";
  if (task.status === "queued") return `En attente - position ${task.position || 1}`;
  return ({
    uploading: "Transmission au scanner", encoding: "Analyse visuelle",
    generating: "Génération de la légende", matching: "Reconnaissance de la carte",
    saving: "Création de la carte", done: "Carte prête", failed: "Analyse interrompue",
  })[task.stage] || "Analyse en cours";
});

watch(() => scanState.value?.progress || 0, (target) => {
  cancelAnimationFrame(animation);
  const from = displayedProgress.value;
  const started = performance.now();
  const draw = (now) => {
    const fraction = Math.min(1, (now - started) / 1100);
    displayedProgress.value = from + (target - from) * (1 - (1 - fraction) ** 3);
    if (fraction < 1) animation = requestAnimationFrame(draw);
  };
  animation = requestAnimationFrame(draw);
});

function applyStatus(task) {
  if (!mounted || !task) return;
  scanState.value = task;
  busy.value = pending(task.status);
  startCooldown(task.cooldownRemainingSeconds || 0);
  if (task.status === "failed" && task.cooldownRemainingSeconds > 0) {
    scanState.value = null;
    error.value = "";
    return;
  }
  if (task.status === "done") {
    result.value = task.result;
    void refreshPlayer().catch(() => {});
  } else if (task.status === "failed") {
    error.value = task.error;
  }
}

async function pollStatus() {
  try {
    const { task } = await api("/imports/status", { signal: controller.signal });
    if (!mounted) return;
    connectionNotice.value = "";
    if (task) applyStatus(task);
    else {
      busy.value = false;
      if (scanState.value) scanState.value = { ...scanState.value, status: "failed", stage: "failed" };
      error.value = "Le suivi a expiré ou le scanner a redémarré. Consultez votre collection avant de réessayer.";
    }
  } catch (e) {
    if (!mounted) return;
    connectionNotice.value = "Connexion au suivi interrompue. Nouvelle tentative automatique...";
  }
  if (mounted && busy.value) pollTimer = setTimeout(pollStatus, 1000);
}
let timer;
let cooldownUntil = 0;

function choose(event) {
  error.value = "";
  result.value = null;
  scanState.value = null;
  displayedProgress.value = 0;
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
  result.value = null;
  connectionNotice.value = "";
  try {
    const task = await api("/imports", {
      method: "POST",
      headers: { "Content-Type": file.value.type },
      body: file.value,
    });
    applyStatus(task);
    if (busy.value) pollTimer = setTimeout(pollStatus, 1000);
  } catch (e) {
    error.value = e.message;
    busy.value = false;
    // A lost POST response must not encourage submitting the same image again.
    if (!e.status) {
      busy.value = true;
      void pollStatus();
    }
  }
}

onMounted(async () => {
  clockTimer = setInterval(() => { clock.value = Date.now(); }, 1000);
  try {
    info.value = await api("/imports/model");
    startCooldown(info.value.cooldownRemainingSeconds);
    if (info.value.activeImport) {
      applyStatus(info.value.activeImport);
      if (busy.value) pollTimer = setTimeout(pollStatus, 1000);
    }
  } catch (e) {
    error.value = e.message;
  }
});

onUnmounted(() => {
  mounted = false;
  controller.abort();
  clearTimeout(pollTimer);
  clearInterval(clockTimer);
  cancelAnimationFrame(animation);
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
        <div v-if="scanState" class="scan-progress" :class="{ failed: scanState.status === 'failed' }">
          <div class="scan-progress-heading">
            <strong role="status">{{ stageLabel }}</strong>
            <span>{{ Math.round(displayedProgress) }} %</span>
          </div>
          <div
            class="scan-progress-track"
            role="progressbar"
            aria-label="Progression estimée de l'analyse"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-valuenow="Math.round(displayedProgress)"
            :aria-valuetext="stageLabel"
          >
            <div class="scan-progress-fill" :style="{ width: `${displayedProgress}%` }" />
          </div>
          <div class="scan-progress-details">
            <span>Progression estimée · {{ elapsed }} s écoulées</span>
            <span v-if="scanState.stage === 'generating'">{{ scanState.step }}/{{ scanState.maxSteps }} étapes maximum</span>
          </div>
          <p v-if="scanState.status === 'queued'" class="scanner-note">Votre illustration est enregistrée. L'analyse démarrera dès que le scanner sera disponible.</p>
          <p v-if="connectionNotice" class="scanner-note" role="status">{{ connectionNotice }}</p>
        </div>
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

<style scoped>
.upload-zone img { image-rendering: pixelated; }
.scan-progress {
  margin-top: 22px;
  padding: 18px;
  border: 1px solid #9c7bdb55;
  border-radius: 12px;
  background: linear-gradient(130deg, #6d37b51a, #3974d51a);
}
.scan-progress-heading, .scan-progress-details {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}
.scan-progress-heading { font-size: 14px; }
.scan-progress-heading > span { color: #d9c4ff; font-variant-numeric: tabular-nums; }
.scan-progress-track { height: 9px; margin: 14px 0 11px; overflow: hidden; border-radius: 20px; background: #ffffff12; }
.scan-progress-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #9b62ed, #79a8ff); box-shadow: 0 0 16px #9857df66; }
.scan-progress-details { flex-wrap: wrap; font-size: 11px; color: #c3b9d9; }
.scan-progress.failed .scan-progress-fill { background: #c97982; }
.scan-progress .scanner-note { margin-bottom: 0; }
@media (prefers-reduced-motion: reduce) {
  .scan-progress-fill { box-shadow: none; }
}
</style>
