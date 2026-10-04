// ============================================================
// RICERCA ISTANTANEA NELLA HERO (home page)
// ============================================================
// Componente autonomo e indipendente dalla ricerca di Material:
// usa gli stessi dati di documenti.json / soggetti.json (generati per
// la pagina Archivio) per suggerire risultati mentre l'utente digita.
// Se l'elemento non esiste in pagina (ogni pagina diversa dalla home),
// lo script non fa nulla.
//
// ACCESSIBILITA' (pattern WAI-ARIA "combobox" con lista di suggerimenti):
// - il focus resta SEMPRE nel campo; frecce su/giu' scorrono i
//   suggerimenti (aria-activedescendant), Invio apre quello evidenziato;
// - Invio senza suggerimento evidenziato invia la ricerca COMPLETA a
//   documenti/?q=... (prima apriva sempre il primo suggerimento);
// - Esc chiude i suggerimenti (o svuota il campo se sono gia' chiusi);
// - il numero di risultati e gli stati di caricamento/errore sono
//   annunciati da una regione live (#hero-search-status).
//
// NOTE SUI TESTI: le descrizioni provenienti da Internet Archive
// possono contenere HTML con stili inline (export Word). Ricerca,
// taglio degli snippet ed evidenziazione avvengono sempre su testo
// pulito; cio' che viene iniettato nel DOM e' escapato (unica
// eccezione: i <mark> dell'evidenziazione).
(function () {
  const input = document.getElementById("hero-search-input");
  const resultsBox = document.getElementById("hero-search-results");
  const form = document.getElementById("hero-search-form");
  const baseUrl = (document.querySelector('meta[name="ami-base-url"]')?.content || "").replace(/\/$/, "");

  if (!input || !resultsBox || !form) {
    return; // non siamo in home: nessuna azione
  }

  // Il banner della hero ha overflow:hidden (necessario per i bordi
  // dell'immagine a piena larghezza), che taglierebbe il dropdown dei
  // risultati. Lo "estraiamo" spostandolo come figlio diretto del body,
  // posizionato via JS in coordinate fisse calcolate dal form. Il focus
  // non lo attraversa mai (resta nel campo), quindi la posizione nel DOM
  // non altera l'ordine di tabulazione.
  document.body.appendChild(resultsBox);
  resultsBox.style.position = "fixed";

  // --- Ruoli ARIA (aggiunti qui: senza JS il campo e' un normale input
  // di ricerca che invia a documenti/?q=...) ---
  const LISTBOX_ID = resultsBox.id;
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", LISTBOX_ID);
  input.setAttribute("aria-describedby", "hero-search-hint");
  resultsBox.setAttribute("role", "listbox");
  resultsBox.setAttribute("aria-label", "Suggerimenti di ricerca");

  // Istruzioni per i lettori di schermo (lette una volta al focus).
  const hint = document.createElement("span");
  hint.id = "hero-search-hint";
  hint.className = "ami-sr-only";
  hint.textContent = "Scrivi per vedere i suggerimenti. Frecce su e giù per sceglierne uno, Invio per aprirlo o per cercare in tutto l'archivio.";
  form.appendChild(hint);

  // Regione live: annuncia conteggi, caricamento ed errori.
  const status = document.createElement("div");
  status.id = "hero-search-status";
  status.className = "ami-sr-only";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  document.body.appendChild(status);

  let annuncioTimer = null;
  function annuncia(testo) {
    // Leggero ritardo: evita che ogni tasto produca un annuncio.
    clearTimeout(annuncioTimer);
    annuncioTimer = setTimeout(() => { status.textContent = testo; }, 400);
  }

  function posizionaDropdown() {
    const rect = form.getBoundingClientRect();
    // Larghezza: mai oltre il viewport (schermi piccoli), mai sotto i
    // 320px se il form e' piu' stretto; posizione clampata ai bordi.
    const larghezza = Math.min(window.innerWidth - 16, Math.max(rect.width, 320));
    const sinistra = Math.max(8, Math.min(rect.left, window.innerWidth - larghezza - 8));
    resultsBox.style.top = rect.bottom + 8 + "px";
    resultsBox.style.left = sinistra + "px";
    resultsBox.style.width = larghezza + "px";
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

  // ------------------------------------------------------------
  // UTILITY TESTO: pulizia, escape, evidenziazione
  // ------------------------------------------------------------
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  const _cacheTesto = new Map();
  function pulisciTesto(raw) {
    if (!raw) return "";
    const s = String(raw);
    const hit = _cacheTesto.get(s);
    if (hit !== undefined) return hit;
    let out;
    if (s.includes("<")) {
      // DOMParser non esegue script: sicuro anche con HTML sporco.
      const doc = new DOMParser().parseFromString(s, "text/html");
      out = (doc.body.textContent || "").replace(/\s+/g, " ").trim();
    } else {
      out = s.replace(/\s+/g, " ").trim();
    }
    _cacheTesto.set(s, out);
    return out;
  }

  // Descrizione senza HTML: preferisce il campo plain generato a monte
  // (json_export.py: descrizione_testo), con fallback alla pulizia
  // client-side per i JSON che non lo contengono ancora.
  function descrizionePulita(doc) {
    if (!doc) return "";
    return doc.descrizione_testo || pulisciTesto(doc.descrizione);
  }

  // Evidenzia il match su testo PULITO, escapando tutto il resto:
  // nessun HTML proveniente dai dati può finire nel DOM.
  function evidenzia(testo, query) {
    if (!testo) return "";
    const q = query.toLowerCase();
    const idx = testo.toLowerCase().indexOf(q);
    if (idx === -1) return escapeHtml(testo);
    return (
      escapeHtml(testo.slice(0, idx)) +
      "<mark>" +
      escapeHtml(testo.slice(idx, idx + q.length)) +
      "</mark>" +
      escapeHtml(testo.slice(idx + q.length))
    );
  }

  // Snippet con confini di parola, mai a metà di una parola/tag.
  function estraiFrammento(campi, query) {
    const q = query.toLowerCase();
    for (const campo of campi) {
      const pulito = pulisciTesto(campo);
      if (!pulito) continue;
      const idx = pulito.toLowerCase().indexOf(q);
      if (idx === -1) continue;
      if (pulito.length <= 160) return evidenzia(pulito, query);
      let inizio = Math.max(0, idx - 40);
      if (inizio > 0) {
        const sb = pulito.lastIndexOf(" ", inizio);
        if (sb > 0) inizio = sb + 1; // non parte a metà parola
      }
      let fine = Math.min(pulito.length, inizio + 160);
      if (fine < pulito.length) {
        const sp = pulito.lastIndexOf(" ", fine);
        if (sp > idx) fine = sp; // non spezza l'ultima parola
      }
      const estratto = (inizio > 0 ? "…" : "") + pulito.slice(inizio, fine) + "…";
      return evidenzia(estratto, query);
    }
    return "";
  }

  // ------------------------------------------------------------
  // CARICAMENTO DATI: al primo focus (non al caricamento della pagina,
  // per non appesantire il primo rendering della home). Una sola
  // richiesta alla volta; in caso di errore si potra' riprovare.
  // ------------------------------------------------------------
  let promessaDati = null;
  let erroreDati = false;

  function caricaDati() {
    if (datiCaricati) return Promise.resolve();
    if (promessaDati) return promessaDati;
    erroreDati = false;

    const json = (url) =>
      fetch(url).then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status} su ${url}`);
        return res.json();
      });

    promessaDati = Promise.all([
      json(`${baseUrl}/documenti.json`),
      json(`${baseUrl}/soggetti.json`)
    ])
      .then(([datiDocumenti, datiSoggetti]) => {
        documenti = datiDocumenti.documenti || [];
        persone = datiSoggetti.persone || [];
        organizzazioni = datiSoggetti.organizzazioni || [];
        datiCaricati = true;
      })
      .catch((err) => {
        console.error("Ricerca hero: errore nel caricamento dei dati", err);
        erroreDati = true;
      })
      .finally(() => {
        promessaDati = null;
      });
    return promessaDati;
  }

  input.addEventListener("focus", () => { caricaDati(); });

  // Restituisce un elenco unificato di risultati (persone, organizzazioni
  // e documenti), ciascuno con tipo/etichetta/link già pronti per il
  // rendering. Le persone e organizzazioni vengono prima: un nome cercato
  // è quasi sempre più specifico e rilevante di un riferimento generico
  // dentro un documento. I filtri usano solo testo pulito: cercare
  // "serif" o "0.75pt" non restituisce più match dentro i tag HTML.
  // Confronto per nome di persone e organizzazioni: minuscole, senza
  // accenti, punteggiatura e trattini ridotti a spazi ("Mao Tse Tung"
  // trova Mao Zedong tramite la variante "Mao Tse-tung").
  function normalizzaNome(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^\p{L}\p{N}]+/gu, " ")
      .trim();
  }

  function cercaTutti(query) {
    const q = query.toLowerCase().trim();
    if (!q) return [];
    const qNome = normalizzaNome(query);

    const risultatiPersone = persone
      .filter((p) => {
        const nomi = normalizzaNome((p.nome || "") + " " + (p.varianti || []).join(" "));
        const campo = ((p.nome || "") + " " + pulisciTesto(p.biografia)).toLowerCase();
        return (qNome && nomi.includes(qNome)) || campo.includes(q);
      })
      .map((p) => {
        const dateVita = ((p.nascita === "s.d." || !p.nascita) && (p.morte === "s.d." || !p.morte))
            ? "s.d."
            : [p.nascita, p.morte].filter(Boolean).join(" – ");
        return {
          tipo: "persona",
          etichetta: "Persona",
          titolo: p.nome,
          href: `${baseUrl}/persone/${p.slug}/`,
          frammento: [dateVita, estraiFrammento([p.biografia], q)].filter(Boolean).join(" · ")
        };
      });

    const risultatiOrganizzazioni = organizzazioni
      .filter((o) => {
        const nomi = normalizzaNome((o.nome || "") + " " + (o.varianti || []).join(" "));
        const campo = ((o.nome || "") + " " + pulisciTesto(o.storia) + " " + (o.categoria || "")).toLowerCase();
        return (qNome && nomi.includes(qNome)) || campo.includes(q);
      })
      .map((o) => {
        return {
          tipo: "organizzazione",
          etichetta: "Organizzazione",
          titolo: o.nome,
          href: `${baseUrl}/organizzazioni/${o.slug}/`,
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
          descrizionePulita(doc);
        return campo.toLowerCase().includes(q);
      })
      .map((doc) => {
        return {
          tipo: "documento",
          etichetta: "Documento",
          titolo: doc.titolo,
          href: `${baseUrl}/documenti/${doc.id}/`,
          frammento: estraiFrammento(
            [descrizionePulita(doc), doc.autore, doc.organizzazione],
            q
          )
        };
      });

    return [...risultatiPersone, ...risultatiOrganizzazioni, ...risultatiDocumenti].slice(0, 8);
  }

  // ------------------------------------------------------------
  // RENDERING E STATO DEI SUGGERIMENTI
  // ------------------------------------------------------------
  let indiceAttivo = -1;

  function opzioni() {
    return Array.prototype.slice.call(resultsBox.querySelectorAll('[role="option"]'));
  }

  function apri() {
    posizionaDropdown();
    resultsBox.classList.add("is-open");
    input.setAttribute("aria-expanded", "true");
  }

  function chiudi() {
    resultsBox.classList.remove("is-open");
    input.setAttribute("aria-expanded", "false");
    impostaAttivo(-1);
  }

  function impostaAttivo(indice) {
    const elenco = opzioni();
    elenco.forEach((el, i) => {
      const attivo = i === indice;
      el.classList.toggle("is-active", attivo);
      el.setAttribute("aria-selected", attivo ? "true" : "false");
    });
    indiceAttivo = indice;
    if (indice >= 0 && elenco[indice]) {
      input.setAttribute("aria-activedescendant", elenco[indice].id);
      elenco[indice].scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  // Messaggio non selezionabile dentro il box (caricamento, errore,
  // nessun risultato). aria-hidden: lo stesso testo passa dalla regione
  // live, e un listbox deve contenere solo opzioni.
  function mostraMessaggio(classe, testo) {
    resultsBox.innerHTML = `<div class="${classe}" aria-hidden="true">${escapeHtml(testo)}</div>`;
    indiceAttivo = -1;
    input.removeAttribute("aria-activedescendant");
    apri();
    annuncia(testo);
  }

  function mostraRisultati(query) {
    if (!query.trim()) {
      resultsBox.innerHTML = "";
      chiudi();
      status.textContent = "";
      return;
    }

    if (!datiCaricati) {
      if (erroreDati) {
        mostraMessaggio(
          "hero-search-empty hero-search-empty--errore",
          "Suggerimenti non disponibili al momento. Premi Invio per cercare in tutto l'archivio."
        );
        return;
      }
      mostraMessaggio("hero-search-empty", "Caricamento dell'archivio…");
      caricaDati().then(() => {
        // Si ridisegna solo se il campo non e' cambiato nel frattempo.
        if (input.value === query) mostraRisultati(query);
      });
      return;
    }

    const risultati = cercaTutti(query);
    if (risultati.length === 0) {
      mostraMessaggio(
        "hero-search-empty",
        "Nessun suggerimento. Premi Invio per cercare in tutto l'archivio."
      );
      return;
    }

    const etichettaConteggio =
      risultati.length === 1 ? "1 suggerimento" : risultati.length + " suggerimenti";
    let html = `<div class="hero-search-count" aria-hidden="true">${etichettaConteggio}</div>`;
    risultati.forEach((r, i) => {
      html += `
        <a class="hero-search-item" href="${escapeHtml(r.href)}" id="hero-opt-${i}" role="option" aria-selected="false" tabindex="-1">
          <span class="hero-search-item-title">
            <span class="hero-search-item-title-text">${evidenzia(r.titolo, query)}</span>
            <span class="hero-search-item-tag hero-search-item-tag--${r.tipo}">${r.etichetta}</span>
          </span>
          ${r.frammento ? `<span class="hero-search-item-snippet">${r.frammento}</span>` : ""}
        </a>
      `;
    });
    resultsBox.innerHTML = html;
    indiceAttivo = -1;
    input.removeAttribute("aria-activedescendant");
    apri();
    annuncia(etichettaConteggio + " disponibili. Usa le frecce per sceglierne uno.");
  }

  // Debounce: con 100+ documenti il filtro e' rapido, ma ridisegnare il
  // box a ogni tasto su un telefono lento fa saltare il layout.
  let inputTimer = null;
  input.addEventListener("input", function () {
    clearTimeout(inputTimer);
    inputTimer = setTimeout(() => mostraRisultati(input.value), 120);
  });

  input.addEventListener("focus", function () {
    if (input.value.trim()) {
      mostraRisultati(input.value);
    }
  });

  // ------------------------------------------------------------
  // TASTIERA
  // ------------------------------------------------------------
  input.addEventListener("keydown", function (event) {
    const elenco = opzioni();
    const aperto = resultsBox.classList.contains("is-open");

    switch (event.key) {
      case "ArrowDown":
        if (!aperto && input.value.trim()) {
          mostraRisultati(input.value);
          event.preventDefault();
          return;
        }
        if (!elenco.length) return;
        event.preventDefault();
        impostaAttivo((indiceAttivo + 1) % elenco.length);
        break;
      case "ArrowUp":
        if (!elenco.length || !aperto) return;
        event.preventDefault();
        impostaAttivo(indiceAttivo <= 0 ? elenco.length - 1 : indiceAttivo - 1);
        break;
      case "Home":
      case "End":
        // Con un suggerimento evidenziato Home/Fine scelgono il primo/ultimo;
        // altrimenti restano tasti di modifica del testo.
        if (indiceAttivo < 0 || !elenco.length) return;
        event.preventDefault();
        impostaAttivo(event.key === "Home" ? 0 : elenco.length - 1);
        break;
      case "Escape":
        if (aperto) {
          event.preventDefault();
          chiudi();
        } else if (input.value) {
          event.preventDefault();
          input.value = "";
          status.textContent = "";
        }
        break;
      case "Tab":
        chiudi();
        break;
    }
  });

  // Chiusura quando il focus lascia il campo (clic altrove, Tab).
  // mousedown sui suggerimenti avviene PRIMA del blur: si impedisce che
  // il blur chiuda il box prima che il clic arrivi al link.
  resultsBox.addEventListener("mousedown", function (event) {
    event.preventDefault();
  });
  input.addEventListener("blur", function () {
    chiudi();
  });

  // Chiude i suggerimenti cliccando fuori dal box.
  document.addEventListener("click", function (event) {
    if (!form.contains(event.target) && !resultsBox.contains(event.target)) {
      chiudi();
    }
  });

  // ------------------------------------------------------------
  // INVIO DEL FORM
  // ------------------------------------------------------------
  form.addEventListener("submit", function (event) {
    const query = input.value.trim();
    // Campo vuoto: nessun invio, si resta sulla home.
    if (!query) {
      event.preventDefault();
      input.focus();
      return;
    }
    // Suggerimento evidenziato con le frecce: si apre quello.
    const attivo = opzioni()[indiceAttivo];
    if (attivo) {
      event.preventDefault();
      window.location.href = attivo.getAttribute("href");
      return;
    }
    // Altrimenti invio nativo a documenti/?q=... (ricerca completa).
  });
})();
