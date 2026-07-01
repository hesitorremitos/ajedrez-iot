import { iniciarPartida, finalizarPartida, getPgnMovetext } from './board.js';

if (localStorage.getItem('user_type') !== 'admin') {
  location.href = 'login.html';
}

document.getElementById('btn-salir').addEventListener('click', function () {
  localStorage.removeItem('user_type');
  location.href = 'index.html';
});

document.getElementById('btn-nueva-partida').addEventListener('click', function () {
  var blancas = document.getElementById('jugador-blancas').value.trim();
  var negras = document.getElementById('jugador-negras').value.trim();
  var minutos = parseInt(document.getElementById('minutos-reloj').value, 10) || 10;
  iniciarPartida({
    minutos: minutos,
    nombresBlancas: blancas,
    nombresNegras: negras,
  });
});
document.getElementById('btn-finalizar').addEventListener('click', finalizarPartida);
document.getElementById('btn-copiar-pgn').addEventListener('click', function () {
  navigator.clipboard.writeText(getPgnMovetext());
});
