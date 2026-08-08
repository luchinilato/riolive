/**
 * Relay de saída do Sinal Carioca — Cloudflare Worker.
 *
 * Por que existe: o MetrôRio devolve 403 (`server: awselb/2.0`) para o IP do
 * nosso VPS e 200 para uma máquina residencial, com o mesmo cliente, os mesmos
 * headers e o mesmo handshake TLS. É WAF barrando a faixa do datacenter, não o
 * projeto. O relay dá outra saída de IP — não disfarça quem somos: o
 * user-agent do coletor continua identificado com o contato do projeto.
 *
 * Duas travas, porque relay sem trava é open proxy e open proxy é achado e
 * abusado em dias:
 *
 * 1. ALVOS: allowlist de host. Qualquer outro host é 403 aqui, antes de sair.
 * 2. TOKEN: segredo compartilhado com o coletor (`wrangler secret put TOKEN`).
 *
 * Publicar:
 *   cd deploy/relay && npx wrangler deploy
 *   npx wrangler secret put TOKEN
 *
 * E no `.env` do servidor:
 *   RIOLIVE_PROXY_SAIDA=https://<nome>.<subdominio>.workers.dev
 *   RIOLIVE_PROXY_HOSTS=api.ondeestameutrem.metrorio.app
 *   RIOLIVE_PROXY_TOKEN=<o mesmo segredo>
 */

const ALVOS = new Set(['api.ondeestameutrem.metrorio.app'])

// Repassados na ida; o resto fica de fora para não vazar cabeçalho interno.
const CABECALHOS_DE_IDA = ['authorization', 'accept', 'user-agent']

export default {
  async fetch(requisicao, env) {
    if (env.TOKEN && requisicao.headers.get('X-Riolive-Token') !== env.TOKEN) {
      return new Response('token inválido', { status: 401 })
    }

    const alvo = requisicao.headers.get('X-Riolive-Alvo')
    if (!alvo) return new Response('falta X-Riolive-Alvo', { status: 400 })

    let url
    try {
      url = new URL(alvo)
    } catch {
      return new Response('X-Riolive-Alvo não é URL', { status: 400 })
    }
    if (url.protocol !== 'https:' || !ALVOS.has(url.hostname)) {
      return new Response(`host não permitido: ${url.hostname}`, { status: 403 })
    }

    const cabecalhos = new Headers()
    for (const nome of CABECALHOS_DE_IDA) {
      const valor = requisicao.headers.get(nome)
      if (valor) cabecalhos.set(nome, valor)
    }

    /* O status da origem volta como está — inclusive o 403, se o bloqueio
       alcançar a Cloudflare também. Traduzir para 200 aqui esconderia a única
       evidência de que o relay não resolveu. */
    const resposta = await fetch(url.toString(), {
      method: 'GET',
      headers: cabecalhos,
    })
    return new Response(resposta.body, {
      status: resposta.status,
      headers: { 'content-type': resposta.headers.get('content-type') || 'application/json' },
    })
  },
}
