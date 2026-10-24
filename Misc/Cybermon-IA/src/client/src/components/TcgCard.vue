<script setup>
import { computed, ref } from "vue";
import { rarityLabel, typeLabel } from "../services/api";
const props = defineProps({
  card: { type: Object, required: true },
  interactive: Boolean,
  showQuantity: Boolean,
});
const emit = defineEmits(["select"]);
const tilt = ref({});
const accessibleLabel = computed(() => {
  const quantity = props.card.quantity || 0;
  const copies = quantity === 1 ? "exemplaire" : "exemplaires";
  return `${props.card.name}, ${rarityLabel(props.card.rarity)}, ${quantity} ${copies}. Voir le détail`;
});
function move(event) {
  if (
    !props.interactive ||
    event.pointerType === "touch" ||
    matchMedia("(prefers-reduced-motion: reduce)").matches
  )
    return;
  const rect = event.currentTarget.getBoundingClientRect();
  tilt.value = {
    transform: `perspective(850px) rotateY(${(event.clientX - rect.left - rect.width / 2) / 30}deg) rotateX(${-(event.clientY - rect.top - rect.height / 2) / 40}deg)`,
  };
}
</script>
<template>
  <component
    :is="interactive ? 'button' : 'div'"
    :type="interactive ? 'button' : undefined"
    class="tcg-card"
    :class="[
      `type-${card.type}`,
      `rarity-${card.rarity}`,
      { 'has-quantity': showQuantity },
    ]"
    :style="tilt"
    :aria-label="interactive ? accessibleLabel : undefined"
    @pointermove="move"
    @pointerleave="tilt = {}"
    @click="interactive && emit('select', card)"
  >
    <div v-if="card.rarity === 'supreme'" class="supreme-card">
      <img
        class="supreme-art"
        :src="card.image"
        :alt="card.name"
        width="733"
        height="1024"
        draggable="false"
      />
    </div>
    <div v-else class="card-inner classic-card">
      <img
        class="classic-frame"
        :src="`/cards/${card.type}.png`"
        alt=""
        width="733"
        height="1024"
        draggable="false"
      />
      <div class="card-heading">
        <strong>{{ card.name }}</strong
        ><span>
          <small>PV</small> {{ card.hp }}
          <img
            :src="`/types/${card.type}.png`"
            :alt="typeLabel(card.type)"
            :title="typeLabel(card.type)"
          />
        </span
        >
      </div>
      <div class="card-art">
        <img
          :src="card.image"
          :alt="card.name"
          width="64"
          height="64"
          draggable="false"
        />
      </div>
      <div class="card-moves">
        <div v-for="move in card.attacks.slice(0, 2)" :key="move.name">
          <span class="energy">
            <img
              v-for="energy in move.cost || 1"
              :key="energy"
              :src="`/types/${move.type || card.type}.png`"
              alt=""
            />
          </span
          ><b>{{ move.name }}</b
          ><strong>{{ move.damage }}</strong>
        </div>
      </div>
      <p class="card-lore">{{ card.lore }}</p>
      <div class="card-bottom">
        <span>{{
          card.rarity === "golden"
            ? "COFFRE · PIÈCE UNIQUE"
            : card.special
              ? "LABO · ANALYSE D’ARCHIVE"
              : `PL · ${String(card.number).padStart(3, "0")}/040`
        }}</span
        ><span
          >{{ rarityLabel(card.rarity) }}
          <b>{{
            ["holo", "secret", "golden"].includes(card.rarity)
              ? "✦"
              : card.rarity === "rare"
                ? "★"
                : card.rarity === "uncommon"
                  ? "◆"
                  : "●"
          }}</b></span
        >
      </div>
    </div>
    <span v-if="showQuantity" class="quantity">×{{ card.quantity }}</span>
  </component>
</template>
