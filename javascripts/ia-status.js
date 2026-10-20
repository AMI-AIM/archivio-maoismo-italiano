/**
 * AVVISO DISPONIBILITÀ INTERNET ARCHIVE — AMI
 * ============================================================
 * L'archivio si appoggia a Internet Archive (IA) per gran parte dei
 * contenuti (visore delle schede, immagini a piena risoluzione della
 * galleria). Se IA è irraggiungibile, degradata o troppo lenta, il
 * lettore potrebbe pensare che il problema sia del sito AMI: questo
 * script lo dice esplicitamente, e distingue tre situazioni:
 *
 *   guasto          IA non risponde o risponde con errori;
 *   non disponibile IA risponde, ma il documento della scheda al momento
 *                   non c'è (manutenzione, record vuoto o oscurato);
 *   offline         il browser non ha rete: la colpa non è di IA.
 *
 * SEGNALI
 *
 * 1. CONTROLLO DEL DOCUMENTO (schede con visore)
 *    a) Miniatura del documento (archive.org/services/img/<id>) caricata
 *       con un <img>: passa per gli stessi server che conservano i file
 *       del visore, quindi si accorge anche dei guasti parziali che
 *       lasciano in piedi archive.org. Un <img> dà un 'error' affidabile
 *       sia per la rete sia per le risposte 4xx/5xx; il tempo massimo lo
 *       mettiamo noi.
 *    b) Metadati del documento (archive.org/metadata/<id>) letti con
 *       fetch: un oggetto vuoto o un record oscurato vuol dire "non
 *       disponibile", un 5xx vuol dire guasto. Se il browser non può
 *       leggere la risposta (rete, CORS) il dato si ignora: decide la
 *       miniatura.
 * 2. CONTROLLO GENERICO (pagine senza visore, es. galleria)
 *    L'icona di archive.org, come prima, con cache di sessione.
 * 3. IMMAGINI: evento 'ami:lazy-error' di lazy-loading.js; 2 errori
 *    di archive.org in 15 s fanno comparire il banner.
 * 4. VISORE: se l'iframe non finisce di caricarsi entro 30 s, guasto.
 *    Se poi arriva lo stesso, l'avviso sparisce e il visore si riapre.
 *
 * I tempi massimi contano solo mentre la scheda del browser è visibile:
 * una scheda aperta "in background" (frequente: si aprono molti
 * documenti dall'archivio) può rimandare il caricamento del visore
 * finché non la si guarda, e non deve trovarsi un guasto che non c'è.
 *
 * DOVE: solo sulle pagine che caricano davvero qualcosa da IA. Sulle
 * schede l'avviso sta dentro il visore (niente banner); altrove è il
 * banner in cima.
 *
 * LIMITI NOTI
 * - un firewall o un'estensione che blocca archive.org sembra un guasto;
 * - se IA serve una pagina d'errore dentro il visore, il visore risulta
 *   caricato: lo intercettano solo i metadati (punto 1b), se leggibili.
 */
(function () {
  'use strict';

  // ------------------------------------------------------------
  // CONFIGURAZIONE
  // ------------------------------------------------------------
  var PROBE_URL_BASE = 'https://archive.org/favicon.ico';
  var MINIATURA_URL = 'https://archive.org/services/img/';
  var METADATI_URL = 'https://archive.org/metadata/';
  // Soglie larghe: su una connessione lenta IA puo' metterci parecchio,
  // e il guasto chiude il visore. Tempi contati solo a scheda visibile.
  var PROBE_TIMEOUT_MS = 15000;
  var METADATI_TIMEOUT_MS = 15000;
  var IFRAME_TIMEOUT_MS = 30000;
  var PROBE_CACHE_KEY = 'ami_ia_probe_status';
  var PROBE_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minuti

  var IMG_ERROR_THRESHOLD = 2;        // n. errori immagine IA per scattare
  var IMG_ERROR_WINDOW_MS = 15000;    // finestra temporale per il conteggio

  var DISMISS_KEY = 'ami_ia_status_dismissed';

  // Priorita': un avviso piu' preciso sostituisce uno piu' generico.
  var PRIORITA = { offline: 1, guasto: 2, nondisponibile: 3 };

  var TESTI_VISORE = {
    guasto: 'I documenti di questo archivio sono ospitati su Internet Archive, ' +
      'piattaforma al momento instabile o irraggiungibile. Se i documenti non si caricano, il problema è ' +
      'temporaneo e non riguarda il solo sito AMI. Riprovare più tardi.',
    nondisponibile: 'Internet Archive risponde, ma al momento non rende disponibile questo documento. ' +
      'Il problema riguarda Internet Archive, non il sito AMI: riprovare più tardi.',
    offline: 'Sembra che il dispositivo sia offline. Il documento, ospitato su Internet Archive, ' +
      'si caricherà quando torna la connessione.'
  };

  var TESTI_BANNER = {
    guasto: {
      lungo: 'I documenti di questo archivio sono ospitati su Internet Archive, piattaforma al momento instabile o irraggiungibile. ' +
        'Se i documenti non si caricano, il problema è temporaneo e non riguarda il solo sito AMI. Riprovare più tardi.',
      breve: 'Internet Archive è instabile: i documenti potrebbero non caricarsi.'
    },
    offline: {
      lungo: 'Sembra che il dispositivo sia offline: i documenti e le immagini ospitati su Internet Archive ' +
        'si caricheranno quando torna la connessione.',
      breve: 'Sei offline: i documenti si caricheranno al ritorno della rete.'
    }
  };

  // Elementi che dipendono da Internet Archive: senza nessuno di questi
  // la pagina non ha nulla da avvisare.
  var SELETTORE_CONTENUTI_IA = [
    '.universal-embed',
    'img[src*="archive.org"]',
    'img[data-src*="archive.org"]',
    '[data-full-src*="archive.org"]'
  ].join(',');

  // ------------------------------------------------------------
  // UTILITY
  // ------------------------------------------------------------
  // sessionStorage sicuro (puo' mancare, es. navigazione privata)
  function ssGet(key) {
    try {
      return sessionStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function ssSet(key, value) {
    try {
      sessionStorage.setItem(key, value);
    } catch (e) {
      /* ignora: si ripete il controllo alla prossima pagina */
    }
  }

  function offline() {
    return navigator.onLine === false;
  }

  // Tipo di avviso per un problema di rete: se il browser sa di essere
  // offline la colpa non e' di Internet Archive.
  function tipoGuasto() {
    return offline() ? 'offline' : 'guasto';
  }

  // Timer che conta solo mentre la pagina e' visibile: si ferma quando
  // la scheda del browser passa in secondo piano e riparte al ritorno.
  function timerVisibile(fn, ms) {
    var restante = ms;
    var inizio = 0;
    var id = null;
    var finito = false;

    function avvia() {
      if (finito || id !== null || document.visibilityState === 'hidden') return;
      inizio = Date.now();
      id = window.setTimeout(function () {
        id = null;
        finito = true;
        document.removeEventListener('visibilitychange', suCambio);
        fn();
      }, restante);
    }
    function ferma() {
      if (id === null) return;
      window.clearTimeout(id);
      id = null;
      restante = Math.max(0, restante - (Date.now() - inizio));
    }
    function suCambio() {
      if (document.visibilityState === 'hidden') ferma();
      else avvia();
    }

    document.addEventListener('visibilitychange', suCambio);
    avvia();
    return {
      annulla: function () {
        finito = true;
        ferma();
        document.removeEventListener('visibilitychange', suCambio);
      }
    };
  }

  // Identificativo IA dall'indirizzo del visore (archive.org/embed/<id>)
  function identificativo(iframe) {
    var m = /archive\.org\/embed\/([^/?#]+)/.exec(iframe.getAttribute('src') || '');
    return m ? decodeURIComponent(m[1]) : null;
  }

  // ------------------------------------------------------------
  // BANNER (pagine senza visore). Stile in extra.css, sezione
  // "STATO DI INTERNET ARCHIVE".
  // ------------------------------------------------------------
  function eDismisso() {
    return ssGet(DISMISS_KEY) === '1';
  }

  function segnaDismisso() {
    ssSet(DISMISS_KEY, '1');
  }

  function testiBanner(banner, tipo) {
    var t = TESTI_BANNER[tipo] || TESTI_BANNER.guasto;
    banner.dataset.tipo = tipo;
    banner.querySelector('.ia-status-banner__lungo').textContent = t.lungo;
    banner.querySelector('.ia-status-banner__breve').textContent = t.breve;
  }

  function mostraAvviso(tipo) {
    tipo = tipo || 'guasto';
    var esistente = document.getElementById('ia-status-banner');
    if (esistente) {
      // Un banner "offline" diventa "guasto" se la rete e' tornata.
      if (esistente.dataset.tipo !== tipo) testiBanner(esistente, tipo);
      return;
    }
    if (eDismisso()) return;

    var banner = document.createElement('div');
    banner.id = 'ia-status-banner';
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');
    banner.innerHTML =
      '<div class="ia-status-banner__inner">' +
        '<svg class="ia-status-banner__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
          '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>' +
        '</svg>' +
        '<span class="ia-status-banner__testo">' +
          '<span class="ia-status-banner__lungo"></span>' +
          '<span class="ia-status-banner__breve" aria-hidden="true"></span>' +
        '</span>' +
        '<button type="button" class="ia-status-banner__chiudi" aria-label="Chiudi avviso">' +
          '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
            '<path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>' +
          '</svg>' +
        '</button>' +
      '</div>';
    testiBanner(banner, tipo);

    // Dopo il link "Vai al contenuto": il primo Tab resta quello.
    var salto = document.querySelector('body > .md-skip');
    if (salto && salto.nextSibling) {
      document.body.insertBefore(banner, salto.nextSibling);
    } else {
      document.body.insertBefore(banner, document.body.firstChild);
    }

    banner.querySelector('.ia-status-banner__chiudi').addEventListener('click', function () {
      banner.remove();
      segnaDismisso();
    });
  }

  function togliBannerOffline() {
    var banner = document.getElementById('ia-status-banner');
    if (banner && banner.dataset.tipo === 'offline') banner.remove();
  }

  // ------------------------------------------------------------
  // CACHE DEL CONTROLLO GENERICO
  // ------------------------------------------------------------
  function leggiCacheProbe() {
    var raw = ssGet(PROBE_CACHE_KEY);
    if (!raw) return null;
    try {
      var parsed = JSON.parse(raw);
      if (!parsed || typeof parsed.timestamp !== 'number') return null;
      if (Date.now() - parsed.timestamp > PROBE_CACHE_TTL_MS) return null;
      return parsed;
    } catch (e) {
      return null;
    }
  }

  function scriviCacheProbe(raggiungibile) {
    ssSet(PROBE_CACHE_KEY, JSON.stringify({
      raggiungibile: raggiungibile,
      timestamp: Date.now()
    }));
  }

  // Carica un'immagine da IA con un tempo massimo (contato a scheda
  // visibile). esito: 'ok', 'errore' (risposta d'errore o rete) o
  // 'scaduto' (nessuna risposta in tempo).
  function provaImmagine(url, ms, esito) {
    var risolto = false;
    var img = new Image();
    var timer = timerVisibile(function () {
      if (risolto) return;
      risolto = true;
      img.src = '';
      esito('scaduto');
    }, ms);
    img.onload = function () {
      if (risolto) return;
      risolto = true;
      timer.annulla();
      esito('ok');
    };
    img.onerror = function () {
      if (risolto) return;
      risolto = true;
      timer.annulla();
      esito('errore');
    };
    // Cache-busting: evita che il browser risponda dalla cache locale.
    img.src = url + (url.indexOf('?') === -1 ? '?' : '&') + '_=' + Date.now();
  }

  // ------------------------------------------------------------
  // 1. CONTROLLO DEL DOCUMENTO (schede con visore)
  // ------------------------------------------------------------
  function controllaDocumento(iframe) {
    var id = identificativo(iframe);
    if (!id) return;

    // a) Miniatura: raggiungibilita' dei server dei file
    provaImmagine(MINIATURA_URL + encodeURIComponent(id), PROBE_TIMEOUT_MS, function (esito) {
      if (esito === 'ok') {
        scriviCacheProbe(true);
        return;
      }
      // Solo un errore vero si memorizza: una risposta lenta no.
      if (esito === 'errore' && !offline()) scriviCacheProbe(false);
      segnalaVisore(iframe, tipoGuasto());
    });

    // b) Metadati: il documento c'e'? Se la risposta non e' leggibile
    //    (rete, CORS) non si conclude nulla.
    if (!window.fetch) return;
    var controller = window.AbortController ? new AbortController() : null;
    var timer = timerVisibile(function () {
      if (controller) controller.abort();
    }, METADATI_TIMEOUT_MS);
    fetch(METADATI_URL + encodeURIComponent(id), {
      cache: 'no-store',
      credentials: 'omit',
      signal: controller ? controller.signal : undefined
    }).then(function (risposta) {
      timer.annulla();
      if (risposta.status >= 500) {
        segnalaVisore(iframe, 'guasto');
        return null;
      }
      if (!risposta.ok) return null;
      return risposta.json();
    }).then(function (dati) {
      if (!dati) return;
      var vuoto = typeof dati === 'object' && Object.keys(dati).length === 0;
      if (vuoto || dati.is_dark === true) {
        segnalaVisore(iframe, 'nondisponibile');
      }
    }).catch(function () {
      timer.annulla();
      /* rete, CORS o tempo scaduto: decide la miniatura */
    });
  }

  // ------------------------------------------------------------
  // 2. CONTROLLO GENERICO (pagine senza visore)
  // ------------------------------------------------------------
  function controlloGenerico(ignoraCache) {
    var cache = ignoraCache ? null : leggiCacheProbe();
    if (cache) {
      if (!cache.raggiungibile) mostraAvviso(tipoGuasto());
      return;
    }
    provaImmagine(PROBE_URL_BASE, PROBE_TIMEOUT_MS, function (esito) {
      if (esito === 'ok') {
        scriviCacheProbe(true);
        return;
      }
      if (esito === 'errore' && !offline()) scriviCacheProbe(false);
      mostraAvviso(tipoGuasto());
    });
  }

  // ------------------------------------------------------------
  // 3. MONITORAGGIO IMMAGINI (evento ami:lazy-error)
  // ------------------------------------------------------------
  var erroriImmagineTimestamps = [];

  function gestisciErroreImmagine(event) {
    var img = event.target;
    if (!img) return;

    // Al momento dell'errore definitivo l'immagine conserva ancora
    // data-src / data-src-fallback (lazy-loading.js li toglie solo in
    // caso di successo): si verifica che puntasse a archive.org.
    var src = img.getAttribute('data-src') || img.getAttribute('data-src-fallback') || img.currentSrc || img.src || '';
    if (!/archive\.org/i.test(src)) return;
    // Sulle schede con il visore l'avviso sta nel visore: niente banner.
    if (document.querySelector('.universal-embed')) return;

    var ora = Date.now();
    erroriImmagineTimestamps.push(ora);
    erroriImmagineTimestamps = erroriImmagineTimestamps.filter(function (t) {
      return ora - t <= IMG_ERROR_WINDOW_MS;
    });

    if (erroriImmagineTimestamps.length >= IMG_ERROR_THRESHOLD) {
      mostraAvviso(tipoGuasto());
    }
  }

  // ------------------------------------------------------------
  // 4. VISORE (.universal-embed)
  // ------------------------------------------------------------
  function sorvegliaIframe(iframe) {
    var caricato = false;

    var timer = timerVisibile(function () {
      if (caricato) return;
      // Nessun 'load' entro la soglia: mancata risposta da IA.
      segnalaVisore(iframe, tipoGuasto());
    }, IFRAME_TIMEOUT_MS);

    iframe.addEventListener('load', function () {
      caricato = true;
      timer.annulla();
      // Arrivato dopo un guasto (rete lenta, falso allarme): si riapre.
      ripristinaVisore(iframe);
    }, { once: true });

    iframe.addEventListener('error', function () {
      caricato = true;
      timer.annulla();
      segnalaVisore(iframe, tipoGuasto());
    }, { once: true });
  }

  function contenitoreDi(iframe) {
    return iframe.closest('.embed-container') || iframe.parentNode;
  }

  // Avviso dentro il visore. Se c'e' gia', viene sostituito solo da uno
  // piu' preciso (offline < guasto < non disponibile).
  function segnalaVisore(iframe, tipo) {
    var contenitore = contenitoreDi(iframe);
    if (!contenitore) return;
    var visore = contenitore.querySelector('.embed-visore');
    var avviso = contenitore.querySelector('.ia-visore-avviso');

    // Visore gia' caricato: un controllo fallito dopo (miniatura assente,
    // rete a singhiozzo) non deve coprire un documento che si vede. Fa
    // eccezione "non disponibile": allora il visore mostra la pagina
    // d'errore di IA e l'avviso spiega di chi e' il problema.
    if (tipo !== 'nondisponibile' && visore && visore.classList.contains('embed-visore--pronto')) return;

    if (avviso) {
      var attuale = contenitore.dataset.iaAvviso;
      if (PRIORITA[tipo] > (PRIORITA[attuale] || 0)) {
        contenitore.dataset.iaAvviso = tipo;
        avviso.querySelector('.ia-visore-avviso__testo').textContent = TESTI_VISORE[tipo];
      }
      return;
    }

    // Il link diretto a Internet Archive c'e' gia' nel piede del visore
    // ("Apri su Internet Archive"): qui non si ripete.
    avviso = document.createElement('div');
    avviso.className = 'ia-visore-avviso';
    avviso.setAttribute('role', 'status');
    avviso.innerHTML =
      '<p class="ia-visore-avviso__testo"></p>' +
      '<div class="ia-visore-avviso__azioni">' +
        '<button type="button" class="ia-visore-avviso__riprova">Riprova</button>' +
      '</div>';
    avviso.querySelector('.ia-visore-avviso__testo').textContent = TESTI_VISORE[tipo];
    contenitore.dataset.iaAvviso = tipo;
    contenitore.insertBefore(avviso, contenitore.firstChild);
    contenitore.classList.add('embed-container--guasto');
    // Il segnale di attesa (documenti.js) sparisce col guasto: il visore
    // non e' piu' "in caricamento" per i lettori di schermo.
    if (visore) visore.removeAttribute('aria-busy');

    avviso.querySelector('.ia-visore-avviso__riprova').addEventListener('click', function () {
      riprova(iframe);
      // Il focus era sul pulsante appena rimosso: va sul visore.
      var bersaglio = visore || iframe;
      if (!bersaglio.hasAttribute('tabindex')) bersaglio.setAttribute('tabindex', '-1');
      bersaglio.focus({ preventScroll: true });
    });
  }

  function togliAvviso(contenitore) {
    var avviso = contenitore.querySelector('.ia-visore-avviso');
    if (avviso) avviso.remove();
    contenitore.classList.remove('embed-container--guasto');
    delete contenitore.dataset.iaAvviso;
  }

  // Il visore e' arrivato dopo l'avviso: si toglie, tranne quando IA ha
  // detto che il documento non c'e' (il visore mostra allora la sua
  // pagina d'errore, l'avviso spiega di chi e' il problema).
  function ripristinaVisore(iframe) {
    var contenitore = contenitoreDi(iframe);
    if (!contenitore || !contenitore.classList.contains('embed-container--guasto')) return;
    if (contenitore.dataset.iaAvviso === 'nondisponibile') return;
    togliAvviso(contenitore);
  }

  function riprova(iframe) {
    var contenitore = contenitoreDi(iframe);
    var visore = contenitore && contenitore.querySelector('.embed-visore');
    if (contenitore) togliAvviso(contenitore);
    // Il segnale di attesa riparte da capo (documenti.js ascolta l'evento:
    // rimette "Caricamento...", aria-busy e il tempo per "lento"). Va
    // prima del ricaricamento, che a fine corsa segna il visore pronto.
    if (visore) {
      visore.dispatchEvent(new CustomEvent('ami:visore-riprova', { bubbles: true }));
    }
    // Ricarica riassegnando lo stesso indirizzo (niente passaggio da
    // about:blank: il suo "load" segnerebbe subito il visore pronto).
    iframe.setAttribute('src', iframe.getAttribute('src'));
    sorvegliaIframe(iframe);
    controllaDocumento(iframe);
  }

  // ------------------------------------------------------------
  // RITORNO DELLA RETE: si riprova da soli
  // ------------------------------------------------------------
  function suOnline() {
    togliBannerOffline();
    document.querySelectorAll('.universal-embed').forEach(function (iframe) {
      var contenitore = contenitoreDi(iframe);
      if (contenitore && contenitore.dataset.iaAvviso === 'offline') riprova(iframe);
    });
  }

  // ------------------------------------------------------------
  // AVVIO
  // ------------------------------------------------------------
  function init() {
    if (!document.querySelector(SELETTORE_CONTENUTI_IA)) return;
    var iframes = document.querySelectorAll('.universal-embed');
    if (iframes.length) {
      iframes.forEach(function (iframe) {
        sorvegliaIframe(iframe);
        controllaDocumento(iframe);
      });
    } else {
      controlloGenerico();
    }
    document.addEventListener('ami:lazy-error', gestisciErroreImmagine, { passive: true });
    window.addEventListener('online', suOnline);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
