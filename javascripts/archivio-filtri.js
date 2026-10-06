// ============================================================
// CARICAMENTO DATI
// ============================================================
let documenti = [];
let varianti = {}; // nome -> altre forme del nome (per restringere gli elenchi)
let ordineNomi = {}; // persona -> chiave d'ordine per cognome ("brandirali aldo")
let annoMin = 1950;
let annoMax = 2025;
let currentPage = 1;
// Stato della voce di cronologia all'arrivo (prima che i filtri
// riscrivano l'URL): contiene la posizione salvata uscendo.
const statoArrivo = window.history.state;
// Parametri all'arrivo: applicaFiltri() riscrive l'URL (tornando a
// pagina 1) prima che si possa leggere la pagina richiesta.
const parametriArrivo = new URLSearchParams(window.location.search);
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

// ------------------------------------------------------------
// RICERCA TESTUALE
// ------------------------------------------------------------
// Testo e query passano per la stessa normalizzazione: minuscole,
// accenti tolti (perche' = perche), punteggiatura ridotta a spazi.
// Il trattino resta dentro la parola, cosi' "AMI-0004" e "Tse-tung"
// restano interi e "lenin" non trova "marxista-leninista".
// Ogni parola della query deve comparire come INIZIO di una parola
// del documento (tutte le parole, in qualsiasi ordine).
const RE_SEPARATORI = /[^\p{L}\p{N}-]+/gu;
const RE_NON_LATINO = /[^\u0000-\u024f]/;

function normalizzaRicerca(s) {
    return String(s || '')
        .toLocaleLowerCase('it')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(RE_SEPARATORI, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

// Ricerca per NOME (elenchi dei filtri Persona e Organizzazione): anche
// il trattino diventa spazio, cosi' "Mao Tse Tung" trova "Mao Tse-tung"
// e "PCd'I m-l" trova "PCd'I (m-l)". Nella ricerca testuale dei documenti
// invece il trattino resta dentro la parola (vedi sopra).
function normalizzaNome(s) {
    return normalizzaRicerca(s).replace(/-+/g, ' ').replace(/\s+/g, ' ').trim();
}

function paroleQuery(q) {
    const n = normalizzaRicerca(q);
    return n ? n.split(' ') : [];
}

// Indice di ricerca del documento, calcolato una volta sola: segnatura,
// titolo, autore, organizzazioni e persone collegate, percorsi tematici
// e descrizione.
function indiceRicerca(doc) {
    if (doc._indiceRicerca === undefined) {
        const parti = [
            doc.id,
            doc.titolo,
            doc.autore,
            doc.organizzazione,
            (doc.organizzazioni || []).join(' '),
            (doc.persone || []).join(' '),
            (Array.isArray(doc.serie) ? doc.serie : []).join(' '),
            descrizionePulita(doc)
        ];
        doc._indiceRicerca = ' ' + normalizzaRicerca(parti.join(' '));
        doc._idRicerca = normalizzaRicerca(doc.id);
    }
    return doc._indiceRicerca;
}

function parolaPresente(doc, indice, p) {
    // Cinese e altre scritture senza spazi tra le parole: basta
    // che la sequenza compaia.
    if (RE_NON_LATINO.test(p)) return indice.includes(p);
    if (indice.includes(' ' + p)) return true;
    // "tse-tung" nella query trova anche "Tse Tung" scritto staccato.
    if (p.includes('-') && indice.includes(' ' + p.replace(/-+/g, ' '))) return true;
    // Solo cifre ("0004", "4"): cerca anche dentro la segnatura.
    return /^\d+$/.test(p) && doc._idRicerca.includes(p);
}

// Trattino e spazio sono equivalenti tra parole VICINE della query:
// "mao tse tung" trova "Mao Tse-tung", "ciu en lai" trova "Ciu-En-lai".
// Una parola sola resta intera: "lenin" non trova "marxista-leninista".
function corrispondeRicerca(doc, parole) {
    const indice = indiceRicerca(doc);
    const trovate = parole.map(p => parolaPresente(doc, indice, p));
    if (trovate.every(Boolean)) return true;
    for (let i = 0; i < parole.length - 1; i++) {
        for (let j = i + 1; j < parole.length; j++) {
            const gruppo = parole.slice(i, j + 1);
            if (gruppo.some(p => RE_NON_LATINO.test(p))) break;
            if (indice.includes(' ' + gruppo.join('-'))) {
                for (let k = i; k <= j; k++) trovate[k] = true;
            }
        }
    }
    return trovate.every(Boolean);
}

function tronca(testo, max) {
    if (!testo || testo.length <= max) return testo || '';
    const taglio = testo.lastIndexOf(' ', max);
    return testo.slice(0, taglio > 0 ? taglio : max) + '…';
}

async function caricaDati() {
    try {
        // CARICAMENTO COMPLETO: ignora il lazy loader e carica tutti i documenti subito
        const response = await fetch(`${baseUrl}/documenti.json`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        documenti = data.documenti;
        varianti = data.varianti || {};
        ordineNomi = data.ordine_nomi || {};
        annoMin = data.anno_min || 1900;
        annoMax = data.anno_max || 2025;
        
        inizializzaFiltri();
        precompilaRicercaDaURL();
        applicaFiltri();
        ripristinaPaginaEPosizione();
    } catch (error) {
        console.error('Errore nel caricamento dei dati:', error);
        const container = document.getElementById('risultati-container');
        if (container) {
            // Errore con via d'uscita: il catalogo e' un file statico, quindi
            // quasi sempre si tratta di rete assente o instabile.
            container.innerHTML =
                '<div class="nessun-risultato nessun-risultato--errore" role="alert">' +
                '<p>Non è stato possibile caricare il catalogo dei documenti. ' +
                'Controlla la connessione e riprova.</p>' +
                '<button type="button" class="riprova-btn">Riprova</button>' +
                '</div>';
            const riprova = container.querySelector('.riprova-btn');
            if (riprova) {
                riprova.addEventListener('click', function () {
                    riprova.disabled = true;
                    riprova.textContent = 'Caricamento…';
                    caricaDati();
                });
            }
        }
    }
}

// ============================================================
// PERSISTENZA FILTRI NELL'URL
// ============================================================
// Ogni filtro attivo nella sidebar viene riflesso come parametro
// query nell'URL (senza aggiungere voci alla cronologia, tramite
// history.replaceState), cosi' un link copiato riproduce esattamente
// la stessa combinazione di filtri. Mappatura parametri <-> filtri:
//   q              -> filtro-testo
//   organizzazione -> filtro-organizzazione (valori multipli, separati da virgola)
//   persona        -> filtro-persona        (valori multipli, separati da virgola)
//   tipo           -> filtro-tipo           (valori multipli, separati da virgola)
//   serie          -> filtro-argomento      (valori multipli, separati da virgola)
//   anno_min / anno_max -> range anni (solo se diverso dal range completo)
//   pagina         -> pagina dei risultati (solo se diversa dalla prima)
const URL_PARAM_PER_SELECT = {
    'filtro-organizzazione': 'organizzazione',
    'filtro-persona': 'persona',
    'filtro-tipo': 'tipo',
    'filtro-argomento': 'serie'
};

function precompilaRicercaDaURL() {
    const params = new URLSearchParams(window.location.search);

    const ordineParam = params.get('ordine');
    const ordina = document.getElementById('ordina-risultati');
    if (ordina) {
        ordina.value = (ordineParam && Array.from(ordina.options).some(o => o.value === ordineParam))
            ? ordineParam : 'data';
    }

    // Lo stato si ricostruisce per intero dall'URL (anche cio' che manca
    // va azzerato): la funzione serve all'arrivo e al tasto Indietro.
    const campoTesto = document.getElementById('filtro-testo');
    if (campoTesto) campoTesto.value = params.get('q') || '';

    // Filtri multi-select: ogni parametro puo' contenere piu' valori
    // separati da virgola (ognuno individualmente URL-encoded, cosi'
    // un nome che contenesse una virgola non spezza il parsing).
    Object.keys(URL_PARAM_PER_SELECT).forEach(selectId => {
        const paramName = URL_PARAM_PER_SELECT[selectId];
        const raw = params.get(paramName);
        if (!raw) {
            caselle(selectId).forEach(c => { c.checked = false; });
            return;
        }

        const valoriRichiesti = raw.split(',').map(v => {
            try {
                return decodeURIComponent(v);
            } catch (e) {
                return v;
            }
        }).filter(Boolean);

        if (!valoriRichiesti.length) return;

        // Valori sconosciuti (link da un catalogo precedente) vengono
        // semplicemente ignorati: nessuna casella spuntata = nessun filtro.
        caselle(selectId).forEach(c => {
            c.checked = valoriRichiesti.includes(c.value);
        });
    });

    // Range anni: entrambi i parametri devono essere presenti e validi
    // per essere applicati, altrimenti si tiene il range completo.
    const annoMinParam = parseInt(params.get('anno_min'), 10);
    const annoMaxParam = parseInt(params.get('anno_max'), 10);
    if (!isNaN(annoMinParam) && !isNaN(annoMaxParam)) {
        const minSlider = document.getElementById('filtro-anno-min');
        const maxSlider = document.getElementById('filtro-anno-max');
        if (minSlider && maxSlider) {
            const minClamp = Math.max(annoMin, Math.min(annoMinParam, annoMax));
            const maxClamp = Math.max(annoMin, Math.min(annoMaxParam, annoMax));
            minSlider.value = Math.min(minClamp, maxClamp);
            maxSlider.value = Math.max(minClamp, maxClamp);
            document.getElementById('anno-min-label').textContent = minSlider.value;
            document.getElementById('anno-max-label').textContent = maxSlider.value;
            aggiornaTrackSlider();
        }
    } else {
        const minSlider = document.getElementById('filtro-anno-min');
        const maxSlider = document.getElementById('filtro-anno-max');
        if (minSlider && maxSlider) {
            minSlider.value = annoMin;
            maxSlider.value = annoMax;
            document.getElementById('anno-min-label').textContent = annoMin;
            document.getElementById('anno-max-label').textContent = annoMax;
            aggiornaTrackSlider();
        }
    }
}

// Ricostruisce l'URL corrente in base allo stato attuale dei filtri.
// Usa replaceState (non pushState) per non intasare la cronologia del
// browser a ogni singola interazione con i filtri; il cambio di pagina
// invece crea una voce (nuovaVoce), cosi' Indietro torna alla pagina
// precedente dei risultati invece di uscire dall'archivio.
function aggiornaURLFiltri(nuovaVoce) {
    const params = new URLSearchParams();

    const campoTesto = document.getElementById('filtro-testo');
    if (campoTesto && campoTesto.value.trim()) {
        params.set('q', campoTesto.value.trim());
    }

    Object.keys(URL_PARAM_PER_SELECT).forEach(selectId => {
        const paramName = URL_PARAM_PER_SELECT[selectId];
        const valori = getSelectedValues(selectId);
        if (valori.length) {
            // Solo virgola e percento vanno protetti (la virgola separa i
            // valori): il resto lo codifica URLSearchParams una volta sola.
            params.set(paramName, valori.map(v => v.replace(/%/g, '%25').replace(/,/g, '%2C')).join(','));
        }
    });

    const minSlider = document.getElementById('filtro-anno-min');
    const maxSlider = document.getElementById('filtro-anno-max');
    if (minSlider && maxSlider) {
        const minVal = parseInt(minSlider.value, 10);
        const maxVal = parseInt(maxSlider.value, 10);
        if (minVal !== annoMin || maxVal !== annoMax) {
            params.set('anno_min', minVal);
            params.set('anno_max', maxVal);
        }
    }

    const ordina = document.getElementById('ordina-risultati');
    if (ordina && ordina.value !== 'data') {
        params.set('ordine', ordina.value);
    }

    if (currentPage > 1) {
        params.set('pagina', currentPage);
    }

    const queryString = params.toString();
    const nuovoURL = window.location.pathname + (queryString ? `?${queryString}` : '');
    if (nuovaVoce) window.history.pushState(null, '', nuovoURL);
    else window.history.replaceState(null, '', nuovoURL);
    // Ultima ricerca, per "Torna ai risultati" nelle schede (documenti.js).
    try { sessionStorage.setItem('ami-ultima-ricerca', nuovoURL); } catch (e) { /* storage non disponibile */ }
}

// ------------------------------------------------------------
// RITORNO DA UNA SCHEDA: pagina e posizione
// ------------------------------------------------------------
// La pagina dei risultati sta nell'URL (parametro "pagina"); la
// posizione di scorrimento si salva nello stato della voce di
// cronologia quando si lascia la pagina, e si ripristina tornando
// indietro, dopo che i risultati sono stati disegnati.
function ripristinaPaginaEPosizione() {
    const pagina = parseInt(parametriArrivo.get('pagina'), 10);
    if (!isNaN(pagina) && pagina > 1) {
        currentPage = pagina;
        mostraRisultati(calcolaRisultati()); // limita pagina al totale
        aggiornaURLFiltri();
    }
    if (statoArrivo && typeof statoArrivo.amiScrollY === 'number') {
        window.scrollTo(0, statoArrivo.amiScrollY);
    }
}

function salvaPosizione() {
    try {
        window.history.replaceState({ amiScrollY: window.scrollY }, '', window.location.href);
    } catch (e) { /* cronologia non disponibile: nessun ripristino */ }
}

// ============================================================
// ISTOGRAMMA CRONOLOGICO (stile Internet Archive)
// ============================================================
// Conta i documenti per anno (usando il campo 'anno' già presente in
// documenti.json) e disegna una barra per ogni anno tra annoMin e
// annoMax, con altezza proporzionale al conteggio. Barre senza
// documenti restano a un'altezza minima, come "asse" visivo.
function costruisciIstogramma() {
    const histContainer = document.getElementById('slider-histogram');
    if (!histContainer) return;

    const conteggioAnni = {};
    documenti.forEach(doc => {
        if (doc.anno) {
            conteggioAnni[doc.anno] = (conteggioAnni[doc.anno] || 0) + 1;
        }
    });

    const conteggiValori = Object.values(conteggioAnni);
    const maxConteggio = conteggiValori.length ? Math.max(...conteggiValori) : 1;

    let html = '';
    for (let anno = annoMin; anno <= annoMax; anno++) {
        const conteggio = conteggioAnni[anno] || 0;
        const altezzaPercento = conteggio > 0
            ? Math.max(8, Math.round((conteggio / maxConteggio) * 100))
            : 2;
        const etichetta = conteggio === 1 ? '1 documento' : `${conteggio} documenti`;
        html += `<div class="hist-bar" data-anno="${anno}" style="height:${altezzaPercento}%" title="${anno}: ${etichetta}"></div>`;
    }
    histContainer.innerHTML = html;
}

// ============================================================
// SLIDER ANNO — TRACK/PILLOLE (estratto in funzione a se' stante:
// serve sia all'evento input dello slider sia alla precompilazione
// da URL, che deve poter aggiornare l'aspetto visivo dello slider
// senza duplicare la logica)
// ============================================================
function aggiornaTrackSlider() {
    const minSlider = document.getElementById('filtro-anno-min');
    const maxSlider = document.getElementById('filtro-anno-max');
    if (!minSlider || !maxSlider) return;

    const min = parseInt(minSlider.value);
    const max = parseInt(maxSlider.value);
    const minVal = parseInt(minSlider.min);
    const maxVal = parseInt(maxSlider.max);
    const range = maxVal - minVal;
    const leftPercent = range ? ((min - minVal) / range) * 100 : 0;
    const rightPercent = range ? ((maxVal - max) / range) * 100 : 0;

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

    const histogram = document.getElementById('slider-histogram');
    if (histogram) {
        const bars = histogram.querySelectorAll('.hist-bar');
        bars.forEach(bar => {
            const anno = parseInt(bar.dataset.anno, 10);
            bar.classList.toggle('hist-bar--in-range', anno >= min && anno <= max);
        });
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
        button.setAttribute('aria-expanded', 'false');
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const target = this.nextElementSibling;
            if (target && target.classList.contains('filtro-contenuto')) {
                const aperto = target.classList.toggle('open');
                this.classList.toggle('open', aperto);
                this.setAttribute('aria-expanded', aperto ? 'true' : 'false');
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

    // ISTOGRAMMA: va costruito DOPO aver fissato annoMin/annoMax,
    // e PRIMA di aggiornaTrackSlider() (che evidenzia le barre nel range).
    costruisciIstogramma();
    
    //  CREA LE PILLOLE PER I VALORI DEGLI ANNI
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
    
    minSlider.addEventListener('input', function () {
        const val = parseInt(this.value);
        const maxVal = parseInt(maxSlider.value);
        if (val > maxVal) this.value = maxVal;
        document.getElementById('anno-min-label').textContent = this.value;
        aggiornaTrackSlider();
        applicaFiltri();
    });
    
    maxSlider.addEventListener('input', function () {
        const val = parseInt(this.value);
        const minVal = parseInt(minSlider.value);
        if (val < minVal) this.value = minVal;
        document.getElementById('anno-max-label').textContent = this.value;
        aggiornaTrackSlider();
        applicaFiltri();
    });
    
    aggiornaTrackSlider();
    
    document.querySelectorAll('#archivio-container select, #archivio-container input:not([data-solo-elenco])')
        .forEach(el => el.addEventListener('change', applicaFiltri));
    document.getElementById('filtro-testo').addEventListener('input', applicaFiltri);
    document.getElementById('reset-filtri').addEventListener('click', resetFiltri);
}

function aggiornaOpzioniFiltri() {
    // Valore -> numero di documenti dell'archivio che lo contengono.
    const organizzazioni = new Map();
    const persone = new Map();
    const tipi = new Map();
    const argomenti = new Map();
    const conta = (mappa, v) => { if (v) mappa.set(v, (mappa.get(v) || 0) + 1); };

    documenti.forEach(doc => {
        new Set(doc.organizzazioni).forEach(org => conta(organizzazioni, org));
        new Set(doc.persone).forEach(persona => conta(persone, persona));
        conta(tipi, doc.tipo);
        if (doc.serie && Array.isArray(doc.serie)) {
            new Set(doc.serie).forEach(tag => conta(argomenti, tag));
        }
    });
    
    popolaSpunte('filtro-organizzazione', organizzazioni, 'organizzazioni');
    popolaSpunte('filtro-persona', persone, 'persone');
    popolaSpunte('filtro-tipo', tipi, 'tipologie');
    popolaSpunte('filtro-argomento', argomenti, 'percorsi tematici');
}

// Elenco di caselle con nome completo (va a capo, mai troncato) e numero
// di documenti. Prima era un <select multiple>: i nomi lunghi venivano
// tagliati (due correnti del PCd'I risultavano identiche) e la scelta
// multipla richiedeva Ctrl/Cmd-clic, mai spiegato.
// Sopra le 10 voci compare un campo per restringere l'elenco.
function caselle(id) {
    const gruppo = document.getElementById(id);
    return gruppo ? Array.from(gruppo.querySelectorAll('input[type="checkbox"]')) : [];
}

function popolaSpunte(id, conteggi, nomePlurale) {
    const gruppo = document.getElementById(id);
    if (!gruppo) return;
    const selezionati = getSelectedValues(id);
    // Persone in ordine di cognome ("Brandirali, Aldo" sotto la B), come
    // nell'indice delle persone; le altre voci in ordine alfabetico.
    const chiave = v => ordineNomi[v] || v;
    const voci = Array.from(conteggi.keys()).sort((a, b) => chiave(a).localeCompare(chiave(b), 'it', { sensitivity: 'base' }));

    let html = '';
    if (voci.length > 10) {
        html += `<input type="search" class="spunte-cerca" aria-label="Restringi l'elenco delle ${escapeHtml(nomePlurale)}" placeholder="Restringi l'elenco…" data-solo-elenco>`;
    }
    html += '<ul class="spunte-elenco">';
    voci.forEach((voce, i) => {
        const n = conteggi.get(voce);
        const idCasella = `${id}-${i}`;
        // Il campo "Restringi l'elenco" trova la voce anche con le altre
        // forme del nome, che restano nascoste (es. "Lin Piao" -> Lin Biao).
        const testoCerca = normalizzaNome([voce].concat(varianti[voce] || []).join(' '));
        html += `<li class="spunta" data-cerca="${escapeHtml(testoCerca)}"><input type="checkbox" id="${idCasella}" value="${escapeHtml(voce)}"${selezionati.includes(voce) ? ' checked' : ''}>` +
            `<label for="${idCasella}"><span class="spunta__nome">${escapeHtml(voce)}</span>` +
            `<span class="spunta__conteggio" aria-label="${n === 1 ? '1 documento' : n + ' documenti'}">${n}</span></label></li>`;
    });
    html += '</ul>';
    gruppo.innerHTML = html;

    const cerca = gruppo.querySelector('.spunte-cerca');
    if (cerca) {
        cerca.addEventListener('input', function () {
            const q = normalizzaNome(this.value);
            gruppo.querySelectorAll('.spunta').forEach(li => {
                li.hidden = q !== '' && !(li.dataset.cerca || '').includes(q);
            });
        });
    }
}

// ============================================================
// APPLICAZIONE FILTRI
// ============================================================
// Unica fonte del filtraggio: usata sia da applicaFiltri() sia dai
// pulsanti di paginazione, per evitare derive tra le due copie.
// Gruppi di caselle e valori del documento che ciascuno filtra.
const GRUPPI_FILTRO = {
    'filtro-organizzazione': doc => doc.organizzazioni || [],
    'filtro-persona': doc => doc.persone || [],
    'filtro-tipo': doc => (doc.tipo ? [doc.tipo] : []),
    'filtro-argomento': doc => (Array.isArray(doc.serie) ? doc.serie : [])
};

function leggiStatoFiltri() {
    const selezioni = {};
    Object.keys(GRUPPI_FILTRO).forEach(id => { selezioni[id] = getSelectedValues(id); });
    return {
        selezioni,
        annoMin: parseInt(document.getElementById('filtro-anno-min').value, 10),
        annoMax: parseInt(document.getElementById('filtro-anno-max').value, 10),
        parole: paroleQuery(document.getElementById('filtro-testo').value)
    };
}

// Entro un gruppo le voci si sommano (o), tra gruppi si restringe (e).
// "escludi" ignora un gruppo: serve a contare le voci di quel gruppo.
function passaFiltri(doc, stato, escludi) {
    for (const id in GRUPPI_FILTRO) {
        if (id === escludi) continue;
        const scelti = stato.selezioni[id];
        if (scelti.length && !GRUPPI_FILTRO[id](doc).some(v => scelti.includes(v))) return false;
    }
    if (doc.anno && (doc.anno < stato.annoMin || doc.anno > stato.annoMax)) return false;
    if (stato.parole.length && !corrispondeRicerca(doc, stato.parole)) return false;
    return true;
}

function calcolaRisultati() {
    const stato = leggiStatoFiltri();
    let risultati = documenti.filter(doc => passaFiltri(doc, stato, null));
    
    // ORDINAMENTO: cronologico (predefinito), cronologico inverso o per
    // titolo. I documenti senza data restano sempre in fondo.
    const ordine = (document.getElementById('ordina-risultati') || {}).value || 'data';
    const perData = (a, b) => {
        const da = a.data_ordine || [9999, 1, 1];
        const db = b.data_ordine || [9999, 1, 1];
        if (da[0] !== db[0]) return da[0] - db[0];
        if (da[1] !== db[1]) return da[1] - db[1];
        return da[2] - db[2];
    };
    const perTitolo = (a, b) => (a.titolo || '').localeCompare(b.titolo || '', 'it', { sensitivity: 'base' });
    risultati.sort((a, b) => {
        if (ordine === 'titolo') return perTitolo(a, b);
        const senzaA = !a.data_ordine || a.data_ordine[0] === 9999;
        const senzaB = !b.data_ordine || b.data_ordine[0] === 9999;
        if (senzaA !== senzaB) return senzaA ? 1 : -1;
        const c = ordine === 'data-desc' ? perData(b, a) : perData(a, b);
        return c || perTitolo(a, b);
    });
    
    return risultati;
}

function applicaFiltri() {
    currentPage = 1; // Reset pagina alla prima quando i filtri cambiano
    aggiornaVista();
    aggiornaURLFiltri();  // Riflette lo stato corrente dei filtri nell'URL
}

function aggiornaVista() {
    mostraRisultati(calcolaRisultati());
    renderFiltriAttivi();     // Aggiorna la riga di chip riepilogo filtri
    aggiornaConteggiFiltri(); // Numeri accanto alle caselle
    aggiornaAvvisoForme();    // "Nel catalogo: Mao Zedong (anche ...)"
}

// ------------------------------------------------------------
// CONTEGGI DELLE CASELLE: seguono i risultati
// ------------------------------------------------------------
// Ogni numero dice quanti documenti si otterrebbero spuntando quella
// voce con gli altri filtri attivi (il proprio gruppo escluso, perche'
// dentro un gruppo le voci si sommano). Le voci a 0 si attenuano ma
// restano cliccabili e in ordine: l'elenco non salta sotto il dito.
function aggiornaConteggiFiltri() {
    const stato = leggiStatoFiltri();
    Object.keys(GRUPPI_FILTRO).forEach(id => {
        const gruppo = document.getElementById(id);
        if (!gruppo) return;
        const conteggi = new Map();
        documenti.forEach(doc => {
            if (!passaFiltri(doc, stato, id)) return;
            new Set(GRUPPI_FILTRO[id](doc)).forEach(v => conteggi.set(v, (conteggi.get(v) || 0) + 1));
        });
        gruppo.querySelectorAll('.spunta').forEach(li => {
            const casella = li.querySelector('input[type="checkbox"]');
            const numero = li.querySelector('.spunta__conteggio');
            if (!casella || !numero) return;
            const n = conteggi.get(casella.value) || 0;
            numero.textContent = n;
            numero.setAttribute('aria-label', n === 1 ? '1 documento' : `${n} documenti`);
            li.classList.toggle('spunta--zero', n === 0 && !casella.checked);
        });
    });
}

// ------------------------------------------------------------
// GRAFIE D'EPOCA NELLA RICERCA TESTUALE
// ------------------------------------------------------------
// Le altre forme del nome non entrano nei risultati della ricerca
// testuale (scelta del curatore). Se pero' la query contiene una di
// queste forme ("mao tse tung", "ciu en lai", "lin piao"), sopra i
// risultati compare la forma del catalogo con l'azione che raccoglie
// tutti i documenti collegati a quella persona o organizzazione.
function trovaFormaVariante(query) {
    const q = ' ' + normalizzaNome(query) + ' ';
    if (!q.trim()) return null;
    let trovata = null;
    Object.keys(varianti).forEach(nome => {
        (varianti[nome] || []).forEach(forma => {
            const f = normalizzaNome(forma);
            if (f && q.includes(' ' + f + ' ') && (!trovata || f.length > trovata.lunghezza)) {
                trovata = { nome, forma, lunghezza: f.length };
            }
        });
    });
    return trovata;
}

function aggiornaAvvisoForme() {
    const campo = document.getElementById('filtro-testo');
    const contenitore = document.getElementById('risultati-container');
    if (!campo || !contenitore) return;
    let avviso = document.getElementById('avviso-forma');

    const trovata = trovaFormaVariante(campo.value);
    let gruppoId = null;
    let casella = null;
    if (trovata) {
        ['filtro-persona', 'filtro-organizzazione'].some(id => {
            casella = caselle(id).find(c => c.value === trovata.nome) || null;
            if (casella) gruppoId = id;
            return Boolean(casella);
        });
    }
    if (!trovata || !casella || casella.checked) {
        if (avviso) avviso.hidden = true;
        return;
    }

    // Quanti documenti darebbe il filtro, con gli altri filtri attivi
    // e senza il testo cercato (che l'azione toglie).
    const stato = leggiStatoFiltri();
    stato.parole = [];
    stato.selezioni[gruppoId] = [trovata.nome];
    const n = documenti.filter(doc => passaFiltri(doc, stato, null)).length;

    if (!avviso) {
        avviso = document.createElement('p');
        avviso.id = 'avviso-forma';
        avviso.className = 'avviso-forma';
        contenitore.parentNode.insertBefore(avviso, contenitore);
    }
    const azione = n === 1 ? 'Vedi il documento collegato' : `Vedi i ${n} documenti collegati`;
    avviso.innerHTML =
        `<span class="avviso-forma__testo">Nel catalogo: <strong>${escapeHtml(trovata.nome)}</strong> ` +
        `<span class="avviso-forma__variante">(anche «${escapeHtml(trovata.forma)}»)</span></span>` +
        `<button type="button" class="avviso-forma__azione">${azione}` +
        '<svg class="ami-icona" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg></button>';
    avviso.hidden = false;
    avviso.querySelector('button').addEventListener('click', function () {
        casella.checked = true;
        campo.value = '';
        applicaFiltri();
        mettiFocusSuiRisultati();
    });
}

// Dopo un'azione che ridisegna l'elenco (pagina, forma del nome) il
// focus va sul conteggio dei risultati: senza, restava sul body.
function mettiFocusSuiRisultati() {
    const conteggio = document.getElementById('risultati-conteggio');
    if (!conteggio) return;
    conteggio.setAttribute('tabindex', '-1');
    conteggio.focus({ preventScroll: true });
}

function getSelectedValues(id) {
    return caselle(id).filter(c => c.checked).map(c => c.value);
}

// ============================================================
// CHIP FILTRI ATTIVI
// ============================================================
// Riepilogo cliccabile dei filtri correntemente applicati, mostrato
// sopra i risultati. Ogni chip rappresenta UN singolo valore
// selezionato (non l'intero gruppo di filtro) ed e' rimovibile
// singolarmente cliccando la ✕, senza dover aprire l'accordion
// corrispondente nella sidebar.
const FILTRO_LABELS = {
    'filtro-organizzazione': 'Organizzazione',
    'filtro-persona': 'Persona',
    'filtro-tipo': 'Tipologia',
    'filtro-argomento': 'Percorso tematico'
};

function creaChip(labelHtml, onRemove) {
    const chip = document.createElement('span');
    chip.className = 'filtro-chip';

    const labelSpan = document.createElement('span');
    labelSpan.className = 'filtro-chip-label';
    labelSpan.innerHTML = labelHtml;
    chip.appendChild(labelSpan);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'filtro-chip-remove';
    removeBtn.setAttribute('aria-label', 'Rimuovi filtro');
    removeBtn.textContent = '✕';
    removeBtn.addEventListener('click', onRemove);
    chip.appendChild(removeBtn);

    return chip;
}

function rimuoviValoreSelezionato(selectId, valore) {
    caselle(selectId).forEach(c => {
        if (c.value === valore) c.checked = false;
    });
    applicaFiltri();
}

function resetFiltroAnno() {
    const minSlider = document.getElementById('filtro-anno-min');
    const maxSlider = document.getElementById('filtro-anno-max');
    if (!minSlider || !maxSlider) return;

    minSlider.value = annoMin;
    maxSlider.value = annoMax;
    document.getElementById('anno-min-label').textContent = annoMin;
    document.getElementById('anno-max-label').textContent = annoMax;

    aggiornaTrackSlider();
    applicaFiltri();
}

function resetFiltroTesto() {
    const campoTesto = document.getElementById('filtro-testo');
    if (campoTesto) campoTesto.value = '';
    applicaFiltri();
}

function renderFiltriAttivi() {
    const container = document.getElementById('filtri-attivi');
    if (!container) return;

    container.innerHTML = '';
    let numeroFiltri = 0;

    // --- Filtri multi-select (organizzazione, persona, tipo, argomento) ---
    Object.keys(FILTRO_LABELS).forEach(selectId => {
        const valori = getSelectedValues(selectId);
        const attivi = document.getElementById('attivi-' + selectId.replace('filtro-', ''));
        if (attivi) attivi.textContent = valori.length ? ` · ${valori.length}` : '';
        valori.forEach(valore => {
            const labelHtml = `<strong>${escapeHtml(FILTRO_LABELS[selectId])}:</strong> ${escapeHtml(valore)}`;
            const chip = creaChip(labelHtml, () => rimuoviValoreSelezionato(selectId, valore));
            container.appendChild(chip);
            numeroFiltri++;
        });
    });

    // --- Filtro anno (solo se diverso dal range completo) ---
    const minSlider = document.getElementById('filtro-anno-min');
    const maxSlider = document.getElementById('filtro-anno-max');
    if (minSlider && maxSlider) {
        const minVal = parseInt(minSlider.value);
        const maxVal = parseInt(maxSlider.value);
        if (minVal !== annoMin || maxVal !== annoMax) {
            const labelHtml = `<strong>Anni:</strong> ${minVal}–${maxVal}`;
            const chip = creaChip(labelHtml, resetFiltroAnno);
            container.appendChild(chip);
            numeroFiltri++;
        }
    }

    // --- Filtro testo ---
    const campoTesto = document.getElementById('filtro-testo');
    if (campoTesto && campoTesto.value.trim()) {
        const labelHtml = `<strong>Testo:</strong> "${escapeHtml(campoTesto.value.trim())}"`;
        const chip = creaChip(labelHtml, resetFiltroTesto);
        container.appendChild(chip);
        numeroFiltri++;
    }

    // Un solo comando per azzerare: "Azzera filtri" nel pannello, mostrato
    // solo quando c'e' qualcosa da azzerare (ogni chip ha gia' la sua x).
    const azioni = document.getElementById('filtri-azioni');
    if (azioni) azioni.hidden = numeroFiltri === 0;
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
        container.innerHTML =
            '<div class="nessun-risultato">' +
            '<p><strong>Nessun documento corrisponde a questa ricerca.</strong></p>' +
            '<p>Prova a togliere un filtro, ad allargare l\'intervallo di anni o a cercare un termine più generico.</p>' +
            '<button type="button" class="riprova-btn" id="nessun-risultato-reset">Azzera filtri</button>' +
            '</div>';
        const azzera = document.getElementById('nessun-risultato-reset');
        if (azzera) azzera.addEventListener('click', resetFiltri);
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
    
    // Aggiorna conteggio - RIMOSSO "tra X di Y caricati"
    if (conteggio) {
        const quanti = totale === 1 ? '1 documento' : `${totale} documenti`;
        conteggio.textContent = totalPages > 1 ? `${quanti} · pagina ${currentPage} di ${totalPages}` : quanti;
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
                <div class="risultato-data">${escapeHtml(doc.data || 's.d.')}<span class="risultato-segnatura">${escapeHtml(doc.id)}</span></div>
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
    
    // Genera paginazione - RIMOSSO BOTTONE "CARICA ALTRI DOCUMENTI"
    if (paginazioneContainer) {
        generaIterfacciaPaginazione(paginazioneContainer, currentPage, totalPages);
        // Bottone "Carica altri documenti" rimosso: tutti i documenti sono già caricati
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
        const corrente = i === current ? ' aria-current="page"' : '';
        html += `<button class="pag-btn ${active}" data-page="${i}" aria-label="Pagina ${i}"${corrente}>${i}</button>`;
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
                aggiornaURLFiltri(true);
                
                // Riporta la vista in cima ai risultati: i pulsanti di paginazione
                // sono in fondo alla lista, senza questo l'utente resterebbe
                // scrollato in basso senza vedere i nuovi risultati. Il focus
                // segue la vista (il pulsante premuto non esiste piu').
                const testata = document.querySelector('.risultati-testata') || document.getElementById('risultati-container');
                if (testata) {
                    const riduci = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                    testata.scrollIntoView({ behavior: riduci ? 'auto' : 'smooth', block: 'start' });
                }
                mettiFocusSuiRisultati();
            }
        });
    });
}

// ============================================================
// RESET FILTRI
// ============================================================
function resetFiltri() {
    Object.keys(URL_PARAM_PER_SELECT).forEach(id => caselle(id).forEach(c => { c.checked = false; }));
    document.querySelectorAll('.spunte-cerca').forEach(campo => {
        campo.value = '';
        campo.dispatchEvent(new Event('input'));
    });
    
    document.getElementById('filtro-testo').value = '';
    document.getElementById('filtro-anno-min').value = annoMin;
    document.getElementById('filtro-anno-max').value = annoMax;
    document.getElementById('anno-min-label').textContent = annoMin;
    document.getElementById('anno-max-label').textContent = annoMax;

    aggiornaTrackSlider();
    
    currentPage = 1;
    applicaFiltri();
}

// ============================================================
// AVVIO
// ============================================================
// ============================================================
// FILTRI RICHIUDIBILI SU MOBILE
// ============================================================
// Sotto i 768px il pannello filtri occupava l'intero primo schermo e i
// risultati partivano sotto la piega. Su mobile i cinque gruppi di
// filtro partono chiusi dietro un pulsante (resta visibile la ricerca
// testuale, la piu' usata); il pulsante mostra quanti filtri sono attivi.
// Senza JS la classe non viene mai applicata: tutto resta visibile.
function inizializzaFiltriMobile() {
    const sidebar = document.getElementById('filtri-sidebar');
    const bottone = document.getElementById('filtri-mostra');
    const conteggio = document.getElementById('filtri-mostra-conteggio');
    const chips = document.getElementById('filtri-attivi');
    if (!sidebar || !bottone) return;

    const etichetta = bottone.querySelector('.filtri-mostra__etichetta');
    const mq = window.matchMedia('(max-width: 768px)');

    // Lo stato CHIUSO e' quello predefinito e lo applica il CSS (html.ami-js,
    // impostato nel <head>): niente salto di layout all'arrivo dello script.
    // Qui si aggiunge/toglie solo la classe che APRE il pannello.
    function imposta(chiusi) {
        sidebar.classList.toggle('filtri--aperti', !chiusi);
        bottone.setAttribute('aria-expanded', chiusi ? 'false' : 'true');
        if (etichetta) etichetta.textContent = chiusi ? 'Mostra filtri' : 'Nascondi filtri';
    }

    function aggiornaConteggio() {
        if (!conteggio || !chips) return;
        const n = chips.querySelectorAll('.filtro-chip').length;
        conteggio.textContent = n ? `${n} attiv${n === 1 ? 'o' : 'i'}` : '';
        const nFlottante = document.querySelector('.filtri-flottante__conteggio');
        if (nFlottante) nFlottante.textContent = n ? String(n) : '';
    }

    bottone.addEventListener('click', function () {
        imposta(sidebar.classList.contains('filtri--aperti'));
    });

    // Pulsante "Filtri" in basso, nella zona del pollice: compare su
    // telefono quando il pannello filtri e' uscito dallo schermo (l'elenco
    // dei risultati supera i 4.000px). Riporta al pannello e lo apre.
    const flottante = document.createElement('button');
    flottante.type = 'button';
    flottante.className = 'filtri-flottante';
    flottante.hidden = true;
    flottante.setAttribute('aria-controls', 'filtri-corpo');
    flottante.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/></svg>' +
        '<span>Filtri</span><span class="filtri-flottante__conteggio"></span>';
    document.body.appendChild(flottante);
    flottante.addEventListener('click', function () {
        imposta(false);
        const riduci = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        sidebar.scrollIntoView({ behavior: riduci ? 'auto' : 'smooth', block: 'start' });
        bottone.focus({ preventScroll: true });
    });
    let sidebarVisibile = true;
    const aggiornaFlottante = function () {
        flottante.hidden = !mq.matches || sidebarVisibile;
    };
    if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (voci) {
            sidebarVisibile = voci[0].isIntersecting;
            aggiornaFlottante();
        }).observe(sidebar);
    }

    // Su desktop il pannello e' sempre aperto; si richiude tornando su mobile.
    const suCambio = function () {
        imposta(mq.matches);
        if (typeof aggiornaFlottante === 'function') aggiornaFlottante();
    };
    if (mq.addEventListener) mq.addEventListener('change', suCambio);
    else if (mq.addListener) mq.addListener(suCambio);
    imposta(mq.matches);

    if (chips && 'MutationObserver' in window) {
        new MutationObserver(aggiornaConteggio).observe(chips, { childList: true, subtree: true });
    }
    aggiornaConteggio();
}

// Lo script e' incluso in tutte le pagine (mkdocs.yml): il catalogo
// (documenti.json, ~100 KB) si scarica solo dove c'e' l'elenco dei risultati.
document.addEventListener('DOMContentLoaded', function () {
    if (!document.getElementById('risultati-container')) return;
    // Il ripristino lo fa lo script, a risultati disegnati: quello del
    // browser arriverebbe prima, su una pagina ancora vuota.
    if ('scrollRestoration' in window.history) window.history.scrollRestoration = 'manual';
    window.addEventListener('pagehide', salvaPosizione);
    // Indietro/Avanti tra le pagine dei risultati: lo stato si rilegge
    // dall'URL della voce di cronologia.
    window.addEventListener('popstate', function () {
        if (!documenti.length) return;
        precompilaRicercaDaURL();
        const pagina = parseInt(new URLSearchParams(window.location.search).get('pagina'), 10);
        currentPage = !isNaN(pagina) && pagina > 1 ? pagina : 1;
        aggiornaVista();
    });
    inizializzaFiltriMobile();
    caricaDati();
});