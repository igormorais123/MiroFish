<template>
  <InteiaBackground />
  <router-view />
</template>

<script setup>
import InteiaBackground from './components/InteiaBackground.vue'
</script>

<style>
/* Tokens, reset e regras globais ficam em src/assets/inteia-theme.css */

/* Garante que conteúdo das views fica acima do canvas neural */
#app > *:not(.inteia-bg) {
  position: relative;
  z-index: var(--z-content, 10);
}
</style>
