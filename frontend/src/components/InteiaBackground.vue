<template>
  <div class="inteia-bg" aria-hidden="true">
    <canvas ref="neuralCanvas" class="neural-bg"></canvas>
    <div class="grain"></div>
  </div>
  <Teleport to="body">
    <div ref="cursorEl" class="cursor-crosshair" aria-hidden="true">
      <svg viewBox="0 0 40 40">
        <circle class="ring" cx="20" cy="20" r="12"/>
        <circle class="ring" cx="20" cy="20" r="18" opacity="0.35"/>
        <circle class="dot" cx="20" cy="20" r="1.6"/>
        <line class="tick" x1="20" y1="0" x2="20" y2="6"/>
        <line class="tick" x1="20" y1="34" x2="20" y2="40"/>
        <line class="tick" x1="0" y1="20" x2="6" y2="20"/>
        <line class="tick" x1="34" y1="20" x2="40" y2="20"/>
      </svg>
      <span class="cursor-crosshair__label" ref="cursorLabel"></span>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

const neuralCanvas = ref(null)
const cursorEl = ref(null)
const cursorLabel = ref(null)

let raf = 0, raf2 = 0
let cleanupFns = []

function initNeural(canvas) {
  const ctx = canvas.getContext('2d')
  let dpr, nodes = []
  let mx = innerWidth / 2, my = innerHeight / 2

  function resize() {
    dpr = window.devicePixelRatio || 1
    canvas.width = innerWidth * dpr
    canvas.height = innerHeight * dpr
    canvas.style.width = innerWidth + 'px'
    canvas.style.height = innerHeight + 'px'
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.scale(dpr, dpr)
    buildNodes()
  }
  function buildNodes() {
    nodes = []
    const step = 96
    for (let y = -step; y < innerHeight + step; y += step) {
      for (let x = -step; x < innerWidth + step; x += step) {
        nodes.push({
          bx: x + (Math.random() - 0.5) * 22,
          by: y + (Math.random() - 0.5) * 22,
          x: 0, y: 0,
          phase: Math.random() * Math.PI * 2,
          freq: 0.3 + Math.random() * 0.4
        })
      }
    }
  }

  const onMove = (e) => { mx = e.clientX; my = e.clientY }
  document.addEventListener('mousemove', onMove)
  window.addEventListener('resize', resize)
  cleanupFns.push(() => {
    document.removeEventListener('mousemove', onMove)
    window.removeEventListener('resize', resize)
  })
  resize()

  const MAX = 96
  const draw = (t) => {
    t *= 0.001
    ctx.clearRect(0, 0, innerWidth, innerHeight)
    for (const n of nodes) {
      const ox = Math.sin(t * n.freq + n.phase) * 3
      const oy = Math.cos(t * n.freq * 0.8 + n.phase) * 3
      const dx = n.bx - mx, dy = n.by - my
      const dist = Math.sqrt(dx * dx + dy * dy)
      const push = dist < 180 ? (180 - dist) / 180 * 22 : 0
      const nx = push > 0 ? dx / dist : 0
      const ny = push > 0 ? dy / dist : 0
      n.x = n.bx + ox + nx * push
      n.y = n.by + oy + ny * push
    }
    ctx.lineWidth = 1
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i]
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j]
        const dx = a.x - b.x, dy = a.y - b.y
        const d2 = dx * dx + dy * dy
        if (d2 < MAX * MAX) {
          const alpha = (1 - Math.sqrt(d2) / MAX) * 0.18
          ctx.strokeStyle = `rgba(80, 70, 50, ${alpha})`
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
        }
      }
    }
    for (const n of nodes) {
      const dx = n.x - mx, dy = n.y - my
      const d = Math.sqrt(dx * dx + dy * dy)
      const glow = d < 220 ? (1 - d / 220) : 0
      ctx.beginPath()
      ctx.arc(n.x, n.y, 1.2 + glow * 1.2, 0, Math.PI * 2)
      // Mouse gera glow dourado próximo (visível em ambos modos via mix-blend)
      const r = 80 + glow * 121, g = 70 + glow * 79, b = 50 + glow * 0
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.28 + glow * 0.5})`
      ctx.fill()
    }
    raf = requestAnimationFrame(draw)
  }
  raf = requestAnimationFrame(draw)
}

function initCursor(cursor, label) {
  let cx = innerWidth / 2, cy = innerHeight / 2
  let tcx = cx, tcy = cy

  const onMove = (e) => { tcx = e.clientX; tcy = e.clientY }
  const onOver = (e) => {
    const el = e.target.closest && e.target.closest('[data-cursor-label]')
    if (el) {
      cursor.classList.add('active', 'has-label', 'large')
      label.textContent = el.dataset.cursorLabel
    } else if (e.target.closest && e.target.closest('a, button, [role=button]')) {
      cursor.classList.add('active')
    }
  }
  const onOut = (e) => {
    const el = e.target.closest && e.target.closest('[data-cursor-label]')
    if (el) {
      cursor.classList.remove('active', 'has-label', 'large')
      label.textContent = ''
    } else if (e.target.closest && e.target.closest('a, button, [role=button]')) {
      cursor.classList.remove('active')
    }
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseover', onOver)
  document.addEventListener('mouseout', onOut)
  cleanupFns.push(() => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseover', onOver)
    document.removeEventListener('mouseout', onOut)
  })

  const loop = () => {
    cx += (tcx - cx) * 0.28
    cy += (tcy - cy) * 0.28
    cursor.style.transform = `translate(${cx - 20}px, ${cy - 20}px)`
    document.documentElement.style.setProperty('--mx', `${cx}px`)
    document.documentElement.style.setProperty('--my', `${cy}px`)
    raf2 = requestAnimationFrame(loop)
  }
  loop()
}

onMounted(() => {
  if (neuralCanvas.value) initNeural(neuralCanvas.value)
  // Cursor crosshair: só em pointer fine + sem reduce-motion
  const fine = window.matchMedia && window.matchMedia('(pointer: fine)').matches
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (fine && !reduce && cursorEl.value && cursorLabel.value) {
    initCursor(cursorEl.value, cursorLabel.value)
  } else if (cursorEl.value) {
    cursorEl.value.style.display = 'none'
  }
})

onBeforeUnmount(() => {
  if (raf) cancelAnimationFrame(raf)
  if (raf2) cancelAnimationFrame(raf2)
  cleanupFns.forEach(fn => fn())
})
</script>

<style scoped>
.inteia-bg {
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 0;
}

.neural-bg {
  position: fixed; inset: 0;
  z-index: 1;
  pointer-events: none;
  mix-blend-mode: screen;
  opacity: 0.85;
}

/* Vinheta + grain editorial */
.inteia-bg::before {
  content: ""; position: fixed; inset: 0;
  background: radial-gradient(ellipse 1400px 900px at 50% 50%, rgba(22, 24, 32, 0.5), transparent 75%);
  pointer-events: none; z-index: 0;
}

.grain {
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 2;
  opacity: 0.12;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' seed='5'/%3E%3CfeColorMatrix values='0 0 0 0 0.96, 0 0 0 0 0.95, 0 0 0 0 0.92, 0 0 0 0.012 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

/* Cursor crosshair vive em <body> via Teleport — estilo está em inteia-theme.css (não-scoped) */

@media (max-width: 768px) {
  .neural-bg { opacity: 0.5; }
}
</style>
