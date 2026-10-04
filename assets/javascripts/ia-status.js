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
 * DOVE SI ATTIVA: solo sulle pagine che caricano davvero qualcosa da
 * Internet Archive (visore delle schede documento, immagini a piena
 * risoluzione della galleria). Altrove il banner non compare e il
 * probe non parte.
 *
 * SUL VISORE: quando il visore di una scheda non risponde, o il probe
 * fallisce, sopra il visore compare un avviso con "Riprova" e il link
 * diretto. L'iframe resta al suo posto: se in realtà sta funzionando
 * (falso allarme del probe) il lettore può continuare a usarlo.
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

  // Elementi che dipendono da Internet Archive: senza nessuno di questi
  // la pagina non ha nulla da avvisare.
  var SELETTORE_CONTENUTI_IA = [
    '.universal-embed',
    'img[src*="archive.org"]',
    'img[data-src*="archive.org"]',
    '[data-full-src*="archive.org"]'
  ].join(',');

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
      '  width: 1.2rem;',
      '  height: 1.2rem;',
      '  fill: currentColor;',
      '}',
      '.ia-status-banner__testo {',
      '  flex: 1;',
      '  font-size: 0.82rem;',
      '  line-height: 1.4;',
      '}',
      '.ia-status-banner__chiudi {',
      '  flex: 0 0 auto;',
      '  display: inline-flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  width: 44px;',
      '  height: 44px;',
      '  margin: -0.4rem -0.4rem -0.4rem 0;',
      '  padding: 0;',
      '  background: transparent;',
      '  border: 0;',
      '  color: inherit;',
      '  border-radius: 50%;',
      '  cursor: pointer;',
      '}',
      '.ia-status-banner__chiudi svg {',
      '  width: 1.25rem;',
      '  height: 1.25rem;',
      '  fill: currentColor;',
      '}',
      '.ia-status-banner__chiudi:focus-visible {',
      '  outline: 2px solid #fff8ec;',
      '  outline-offset: 0;',
      '}',
      '.ia-status-banner__chiudi:hover {',
      '  background: rgba(255,255,255,0.15);',
      '}',
      '.ia-status-banner__breve { display: none; }',
      /* Avviso dentro il visore della scheda documento */
      '.ia-visore-avviso {',
      '  display: flex;',
      '  flex-wrap: wrap;',
      '  align-items: center;',
      '  gap: 0.5rem 1rem;',
      '  padding: 0.6rem 0.8rem;',
      '  border-bottom: 1px solid var(--md-default-fg-color--lightest);',
      '  background: var(--md-default-bg-color);',
      '  font-family: var(--ami-font-label, "Archivo", sans-serif);',
      '  font-size: var(--ami-font-size-sm, 0.75rem);',
      '  line-height: 1.4;',
      '  color: var(--md-default-fg-color);',
      '}',
      '.ia-visore-avviso__testo { flex: 1 1 18rem; margin: 0; }',
      '.ia-visore-avviso__azioni { display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; align-items: center; }',
      '.ia-visore-avviso__riprova {',
      '  min-height: 2.2rem;',
      '  padding: 0 0.9rem;',
      '  border: 1px solid var(--md-primary-fg-color);',
      '  border-radius: var(--ami-radius-sm, 4px);',
      '  background: transparent;',
      '  color: var(--md-primary-fg-color);',
      '  font: inherit;',
      '  font-weight: 600;',
      '  cursor: pointer;',
      '}',
      '.ia-visore-avviso__riprova:hover { background: var(--ami-rosso-tenue, #f9ecec); }',
      '.ia-visore-avviso__riprova:focus-visible { outline: 2px solid var(--md-primary-fg-color); outline-offset: 2px; }',
      '.ia-visore-avviso a { color: var(--md-primary-fg-color); font-weight: 600; }',
      /* Telefono: una riga, non fissato in cima (scorre via con la pagina
         e non copre l'header). Il testo completo resta per i lettori di
         schermo. */
      '@media (max-width: 600px) {',
      '  #ia-status-banner { position: static; box-shadow: none; }',
      '  .ia-status-banner__inner { padding: 0.15rem 0.2rem 0.15rem 0.8rem; gap: 0.5rem; }',
      '  .ia-status-banner__icon { width: 1rem; height: 1rem; }',
      '  .ia-status-banner__testo { font-size: 0.7rem; line-height: 1.3; }',
      '  .ia-status-banner__lungo { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }',
      '  .ia-status-banner__breve { display: inline; }',
      '  .ia-status-banner__chiudi { margin: 0; }',
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
        '<svg class="ia-status-banner__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
          '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>' +
        '</svg>' +
        '<span class="ia-status-banner__testo">' +
          '<span class="ia-status-banner__lungo">' +
          'I documenti di questo archivio sono ospitati su Internet Archive, piattaforma al momento instabile o irraggiungibile. ' +
          'Se i documenti non si caricano, il problema è temporaneo e non riguarda il solo sito AMI. Riprovare più tardi.' +
          '</span>' +
          '<span class="ia-status-banner__breve" aria-hidden="true">Internet Archive è instabile: i documenti potrebbero non caricarsi.</span>' +
        '</span>' +
        '<button type="button" class="ia-status-banner__chiudi" aria-label="Chiudi avviso">' +
          '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
            '<path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>' +
          '</svg>' +
        '</button>' +
      '</div>';

    // Dopo il link "Vai al contenuto": il primo Tab resta quello.
    var salto = document.querySelector('body > .md-skip');
    if (salto && salto.nextSibling) {
      document.body.insertBefore(banner, salto.nextSibling);
    } else {
      document.body.insertBefore(banner, document.body.firstChild);
    }

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

  function segnalaGuasto() {
    mostraAvviso();
    segnalaVisori();
  }

  function eseguiProbe(ignoraCache) {
    var cache = ignoraCache ? null : leggiCacheProbe();
    if (cache) {
      if (!cache.raggiungibile) {
        segnalaGuasto();
      }
      return;
    }

    var risolto = false;
    var img = new Image();
    var timeoutId = setTimeout(function () {
      if (risolto) return;
      risolto = true;
      scriviCacheProbe(false);
      segnalaGuasto();
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
      segnalaGuasto();
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
  function sorvegliaIframe(iframe) {
    var caricato = false;

    var timeoutId = setTimeout(function () {
      if (caricato) return;
      // L'iframe non ha emesso 'load' entro la soglia: possibile
      // mancata risposta da IA (non copre il caso di risposta
      // ricevuta ma con contenuto d'errore, che emette comunque load).
      mostraAvviso();
      segnalaVisore(iframe);
    }, IFRAME_TIMEOUT_MS);

    iframe.addEventListener('load', function () {
      caricato = true;
      clearTimeout(timeoutId);
    }, { once: true });

    iframe.addEventListener('error', function () {
      caricato = true;
      clearTimeout(timeoutId);
      mostraAvviso();
      segnalaVisore(iframe);
    }, { once: true });
  }

  function attivaMonitoraggioIframe() {
    var iframes = document.querySelectorAll('.universal-embed');
    if (!iframes.length) return;
    iframes.forEach(sorvegliaIframe);
  }

  // ------------------------------------------------------------
  // AVVISO NEL VISORE (schede documento)
  // ------------------------------------------------------------
  function segnalaVisori() {
    var iframes = document.querySelectorAll('.universal-embed');
    for (var i = 0; i < iframes.length; i++) segnalaVisore(iframes[i]);
  }

  function segnalaVisore(iframe) {
    var contenitore = iframe.closest('.embed-container') || iframe.parentNode;
    if (!contenitore || contenitore.querySelector('.ia-visore-avviso')) return;
    iniettaStile();

    // Link diretto: lo stesso "Apri su Internet Archive" del piede del
    // visore, se c'e'; altrimenti la pagina dell'oggetto ricavata
    // dall'indirizzo dell'embed.
    var link = contenitore.querySelector('a.embed-azione[href*="archive.org"]');
    var href = link ? link.getAttribute('href')
      : (iframe.getAttribute('src') || '').replace('/embed/', '/details/').split('?')[0];

    var avviso = document.createElement('div');
    avviso.className = 'ia-visore-avviso';
    avviso.setAttribute('role', 'status');
    avviso.innerHTML =
      '<p class="ia-visore-avviso__testo">Il visore di Internet Archive non risponde. ' +
      'Di solito torna disponibile entro poco.</p>' +
      '<div class="ia-visore-avviso__azioni">' +
        '<button type="button" class="ia-visore-avviso__riprova">Riprova</button>' +
        (href ? '<a href="' + href.replace(/"/g, '&quot;') + '" target="_blank" rel="noopener">' +
          'Apri su Internet Archive<span class="ami-sr-only"> (si apre in una nuova scheda)</span></a>' : '') +
      '</div>';
    contenitore.insertBefore(avviso, contenitore.firstChild);

    avviso.querySelector('.ia-visore-avviso__riprova').addEventListener('click', function () {
      avviso.remove();
      var src = iframe.getAttribute('src');
      iframe.setAttribute('src', 'about:blank');
      iframe.setAttribute('src', src);
      sorvegliaIframe(iframe);
      eseguiProbe(true);
    });
  }

  // ------------------------------------------------------------
  // AVVIO
  // ------------------------------------------------------------
  function init() {
    if (!document.querySelector(SELETTORE_CONTENUTI_IA)) return;
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