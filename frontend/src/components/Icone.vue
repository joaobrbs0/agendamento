<script setup>
defineProps({ nome: { type: String, required: true } })

const CAMINHOS = {
  calendario: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  nova: '<circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/>',
  minhas: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  painel: '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  gestao: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
  sair: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  esq: '<path d="M15 18l-6-6 6-6"/>',
  dir: '<path d="M9 18l6-6-6-6"/>',
  usuario: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  escudo: '<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/>',
  carro: '<path d="M5 17h14M3 13l2-6a2 2 0 0 1 2-1h10a2 2 0 0 1 2 1l2 6v4H3z"/><circle cx="7.5" cy="17" r="1.5"/><circle cx="16.5" cy="17" r="1.5"/>',
  troca: '<path d="M17 3l4 4-4 4M3 7h18M7 21l-4-4 4-4M21 17H3"/>',
}
</script>

<template>
  <svg
    viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
    v-html="CAMINHOS[nome]"
  />
</template>
