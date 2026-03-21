<template>
  <router-view />
</template>

<script setup>
// Usa Vue Router para gerenciar páginas
</script>

<style>
:root {
  --inteia-navy: #0b1426;
  --inteia-navy-soft: #16233b;
  --inteia-amber: #f59e0b;
  --inteia-amber-soft: #fbbf24;
  --inteia-ink: #101826;
  --inteia-paper: #f6f3ec;
  --inteia-line: rgba(12, 23, 42, 0.12);
}

/* Reset global de estilos */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Inter', 'Space Grotesk', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--inteia-ink);
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.12), transparent 28%),
    linear-gradient(180deg, #f7f3ea 0%, #f3efe6 100%);
}

/* Estilo da barra de rolagem */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(11, 20, 38, 0.08);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--inteia-amber), #b45309);
  border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--inteia-amber-soft), var(--inteia-amber));
}

/* Estilo global de botões */
button {
  font-family: inherit;
}
</style>
