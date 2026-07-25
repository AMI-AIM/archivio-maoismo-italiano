// ============================================================
// RICERCA ISTANTANEA NELLA HERO (home page)
// ============================================================
// Componente completamente autonomo e indipendente dalla ricerca
// di Material (header): usa gli stessi dati di documenti.json
// (già generati per la pagina Archivio) per mostrare suggerimenti
// mentre l'utente digita. Se l'elemento non esiste in pagina (cioè
// su qualsiasi pagina diversa dalla home), lo script non fa nulla.

(function () {
  const input = document.getElementById("hero-search-input");
  const resultsBox = document.getElementById("hero-search-results");
  const form = document.getElementById("hero-search-form");

  if (!input || !resultsBox || !form) {
    return; // non siamo in home: nessuna azione
  }

  let documenti = [];
  let datiCaricati = false;

  function caricaDati() {
    if (datiCaricati) return;
    fetch("/archivio-maoismo-italiano/documenti.json")
      .then((res) => res.json())
      .then((data) => {
        documenti = data.documenti || [];
        datiCaricati = true;
      })
      .catch((err) => {
        console.error("Ricerca hero: errore nel caricamento dei dati", err);
      });
  }

  // Carichiamo i dati al primo focus sulla barra, non al caricamento
  // della pagina, per non appesantire il primo rendering della home.
  input.addEventListener("focus", caricaDati, { once: true });

  function evidenzia(testo, query) {
    if (!testo) return "";
    const idx = testo.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return testo;
    return (
      testo.slice(0, idx) +
      "<mark>" +
      testo.slice(idx, idx + query.length) +
      "</mark>" +
      testo.slice(idx + query.length)
    );
  }

  function estraiFrammento(doc, query) {
    const campi = [doc.descrizione, doc.keywords, doc.autore, doc.organizzazione];
    for (const campo of campi) {
      if (campo && campo.toLowerCase().includes(query.toLowerCase())) {
        if (campo.length > 140) {
          const idx = campo.toLowerCase().indexOf(query.toLowerCase());
          const inizio = Math.max(0, idx - 40);
          const estratto = (inizio > 0 ? "…" : "") + campo.slice(inizio, inizio + 140) + "…";
          return evidenzia(estratto, query);
        }
        return evidenzia(campo, query);
      }
    }
    return "";
  }

  function cercaDocumenti(query) {
    const q = query.toLowerCase().trim();
    if (!q) return [];

    return documenti
      .filter((doc) => {
        const campo =
          (doc.titolo || "") +
          " " +
          (doc.autore || "") +
          " " +
          (doc.organizzazione || "") +
          " " +
          (doc.keywords || "") +
          " " +
          (doc.descrizione || "");
        return campo.toLowerCase().includes(q);
      })
      .slice(0, 8);
  }

  function mostraRisultati(query) {
    const risultati = cercaDocumenti(query);

    if (!query.trim()) {
      resultsBox.innerHTML = "";
      resultsBox.classList.remove("is-open");
      return;
    }

    if (risultati.length === 0) {
      resultsBox.innerHTML =
        '<div class="hero-search-empty">Nessun documento trovato.</div>';
      resultsBox.classList.add("is-open");
      return;
    }

    let html = '<div class="hero-search-count">' + risultati.length + " risultati</div>";
    risultati.forEach((doc) => {
      const frammento = estraiFrammento(doc, query);
      html += `
        <a class="hero-search-item" href="/archivio-maoismo-italiano/documenti/${doc.id}/">
          <div class="hero-search-item-title">${evidenzia(doc.titolo, query)}</div>
          ${frammento ? `<div class="hero-search-item-snippet">${frammento}</div>` : ""}
        </a>
      `;
    });

    resultsBox.innerHTML = html;
    resultsBox.classList.add("is-open");
  }

  input.addEventListener("input", function () {
    if (!datiCaricati) {
      // Se l'utente digita prima che il fetch sia finito, riproviamo
      // a mostrare i risultati appena i dati sono pronti.
      caricaDati();
      setTimeout(() => mostraRisultati(input.value), 300);
      return;
    }
    mostraRisultati(input.value);
  });

  // Chiude i suggerimenti cliccando fuori dal box (scoped solo a
  // questo componente, non interferisce con nient'altro in pagina)
  document.addEventListener("click", function (event) {
    if (!form.contains(event.target)) {
      resultsBox.classList.remove("is-open");
    }
  });

  input.addEventListener("focus", function () {
    if (input.value.trim()) {
      mostraRisultati(input.value);
    }
  });

  // Se ci sono suggerimenti e l'utente preme Invio, vai al primo
  // risultato invece di far partire il submit nativo del form.
  form.addEventListener("submit", function (event) {
    const primoRisultato = resultsBox.querySelector(".hero-search-item");
    if (primoRisultato) {
      event.preventDefault();
      window.location.href = primoRisultato.getAttribute("href");
    }
    // Se non ci sono risultati (o i dati non sono ancora caricati),
    // lasciamo che il form invii normalmente a documenti/?q=...
  });
})();
