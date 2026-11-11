<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { entrar } from '../auth'

const router = useRouter()
const usuario = ref('')
const senha = ref('')
const erro = ref('')
const enviando = ref(false)

async function enviar() {
  erro.value = ''
  enviando.value = true
  try {
    await entrar(usuario.value.trim(), senha.value)
    router.push({ name: 'calendario' })
  } catch (e) {
    erro.value = e.message
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="login cartao">
    <h1>Reserva de veículos</h1>
    <label>
      <span>Usuário</span>
      <input v-model="usuario" autocomplete="username" autofocus @keyup.enter="enviar" />
    </label>
    <label>
      <span>Senha</span>
      <input v-model="senha" type="password" autocomplete="current-password" @keyup.enter="enviar" />
    </label>
    <p v-if="erro" class="erro">{{ erro }}</p>
    <button :disabled="enviando || !usuario || !senha" @click="enviar">Entrar</button>
  </div>
</template>
