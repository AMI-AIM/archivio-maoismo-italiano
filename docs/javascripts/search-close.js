// PASSO 1 di test: solo chiusura al click fuori dalla barra di ricerca.
(function () {
  var toggle = document.getElementById("__search");
  var searchBox = document.querySelector(".md-search");

  if (!toggle || !searchBox) {
    return;
  }

  document.addEventListener("click", function (event) {
    if (toggle.checked && !searchBox.contains(event.target)) {
      toggle.checked = false;
    }
  });
})();