// Chiude il pannello di ricerca cliccando fuori dalla barra, o con Esc.
// Necessario perché la personalizzazione dell'header (layout logo + nav + ricerca
// sulla stessa riga) rompe il meccanismo CSS-only (:checked ~ ...) usato di
// default da Material for MkDocs per gestire l'overlay di ricerca.
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("__search");
  var searchBox = document.querySelector(".md-search");

  if (!toggle || !searchBox) {
    return;
  }

  // Click fuori dalla barra di ricerca -> chiude
  document.addEventListener("click", function (event) {
    if (toggle.checked && !searchBox.contains(event.target)) {
      toggle.checked = false;
    }
  });

  // Tasto Esc -> chiude
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && toggle.checked) {
      toggle.checked = false;
    }
  });
});
