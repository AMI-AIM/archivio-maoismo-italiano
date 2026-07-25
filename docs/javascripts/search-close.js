// Chiude la ricerca al click fuori dal box, senza affidarsi a riferimenti
// DOM salvati una volta sola all'avvio: ad ogni click verifica dinamicamente
// se il toggle di ricerca attivo corrisponde a un box che contiene il click.
document.addEventListener("click", function (event) {
  var openToggle = document.querySelector('[data-md-toggle="search"]:checked');
  if (!openToggle) {
    return; // la ricerca non è aperta, non c'è nulla da chiudere
  }
 
  var clickedInsideSearch = event.target.closest && event.target.closest(".md-search");
  if (!clickedInsideSearch) {
    openToggle.checked = false;
  }
});
 