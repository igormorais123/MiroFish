from pathlib import Path
import shutil


engine_path = Path(r"C:\Users\IgorPC\projetos\projetos-claude\lenia-eleitoral\public\lenia-eleitoral\js\network-engine.js")
backup_path = engine_path.with_name("network-engine.mirofish-v5-backup.js")

if not backup_path.exists():
    shutil.copy2(engine_path, backup_path)


engine_content = """/**
 * network-engine.js - Motor de dinamica eleitoral baseado em rede territorial.
 * Esta versao aceita contexto regional e modula eventos por sensibilidade local.
 */

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function percentile(sortedValues, q) {
  if (!sortedValues.length) return 0;
  const idx = clamp(Math.floor((sortedValues.length - 1) * q), 0, sortedValues.length - 1);
  return sortedValues[idx];
}

function normalizeName(value) {
  return String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\\u0300-\\u036f]/g, '')
    .replace(/[^a-z0-9]/g, '');
}

class RANode {
  constructor(profile) {
    this.nome = profile.ra_nome;
    this.sigla = profile.sigla;
    this.codigo = profile.ra_codigo;
    this.populacao = profile.populacao;
    this.eleitorado = profile.eleitorado_estimado;
    this.renda = profile.renda_media_sm;
    this.latitude = profile.latitude;
    this.longitude = profile.longitude;

    this.orientacao = profile.orientacao_media;
    this.engajamento = profile.engajamento_medio;
    this.tolerancia = profile.tolerancia_media;

    this.baseOrient = profile.orientacao_media;
    this.baseEngaj = profile.engajamento_medio;
    this.baseToler = profile.tolerancia_media;

    this.attrOrient = profile.orientacao_media;
    this.attrEngaj = profile.engajamento_medio;
    this.attrToler = profile.tolerancia_media;

    const rendaBase = 0.20 + Math.min(profile.renda_media_sm / 18, 0.35);
    const digitalBase = (profile.alcance_digital || 0.5) * 0.10;
    const tolerBase = (profile.tolerancia_media || 0.5) * 0.08;
    const fragility = (profile.susceptibilidade_desinformacao || 0.45) * 0.15;
    this.baseInercia = clamp(rendaBase + digitalBase + tolerBase - fragility, 0.18, 0.78);
    this.inercia = this.baseInercia;
    this.volatilidade = 1.0 - this.inercia;

    this.vizinhos = [];

    this.prevOrient = this.orientacao;
    this.prevEngaj = this.engajamento;
    this.prevToler = this.tolerancia;

    this.history = { orient: [], engaj: [], toler: [] };
    this.maxHistory = 200;

    this.residualOrient = 0;
    this.residualEngaj = 0;
    this.residualToler = 0;

    this.issueProfile = {
      desinfo: 0.35,
      saude: 0.30,
      educacao: 0.25,
      seguranca: 0.25,
      imigracao: 0.20,
      garimpo: 0.20,
      demarcacao: 0.20,
      social: 0.25,
      direita: clamp((this.baseOrient - 0.5) * 1.7 + 0.5, 0, 1),
      esquerda: clamp((0.5 - this.baseOrient) * 1.7 + 0.5, 0, 1),
      territorial: 0.25,
      concern: 'geral',
      sample: 0,
    };
  }

  pushHistory() {
    this.history.orient.push(this.orientacao);
    this.history.engaj.push(this.engajamento);
    this.history.toler.push(this.tolerancia);
    if (this.history.orient.length > this.maxHistory) {
      this.history.orient.shift();
      this.history.engaj.shift();
      this.history.toler.shift();
    }
  }

  applyRegionalProfile(agg, mirofishSignals = {}) {
    if (!agg) return;
    const desinfo = clamp((agg.desinformacao_media || 0) / 5, 0, 1);
    const saude = clamp(1 - ((agg.avaliacao_saude_media || 0) / 5), 0, 1);
    const educacao = clamp(1 - ((agg.avaliacao_educacao_media || 0) / 5), 0, 1);
    const seguranca = clamp(1 - ((agg.avaliacao_seguranca_media || 0) / 5), 0, 1);
    const imigracao = clamp(agg.imigracao_negativa_share || 0, 0, 1);
    const garimpo = clamp(agg.garimpo_favor_share || 0, 0, 1);
    const demarcacao = clamp(agg.demarcacao_favor_share || 0, 0, 1);
    const social = clamp(agg.recebe_programa_social_share || 0, 0, 1);
    const direita = clamp(agg.bolsonaro_apoio_share || 0, 0, 1);
    const esquerda = clamp(1 - direita, 0, 1);
    const narrative = clamp((mirofishSignals.narrative_pressure || 0) / 100, 0, 1);
    const mobilization = clamp((mirofishSignals.mobilization_score || 0) / 100, 0, 1);
    const territorial = clamp(
      0.18 + desinfo * 0.24 + saude * 0.18 + seguranca * 0.12 + imigracao * 0.14 + social * 0.10,
      0.15,
      0.95,
    );

    this.issueProfile = {
      desinfo,
      saude,
      educacao,
      seguranca,
      imigracao,
      garimpo,
      demarcacao,
      social,
      direita,
      esquerda,
      territorial: clamp(territorial + narrative * 0.10 + mobilization * 0.08, 0.15, 1),
      concern: agg.top_preocupacoes?.[0]?.tema || 'geral',
      sample: agg.amostra_n || 0,
    };

    this.attrOrient = clamp(
      this.baseOrient + (direita - 0.5) * 0.14 - (social - 0.45) * 0.05 + (imigracao - 0.3) * 0.04,
      0.05,
      0.95,
    );
    this.attrEngaj = clamp(
      this.baseEngaj + desinfo * 0.05 + saude * 0.04 + seguranca * 0.03 + mobilization * 0.05,
      0.05,
      0.95,
    );
    this.attrToler = clamp(
      this.baseToler - desinfo * 0.06 - imigracao * 0.04 - seguranca * 0.03 + social * 0.03,
      0.05,
      0.95,
    );
    this.inercia = clamp(this.baseInercia - desinfo * 0.06 - saude * 0.02 + Math.abs(direita - 0.5) * 0.03, 0.14, 0.82);
    this.volatilidade = 1.0 - this.inercia;

    this.orientacao = clamp(this.attrOrient, 0.01, 0.99);
    this.engajamento = clamp(this.attrEngaj, 0.01, 0.99);
    this.tolerancia = clamp(this.attrToler, 0.01, 0.99);
    this.prevOrient = this.orientacao;
    this.prevEngaj = this.engajamento;
    this.prevToler = this.tolerancia;
  }
}

class NetworkElectoralEngine {
  constructor() {
    this.nodes = [];
    this.nodeByName = {};
    this.nodeBySigla = {};
    this.step = 0;
    this.dt = 0.02;
    this.params = {
      diffusion: 0.15,
      reversion: 0.008,
      noise: 0.003,
      crossChannel: 0.04,
      eventResidual: 0.30,
    };
    this.calibration = null;
    this._rngState = 42;
    this.mirofishSignals = {};
  }

  _rng() {
    this._rngState = (this._rngState * 1664525 + 1013904223) & 0x7fffffff;
    return this._rngState / 0x7fffffff;
  }

  _rngNorm() {
    const u1 = Math.max(1e-10, this._rng());
    const u2 = this._rng();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  }

  _distance(a, b) {
    const dlat = a.latitude - b.latitude;
    const dlon = a.longitude - b.longitude;
    return Math.sqrt(dlat * dlat + dlon * dlon);
  }

  _calibrate(raProfiles) {
    const pairs = [];
    let maxDist = 0;
    for (let i = 0; i < raProfiles.length; i++) {
      for (let j = i + 1; j < raProfiles.length; j++) {
        const dist = this._distance(raProfiles[i], raProfiles[j]);
        if (Number.isFinite(dist) && dist > 0) {
          pairs.push(dist);
          if (dist > maxDist) maxDist = dist;
        }
      }
    }

    pairs.sort((a, b) => a - b);
    const totalPop = raProfiles.reduce((sum, p) => sum + (p.populacao || 0), 0) || 1;
    const capitalShare = Math.max(...raProfiles.map(p => (p.populacao || 0) / totalPop));
    const avgDigital = raProfiles.reduce((sum, p) => sum + (p.alcance_digital || 0.5), 0) / raProfiles.length;
    const avgToler = raProfiles.reduce((sum, p) => sum + (p.tolerancia_media || 0.5), 0) / raProfiles.length;
    const avgSuscept = raProfiles.reduce((sum, p) => sum + (p.susceptibilidade_desinformacao || 0.45), 0) / raProfiles.length;
    const spreadNorm = clamp(maxDist / 3.5, 0, 1);

    const thresholdQ = raProfiles.length > 20 ? 0.12 : 0.22;
    const rawThreshold = percentile(pairs, thresholdQ);
    const distThreshold = clamp(rawThreshold || 0.12, Math.max(0.04, maxDist * 0.06), Math.max(0.12, maxDist * 0.32));
    const minNeighbors = raProfiles.length > 20 ? 2 : 3;

    this.params.diffusion = clamp(0.18 - spreadNorm * 0.08 - capitalShare * 0.03 + avgToler * 0.02, 0.07, 0.18);
    this.params.reversion = clamp(0.007 + capitalShare * 0.004 + avgDigital * 0.002 - avgSuscept * 0.002, 0.006, 0.014);
    this.params.noise = clamp(0.002 + avgSuscept * 0.003 + spreadNorm * 0.002 - capitalShare * 0.001, 0.002, 0.006);
    this.params.crossChannel = clamp(0.035 + (1 - avgToler) * 0.03 + avgDigital * 0.01, 0.035, 0.08);
    this.params.eventResidual = clamp(0.24 + avgSuscept * 0.20 + spreadNorm * 0.10, 0.24, 0.46);

    this.calibration = { distThreshold, minNeighbors };
  }

  init(raProfiles) {
    this.nodes = [];
    this.nodeByName = {};
    this.nodeBySigla = {};
    this.step = 0;

    for (const prof of raProfiles) {
      const node = new RANode(prof);
      this.nodes.push(node);
      this.nodeByName[normalizeName(prof.ra_nome)] = node;
      this.nodeBySigla[prof.sigla] = node;
    }

    this._calibrate(raProfiles);

    const distThreshold = this.calibration?.distThreshold || 0.07;
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const a = this.nodes[i];
        const b = this.nodes[j];
        const dist = this._distance(a, b);
        if (dist < distThreshold) {
          const peso = clamp(Math.exp(-dist / Math.max(distThreshold, 1e-6)), 0.15, 0.95);
          a.vizinhos.push({ node: b, peso });
          b.vizinhos.push({ node: a, peso });
        }
      }
    }

    const minNeighbors = this.calibration?.minNeighbors || 2;
    for (const node of this.nodes) {
      if (node.vizinhos.length < minNeighbors) {
        const dists = this.nodes
          .filter(n => n !== node && !node.vizinhos.some(v => v.node === n))
          .map(n => ({ node: n, dist: this._distance(node, n) }))
          .sort((a, b) => a.dist - b.dist);

        const needed = minNeighbors - node.vizinhos.length;
        for (let k = 0; k < Math.min(needed, dists.length); k++) {
          const peso = clamp(Math.exp(-dists[k].dist / Math.max(distThreshold, 1e-6)), 0.12, 0.90);
          node.vizinhos.push({ node: dists[k].node, peso });
          dists[k].node.vizinhos.push({ node, peso });
        }
      }
    }
  }

  applyRegionalContext(regionMap, mirofishContext) {
    this.mirofishSignals = mirofishContext?.signals || {};
    for (const node of this.nodes) {
      const agg = regionMap?.[normalizeName(node.nome)] || null;
      node.applyRegionalProfile(agg, this.mirofishSignals);
    }
  }

  _eventBias(node, eventDef) {
    const impacts = eventDef.impacts || {};
    const issue = node.issueProfile || {};
    const narrative = clamp((this.mirofishSignals.narrative_pressure || 0) / 100, 0, 1);
    const mobilization = clamp((this.mirofishSignals.mobilization_score || 0) / 100, 0, 1);
    let bias = 1;
    bias += (impacts.desinfo || 0) * (issue.desinfo || 0) * 0.85;
    bias += (impacts.saude || 0) * (issue.saude || 0) * 0.70;
    bias += (impacts.educacao || 0) * (issue.educacao || 0) * 0.40;
    bias += (impacts.seguranca || 0) * (issue.seguranca || 0) * 0.60;
    bias += (impacts.imigracao || 0) * (issue.imigracao || 0) * 0.85;
    bias += (impacts.garimpo || 0) * (issue.garimpo || 0) * 0.75;
    bias += (impacts.demarcacao || 0) * (issue.demarcacao || 0) * 0.55;
    bias += (impacts.social || 0) * (issue.social || 0) * 0.75;
    bias += (impacts.direita || 0) * (issue.direita || 0) * 0.70;
    bias += (impacts.esquerda || 0) * (issue.esquerda || 0) * 0.70;
    bias += (impacts.territorial || 0) * (issue.territorial || 0) * 0.75;
    bias += (impacts.narrativa || 0) * narrative * 0.45;
    bias += (impacts.mobilizacao || 0) * mobilization * 0.35;
    return clamp(bias, 0.30, 2.60);
  }

  _applyDelta(node, dOrient, dEngaj, dToler, residualFrac) {
    node.orientacao = clamp(node.orientacao + dOrient, 0.01, 0.99);
    node.engajamento = clamp(node.engajamento + dEngaj, 0.01, 0.99);
    node.tolerancia = clamp(node.tolerancia + dToler, 0.01, 0.99);
    node.residualOrient += dOrient * residualFrac;
    node.residualEngaj += dEngaj * residualFrac;
    node.residualToler += dToler * residualFrac;
  }

  _impactFor(node, eventDef, strength) {
    const bias = this._eventBias(node, eventDef);
    const inertiaFactor = 1 - node.inercia * 0.45;
    return {
      dOrient: (eventDef.dOrient || 0) * strength * bias * inertiaFactor,
      dEngaj: (eventDef.dEngaj || 0) * strength * bias * inertiaFactor,
      dToler: (eventDef.dToler || 0) * strength * bias * inertiaFactor,
    };
  }

  tick() {
    const { diffusion, reversion, noise, crossChannel } = this.params;
    const neighborAvgs = this.nodes.map(node => {
      if (node.vizinhos.length === 0) return { orient: node.orientacao, engaj: node.engajamento, toler: node.tolerancia };
      let wSum = 0, oSum = 0, eSum = 0, tSum = 0;
      for (const v of node.vizinhos) {
        const w = v.peso;
        wSum += w;
        oSum += v.node.orientacao * w;
        eSum += v.node.engajamento * w;
        tSum += v.node.tolerancia * w;
      }
      return { orient: oSum / wSum, engaj: eSum / wSum, toler: tSum / wSum };
    });

    for (let i = 0; i < this.nodes.length; i++) {
      const node = this.nodes[i];
      const navg = neighborAvgs[i];
      const issueHeat = ((node.issueProfile.desinfo || 0) * 0.34)
        + ((node.issueProfile.saude || 0) * 0.22)
        + ((node.issueProfile.seguranca || 0) * 0.16)
        + ((node.issueProfile.imigracao || 0) * 0.14)
        + ((node.issueProfile.social || 0) * 0.14);

      node.prevOrient = node.orientacao;
      node.prevEngaj = node.engajamento;
      node.prevToler = node.tolerancia;

      const diffStrength = diffusion * node.tolerancia * (1 - node.inercia * 0.5);
      const dOrientDiff = (navg.orient - node.orientacao) * diffStrength;
      const dEngajDiff = (navg.engaj - node.engajamento) * diffStrength;
      const dTolerDiff = (navg.toler - node.tolerancia) * diffStrength * 0.5;

      const revStr = reversion * node.inercia;
      const targetOrient = node.attrOrient + node.residualOrient;
      const targetEngaj = node.attrEngaj + node.residualEngaj;
      const targetToler = node.attrToler + node.residualToler;
      const dOrientRev = (targetOrient - node.orientacao) * revStr;
      const dEngajRev = (targetEngaj - node.engajamento) * revStr;
      const dTolerRev = (targetToler - node.tolerancia) * revStr;

      const orientExtreme = Math.abs(node.orientacao - 0.5) * 2;
      const dEngajCross = orientExtreme * crossChannel * 0.3 + issueHeat * crossChannel * 0.10;
      const dOrientCross = ((node.issueProfile.direita || 0.5) - (node.issueProfile.esquerda || 0.5)) * 0.01 * issueHeat;
      const dTolerCross = -issueHeat * 0.006 * node.volatilidade;

      const dOrientNoise = this._rngNorm() * noise * node.volatilidade;
      const dEngajNoise = this._rngNorm() * noise * node.volatilidade * 0.7;
      const dTolerNoise = this._rngNorm() * noise * node.volatilidade * 0.5;

      node.orientacao = clamp(node.orientacao + dOrientDiff + dOrientRev + dOrientCross + dOrientNoise, 0.01, 0.99);
      node.engajamento = clamp(node.engajamento + dEngajDiff + dEngajRev + dEngajCross + dEngajNoise, 0.01, 0.99);
      node.tolerancia = clamp(node.tolerancia + dTolerDiff + dTolerRev + dTolerCross + dTolerNoise, 0.01, 0.99);
      node.pushHistory();
    }

    this.step++;
  }

  injectEvent(eventDef, targetNode) {
    if (!targetNode && !eventDef.global) return;
    const residualFrac = this.params.eventResidual;

    if (eventDef.global) {
      for (const node of this.nodes) {
        const strength = 1 - node.inercia * 0.5;
        const delta = this._impactFor(node, eventDef, strength);
        this._applyDelta(node, delta.dOrient, delta.dEngaj, delta.dToler, residualFrac);
      }
      return;
    }

    const applyLocal = (node, strength) => {
      const delta = this._impactFor(node, eventDef, strength);
      this._applyDelta(node, delta.dOrient, delta.dEngaj, delta.dToler, residualFrac);
    };

    applyLocal(targetNode, 1.0);
    const firstRing = new Set();
    for (const v of targetNode.vizinhos) {
      applyLocal(v.node, 0.52 * v.peso);
      firstRing.add(v.node);
    }

    for (const v of targetNode.vizinhos) {
      for (const v2 of v.node.vizinhos) {
        if (v2.node !== targetNode && !firstRing.has(v2.node)) {
          applyLocal(v2.node, 0.22 * v2.peso);
        }
      }
    }
  }

  findNode(name) {
    if (!name) return null;
    const lower = normalizeName(name);
    for (const node of this.nodes) {
      const nodeLower = normalizeName(node.nome);
      if (nodeLower === lower || node.sigla.toLowerCase() === lower) return node;
    }
    for (const node of this.nodes) {
      const nodeLower = normalizeName(node.nome);
      if (nodeLower.includes(lower) || lower.includes(nodeLower)) return node;
    }
    return null;
  }

  computeMetrics() {
    let totalPop = 0;
    let wOrient = 0, wEngaj = 0, wToler = 0;
    let wOrient2 = 0;
    let totalDelta = 0;
    let territorialHeat = 0;

    for (const node of this.nodes) {
      const p = node.populacao;
      totalPop += p;
      wOrient += node.orientacao * p;
      wEngaj += node.engajamento * p;
      wToler += node.tolerancia * p;
      wOrient2 += node.orientacao * node.orientacao * p;
      territorialHeat += ((node.issueProfile?.territorial || 0.3) * (1 - node.tolerancia) * p);
      totalDelta += Math.abs(node.orientacao - node.prevOrient)
                  + Math.abs(node.engajamento - node.prevEngaj)
                  + Math.abs(node.tolerancia - node.prevToler);
    }

    const meanOrient = wOrient / totalPop;
    const varOrient = wOrient2 / totalPop - meanOrient * meanOrient;
    const stdOrient = Math.sqrt(Math.max(0, varOrient));

    return {
      polarizacao: Math.min(0.95, Math.max(0.05, stdOrient * 8)),
      engajamento: wEngaj / totalPop,
      tolerancia: wToler / totalPop,
      orientacao_media: meanOrient,
      estabilidade: Math.min(0.99, Math.max(0.01, 1 - totalDelta / (this.nodes.length * 3) * 50)),
      atividade: 1.0,
      delta_bruto: totalDelta / (this.nodes.length * 3),
      calor_territorial: territorialHeat / totalPop,
    };
  }

  perRA() {
    return this.nodes.map(node => ({
      nome: node.nome,
      sigla: node.sigla,
      orientacao: node.orientacao,
      engajamento: node.engajamento,
      tolerancia: node.tolerancia,
      atividade: node.populacao,
      populacao: node.populacao,
      inercia: node.inercia,
      deltaOrient: node.orientacao - node.prevOrient,
      deltaEngaj: node.engajamento - node.prevEngaj,
      deltaToler: node.tolerancia - node.prevToler,
      issueProfile: { ...node.issueProfile },
    }));
  }

  reset() {
    for (const node of this.nodes) {
      node.orientacao = node.attrOrient;
      node.engajamento = node.attrEngaj;
      node.tolerancia = node.attrToler;
      node.prevOrient = node.orientacao;
      node.prevEngaj = node.engajamento;
      node.prevToler = node.tolerancia;
      node.residualOrient = 0;
      node.residualEngaj = 0;
      node.residualToler = 0;
      node.history = { orient: [], engaj: [], toler: [] };
    }
    this.step = 0;
    this._rngState = 42;
  }
}

window.NetworkElectoralEngine = NetworkElectoralEngine;
window.RANode = RANode;
"""

engine_path.write_text(engine_content, encoding="utf-8")
print("patched-lenia-rr-engine")
