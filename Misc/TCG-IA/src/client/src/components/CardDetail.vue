<script setup>
import { onMounted, ref } from "vue";
import { X } from "lucide-vue-next";
import { api, rarityLabel, statLabel, typeLabel } from "../services/api";
import TcgCard from "./TcgCard.vue";
const props = defineProps({ card: Object, foreign: Boolean });
const emit = defineEmits(["close"]);
const dialog = ref(null),
  details = ref(props.card),
  error = ref("");
onMounted(async () => {
  dialog.value.showModal();
  if (props.card.special) return;
  try {
    details.value = await api(`/cards/${props.card.id}`);
  } catch (e) {
    error.value = e.message;
  }
});
function backdrop(event) {
  if (event.target === dialog.value) emit("close");
}
</script>
<template>
  <dialog
    ref="dialog"
    class="card-dialog"
    aria-labelledby="detail-title"
    @click="backdrop"
    @cancel.prevent="emit('close')"
    @close="emit('close')"
  >
    <div class="detail-layout">
      <button
        class="close-button"
        aria-label="Fermer le détail de la carte"
        autofocus
        @click="emit('close')"
      >
        <X />
      </button>
      <TcgCard :card="details" />
      <section class="detail-copy">
        <p class="eyebrow">
          {{
            details.rarity === "supreme"
              ? "CARTE SUPRÊME / PIÈCE UNIQUE"
              : details.special
                ? "LABORATOIRE D’ILLUSTRATION / ANALYSE D’ARCHIVE"
                : `PREMIÈRE LUEUR / Nº ${String(details.number).padStart(3, "0")}`
          }}
        </p>
        <h2 id="detail-title">{{ details.name }}</h2>
        <p class="detail-rarity">
          {{ typeLabel(details.type) }} <span>·</span> {{ rarityLabel(details.rarity) }}
        </p>
        <p class="lore-full">{{ details.lore }}</p>
        <div v-if="details.rarity !== 'supreme'" class="stat-bars">
          <div v-for="(value, stat) in details.stats" :key="stat">
            <span>{{ statLabel(stat) }}</span
            ><meter min="0" max="100" :value="value" :aria-label="statLabel(stat)" /><b>{{
              value
            }}</b>
          </div>
        </div>
        <div v-if="details.rarity !== 'supreme'" class="detail-attacks">
          <p class="eyebrow">ATTAQUES</p>
          <div v-for="attack in details.attacks" :key="attack.name">
            <span>{{ attack.name }}</span
            ><b>{{ attack.damage }}</b>
          </div>
        </div>
        <p class="owned-line">
          <span>{{ props.foreign ? "Dans cette collection" : "Dans votre collection" }}</span
          ><strong
            >{{ details.quantity || 0 }}
            {{ details.quantity === 1 ? "exemplaire" : "exemplaires" }}</strong
          >
        </p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
      </section>
    </div>
  </dialog>
</template>
