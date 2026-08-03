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

  // Il banner della hero ha overflow:hidden (necessario per i bordi
  // dell'immagine a piena larghezza), che taglierebbe il dropdown dei
  // risultati. Lo "estraiamo" spostandolo come figlio diretto del body,
  // posizionato via JS in coordinate fisse calcolate dal form: così può
  // comparire sopra qualsiasi elemento senza mai essere tagliato.
  document.body.appendChild(resultsBox);
  resultsBox.style.position = "fixed";

  function posizionaDropdown() {
    const rect = form.getBoundingClientRect();
    resultsBox.style.top = rect.bottom + 8 + "px";
    resultsBox.style.left = rect.left + "px";
    resultsBox.style.width = Math.max(rect.width, 320) + "px";
  }

  window.addEventListener("resize", function () {
    if (resultsBox.classList.contains("is-open")) {
      posizionaDropdown();
    }
  });
  window.addEventListener(
    "scroll",
    function () {
      if (resultsBox.classList.contains("is-open")) {
        posizionaDropdown();
      }
    },
    { passive: true }
  );

  let documenti = [];
  let persone = [];
  let organizzazioni = [];
  let datiCaricati = false;

  function caricaDati() {
    if (datiCaricati) return;
    Promise.all([
      fetch("/archivio-maoismo-italiano/documenti.json").then((res) => res.json()),
      fetch("/archivio-maoismo-italiano/soggetti.json").then((res) => res.json())
    ])
      .then(([datiDocumenti, datiSoggetti]) => {
        documenti = datiDocumenti.documenti || [];
        persone = datiSoggetti.persone || [];
        organizzazioni = datiSoggetti.organizzazioni || [];
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

  function estraiFrammento(campi, query) {
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

  // Restituisce un elenco unificato di risultati (persone, organizzazioni
  // e documenti), ciascuno con tipo/etichetta/link già pronti per il
  // rendering. Le persone e organizzazioni vengono prima: un nome cercato
  // è quasi sempre più specifico e rilevante di un riferimento generico
  // dentro un documento.
  function cercaTutti(query) {
    const q = query.toLowerCase().trim();
    if (!q) return [];

    const risultatiPersone = persone
      .filter((p) => {
        const campo = (p.nome || "") + " " + (p.biografia || "");
        return campo.toLowerCase().includes(q);
      })
      .map((p) => {
        const dateVita = [p.nascita, p.morte].filter(Boolean).join(" – ");
        return {
          tipo: "persona",
          etichetta: "Persona",
          titolo: p.nome,
          href: `/archivio-maoismo-italiano/persone/${p.slug}/`,
          frammento: [dateVita, estraiFrammento([p.biografia], q)].filter(Boolean).join(" · ")
        };
      });

    const risultatiOrganizzazioni = organizzazioni
      .filter((o) => {
        const campo = (o.nome || "") + " " + (o.storia || "") + " " + (o.categoria || "");
        return campo.toLowerCase().includes(q);
      })
      .map((o) => {
        return {
          tipo: "organizzazione",
          etichetta: "Organizzazione",
          titolo: o.nome,
          href: `/archivio-maoismo-italiano/organizzazioni/${o.slug}/`,
          frammento: [o.categoria, estraiFrammento([o.storia], q)].filter(Boolean).join(" · ")
        };
      });

    const risultatiDocumenti = documenti
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
      .map((doc) => {
        return {
          tipo: "documento",
          etichetta: "Documento",
          titolo: doc.titolo,
          href: `/archivio-maoismo-italiano/documenti/${doc.id}/`,
          frammento: estraiFrammento(
            [doc.descrizione, doc.keywords, doc.autore, doc.organizzazione],
            q
          )
        };
      });

    return [...risultatiPersone, ...risultatiOrganizzazioni, ...risultatiDocumenti].slice(0, 8);
  }

  function mostraRisultati(query) {
    const risultati = cercaTutti(query);

    if (!query.trim()) {
      resultsBox.innerHTML = "";
      resultsBox.classList.remove("is-open");
      return;
    }

    if (risultati.length === 0) {
      resultsBox.innerHTML =
        '<div class="hero-search-empty">Nessun risultato trovato.</div>';
      posizionaDropdown();
      resultsBox.classList.add("is-open");
      return;
    }

    let html = '<div class="hero-search-count">' + risultati.length + " risultati</div>";
    risultati.forEach((r) => {
      html += `
        <a class="hero-search-item" href="${r.href}">
          <div class="hero-search-item-title">
            <span class="hero-search-item-title-text">${evidenzia(r.titolo, query)}</span>
            <span class="hero-search-item-tag hero-search-item-tag--${r.tipo}">${r.etichetta}</span>
          </div>
          ${r.frammento ? `<div class="hero-search-item-snippet">${r.frammento}</div>` : ""}
        </a>
      `;
    });

    resultsBox.innerHTML = html;
    posizionaDropdown();
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
  // questo componente, non interferisce con nient'altro in pagina).
  // Il dropdown ora è un figlio del body (non più del form), quindi
  // controlliamo entrambi.
  document.addEventListener("click", function (event) {
    if (!form.contains(event.target) && !resultsBox.contains(event.target)) {
      resultsBox.classList.remove("is-open");
    }
  });

  input.addEventListener("focus", function () {
    if (input.value.trim()) {
      mostraRisultati(input.value);
    }
  });

  // === NUOVA MODIFICA: gestione del submit ===
  // Se il campo di ricerca è vuoto, blocchiamo il submit e restiamo
  // sulla home. Se invece c'è testo, il form invia a documenti/?q=...
  form.addEventListener("submit", function (event) {
    const query = input.value.trim();
    
    // Se non c'è testo, blocchiamo il submit e usciamo
    if (!query) {
      event.preventDefault();
      return;
    }

    // Se ci sono suggerimenti e l'utente preme Invio, vai al primo
    // risultato invece di far partire il submit nativo del form.
    const primoRisultato = resultsBox.querySelector(".hero-search-item");
    if (primoRisultato) {
      event.preventDefault();
      window.location.href = primoRisultato.getAttribute("href");
      return;
    }
    // Altrimenti, se non ci sono suggerimenti ma c'è testo,
    // lasciamo che il form invii normalmente a documenti/?q=...
    // (il submit viene eseguito normalmente)
  });
})();