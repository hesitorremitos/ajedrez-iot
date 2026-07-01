import mqtt from 'mqtt';
import { Chess } from 'chess.js';
import { Chessground } from '@lichess-org/chessground';
import { initClock, syncReloj } from './clock.js';

var MQTT_URL = 'ws://mqtt.inginformatica.dev/mqtt';
var MQTT_TOPIC = 'ajedrez';

var FEN_INICIAL = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
var FEN_PIEZAS = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR';

var textos = {
  conectado: 'Broker conectado',
  esperando: 'Conectando...',
  desconectado: 'Broker desconectado',
  error: 'Error de conexion',
};

var historial = [];
var ultimoMoveRecibido = '';
var ultimoMovetext = '';

var ground = Chessground(document.getElementById('tablero'), {
  fen: FEN_INICIAL,
  orientation: 'white',
  viewOnly: true,
  coordinates: false,
  draggable: { enabled: false },
});

var pgnEl = document.getElementById('pgn-moves');
var ultimoMovEl = document.getElementById('ultimo-mov');
var sensoresEl = document.getElementById('sensores-activos');
var blancasTiempo = document.getElementById('blancas-tiempo');
var negrasTiempo = document.getElementById('negras-tiempo');
var nombreBlancas = document.getElementById('nombre-blancas-esp');
var nombreNegras = document.getElementById('nombre-negras-esp');
var relojBlancas = document.getElementById('reloj-blancas-caja');
var relojNegras = document.getElementById('reloj-negras-caja');
var turnoTexto = document.getElementById('turno-texto');
var turnoFicha = document.getElementById('turno-ficha');

initClock({
  blancasEl: blancasTiempo,
  negrasEl: negrasTiempo,
  cajaBlancasEl: relojBlancas,
  cajaNegrasEl: relojNegras,
});

function setEstado(estado) {
  var statusAdmin = document.getElementById('conexion-status');
  if (statusAdmin) {
    statusAdmin.textContent = textos[estado] || textos.desconectado;
    statusAdmin.className = 'status ' + estado;
  }

  var statusIndex = document.getElementById('conexion-status-esp');
  if (statusIndex) {
    statusIndex.textContent = textos[estado] || textos.desconectado;
    statusIndex.className = 'status ' + estado;
  }
}

function parseEsp32Move(move) {
  move = move.trim();
  if (move === 'O-O' || move === 'O-O-O') {
    return move;
  }

  var promo = move.match(/^([a-h][1-8])-([a-h][1-8])=([QRBN])$/i);
  if (promo) {
    return {
      from: promo[1],
      to: promo[2],
      promotion: promo[3].toLowerCase(),
    };
  }

  var parts = move.split('-');
  if (parts.length === 2 && parts[0].length === 2 && parts[1].length === 2) {
    return { from: parts[0].toLowerCase(), to: parts[1].toLowerCase() };
  }

  return null;
}

function esPartidaNueva(datos) {
  if (!datos.fen) {
    return false;
  }
  if (datos.move) {
    return false;
  }
  return datos.fen.indexOf(FEN_PIEZAS) === 0;
}

function renderPgnEmpty() {
  return '<p class="pgn-empty">Esperando movimientos...</p>';
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function buildMovetext(moves) {
  var text = '';
  for (var i = 0; i < moves.length; i++) {
    if (i % 2 === 0) {
      text += (Math.floor(i / 2) + 1) + '. ';
    }
    text += moves[i] + ' ';
  }
  return text.trim();
}

function renderPgnTable(moves) {
  if (!moves || moves.length === 0) {
    return renderPgnEmpty();
  }

  var rows = '';
  var totalRows = Math.ceil(moves.length / 2);
  for (var r = 0; r < totalRows; r++) {
    var num = r + 1;
    var white = moves[r * 2];
    var black = moves[r * 2 + 1] || '\u2014';
    var rowClass = r === totalRows - 1 ? 'pgn-row pgn-row--activo' : 'pgn-row';
    rows += '<tr class="' + rowClass + '">';
    rows += '<td class="pgn-num">' + num + '</td>';
    rows += '<td class="pgn-w">' + white + '</td>';
    rows += '<td class="pgn-b">' + black + '</td>';
    rows += '</tr>';
  }

  return (
    '<table class="pgn-table">' +
    '<thead><tr><th>#</th><th>Blancas</th><th>Negras</th></tr></thead>' +
    '<tbody>' + rows + '</tbody></table>'
  );
}

function resetHistorial() {
  historial = [];
  ultimoMoveRecibido = '';
  ultimoMovetext = '';
  if (pgnEl) {
    pgnEl.innerHTML = renderPgnEmpty();
  }
}

function rebuildPgn() {
  if (!pgnEl) {
    return;
  }
  if (historial.length === 0) {
    ultimoMovetext = '';
    pgnEl.innerHTML = renderPgnEmpty();
    return;
  }

  var game = new Chess();
  for (var i = 0; i < historial.length; i++) {
    var parsed = parseEsp32Move(historial[i]);
    if (!parsed) {
      continue;
    }
    var result = game.move(parsed);
    if (!result) {
      break;
    }
  }

  var moves = game.history();
  ultimoMovetext = buildMovetext(moves);
  pgnEl.innerHTML = renderPgnTable(moves);
  pgnEl.scrollTop = pgnEl.scrollHeight;
}

export function getPgnMovetext() {
  return ultimoMovetext;
}

function agregarMovimiento(move) {
  if (!move || move === ultimoMoveRecibido) {
    return;
  }
  ultimoMoveRecibido = move;
  historial.push(move);
  rebuildPgn();
}

function actualizar(datos) {
  if (esPartidaNueva(datos)) {
    resetHistorial();
  }

  if (datos.fen) {
    ground.set({ fen: datos.fen, viewOnly: true, coordinates: false, draggable: { enabled: false } });
  }

  if (datos.pgn && pgnEl) {
    ultimoMovetext = datos.pgn;
    pgnEl.innerHTML = '<pre class="pgn-raw">' + escapeHtml(datos.pgn) + '</pre>';
    pgnEl.scrollTop = pgnEl.scrollHeight;
  } else if (datos.move) {
    agregarMovimiento(datos.move);
  }

  if (ultimoMovEl && (datos.move || datos.ultimoMov)) {
    ultimoMovEl.textContent = datos.move || datos.ultimoMov;
  }

  if (sensoresEl && datos.sensores !== undefined) {
    sensoresEl.textContent = datos.sensores + ' / 64';
  }

  if (datos.tiempoW !== undefined || datos.tiempoB !== undefined || datos.active !== undefined) {
    syncReloj(datos);
  }

  if (datos.nombresBlancas && nombreBlancas) {
    nombreBlancas.textContent = datos.nombresBlancas;
  }
  if (datos.nombresNegras && nombreNegras) {
    nombreNegras.textContent = datos.nombresNegras;
  }

  if (datos.turno) {
    if (turnoTexto) {
      turnoTexto.textContent = datos.turno === 'w' ? 'Blancas' : 'Negras';
    }
    if (turnoFicha) {
      turnoFicha.style.background = datos.turno === 'w' ? '#ffffff' : '#222222';
      turnoFicha.style.borderColor = datos.turno === 'w' ? '#aaa' : '#555';
    }
  }
}

var client = mqtt.connect(MQTT_URL, {
  clientId: 'web-' + Math.random().toString(16).slice(2, 10),
  clean: true,
  reconnectPeriod: 3000,
});

client.on('connect', function () {
  client.subscribe(MQTT_TOPIC);
  setEstado('conectado');
});

client.on('reconnect', function () {
  setEstado('esperando');
});

client.on('close', function () {
  setEstado('desconectado');
});

client.on('error', function () {
  setEstado('error');
});

client.on('message', function (topic, buf) {
  try {
    var datos = JSON.parse(buf.toString());
    if (datos.tipo) {
      return;
    }
    actualizar(datos);
  } catch (err) {
    actualizar({ fen: buf.toString().trim() });
  }
});

export function iniciarPartida() {
  // pendiente: ESP32 no escucha MQTT aun
}

export function finalizarPartida() {
  // pendiente: ESP32 no escucha MQTT aun
}

setEstado('esperando');
