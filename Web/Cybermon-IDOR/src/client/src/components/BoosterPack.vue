<script setup>
defineProps({ opening: Boolean });
</script>
<template>
  <div
    class="booster"
    :class="{ tearing: opening }"
    aria-label="Booster Première Lueur"
  >
    <div class="pack-seal top" />
    <div class="pack-face">
      <div class="pack-brand">Cybermon<span>JEU DE CARTES À COLLECTIONNER</span></div>
      <div class="pack-emblem">
        <span class="emblem-ring" /><img
          src="/creatures/agnigon.png"
          alt="Agnigon"
          draggable="false"
          width="64"
          height="64"
        />
      </div>
      <div class="pack-title">
        <small>SÉRIE 001</small><strong>PREMIÈRE<br />LUEUR</strong
        ><span>L’AVENTURE COMMENCE ICI</span>
      </div>
      <div class="pack-foot"><span>5 CARTES À JOUER</span><span>✦</span></div>
    </div>
    <div class="pack-seal bottom" />
  </div>
</template>
