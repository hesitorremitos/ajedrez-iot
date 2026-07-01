var tiempoWms = 0;
var tiempoBms = 0;
var turno = null;
var activo = false;
var anchorMs = 0;
var intervalId = null;

var blancasEl = null;
var negrasEl = null;
var cajaBlancasEl = null;
var cajaNegrasEl = null;

function parseMmSs(text) {
  if (!text || typeof text !== 'string') {
    return 0;
  }
  var parts = text.split(':');
  if (parts.length !== 2) {
    return 0;
  }
  var minutes = parseInt(parts[0], 10) || 0;
  var seconds = parseInt(parts[1], 10) || 0;
  return (minutes * 60 + seconds) * 1000;
}

function formatMs(ms) {
  ms = ms < 0 ? 0 : ms;
  var totalSeconds = Math.floor(ms / 1000);
  var minutes = Math.floor(totalSeconds / 60);
  var seconds = totalSeconds % 60;
  return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
}

function paint(msW, msB) {
  if (blancasEl) {
    blancasEl.textContent = formatMs(msW);
  }
  if (negrasEl) {
    negrasEl.textContent = formatMs(msB);
  }

  if (cajaBlancasEl) {
    cajaBlancasEl.classList.toggle('tiempo-critico', turno === 'w' && msW < 60000 && activo);
  }
  if (cajaNegrasEl) {
    cajaNegrasEl.classList.toggle('tiempo-critico', turno === 'b' && msB < 60000 && activo);
  }
}

function updateTurnoHighlight() {
  if (cajaBlancasEl) {
    cajaBlancasEl.classList.toggle('activo', turno === 'w' && activo);
  }
  if (cajaNegrasEl) {
    cajaNegrasEl.classList.toggle('activo', turno === 'b' && activo);
  }
}

function tick() {
  if (!activo) {
    return;
  }

  var elapsed = Date.now() - anchorMs;
  var showW = tiempoWms;
  var showB = tiempoBms;

  if (turno === 'w') {
    showW = Math.max(0, tiempoWms - elapsed);
  } else if (turno === 'b') {
    showB = Math.max(0, tiempoBms - elapsed);
  }

  paint(showW, showB);
}

function startTick() {
  if (intervalId !== null) {
    return;
  }
  intervalId = setInterval(tick, 1000);
  tick();
}

export function initClock(els) {
  blancasEl = els.blancasEl;
  negrasEl = els.negrasEl;
  cajaBlancasEl = els.cajaBlancasEl;
  cajaNegrasEl = els.cajaNegrasEl;
}

export function stopReloj() {
  activo = false;
  if (intervalId !== null) {
    clearInterval(intervalId);
    intervalId = null;
  }
  if (cajaBlancasEl) {
    cajaBlancasEl.classList.remove('activo', 'tiempo-critico');
  }
  if (cajaNegrasEl) {
    cajaNegrasEl.classList.remove('activo', 'tiempo-critico');
  }
}

export function syncReloj(datos) {
  var hasTimes = datos.tiempoW !== undefined || datos.tiempoB !== undefined;
  var hasActive = datos.active !== undefined;

  if (!hasTimes && !hasActive) {
    return;
  }

  if (datos.tiempoW !== undefined) {
    tiempoWms = parseMmSs(datos.tiempoW);
  }
  if (datos.tiempoB !== undefined) {
    tiempoBms = parseMmSs(datos.tiempoB);
  }

  if (datos.turno) {
    turno = datos.turno;
  }

  if (datos.active === false) {
    paint(tiempoWms, tiempoBms);
    stopReloj();
    return;
  }

  anchorMs = Date.now();
  activo = true;
  updateTurnoHighlight();
  startTick();
}
