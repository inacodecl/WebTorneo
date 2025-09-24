const video = document.getElementById('introVideo');
const skipBtn = document.getElementById('skipBtn');
const contenido = document.getElementById('contenido');
const logo = document.getElementById('logoFinal');
const overlay = document.getElementById('overlayMensaje');

document.addEventListener('DOMContentLoaded', () => {
  document.body.addEventListener('click', () => {
    overlay.style.opacity = '0';
    setTimeout(() => overlay.style.display = 'none', 500);

    video.muted = false;
    video.play().catch((error) => {
      console.log("Error al reproducir video:", error);
    });
  }, { once: true });
});

function mostrarContenido() {
  video.pause();
  video.style.display = 'none';
  skipBtn.style.display = 'none';
  contenido.style.display = 'flex';
  logo.style.opacity = '1';
}

video.addEventListener('ended', mostrarContenido);
skipBtn.addEventListener('click', mostrarContenido);