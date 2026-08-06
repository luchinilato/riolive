// @ts-nocheck — porte literal da lógica do protótipo (JS); tipagem fina na estabilização
/* View-model do painel — portado do handoff do Claude Design (2026-08-06).
   Os valores fixos são o modo demonstração (calmo/crise/zona) do protótipo;
   dadosReais.ts sobrepõe com a API onde a fonte já existe. */

import type { Acoes, EstadoUi, Modelo } from './tipos'

const SEV = [null,
  {n:1,l:'Normalidade',c:'var(--s1)',i:'●',bg:'var(--s1-bg)'},
  {n:2,l:'Mobilização',c:'var(--s2)',i:'◆',bg:'var(--s2-bg)'},
  {n:3,l:'Atenção',c:'var(--s3)',i:'▲',bg:'var(--s3-bg)'},
  {n:4,l:'Alerta',c:'var(--s4)',i:'◼',bg:'var(--s4-bg)'},
  {n:5,l:'Crise',c:'var(--s5)',i:'✦',bg:'var(--s5-bg)'}];
const RAMP = ['#9bd7ec','#57b7dc','#2c96c4','#1d7cab','#166490','#114e75'];
const rnd = (s) => { let x = Math.sin(s) * 10000; return x - Math.floor(x); };

function poly(vals, w, h, max) {
  const m = max || Math.max(1, ...vals);
  return vals.map((v,i) => (i*(w/(vals.length-1))).toFixed(1) + ',' + (h - (v/m)*(h-3)).toFixed(1)).join(' ');
}

export { SEV, RAMP, poly }

export function modeloBase(s: EstadoUi, acoes: Acoes): Modelo {
  const defina = acoes.defina

    
    const crisis = s.mode === 'crise';
    const zone = s.zone;
    const zn = zone === 'norte';

    const citySev = SEV[crisis ? 4 : 1];
    const headline = crisis
      ? 'Chuva forte na Zona Oeste e Jacarepaguá · 14 linhas de ônibus sem circular · risco de alagamento até 18h.'
      : (zn ? 'A Zona Norte opera normalmente. Sem chuva nas últimas 24 h; 1.184 veículos em circulação.'
            : 'A cidade opera normalmente. Sem chuva nas últimas 24h.');

    // ---------- painéis ----------
    const chuva = crisis ? {
      sev:SEV[4], bd:'var(--s4-bd)', hero:'45,2', hc:'var(--s4)', count:'33 ESTAÇÕES',
      sub:'máx. em Jacarepaguá · 12 estações acima de 20 mm/h',
      rios:'Rios: Acari 210 cm ▲ transbordo · Faria-Timbó 178 cm ▲ · Tijuca 94 cm ▲',
      spark:poly([0,0,1,2,6,14,22,31,38,45,42,40], 220, 34, 50),
      echo1:'rgba(205,64,72,.55)', echo2:'rgba(29,124,171,.6)'
    } : {
      sev:SEV[1], bd:'var(--bd)', hero:'0,0', hc:'var(--tx)', count: zn ? '9 ESTAÇÕES' : '33 ESTAÇÕES',
      sub: zn ? 'na última hora · 9 estações da Zona Norte' : 'na última hora · todas as 33 estações reportando',
      rios: zn ? 'Rios: Acari 48 cm — estável · Faria-Timbó ok' : 'Rios: Tijuca 65 cm — estável · Acari, Maracanã, Faria-Timbó ok',
      spark:poly([0,0,0,0,0,0,0,0,0,0,0,0], 220, 34, 10),
      echo1:'rgba(63,169,107,.22)', echo2:'rgba(63,169,107,.16)'
    };

    const mob = crisis ? {
      sev:SEV[3], bd:'var(--s3-bd)', hero:'3.108', count:'96 LINHAS',
      sub:'2.702 ônibus + 406 BRT · 71% das linhas planejadas ativas',
      warn:'14 linhas sem circular há 40+ min — concentradas em Jacarepaguá e Bangu',
      warnBg:'var(--s3-bg)', warnBd:'var(--s3-bd)', warnC:'var(--s3-tx)',
      m1:'var(--s1)', m2:'var(--s2)', m4:'var(--s1)', metro:'METRÔ: L2 COM LENTIDÃO'
    } : {
      sev:SEV[1], bd:'var(--bd)', hero: zn ? '1.184' : '4.212', count: zn ? '82 LINHAS' : '312 LINHAS',
      sub: zn ? '1.021 ônibus + 163 BRT · 97% das linhas da zona ativas' : '3.642 ônibus + 558 BRT · 96% das linhas planejadas ativas',
      warn: zn ? '1 linha sem circular há 40+ min: 232' : '3 linhas sem circular há 40+ min: 232, SV790, 863',
      warnBg:'var(--s2-bg)', warnBd:'var(--warn-bd)', warnC:'var(--warn-tx)',
      m1:'var(--s1)', m2:'var(--s1)', m4:'var(--s1)', metro:'METRÔ NORMAL'
    };

    const transito = {
      sev: crisis ? SEV[3] : SEV[1], count: crisis ? '9 CORR' : '12 CORR',
      hero: crisis ? '19' : (zn ? '28' : '31'),
      sub: crisis ? 'fluxo livre 42 km/h · 4 corredores interditados' : 'fluxo livre 42 km/h · derivado da nossa frota + TomTom',
      rows: crisis ? [
        {n:'Linha Amarela', v:'8', d:'▼', dc:'var(--s4)'},
        {n:'Av. Brasil', v:'11', d:'▼', dc:'var(--s4)'},
        {n:'Av. das Américas', v:'14', d:'▼', dc:'var(--s4)'},
        {n:'Aterro', v:'38', d:'▬', dc:'var(--tx2)'}
      ] : [
        {n:'Av. Brasil', v:'18', d:'▼', dc:'var(--s3)'},
        {n:'Linha Amarela', v:'24', d:'▬', dc:'var(--tx2)'},
        {n:'Av. das Américas', v:'27', d:'▬', dc:'var(--tx2)'},
        {n:'Aterro', v:'51', d:'▲', dc:'var(--s1)'}
      ]
    };

    const hours = [];
    for (let i=0;i<12;i++){
      const t = (14+i)%24;
      const temp = crisis ? 22 + Math.round(rnd(i+7)*3) : 31 - Math.round(Math.abs(i-1)*0.9);
      const rain = crisis ? 40 + Math.round(rnd(i+3)*45) : Math.round(rnd(i)*8);
      hours.push({ t:String(t).padStart(2,'0'), h:temp + '°', bar: Math.round((temp-14)*2.2), rain: Math.max(2, Math.round(rain*0.28)) });
    }
    const previsao = {
      sev: crisis ? SEV[3] : SEV[1],
      hero: crisis ? '23 °C' : '31 °C',
      heroSub: crisis ? 'chuva forte até 18h' : 'sem chuva à vista',
      hours
    };

    const seguranca = {
      sev: crisis ? SEV[2] : SEV[2], count: crisis ? '24H' : '24H',
      hero: zn ? '2' : '3',
      sub: zn ? 'todas na Zona Norte · nenhuma nas últimas 6 h' : 'Zona Norte 2 · Zona Oeste 1 · nenhuma nas últimas 6 h'
    };

    const ar = crisis ? {
      sev:SEV[1], hero:'Boa', hc:'var(--s1)', heroSub:'PM2.5 máx 9,4 µg/m³ (chuva lavou o ar)', count:'28 EST',
      rows:[{n:'Bangu',v:'9,4',p:24,c:'var(--s1)'},{n:'Irajá',v:'8,1',p:20,c:'var(--s1)'},{n:'Centro',v:'7,7',p:19,c:'var(--s1)'}]
    } : {
      sev:SEV[1], hero:'Boa', hc:'var(--s1)', heroSub: zn ? 'PM2.5 máx 14,1 µg/m³ (Irajá)' : 'PM2.5 máx 16,7 µg/m³ (Campinho)', count: zn ? '9 EST' : '28 EST',
      rows: zn
        ? [{n:'Irajá',v:'14,1',p:42,c:'#c08428'},{n:'Pilares',v:'12,8',p:38,c:'#149cc6'},{n:'Bonsucesso',v:'11,3',p:34,c:'#149cc6'}]
        : [{n:'Campinho',v:'16,7',p:48,c:'#c08428'},{n:'Irajá',v:'13,3',p:39,c:'#149cc6'},{n:'Bangu',v:'12,1',p:35,c:'#149cc6'}]
    };

    const ceu = crisis
      ? { sev:SEV[2], hero:'6', count:'SDU ✕', sdu:'0 (fechado)', sduC:'var(--s4)', gig:'9' }
      : { sev:SEV[1], hero:'14', count:'2 AEROP', sdu:'12', sduC:'var(--tx)', gig:'21' };
    const mar = crisis
      ? { sev:SEV[3], hero:'2,8', hc:'var(--s3)', heroSub:'m · período 11 s · mar agitado', proprias:'6', improprias:'11', list:'Impróprias após a chuva: toda a orla da Zona Sul e Ramos' }
      : { sev:SEV[1], hero:'1,4', hc:'var(--tx)', heroSub:'m · período 9 s · mar calmo', proprias:'14', improprias:'3', list:'Impróprias: Botafogo, Flamengo, Ramos' };

    const memoria = crisis ? {
      quote1:'Choveu em 3 horas', quoteHi:'mais que a média do mês inteiro',
      quote2:'de agosto em Jacarepaguá.',
      sub:'112 mm desde as 11h30 · média histórica de agosto: 36 mm (1997–2025)',
      bars:[{h:44,c:'#1d7cab'},{h:70,c:'#1d7cab'},{h:32,c:'#1d7cab'},{h:56,c:'#1d7cab'},{h:88,c:'#1d7cab'},{h:24,c:'#1d7cab'},{h:60,c:'#1d7cab'},{h:38,c:'#1d7cab'},{h:52,c:'#1d7cab'},{h:100,c:'var(--live-tx)'}]
    } : {
      quote1:'Agosto até agora:', quoteHi:'12 mm de chuva',
      quote2:'— 34% da média histórica do mês.',
      sub: zn ? 'Zona Norte: 9 mm · 4º agosto mais seco desde 1997' : 'Terceiro agosto mais seco desde o início da série, em 1997.',
      bars:[{h:64,c:'#1d7cab'},{h:88,c:'#1d7cab'},{h:52,c:'#1d7cab'},{h:76,c:'#1d7cab'},{h:44,c:'#1d7cab'},{h:92,c:'#1d7cab'},{h:58,c:'#1d7cab'},{h:70,c:'#1d7cab'},{h:40,c:'#1d7cab'},{h:18,c:'var(--live-tx)'}]
    };

    // ---------- layout (ordem por severidade) ----------
    const lay = crisis ? {
      chuva:{s:2,o:1}, mob:{s:2,o:2}, transito:{s:1,o:3},
      previsao:{s:1,o:4}, seguranca:{s:1,o:5}, ar:{s:1,o:6}, mar:{s:1,o:7}, ceu:{s:1,o:8},
      memoria:{s:2,o:9}, queimadas:{s:1,o:10}, cidade:{s:1,o:11}, navios:{s:1,o:12}
    } : {
      chuva:{s:2,o:1}, mob:{s:2,o:2}, transito:{s:1,o:3}, previsao:{s:1,o:4},
      seguranca:{s:1,o:5}, ar:{s:1,o:6}, mar:{s:1,o:7}, ceu:{s:1,o:8},
      memoria:{s:2,o:9}, queimadas:{s:1,o:10}, cidade:{s:1,o:11}, navios:{s:1,o:12}
    };

    // ---------- ticker ----------
    const tick = crisis ? [
      {k:'JACAREPAGUÁ',v:'45,2mm/h',d:'▲',dc:'var(--s4)'},{k:'ACARI',v:'210cm',d:'▲',dc:'var(--s4)'},
      {k:'ESTÁGIO',v:'4 ALERTA',d:'▲',dc:'var(--s4)'},{k:'FROTA',v:'3.108',d:'▼',dc:'var(--s3)'},
      {k:'LINHAS PARADAS',v:'14',d:'▲',dc:'var(--s3)'},{k:'PM2.5 IRAJÁ',v:'8,1',d:'▼',dc:'var(--s1)'},
      {k:'ONDAS',v:'2,8m',d:'▲',dc:'var(--s3)'},{k:'SDU',v:'0 POUSOS/H',d:'▼',dc:'var(--s4)'},
      {k:'METRÔ L2',v:'LENTIDÃO',d:'▬',dc:'var(--s2)'},{k:'VELOCIDADE',v:'19km/h',d:'▼',dc:'var(--s4)'}
    ] : [
      {k:'COPACABANA',v:'0,0mm',d:'▬',dc:'var(--tx2)'},{k:'PM2.5 IRAJÁ',v:'13,3',d:'▬',dc:'var(--tx2)'},
      {k:'RIO TIJUCA',v:'65cm',d:'▬',dc:'var(--tx2)'},{k:'VEÍCULOS',v:'4.212',d:'▲',dc:'var(--s1)'},
      {k:'ONDAS',v:'1,4m',d:'▬',dc:'var(--tx2)'},{k:'METRÔ L1',v:'NORMAL',d:'▬',dc:'var(--tx2)'},
      {k:'SDU',v:'12 POUSOS/H',d:'▲',dc:'var(--s1)'},{k:'ESTÁGIO',v:'1',d:'▬',dc:'var(--s1)'},
      {k:'PM10 BANGU',v:'27,8',d:'▲',dc:'var(--s2)'},{k:'TEMP CENTRO',v:'31,2°C',d:'▲',dc:'var(--tx2)'},
      {k:'FOCOS INPE',v:'0',d:'▬',dc:'var(--tx2)'},{k:'PRAIAS PRÓPRIAS',v:'14/17',d:'▬',dc:'var(--tx2)'}
    ];

    // ---------- feed ----------
    let feed = crisis ? [
      {h:'14:31',sev:SEV[4],txt:'COR elevou a cidade para Estágio 4 — Alerta',src:'COR'},
      {h:'14:26',sev:SEV[4],txt:'Acari transbordou em Pavuna — via interditada',src:'INEA'},
      {h:'14:19',sev:SEV[3],txt:'14 linhas de ônibus sem circular há 40+ min',src:'SMTR'},
      {h:'14:08',sev:SEV[3],txt:'45,2 mm/h em Jacarepaguá — recorde do mês',src:'Alerta Rio'},
      {h:'13:55',sev:SEV[3],txt:'Linha Amarela a 8 km/h no sentido Fundão',src:'TomTom'},
      {h:'13:40',sev:SEV[2],txt:'SDU suspendeu pousos por teto baixo',src:'adsb.lol'},
      {h:'13:22',sev:SEV[2],txt:'COR: 9 bolsões d’água na Zona Oeste',src:'COR'},
      {h:'12:58',sev:SEV[1],txt:'PM2.5 caiu para 8,1 em Irajá com a chuva',src:'OpenAQ'}
    ] : [
      {h:'14:28',sev:SEV[1],txt:'Linha 232 voltou a circular',src:'SMTR'},
      {h:'14:11',sev:SEV[2],txt:'PM10 subiu para moderado em Bangu',src:'OpenAQ'},
      {h:'13:47',sev:SEV[2],txt:'COR: bolsão d’água em Jacarepaguá — resolvido 14:20',src:'COR'},
      {h:'13:12',sev:SEV[1],txt:'BRT Transoeste normalizou intervalo (7 min)',src:'SMTR'},
      {h:'12:40',sev:SEV[1],txt:'2 focos de calor na Região Metropolitana (fora do município)',src:'INPE'},
      {h:'12:03',sev:SEV[2],txt:'Linha SV790 sem GPS há 41 min',src:'SMTR'},
      {h:'11:35',sev:SEV[1],txt:'Maré alta em Copacabana sem ressaca',src:'Marine'},
      {h:'10:58',sev:SEV[2],txt:'Navios (AIS): fonte marcada como degradada',src:'Status'},
      {h:'10:22',sev:SEV[1],txt:'Rio Tijuca estável em 65 cm há 6 h',src:'ANA'},
      {h:'09:47',sev:SEV[1],txt:'28 de 28 estações de ar reportando',src:'OpenAQ'},
      {h:'09:10',sev:SEV[1],txt:'COR manteve Estágio 1 após a passagem da frente',src:'COR'}
    ];
    if (zn) feed = feed.filter((f,i) => i % 3 !== 2);
    const feedAll = feed;
    if (s.onlyAbn) feed = feed.filter(f => f.sev.n >= 2);

    // ---------- pontos ----------
    const fleetDots = []; for (let i=0;i<46;i++) fleetDots.push({ x:(rnd(i)*88+4).toFixed(0), y:(rnd(i+40)*84+8).toFixed(0), c: rnd(i+9) > .88 ? 'var(--s3)' : '#149cc6' });
    const hexes = []; for (let i=0;i<11;i++) hexes.push({ x:(rnd(i+3)*76+6).toFixed(0), y:(rnd(i+21)*70+10).toFixed(0), c: i < 2 ? 'rgba(205,64,72,.55)' : 'rgba(90,102,118,.28)' });
    const mapFleet = []; for (let i=0;i<180;i++) mapFleet.push({ x:(rnd(i+2)*94+3).toFixed(1), y:(rnd(i+300)*88+6).toFixed(1) });
    const mapIncidents = []; for (let i=0;i<7;i++) mapIncidents.push({ x:(rnd(i+55)*70+12).toFixed(0), y:(rnd(i+77)*64+14).toFixed(0), c: i<3 ? 'var(--s4)' : 'var(--s4-dim)' });

    // ---------- mapa ----------
    const presets = [
      {key:'chuva', label:'Chuva agora', n:'3 CAMADAS', icon:'●', dot:'#149cc6'},
      {key:'transporte', label:'Transporte', n:'3 CAMADAS', icon:'●', dot:'#149cc6'},
      {key:'segxtrans', label:'Segurança × transporte', n:'2 CAMADAS', icon:'◆', dot:'var(--live-tx)'},
      {key:'bairro', label:'Meu bairro', n:'TUDO ANORMAL', icon:'▲', dot:'var(--s3)'},
      {key:'custom', label:'Personalizar', n:'', icon:'⚙', dot:'var(--tx3)'}
    ];
    const active = s.preset || 'segxtrans';
    const mapPresets = presets.map(p => ({
      label:p.label, n:p.n, icon:p.icon, dot:p.dot,
      bd: p.key===active ? 'var(--brand2)' : 'var(--bd)',
      bg: p.key===active ? 'var(--brand)' : 'var(--card)',
      c: p.key===active ? 'var(--on-brand)' : 'var(--tx2)',
      pick: () => defina({ preset:p.key })
    }));
    const layerDefs = [
      ['Ocorrências de tiro (24 h)', 'FOGO CRUZADO · HÁ 12 MIN', true],
      ['Frota em circulação', 'SMTR · AO VIVO', true],
      ['Linhas sem circular', 'DETECTOR PLANEJADO×REALIZADO · 1 MIN', true],
      ['Bairros', 'IPP · ESTÁTICO', true],
      ['Radar de chuva', 'ALERTA RIO · HÁ 4 MIN', false],
      ['Chuva por estação (33)', 'ALERTA RIO · HÁ 4 MIN', false],
      ['Nível de rios', 'ANA · HÁ 9 MIN', false],
      ['Qualidade do ar (28)', 'OPENAQ · HÁ 20 MIN', false],
      ['Focos de calor', 'INPE · HÁ 8 MIN', false],
      ['Aeronaves', 'ADSB.LOL · AO VIVO', false],
      ['Navios (AIS)', 'DEGRADADA · HÁ 19 H', false]
    ];
    const layers = layerDefs.map((l,i) => ({
      n:l[0], src:l[1], mark: l[2] ? '✓' : '',
      bd: l[2] ? 'var(--live-tx)' : 'var(--tx4)', bg: l[2] ? 'var(--live-tx)' : 'transparent',
      tc: l[2] ? 'var(--tx)' : 'var(--tx2)',
      sc: l[1].indexOf('DEGRADADA') === 0 ? 'var(--s2)' : 'var(--tx3)',
      toggle: () => {}
    }));
    const frames = []; for (let i=0;i<24;i++) frames.push({ h: 6 + Math.round(rnd(i+11)*12), c: i > 19 ? 'var(--live-tx)' : 'var(--bd4)' });

    // ---------- status ----------
    const srcDefs = [
      ['Chuva — 33 pluviômetros','Alerta Rio / COR','online','há 4 min','99,8%'],
      ['Radar meteorológico','Alerta Rio','online','há 4 min','99,1%'],
      ['Estágio operacional','COR','online','há 3 min','100%'],
      ['GPS da frota (ônibus + BRT)','SMTR','online','há 1 min','98,7%'],
      ['Tabela de horários (GTFS)','SMTR','online','há 6 h','100%'],
      ['Nível de rios','ANA / INEA','online','há 9 min','97,4%'],
      ['Qualidade do ar — 28 estações','OpenAQ','online','há 20 min','96,9%'],
      ['Focos de calor','INPE','online','há 8 min','99,9%'],
      ['Previsão do tempo e do mar','Open-Meteo','online','há 31 min','100%'],
      ['Balneabilidade','INEA','online','boletim 04/08','94,2%'],
      ['Aeronaves','adsb.lol','online','ao vivo','99,5%'],
      ['Navios (AIS)','aisstream.io','degradada','há 19 h','71,3%']
    ];
    const sources = srcDefs.map((d,i) => {
      const deg = d[2] === 'degradada';
      const bars = [];
      for (let j=0;j<30;j++) {
        const bad = deg ? (j > 26 ? 1 : (rnd(i*30+j) > .96 ? 1 : 0)) : (rnd(i*30+j) > .985 ? 1 : 0);
        bars.push(bad ? (deg && j > 26 ? 'var(--s2)' : 'var(--s3)') : 'var(--up-ok)');
      }
      return { n:d[0], org:d[1], state: deg ? 'Degradada' : 'Online', i: deg ? '◆' : '●',
        c: deg ? 'var(--s2)' : 'var(--s1)', age:d[3], agec: deg ? 'var(--s2)' : 'var(--tx2)', up:d[4], bars };
    });

    // ---------- dossiê ----------
    let dossier = null;
    if (s.route !== 'home' && s.route !== 'mapa' && s.route !== 'status') {
      const rainSeries = crisis
        ? [0,0,1,1,2,3,2,4,6,9,14,22,31,38,45,42,38,30,22,16,11,7,4,2]
        : [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
      const histSeries = [2,2,3,3,4,4,5,5,6,7,7,8,8,9,9,8,7,6,5,4,4,3,3,2];
      const stations = ['Jacarepaguá','Bangu','Copacabana','Tijuca','Irajá','Santa Teresa','Grajaú','Ilha do Governador','Madureira','Guaratiba','Campo Grande','Barra/Riocentro','São Cristóvão','Anchieta','Grande Méier','Recreio','Laranjeiras','Saúde','Alto da Boa Vista','Vidigal','Rocinha','Piedade','Sepetiba','Cidade de Deus','Penha','Urca','Sumaré','Grota Funda','Realengo','Grumari','Pavuna','Riocentro','Barrinha'];
      const rows = stations.map((n,i) => {
        const v = crisis ? (45 - i*1.2 + rnd(i)*3) : 0;
        const acc = crisis ? v*2.4 + rnd(i+5)*8 : rnd(i+5)*1.4;
        return { a:n, b:(v).toFixed(1).replace('.',','), c:(acc).toFixed(1).replace('.',','),
          d: crisis ? (12 + Math.round(rnd(i+2)*40)) + ' min' : '—',
          e: crisis && i < 12 ? 'acima P95' : 'normal',
          ec: crisis && i < 12 ? 'var(--s4)' : 'var(--tx2)' };
      });
      const mapDots = stations.slice(0,22).map((n,i) => ({ x:(rnd(i+13)*86+6).toFixed(0), y:(rnd(i+61)*78+10).toFixed(0),
        c: crisis ? (i<8 ? 'var(--s4)' : (i<14 ? 'var(--s3)' : '#1d7cab')) : '#2c96c4' }));
      dossier = {
        sev: chuva.sev, title:'Chuva e água', route:'/chuva?' + ['periodo=' + s.period].concat(zone ? ['zona=' + zone] : []).join('&'),
        kpis: crisis ? [
          {l:'Acumulado 24 h (máx.)', v:'112', u:'mm · Jacarepaguá', c:'var(--s4)', d:'311% da média diária de agosto'},
          {l:'Intensidade agora (máx.)', v:'45,2', u:'mm/h', c:'var(--s4)', d:'12 estações acima de 20 mm/h'},
          {l:'Estações acima do P95', v:'12', u:'de 33', c:'var(--s3)', d:'percentil 95 de agosto = 8,4 mm/h'},
          {l:'Rios em atenção', v:'3', u:'de 8 monitorados', c:'var(--s3)', d:'Acari transbordou às 14:26'}
        ] : [
          {l:'Chuva na última hora', v:'0,0', u:'mm (média das 33)', c:'var(--tx)', d:'nenhuma estação com registro'},
          {l:'Acumulado em agosto', v:'12', u:'mm', c:'var(--tx)', d:'34% da média histórica do mês'},
          {l:'Dias sem chuva', v:'11', u:'consecutivos', c:'var(--tx)', d:'maior sequência do ano até aqui'},
          {l:'Rios monitorados', v:'8', u:'todos estáveis', c:'var(--s1)', d:'Tijuca 65 cm · variação < 3 cm em 6 h'}
        ],
        chartTitle:'Chuva por hora · últimas 24 h', s1:'chuva observada (mm)', s2:'média histórica de agosto',
        series1: poly(rainSeries, 1000, 205, crisis ? 50 : 10),
        series2: poly(histSeries, 1000, 205, crisis ? 50 : 10),
        annX: crisis ? 560 : -10, annW: crisis ? 200 : 0,
        annLeft: crisis ? 57 : -20, annLabel: crisis ? 'CIDADE EM ESTÁGIO 3 · 13:40' : '',
        tipTime: crisis ? '13:00 · JACAREPAGUÁ' : '09:00 · MÉDIA DAS 33',
        tip1: crisis ? '38,0 mm' : '0,0 mm', tip2: crisis ? 'média 5,0 mm' : 'média 3,0 mm',
        axis:['14:00','17:00','20:00','23:00','02:00','05:00','08:00','11:00'],
        tableTitle:'33 estações pluviométricas', sortBy:'INTENSIDADE',
        cols:['Estação','mm/h','24 h','Duração','Contexto'], rows,
        mapTitle:'Estações e radar', mapDots,
        context: crisis
          ? 'Em 3 horas choveu mais do que a média de todo o mês de agosto em Jacarepaguá — 112 mm contra 36 mm.'
          : 'Agosto vai a 12 mm: percentil 5 da série 1997–2025. O agosto mais seco registrado teve 4 mm, em 2010.',
        seal:'ALERTA RIO · SÉRIE 1997–2025 · HÁ 4 MIN'
      };
    }

    const periods = ['24h','7d','30d'].map(p => ({
      label:p, bd: s.period===p ? 'var(--brand2)' : 'var(--bd)', bg: s.period===p ? 'var(--brand)' : 'var(--card)',
      c: s.period===p ? 'var(--on-brand)' : 'var(--tx2)', pick: () => defina({ period:p })
    }));

    const zoneNames = { norte:'Zona Norte', sul:'Zona Sul', oeste:'Zona Oeste', centro:'Centro' };
    const zones = [
      {k:null,label:'Cidade inteira',meta:'33 EST · 4.212 VEÍC'},
      {k:'norte',label:'Zona Norte',meta:'9 EST · 1.184 VEÍC'},
      {k:'sul',label:'Zona Sul',meta:'6 EST · 806 VEÍC'},
      {k:'oeste',label:'Zona Oeste',meta:'11 EST · 1.402 VEÍC'},
      {k:'centro',label:'Centro',meta:'4 EST · 620 VEÍC'},
      {k:'norte',label:'Tijuca',meta:'BAIRRO · 2 EST'},
      {k:'oeste',label:'Jacarepaguá',meta:'BAIRRO · 3 EST'}
    ].map(z => ({ label:z.label, meta:z.meta, pick: () => defina({ zone:z.k, zonePicker:false }) }));

    const nav = (r) => ({ c: s.route === r ? 'var(--on-brand)' : 'var(--tx2)', b: s.route === r ? 'var(--brand)' : 'transparent' });

    const mobileList = [
      {t:'Chuva e água', sev:chuva.sev, v:chuva.hero, u:'mm/h · última hora', sub:chuva.sub, hc:chuva.hc, seal:'ALERTA RIO · HÁ 4 MIN', dot:'var(--s1)'},
      {t:'Mobilidade', sev:mob.sev, v:mob.hero, u:'veículos', sub:mob.sub, hc:'var(--tx)', seal:'SMTR · AO VIVO', dot:'var(--live-tx)'},
      {t:'Segurança', sev:seguranca.sev, v:seguranca.hero, u:'tiros · 24 h', sub:seguranca.sub, hc:'var(--tx)', seal:'FOGO CRUZADO · HÁ 12 MIN', dot:'var(--s1)'},
      {t:'Trânsito', sev:transito.sev, v:transito.hero, u:'km/h médios', sub:transito.sub, hc:'var(--tx)', seal:'SMTR/TOMTOM · HÁ 5 MIN', dot:'var(--s1)'},
      {t:'Previsão', sev:previsao.sev, v:previsao.hero, u:previsao.heroSub, sub:'umidade 58% · vento 18 km/h SE', hc:'var(--tx)', seal:'OPEN-METEO · 14H', dot:'var(--s1)'},
      {t:'Qualidade do ar', sev:ar.sev, v:ar.hero, u:ar.heroSub, sub:'28 estações reportando', hc:'var(--s1)', seal:'OPENAQ · HÁ 20 MIN', dot:'var(--s1)'},
      {t:'Navios (AIS)', sev:SEV[2], v:'38', u:'embarcações · leitura de há 19 h', sub:'Fonte degradada desde 05/08 — exibindo a última leitura válida.', hc:'var(--tx2)', seal:'AISSTREAM · DEGRADADA', dot:'var(--s2)'}
    ];

    const open = (r) => () => defina({ route:r, dossier:r });

    // cockpit com largura de projeto fixa: abaixo de 1440 px escala pra caber, nunca compacta as células
    const DESIGN_W = 1440;
    const vw = s.vw || 1440, vh = s.vh || 900;
    const k = vw >= DESIGN_W ? 1 : vw / DESIGN_W;
    const stage = { w: Math.round(vw / k), h: Math.round(vh / k), t: k === 1 ? 'none' : 'scale(' + k.toFixed(4) + ')' };

    const pk = Math.min(1, (vh - 32) / 844);
    const phone = { t: pk >= 1 ? 'none' : 'scale(' + pk.toFixed(4) + ')' };

    return {
      stage, phone,
      themeIcon: s.theme === 'claro' ? '☀' : '☾',
      themeLabel: s.theme === 'claro' ? 'CLARO' : 'ESCURO',
      toggleTheme: () => acoes.aplicarTema(s.theme === 'claro' ? 'escuro' : 'claro'),
      showMobileBadge: s.device === 'desktop' && !dossier,
      isDesktop: s.device === 'desktop', isMobile: s.device === 'mobile',
      toggleDevice: () => defina({ device: s.device === 'desktop' ? 'mobile' : 'desktop' }),
      sev:citySev, headline,
      headlineShort: crisis ? 'Chuva forte na Zona Oeste · 14 linhas paradas.' : 'A cidade opera normalmente. Sem chuva nas últimas 24 h.',
      zoneLabel: zone ? zoneNames[zone] : 'Cidade inteira',
      zoneChip: zone ? zoneNames[zone] : null,
      clearZone: (e) => { e.stopPropagation(); defina({ zone:null }); },
      zonePickerOpen: s.zonePicker, zones,
      toggleZonePicker: () => defina({ zonePicker: !s.zonePicker }),
      modeLabel: crisis ? 'DIA DE CRISE' : 'DIA CALMO',
      toggleMode: () => defina({ mode: crisis ? 'calmo' : 'crise' }),
      copyLabel: s.copied ? 'link copiado' : 'copiar link deste recorte',
      copyLink: () => acoes.piscar('copied'),
      quoteLabel: s.quoted ? 'dado copiado' : 'copiar dado citável',
      copyQuote: () => acoes.piscar('quoted'),
      navA:nav('home'), navM:nav('mapa'), navS:nav('status'),
      goHome: () => defina({ route:'home', dossier:null }),
      goMapa: () => defina({ route:'mapa', dossier:null }),
      goStatus: () => defina({ route:'status', dossier:null }),
      isHome: s.route === 'home', isMapa: s.route === 'mapa', isStatus: s.route === 'status',
      tickerLoop: tick.concat(tick), tickerState: s.paused ? 'paused' : 'running',
      pauseTicker: () => defina({ paused:true }), resumeTicker: () => defina({ paused:false }),
      chuva, mob, transito, previsao, seguranca, ar, ceu, mar, memoria, lay, ramp:RAMP,
      cidadeVivaItens: [
        { quando:'SÁB 19:30', cor:'var(--live-tx)', titulo:'Flamengo × Vitória, Maracanã', sub:'esquema especial de trânsito' },
        { quando:'QUI 22H', cor:'var(--s2)', titulo:'Águas do Rio: manutenção programada em Irajá', sub:'até 5h' },
        { quando:'DOM 07:00', cor:null, titulo:'Aterro do Flamengo fechado para lazer', sub:null },
      ],
      fleetDots, hexes, mapFleet, mapIncidents, mapPresets, layers, frames, sources, presetAtivo: active,
      feed, feedCount: feedAll.length + ' EVENTOS · 24H',
      abn: { track: s.onlyAbn ? 'var(--brand)' : 'var(--bd4)', x: s.onlyAbn ? 14 : 2, c: s.onlyAbn ? 'var(--live-tx)' : 'var(--tx2)' },
      toggleAbnormal: () => defina({ onlyAbn: !s.onlyAbn }),
      openChuva: open('chuva'), openMob: open('mobilidade'), openTransito: open('transito'),
      openPrevisao: open('previsao'), openSeguranca: open('seguranca'), openAr: open('ar'),
      openMar: open('mar'), openCeu: open('ceu'), openQueimadas: open('queimadas'),
      openCidade: open('cidade'), openNavios: open('navios'),
      dossier, closeDossier: () => defina({ route:'home', dossier:null }),
      periods, gridY:[24,66,108,150,192],
      mobileCards: s.mtab === 'cards', mobileFeed: s.mtab === 'feed', mobileList,
      mTabCards: () => defina({ mtab:'cards' }), mTabFeed: () => defina({ mtab:'feed' }),
      mt: { a: { c: s.mtab==='cards' ? 'var(--live-tx)' : 'var(--tx2)', b: s.mtab==='cards' ? 'var(--live-tx)' : 'transparent' },
            f: { c: s.mtab==='feed' ? 'var(--live-tx)' : 'var(--tx2)', b: s.mtab==='feed' ? 'var(--live-tx)' : 'transparent' } }
    };
}
