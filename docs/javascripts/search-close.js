// Chiude il pannello di ricerca cliccando fuori dalla barra, o con Esc.
// Necessario perché la personalizzazione dell'header (layout logo + nav + ricerca
// sulla stessa riga) rompe il meccanismo CSS-only (:checked ~ ...) usato di
// default da Material for MkDocs per gestire l'overlay di ricerca.
document.addEventListener("DOMContentLoaded", function () {
  try {
    var toggle = document.getElementById("__search");
    var searchBox = document.querySelector(".md-search");

    if (!toggle || !searchBox) {
      return;
    }

    // Click fuori dalla barra di ricerca -> chiude
    document.addEventListener("click", function (event) {
      try {
        if (toggle.checked && !searchBox.contains(event.target)) {
          toggle.checked = false;
        }
      } catch (err) {
        /* non blocca il resto della pagina in caso di errore */
      }
    });

    // Tasto Esc -> chiude
    document.addEventListener("keydown", function (event) {
      try {
        if (event.key === "Escape" && toggle.checked) {
          toggle.checked = false;
        }
      } catch (err) {
        /* non blocca il resto della pagina in caso di errore */
      }
    });
  } catch (err) {
    /* fallimento silenzioso: la ricerca nativa di Material deve continuare a funzionare */
  }
});
