<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { entrarComGoogle, sessao, sair } from '../auth'
import Icone from '../components/Icone.vue'

const router = useRouter()
const modo = ref('usuario')
const erro = ref('')
const enviando = ref(false)
const botaoGoogle = ref(null)
const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

function trocar(m) {
  modo.value = m
  erro.value = ''
}

async function aoReceberGoogle(resposta) {
  erro.value = ''
  enviando.value = true
  try {
    await entrarComGoogle(resposta.credential)
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

// O script do Google carrega de forma assíncrona; espera ele ficar disponível.
function iniciarGoogle(tentativas = 0) {
  if (window.google?.accounts?.id) {
    window.google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: aoReceberGoogle,
    })
    window.google.accounts.id.renderButton(botaoGoogle.value, {
      theme: 'outline', size: 'large', text: 'signin_with', locale: 'pt-BR', width: 320,
    })
  } else if (tentativas < 50) {
    setTimeout(() => iniciarGoogle(tentativas + 1), 100)
  }
}

onMounted(() => { if (CLIENT_ID) iniciarGoogle() })
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
          <template v-if="CLIENT_ID">
            <p class="sub">
              Entre com sua conta institucional do Google
              para acessar como {{ modo === 'admin' ? 'administrador' : 'usuário' }}.
            </p>
            <div ref="botaoGoogle" class="google-botao" />
          </template>
          <p v-else class="erro">Login com Google não configurado (VITE_GOOGLE_CLIENT_ID).</p>
          <p v-if="erro" class="erro">{{ erro }}</p>
        </div>
      </div>
    </section>
  </div>
</template>