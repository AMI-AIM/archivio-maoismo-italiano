// ============================================================
// CARICAMENTO DATI
// ============================================================
let documenti = [];
let annoMin = 1950;
let annoMax = 2025;
let currentPage = 1;
const DOCS_PER_PAGE = 20;
const baseUrl = (document.querySelector('meta[name="ami-base-url"]')?.content || '').replace(/\/$/, '');

// ------------------------------------------------------------
// UTILITY TESTO: le descrizioni IA contengono HTML con stili
// inline (export Word). Per ricerca e card usiamo solo testo
// pulito; nel DOM injectiamo sempre testo escapato.
// ------------------------------------------------------------
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const _cacheTesto = new Map();
function pulisciTesto(raw) {
  if (!raw) return '';
  const s = String(raw);
  const hit = _cacheTesto.get(s);
  if (hit !== undefined) return hit;
  let out;
  if (s.includes('<')) {
    const doc = new DOMParser().parseFromString(s, 'text/html');
    out = (doc.body.textContent || '').replace(/\s+/g, ' ').trim();
  } else {
    out = s.replace(/\s+/g, ' ').trim();
  }
  _cacheTesto.set(s, out);
  return out;
}

// Preferisce il campo plain generato a monte (descrizione_testo),
// con fallback client-side per JSON/chunk che non lo hanno ancora.
// Memoizza sul documento per non ripulire a ogni keystroke/pagina.
function descrizionePulita(doc) {
  if (!doc) return '';
  if (doc._descrizionePulita === undefined) {
    doc._descrizionePulita = doc.descrizione_testo || pulisciTesto(doc.descrizione);
  }
  return doc._descrizionePulita;
}

function tronca(testo, max) {
  if (!testo || testo.length <= max) return testo || '';
  const taglio = testo.lastIndexOf(' ', max);
  return testo.slice(0, taglio > 0 ? taglio : max) + '…';
}

async function caricaDati() {
  try {
    const lazyLoader = window.amiLazyLoader;
    const manifest = lazyLoader ? await lazyLoader.init() : null;
    if (manifest) {
      await lazyLoader.loadNext();
      documenti = lazyLoader.documents();
      annoMin = manifest.anno_min || 1900;
      annoMax = manifest.anno_max || 2025;
    } else {
      const response = await fetch(`${baseUrl}/documenti.json`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      documenti = data.documenti;
      annoMin = data.anno_min || 1900;
      annoMax = data.anno_max || 2025;
    }
    inizializzaFiltri();
    precompilaRicercaDaURL();
    applicaFiltri();
  } catch (error) {
    console.error('Errore nel caricamento dei dati:', error);
    const container = document.getElementById('risultati-container');
    if (container) {
      container.innerHTML = '<p class="nessun-risultato">Errore nel caricamento dei dati.</p>';
    }
  }
}

function precompilaRicercaDaURL() {
  const params = new URLSearchParams(window.location.search);
  const query = params.get('q');
  if (query) {
    const campoTesto = document.getElementById('filtro-testo');
    if (campoTesto) {
      campoTesto.value = query;
    }
  }
  const serie = params.get('serie');
  if (serie) {
    const select = document.getElementById('filtro-argomento');
    if (select) {
      Array.from(select.options).forEach(opt => opt.selected = false);
      let found = false;
      for (let opt of select.options) {
        if (opt.value === serie) {
          opt.selected = true;
          found = true;
          break;
        }
      }
    }
  }
}

// ============================================================
// INIZIALIZZAZIONE FILTRI
// ============================================================
function inizializzaFiltri() {
  const toggleIds = ['toggle-organizzazione', 'toggle-persona', 'toggle-tipo', 'toggle-argomento', 'toggle-anno'];
  toggleIds.forEach(id => {
    const button = document.getElementById(id);
    if (!button) return;
    const container = button.nextElementSibling;
    if (!container || !container.classList.contains('filtro-contenuto')) return;
    container.classList.remove('open');
    button.classList.remove('open');
    button.addEventListener('click', function (e) {
      e.stopPropagation();
      const target = this.nextElementSibling;
      if (target && target.classList.contains('filtro-contenuto')) {
        target.classList.toggle('open');
        this.classList.toggle('open');
      }
    });
  });

  aggiornaOpzioniFiltri();

  const minSlider = document.getElementById('filtro-anno-min');
  const maxSlider = document.getElementById('filtro-anno-max');
  const minLabel = document.getElementById('anno-min-label');
  const maxLabel = document.getElementById('anno-max-label');

  minSlider.min = annoMin;
  minSlider.max = annoMax;
  minSlider.value = annoMin;
  maxSlider.min = annoMin;
  maxSlider.max = annoMax;
  maxSlider.value = annoMax;
  minLabel.textContent = annoMin;
  maxLabel.textContent = annoMax;

  // 🔥 CREA LE PILLOLE PER I VALORI DEGLI ANNI
  const minPill = document.createElement('span');
  minPill.className = 'slider-value-pill';
  minPill.id = 'anno-min-pill';
  minPill.textContent = annoMin;
  minSlider.parentNode.appendChild(minPill);

  const maxPill = document.createElement('span');
  maxPill.className = 'slider-value-pill';
  maxPill.id = 'anno-max-pill';
  maxPill.textContent = annoMax;
  maxSlider.parentNode.appendChild(maxPill);

  function aggiornaTrack() {
    const min = parseInt(minSlider.value);
    const max = parseInt(maxSlider.value);
    const minVal = parseInt(minSlider.min);
    const maxVal = parseInt(minSlider.max);
    const range = maxVal - minVal;
    const leftPercent = ((min - minVal) / range) * 100;
    const rightPercent = ((maxVal - max) / range) * 100;
    const track = document.getElementById('slider-track-fill');
    if (track) {
      track.style.left = leftPercent + '%';
      track.style.right = rightPercent + '%';
    }
    const minPillEl = document.getElementById('anno-min-pill');
    const maxPillEl = document.getElementById('anno-max-pill');
    if (minPillEl) {
      minPillEl.style.left = leftPercent + '%';
      minPillEl.textContent = min;
    }
    if (maxPillEl) {
      maxPillEl.style.left = (100 - rightPercent) + '%';
      maxPillEl.textContent = max;
    }
  }

  minSlider.addEventListener('input', function () {
    const val = parseInt(this.value);
    const maxVal = parseInt(maxSlider.value);
    if (val > maxVal) this.value = maxVal;
    document.getElementById('anno-min-label').textContent = this.value;
    aggiornaTrack();
    applicaFiltri();
  });

  maxSlider.addEventListener('input', function () {
    const val = parseInt(this.value);
    const minVal = parseInt(minSlider.value);
    if (val < minVal) this.value = minVal;
    document.getElementById('anno-max-label').textContent = this.value;
    aggiornaTrack();
    applicaFiltri();
  });

  aggiornaTrack();

  document.querySelectorAll('select, input').forEach(el => el.addEventListener('change', applicaFiltri));
  document.getElementById('filtro-testo').addEventListener('input', applicaFiltri);
  document.getElementById('reset-filtri').addEventListener('click', resetFiltri);
}

function aggiornaOpzioniFiltri() {
  const organizzazioni = new Set();
  const persone = new Set();
  const tipi = new Set();
  const argomenti = new Set();
  documenti.forEach(doc => {
    doc.organizzazioni.forEach(org => organizzazioni.add(org));
    doc.persone.forEach(persona => persone.add(persona));
    if (doc.tipo) tipi.add(doc.tipo);
    if (doc.serie && Array.isArray(doc.serie)) {
      doc.serie.forEach(tag => argomenti.add(tag));
    }
  });
  popolaSelect('filtro-organizzazione', organizzazioni);
  popolaSelect('filtro-persona', persone);
  popolaSelect('filtro-tipo', tipi);
  popolaSelect('filtro-argomento', argomenti);
}

function popolaSelect(id, items) {
  const select = document.getElementById(id);
  if (!select) return;
  const selectedValues = Array.from(select.selectedOptions).map(opt => opt.value);
  const sorted = Array.from(items).sort();
  const allOption = select.querySelector('option[value="all"]');
  select.innerHTML = '';
  if (allOption) {
    select.appendChild(allOption);
  } else {
    const opt = document.createElement('option');
    opt.value = 'all';
    opt.textContent = id === 'filtro-argomento' ? 'Tutti' : 'Tutte';
    select.appendChild(opt);
  }
  sorted.forEach(item => {
    const opt = document.createElement('option');
    opt.value = item;
    opt.textContent = item;
    opt.selected = selectedValues.includes(item);
    select.appendChild(opt);
  });
}

// ============================================================
// APPLICAZIONE FILTRI
// ============================================================
// Unica fonte del filtraggio: usata sia da applicaFiltri() sia dai
// pulsanti di paginazione, per evitare derive tra le due copie.
function calcolaRisultati() {
  const orgSelezionate = getSelectedValues('filtro-organizzazione');
  const personeSelezionate = getSelectedValues('filtro-persona');
  const tipiSelezionati = getSelectedValues('filtro-tipo');
  const argomentiSelezionati = getSelectedValues('filtro-argomento');
  const annoMinVal = parseInt(document.getElementById('filtro-anno-min').value);
  const annoMaxVal = parseInt(document.getElementById('filtro-anno-max').value);
  const testo = document.getElementById('filtro-testo').value.toLowerCase().trim();

  let risultati = documenti.filter(doc => {
    if (orgSelezionate.length > 0 && !orgSelezionate.some(o => doc.organizzazioni.includes(o))) {
      return false;
    }
    if (personeSelezionate.length > 0 && !personeSelezionate.some(p => doc.persone.includes(p))) {
      return false;
    }
    if (tipiSelezionati.length > 0 && !tipiSelezionati.includes(doc.tipo)) {
      return false;
    }
    if (argomentiSelezionati.length > 0) {
      if (!doc.serie || !Array.isArray(doc.serie)) {
        return false;
      }
      if (!argomentiSelezionati.some(arg => doc.serie.includes(arg))) {
        return false;
      }
    }
    if (doc.anno && (doc.anno < annoMinVal || doc.anno > annoMaxVal)) {
      return false;
    }
    if (testo) {
      // Ricerca solo su testo pulito: niente match dentro tag HTML.
      const serieText = (doc.serie && Array.isArray(doc.serie)) ? doc.serie.join(' ') : '';
      const testoDoc = (
        (doc.titolo || '') + ' ' +
        (doc.autore || '') + ' ' +
        serieText + ' ' +
        descrizionePulita(doc)
      ).toLowerCase();
      if (!testoDoc.includes(testo)) {
        return false;
      }
    }
    return true;
  });

  // ORDINA CRONOLOGICAMENTE (data_ordine)
  risultati.sort((a, b) => {
    const da = a.data_ordine || [9999, 1, 1];
    const db = b.data_ordine || [9999, 1, 1];
    if (da[0] !== db[0]) return da[0] - db[0];
    if (da[1] !== db[1]) return da[1] - db[1];
    if (da[2] !== db[2]) return da[2] - db[2];
    return a.titolo.localeCompare(b.titolo);
  });
  return risultati;
}

function applicaFiltri() {
  currentPage = 1; // 🔥 Reset pagina alla prima quando i filtri cambiano
  mostraRisultati(calcolaRisultati());
}

function getSelectedValues(id) {
  const select = document.getElementById(id);
  if (!select) return [];
  const selected = Array.from(select.selectedOptions);
  if (selected.some(opt => opt.value === 'all')) {
    return [];
  }
  return selected.map(opt => opt.value);
}

// ============================================================
// VISUALIZZAZIONE RISULTATI (CON PAGINAZIONE)
// ============================================================
function capitalizza(s) {
  if (!s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function mostraRisultati(risultati) {
  const container = document.getElementById('risultati-container');
  const conteggio = document.getElementById('risultati-conteggio');
  const paginazioneContainer = document.getElementById('paginazione');
  if (!container) return;

  const totale = risultati.length;
  if (totale === 0) {
    container.innerHTML = '<p class="nessun-risultato">Nessun documento trovato con i filtri selezionati.</p>';
    if (conteggio) conteggio.textContent = '0 documenti';
    if (paginazioneContainer) paginazioneContainer.innerHTML = '';
    return;
  }

  // Calcola pagine
  const totalPages = Math.ceil(totale / DOCS_PER_PAGE);
  if (currentPage > totalPages) currentPage = totalPages;
  const start = (currentPage - 1) * DOCS_PER_PAGE;
  const end = Math.min(start + DOCS_PER_PAGE, totale);
  const paginaCorrente = risultati.slice(start, end);

  // Aggiorna conteggio
  if (conteggio) {
    const manifest = window.amiLazyLoader?.metadata();
    const caricati = manifest ? ` tra ${documenti.length} di ${manifest.totale} caricati` : '';
    conteggio.textContent = `${totale} documenti${caricati} (pagina ${currentPage} di ${totalPages})`;
  }

  // Costruisci HTML dei risultati (tutto escapato: i dati sono testo,
  // non markup; la descrizione è testo puro troncato a 300 caratteri)
  let html = '';
  paginaCorrente.forEach(doc => {
    let metaParts = [];
    if (doc.autore && doc.autore !== 'N/A' && doc.autore !== '') {
      metaParts.push(doc.autore);
    }
    const autoreNormalizzato = (doc.autore || '').trim().toLowerCase();
    const orgNormalizzata = (doc.organizzazione || '').trim().toLowerCase();
    if (doc.organizzazione && doc.organizzazione !== '' && orgNormalizzata !== autoreNormalizzato) {
      metaParts.push(doc.organizzazione);
    }
    if (doc.tipo && doc.tipo !== '') {
      metaParts.push(capitalizza(doc.tipo));
    }
    let metaLine = metaParts.length > 0 ? metaParts.join(' · ') : 'N/A';
    const descPulita = tronca(descrizionePulita(doc), 300);

    html += `
    <div class="risultato-card">
        <div class="risultato-data">${escapeHtml(doc.data || 'n.d.')}</div>
        <div class="risultato-contenuto">
            <div class="risultato-titolo">
                <a href="${baseUrl}/documenti/${doc.id}/">${escapeHtml(doc.titolo)}</a>
            </div>
            <div class="risultato-meta">${escapeHtml(metaLine)}</div>
            ${descPulita ? `<div class="risultato-desc">${escapeHtml(descPulita)}</div>` : ''}
        </div>
    </div>
    `;
  });
  container.innerHTML = html;

  // Genera paginazione
  if (paginazioneContainer) {
    generaIterfacciaPaginazione(paginazioneContainer, currentPage, totalPages);
    if (window.amiLazyLoader?.hasMore()) {
      const loadMore = document.createElement('button');
      loadMore.type = 'button';
      loadMore.className = 'pag-btn';
      loadMore.textContent = 'Carica altri documenti';
      loadMore.addEventListener('click', caricaProssimoChunk);
      paginazioneContainer.appendChild(loadMore);
    }
  }
}

async function caricaProssimoChunk() {
  const loader = window.amiLazyLoader;
  if (!loader?.hasMore()) return;
  try {
    await loader.loadNext();
    documenti = loader.documents();
    aggiornaOpzioniFiltri();
    applicaFiltri();
  } catch (error) {
    console.error('Errore nel caricamento del catalogo:', error);
  }
}

function generaIterfacciaPaginazione(container, current, total) {
  if (total <= 1) {
    container.innerHTML = '';
    return;
  }
  let html = '';

  // Pulsante "Precedente"
  html += `<button class="pag-btn pag-btn--nav" data-page="${current - 1}" aria-label="Pagina precedente" ${current <= 1 ? 'disabled' : ''}>‹</button>`;

  // Numeri di pagina
  const maxVisible = 7;
  let startPage = Math.max(1, current - Math.floor(maxVisible / 2));
  let endPage = Math.min(total, startPage + maxVisible - 1);
  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }
  if (startPage > 1) {
    html += `<button class="pag-btn" data-page="1">1</button>`;
    if (startPage > 2) html += `<span class="pag-btn pag-btn--disabled" style="border:none; background:transparent;">…</span>`;
  }
  for (let i = startPage; i <= endPage; i++) {
    const active = i === current ? 'pag-btn--active' : '';
    html += `<button class="pag-btn ${active}" data-page="${i}">${i}</button>`;
  }
  if (endPage < total) {
    if (endPage < total - 1) html += `<span class="pag-btn pag-btn--disabled" style="border:none; background:transparent;">…</span>`;
    html += `<button class="pag-btn" data-page="${total}">${total}</button>`;
  }

  // Pulsante "Successivo"
  html += `<button class="pag-btn pag-btn--nav" data-page="${current + 1}" aria-label="Pagina successiva" ${current >= total ? 'disabled' : ''}>›</button>`;

  container.innerHTML = html;

  // Aggiungi event listener ai pulsanti
  container.querySelectorAll('.pag-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', function () {
      const page = parseInt(this.dataset.page);
      if (!isNaN(page) && page !== current) {
        currentPage = page;
        const risultati = calcolaRisultati();
        mostraRisultati(risultati);
        // Riporta la vista in cima ai risultati: i pulsanti di paginazione
        // sono in fondo alla lista, senza questo l'utente resterebbe
        // scrollato in basso senza vedere i nuovi risultati.
        const risultatiContainer = document.getElementById('risultati-container');
        if (risultatiContainer) {
          risultatiContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });
}

// ============================================================
// RESET FILTRI
// ============================================================
function resetFiltri() {
  document.querySelectorAll('select').forEach(sel => {
    const allOpt = sel.querySelector('option[value="all"]');
    if (allOpt) {
      Array.from(sel.options).forEach(opt => opt.selected = false);
      allOpt.selected = true;
    }
  });
  document.getElementById('filtro-testo').value = '';
  document.getElementById('filtro-anno-min').value = annoMin;
  document.getElementById('filtro-anno-max').value = annoMax;
  document.getElementById('anno-min-label').textContent = annoMin;
  document.getElementById('anno-max-label').textContent = annoMax;

  const minPillReset = document.getElementById('anno-min-pill');
  const maxPillReset = document.getElementById('anno-max-pill');
  if (minPillReset) minPillReset.textContent = annoMin;
  if (maxPillReset) maxPillReset.textContent = annoMax;

  const minSlider = document.getElementById('filtro-anno-min');
  const maxSlider = document.getElementById('filtro-anno-max');
  const min = parseInt(minSlider.value);
  const max = parseInt(maxSlider.value);
  const minVal = parseInt(minSlider.min);
  const maxVal = parseInt(maxSlider.max);
  const range = maxVal - minVal;
  const leftPercent = ((min - minVal) / range) * 100;
  const rightPercent = ((maxVal - max) / range) * 100;
  const track = document.getElementById('slider-track-fill');
  if (track) {
    track.style.left = leftPercent + '%';
    track.style.right = rightPercent + '%';
  }
  if (minPillReset) minPillReset.style.left = leftPercent + '%';
  if (maxPillReset) maxPillReset.style.left = (100 - rightPercent) + '%';

  currentPage = 1;
  applicaFiltri();
}

// ============================================================
// AVVIO
// ============================================================
document.addEventListener('DOMContentLoaded', caricaDati);