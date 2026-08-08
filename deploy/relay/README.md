# Relay de saída

Worker da Cloudflare que dá ao coletor um IP de saída diferente do VPS, para
origens que barram a faixa do datacenter. Hoje serve uma fonte: o MetrôRio.

## O que foi medido (2026-08-07)

| de onde | `metrorio.com.br` (site) | `api.ondeestameutrem.metrorio.app` |
|---|---|---|
| máquina residencial | 200 | 200 — devolve as 3 linhas |
| VPS Contabo | 200 | **403**, `server: awselb/2.0` |

curl e httpx tomam 403 igual a partir do VPS, então **não é o handshake TLS** —
é diferente do caso do COR, onde `exige_libcurl` resolveu. É WAF da AWS
barrando a faixa de IP.

## O que ainda NÃO foi medido

**Se o IP de saída da Cloudflare passa.** A regra da AWS pode ser uma lista de
IPs de hospedagem em geral, e nesse caso o Worker toma o mesmo 403. O relay
devolve o status da origem sem traduzir justamente para esse teste ser direto:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "X-Riolive-Token: $TOKEN" \
  -H 'X-Riolive-Alvo: https://api.ondeestameutrem.metrorio.app/v1/StatusLinha' \
  https://riolive-relay.<subdominio>.workers.dev
```

`401` sem o token, `200` se o relay resolveu, `403` se a AWS bloqueia a
Cloudflare também. Nesse último caso o caminho é outra saída (outro provedor,
ou pedir acesso ao MetrôRio) — não vale insistir em rodízio de IP.

## Publicar

```bash
cd deploy/relay
npx wrangler deploy
npx wrangler secret put TOKEN      # gere com: openssl rand -hex 32
```

E no `.env` do servidor:

```
RIOLIVE_PROXY_SAIDA=https://riolive-relay.<subdominio>.workers.dev
RIOLIVE_PROXY_HOSTS=api.ondeestameutrem.metrorio.app
RIOLIVE_PROXY_TOKEN=<o mesmo segredo>
```

Só os hosts listados em `RIOLIVE_PROXY_HOSTS` desviam — o resto sai direto. É
de propósito: rotear tudo por um ponto único trocaria um bloqueio conhecido por
uma dependência capaz de derrubar todas as fontes de uma vez.

## Custo

Plano grátis: 100 mil requisições por dia. O metrô coleta a cada poucos minutos
— duas ordens de grandeza abaixo do limite.
