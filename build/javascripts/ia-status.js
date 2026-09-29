/**
 * AVVISO DISPONIBILITÀ INTERNET ARCHIVE — AMI
 * ============================================================
 * L'archivio si appoggia a Internet Archive (IA) per gran parte dei
 * contenuti (embed multimediali, testi, immagini, copertine). Se IA
 * è irraggiungibile, degradata o troppo lenta, l'utente potrebbe
 * pensare che il problema sia del sito AMI stesso: questo script
 * mostra un avviso esplicito in cima alla pagina quando rileva
 * indizi di malfunzionamento da parte di IA.
 *
 * STRATEGIA A PIÙ SEGNALI (un singolo probe generico intercetta solo
 * i blackout totali, non le degradazioni parziali): questo script
 * combina tre fonti di segnale indipendenti, ciascuna con soglie
 * proprie, per coprire meglio gli scenari reali:
 *
 * 1. PROBE DI RAGGIUNGIBILITÀ (attivo su ogni pagina)
 *    Carica un'immagine leggera da archive.org con un tag <img>
 *    creato via JS (non fetch): a differenza di fetch in modalità
 *    'no-cors' (che spesso risulta "riuscito" anche su risposte di
 *    errore HTTP, essendo una risposta opaca), un tag <img> genera
 *    un evento 'error' affidabile sia su errori di rete sia su
 *    risposte HTTP 4xx/5xx, perché il browser non riesce a
 *    decodificare l'immagine. Ha anche un timeout manuale, perché
 *    <img> non ne ha uno nativo.
 *
 * 2. MONITORAGGIO IMMAGINI (attivo sulle pagine con immagini IA)
 *    Si aggancia all'evento 'ami:lazy-error', già emesso da
 *    lazy-loading.js quando un'immagine fallisce definitivamente
 *    (dopo aver esaurito anche l'eventuale fallback). Se n. errori
 *    riconducibili a archive.org si accumulano in una finestra
 *    breve, è un indizio che il problema è sistemico e non di un
 *    singolo file mancante (quel caso resta gestito a parte dai
 *    fallback già presenti in documenti.css/lazy-loading.js).
 *
 * 3. MONITORAGGIO IFRAME (attivo sulle schede documento con embed)
 *    Se l'iframe .universal-embed non emette 'load' entro una
 *    soglia di tempo, è un segnale di mancata risposta da IA.
 *
 * LIMITI NOTI (nessun sistema client-side può coprire tutto):
 * - non distingue "IA giù" da problemi di rete locali dell'utente
 *   (adblocker, VPN, firewall aziendale che blocca archive.org);
 * - il monitoraggio iframe rileva la mancata risposta di rete, ma
 *   non un contenuto d'errore renderizzato correttamente da IA
 *   (in quel caso l'iframe emette comunque 'load');
 * - la cache di sessione del probe (punto 1) potrebbe ritardare la
 *   rilevazione di un'interruzione iniziata a metà sessione: per
 *   questo i segnali reattivi (punti 2-3) restano sempre attivi,
 *   indipendentemente dalla cache del probe.
 */
(function () {
  'use strict';

  // ------------------------------------------------------------
  // CONFIGURAZIONE
  // ------------------------------------------------------------
  var PROBE_URL_BASE = 'https://archive.org/favicon.ico';
  var PROBE_TIMEOUT_MS = 7000;
  var PROBE_CACHE_KEY = 'ami_ia_probe_status';
  var PROBE_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minuti

  var IMG_ERROR_THRESHOLD = 2;        // n. errori immagine IA per scattare
  var IMG_ERROR_WINDOW_MS = 15000;    // finestra temporale per il conteggio

  var IFRAME_TIMEOUT_MS = 15000;      // tempo massimo di attesa per l'iframe

  var DISMISS_KEY = 'ami_ia_status_dismissed';

  var bannerMostrato = false;

  // ------------------------------------------------------------
  // UTILITY: sessionStorage sicuro (può non essere disponibile,
  // es. modalità privata restrittiva su alcuni browser)
  // ------------------------------------------------------------
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
      /* ignora: nessun problema, si ripete il controllo alla prossima pagina */
    }
  }

  function eDismisso() {
    return ssGet(DISMISS_KEY) === '1';
  }

  function segnaDismisso() {
    ssSet(DISMISS_KEY, '1');
  }

  // ------------------------------------------------------------
  // BANNER: creazione e stile
  // ------------------------------------------------------------
  function iniettaStile() {
    if (document.getElementById('ia-status-banner-style')) return;
    var style = document.createElement('style');
    style.id = 'ia-status-banner-style';
    style.textContent = [
      '#ia-status-banner {',
      '  position: sticky;',
      '  top: 0;',
      '  z-index: 1000;',
      '  background: #7a4a00;',
      '  color: #fff8ec;',
      '  font-family: var(--ami-font-label, "Archivo", sans-serif);',
      '  box-shadow: 0 2px 10px rgba(0,0,0,0.25);',
      '}',
      '.ia-status-banner__inner {',
      '  max-width: 1200px;',
      '  margin: 0 auto;',
      '  padding: 0.6rem 1rem;',
      '  display: flex;',
      '  align-items: center;',
      '  gap: 0.7rem;',
      '}',
      '.ia-status-banner__icon {',
      '  flex: 0 0 auto;',
      '  font-size: 1.1rem;',
      '}',
      '.ia-status-banner__testo {',
      '  flex: 1;',
      '  font-size: 0.82rem;',
      '  line-height: 1.4;',
      '}',
      '.ia-status-banner__chiudi {',
      '  flex: 0 0 auto;',
      '  background: transparent;',
      '  border: 1px solid rgba(255,255,255,0.5);',
      '  color: inherit;',
      '  border-radius: 4px;',
      '  padding: 0.15rem 0.5rem;',
      '  font-size: 0.8rem;',
      '  cursor: pointer;',
      '  line-height: 1;',
      '}',
      '.ia-status-banner__chiudi:hover {',
      '  background: rgba(255,255,255,0.15);',
      '}',
      '@media (max-width: 600px) {',
      '  .ia-status-banner__inner {',
      '    padding: 0.5rem 0.7rem;',
      '  }',
      '  .ia-status-banner__testo {',
      '    font-size: 0.75rem;',
      '  }',
      '}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function mostraAvviso() {
    if (eDismisso() || bannerMostrato) return;
    if (document.getElementById('ia-status-banner')) return;

    bannerMostrato = true;

    var banner = document.createElement('div');
    banner.id = 'ia-status-banner';
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');
    banner.innerHTML =
      '<div class="ia-status-banner__inner">' +
        '<span class="ia-status-banner__icon" aria-hidden="true">⚠️</span>' +
        '<span class="ia-status-banner__testo">' +
          'I documenti di questo archivio sono ospitati su Internet Archive, piattaforma al momento instabile o irraggiungibile. ' +
          'Se i documenti non si caricano, il problema è temporaneo e non riguarda il solo sito AMI. Riprovare più tardi.' +
        '</span>' +
        '<button type="button" class="ia-status-banner__chiudi" aria-label="Chiudi avviso">✕</button>' +
      '</div>';

    document.body.insertBefore(banner, document.body.firstChild);

    var chiudiBtn = banner.querySelector('.ia-status-banner__chiudi');
    if (chiudiBtn) {
      chiudiBtn.addEventListener('click', function () {
        banner.remove();
        bannerMostrato = false;
        segnaDismisso();
      });
    }

    iniettaStile();
  }

  // ------------------------------------------------------------
  // SEGNALE 1: PROBE DI RAGGIUNGIBILITÀ (via <img>, con cache)
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

  function eseguiProbe() {
    var cache = leggiCacheProbe();
    if (cache) {
      if (!cache.raggiungibile) {
        mostraAvviso();
      }
      return;
    }

    var risolto = false;
    var img = new Image();
    var timeoutId = setTimeout(function () {
      if (risolto) return;
      risolto = true;
      scriviCacheProbe(false);
      mostraAvviso();
    }, PROBE_TIMEOUT_MS);

    img.onload = function () {
      if (risolto) return;
      risolto = true;
      clearTimeout(timeoutId);
      scriviCacheProbe(true);
    };

    img.onerror = function () {
      if (risolto) return;
      risolto = true;
      clearTimeout(timeoutId);
      scriviCacheProbe(false);
      mostraAvviso();
    };

    // Cache-busting: evita che il browser risponda da cache locale
    // senza generare traffico reale verso archive.org.
    img.src = PROBE_URL_BASE + '?_=' + Date.now();
  }

  // ------------------------------------------------------------
  // SEGNALE 2: MONITORAGGIO IMMAGINI (evento ami:lazy-error)
  // ------------------------------------------------------------
  var erroriImmagineTimestamps = [];

  function eDominioArchiveOrg(url) {
    if (!url) return false;
    return /archive\.org/i.test(url);
  }

  function gestisciErroreImmagine(event) {
    var img = event.target;
    if (!img) return;

    // Al momento dell'errore definitivo, l'immagine conserva ancora
    // gli attributi data-src / data-src-fallback (rimossi solo in
    // caso di successo da lazy-loading.js), quindi possiamo verificare
    // se la fonte fallita puntava a archive.org.
    var src = img.getAttribute('data-src') || img.getAttribute('data-src-fallback') || img.currentSrc || img.src || '';
    if (!eDominioArchiveOrg(src)) return;

    var ora = Date.now();
    erroriImmagineTimestamps.push(ora);
    // Mantiene solo i timestamp nella finestra temporale configurata
    erroriImmagineTimestamps = erroriImmagineTimestamps.filter(function (t) {
      return ora - t <= IMG_ERROR_WINDOW_MS;
    });

    if (erroriImmagineTimestamps.length >= IMG_ERROR_THRESHOLD) {
      mostraAvviso();
    }
  }

  function attivaMonitoraggioImmagini() {
    // 'ami:lazy-error' è dispatchato con bubbles:true da lazy-loading.js:
    // un solo listener sul document intercetta tutte le immagini della pagina.
    document.addEventListener('ami:lazy-error', gestisciErroreImmagine, { passive: true });
  }

  // ------------------------------------------------------------
  // SEGNALE 3: MONITORAGGIO IFRAME (.universal-embed)
  // ------------------------------------------------------------
  function attivaMonitoraggioIframe() {
    var iframes = document.querySelectorAll('.universal-embed');
    if (!iframes.length) return;

    iframes.forEach(function (iframe) {
      var caricato = false;

      var timeoutId = setTimeout(function () {
        if (caricato) return;
        // L'iframe non ha emesso 'load' entro la soglia: possibile
        // mancata risposta da IA (non copre il caso di risposta
        // ricevuta ma con contenuto d'errore, che emette comunque load).
        mostraAvviso();
      }, IFRAME_TIMEOUT_MS);

      iframe.addEventListener('load', function () {
        caricato = true;
        clearTimeout(timeoutId);
      }, { once: true });

      iframe.addEventListener('error', function () {
        caricato = true;
        clearTimeout(timeoutId);
        mostraAvviso();
      }, { once: true });
    });
  }

  // ------------------------------------------------------------
  // AVVIO
  // ------------------------------------------------------------
  function init() {
    eseguiProbe();
    attivaMonitoraggioImmagini();
    attivaMonitoraggioIframe();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();