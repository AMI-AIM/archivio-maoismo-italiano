// Chiude il pannello di ricerca cliccando fuori dalla barra, o con Esc.
// Versione minimale: non tocca in alcun modo il submit del form né altri
// eventi già gestiti dal JS nativo di Material, per evitare interferenze.
(function () {
  function init() {
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // Il DOM è già pronto (lo script è caricato in coda al body da MkDocs)
    init();
  }
})();
