<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { entrar } from '../auth'
import { sessao, sair } from '../auth'
import Icone from '../components/Icone.vue'

const router = useRouter()
const modo = ref('usuario')
const usuario = ref('')
const senha = ref('')
const erro = ref('')
const enviando = ref(false)

function trocar(m) {
  modo.value = m
  erro.value = ''
}

async function enviar() {
  erro.value = ''
  enviando.value = true
  try {
    await entrar(usuario.value.trim(), senha.value)
    if (modo.value === 'admin') {
      if (!sessao.usuario.gestor) {
        sair()
        erro.value = 'Esta conta não tem acesso de administrador.'
        return
      }
      router.push({ name: 'painel' })
    } else {
      router.push({ name: 'calendario' })
    }
  } catch (e) {
    erro.value = e.message
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="login-pagina">
    <section class="login-lado">
      <span class="brasao"><Icone nome="escudo" /></span>
      <h2>Reserva de Veículos</h2>
      <p>
        Consulte a disponibilidade da frota no calendário, solicite reservas
        e acompanhe o andamento dos seus pedidos.
      </p>
      <small>Prefeitura de Joinville</small>
    </section>

    <section class="login-form">
      <div class="login-caixa">
        <h1>Entrar</h1>
        <p class="sub">Escolha o tipo de acesso.</p>

        <div class="acesso">
          <button :class="{ ativo: modo === 'usuario' }" @click="trocar('usuario')">
            <Icone nome="usuario" /> Usuário
          </button>
          <button :class="{ ativo: modo === 'admin' }" @click="trocar('admin')">
            <Icone nome="escudo" /> Administrador
          </button>
        </div>

        <div class="cartao">
          <label>
            <span>Usuário</span>
            <input v-model="usuario" autocomplete="username" autofocus @keyup.enter="enviar" />
          </label>
          <label>
            <span>Senha</span>
            <input v-model="senha" type="password" autocomplete="current-password" @keyup.enter="enviar" />
          </label>
          <p v-if="erro" class="erro">{{ erro }}</p>
          <button class="entrar" :disabled="enviando || !usuario || !senha" @click="enviar">
            Entrar como {{ modo === 'admin' ? 'administrador' : 'usuário' }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
