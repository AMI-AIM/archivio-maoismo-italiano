// ============================================================
// NAVIGAZIONE: drawer mobile + menu a tendina dell'header
// ============================================================
// Gestisce in modo accessibile i due menu costruiti in
// overrides/partials/header.html:
//
// 1) DRAWER MOBILE. Lo stato vive nel checkbox #__drawer (lo stesso che
//    usano Material e il CSS). Il pulsante hamburger lo commuta e tiene
//    sincronizzato aria-expanded; all'apertura il focus entra nel menu,
//    resta intrappolato al suo interno (Tab / Maiusc+Tab) e alla chiusura
//    (Esc, pulsante "Chiudi", clic sull'overlay) torna all'hamburger.
//
// 2) DROPDOWN DELL'HEADER ("Archivio"). Pattern "disclosure": il trigger
//    e' un <button> con aria-expanded; si apre con clic, Invio, Spazio o
//    freccia giu', e al passaggio del mouse sui dispositivi con hover. Si
//    chiude con Esc (il focus torna al trigger), con un clic fuori o
//    quando il focus esce dalla voce.
(function () {
  "use strict";

  /* ------------------------------------------------------------
     1) DRAWER MOBILE
     ------------------------------------------------------------ */
  var toggle = document.getElementById("__drawer");
  var hamburger = document.getElementById("hamburger-btn");
  var drawer = document.getElementById("custom-drawer");
  var closeBtn = document.getElementById("drawer-close");

  if (toggle && hamburger && drawer) {
    var focusabili = function () {
      return Array.prototype.slice.call(
        drawer.querySelectorAll('a[href], button:not([disabled])')
      );
    };

    // Allinea ARIA e focus allo stato del checkbox. "restituisci" indica
    // se, in chiusura, il focus deve tornare all'hamburger (non serve
    // quando la chiusura nasce da un clic su un link del menu).
    var sincronizza = function (restituisci) {
      var aperto = toggle.checked;
      hamburger.setAttribute("aria-expanded", aperto ? "true" : "false");
      hamburger.setAttribute("aria-label", aperto ? "Chiudi il menu" : "Apri il menu");
      if (aperto) {
        var primo = drawer.querySelector(".md-drawer__link--active") ||
          drawer.querySelector(".md-drawer__link") || focusabili()[0];
        // Il drawer diventa visibile con la transizione: si attende un
        // frame perche' visibility:hidden impedirebbe il focus.
        window.requestAnimationFrame(function () {
          if (primo) primo.focus({ preventScroll: true });
        });
      } else if (restituisci && drawer.contains(document.activeElement)) {
        hamburger.focus();
      }
    };

    var impostaDrawer = function (aperto, restituisci) {
      if (toggle.checked === aperto) return;
      toggle.checked = aperto;
      sincronizza(restituisci);
    };

    hamburger.addEventListener("click", function () {
      impostaDrawer(!toggle.checked, true);
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        impostaDrawer(false, true);
        hamburger.focus();
      });
    }

    // Overlay (label for="__drawer") e qualsiasi altro cambio nativo.
    toggle.addEventListener("change", function () {
      sincronizza(true);
    });

    // Un link interno chiude il drawer prima della navigazione: evita
    // che resti aperto tornando indietro con la cache del browser.
    drawer.addEventListener("click", function (event) {
      if (event.target.closest("a[href]")) impostaDrawer(false, false);
    });

    document.addEventListener("keydown", function (event) {
      if (!toggle.checked) return;

      if (event.key === "Escape") {
        event.preventDefault();
        impostaDrawer(false, true);
        hamburger.focus();
        return;
      }

      // Trappola del focus: il menu e' modale mentre l'overlay copre la
      // pagina, quindi Tab non deve finire sui contenuti sottostanti.
      if (event.key === "Tab") {
        var elementi = focusabili();
        if (!elementi.length) return;
        var primo = elementi[0];
        var ultimo = elementi[elementi.length - 1];
        if (event.shiftKey && document.activeElement === primo) {
          event.preventDefault();
          ultimo.focus();
        } else if (!event.shiftKey && document.activeElement === ultimo) {
          event.preventDefault();
          primo.focus();
        } else if (!drawer.contains(document.activeElement)) {
          event.preventDefault();
          primo.focus();
        }
      }
    });

    // Passando al layout desktop con il drawer aperto (rotazione del
    // tablet, finestra allargata) il menu va chiuso: su desktop e' nascosto.
    var mqDesktop = window.matchMedia("(min-width: 769px)");
    var suCambioLayout = function (e) {
      if (e.matches) impostaDrawer(false, false);
    };
    if (mqDesktop.addEventListener) {
      mqDesktop.addEventListener("change", suCambioLayout);
    } else if (mqDesktop.addListener) {
      mqDesktop.addListener(suCambioLayout);
    }

    // Ritorno con il tasto "indietro" (bfcache): riallinea lo stato.
    window.addEventListener("pageshow", function () {
      if (toggle.checked) impostaDrawer(false, false);
      else sincronizza(false);
    });

    sincronizza(false);
  }

  /* ------------------------------------------------------------
     2) DROPDOWN DELL'HEADER
     ------------------------------------------------------------ */
  var voci = Array.prototype.slice.call(
    document.querySelectorAll(".md-header__nav-item--dropdown")
  );
  if (!voci.length) return;

  var conHover = window.matchMedia("(hover: hover) and (pointer: fine)");

  var chiudiTutte = function (tranne) {
    voci.forEach(function (voce) {
      if (voce !== tranne) impostaVoce(voce, false);
    });
  };

  var impostaVoce = function (voce, aperta) {
    var trigger = voce.querySelector(".md-header__nav-link--dropdown");
    voce.classList.toggle("is-open", aperta);
    if (trigger) trigger.setAttribute("aria-expanded", aperta ? "true" : "false");
  };

  voci.forEach(function (voce) {
    var trigger = voce.querySelector(".md-header__nav-link--dropdown");
    var menu = voce.querySelector(".md-header__dropdown-menu");
    if (!trigger || !menu) return;

    var link = function () {
      return Array.prototype.slice.call(menu.querySelectorAll("a[href]"));
    };
    var timerChiusura = null;

    trigger.addEventListener("click", function () {
      var aperta = !voce.classList.contains("is-open");
      chiudiTutte(voce);
      impostaVoce(voce, aperta);
    });

    trigger.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        chiudiTutte(voce);
        impostaVoce(voce, true);
        var primo = link()[0];
        if (primo) primo.focus();
      }
    });

    // Frecce su/giu' tra le voci del menu aperto (Tab funziona comunque).
    menu.addEventListener("keydown", function (event) {
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
      var elenco = link();
      var i = elenco.indexOf(document.activeElement);
      if (i === -1) return;
      event.preventDefault();
      var prossimo = event.key === "ArrowDown"
        ? elenco[(i + 1) % elenco.length]
        : elenco[(i - 1 + elenco.length) % elenco.length];
      prossimo.focus();
    });

    voce.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && voce.classList.contains("is-open")) {
        event.preventDefault();
        impostaVoce(voce, false);
        trigger.focus();
      }
    });

    // Il focus esce dalla voce (Tab oltre l'ultimo link): si chiude.
    voce.addEventListener("focusout", function (event) {
      if (!voce.contains(event.relatedTarget)) impostaVoce(voce, false);
    });

    // Hover solo con un puntatore preciso: su touch l'apertura e' il tap.
    // Un breve ritardo in chiusura perdona il tragitto diagonale verso il menu.
    voce.addEventListener("mouseenter", function () {
      if (!conHover.matches) return;
      clearTimeout(timerChiusura);
      chiudiTutte(voce);
      impostaVoce(voce, true);
    });
    voce.addEventListener("mouseleave", function () {
      if (!conHover.matches) return;
      clearTimeout(timerChiusura);
      timerChiusura = setTimeout(function () {
        if (!voce.contains(document.activeElement)) impostaVoce(voce, false);
      }, 180);
    });
  });

  document.addEventListener("click", function (event) {
    voci.forEach(function (voce) {
      if (!voce.contains(event.target)) impostaVoce(voce, false);
    });
  });
})();

// ============================================================
// "IL PROGETTO" — COME CITARE L'AMI
// ============================================================
// Stessi formati e stesso pannello di "Cita questo documento" nelle
// schede (documenti.js): Chicago, MLA, BibTeX, Semplice, con la data di
// consultazione di oggi. Senza JavaScript resta la forma semplice scritta
// in progetto.md, con "[data di consultazione]".
(function () {
  var testo = document.getElementById("progetto-citazione-testo");
  if (!testo) return;
  var pannello = testo.parentNode;
  var schede = pannello.querySelector(".citazione-tabs");
  var pulsante = document.getElementById("progetto-citazione-copia");

  var URL_AMI = "https://ami-aim.github.io/archivio-maoismo-italiano/";
  var TITOLO = "Archivio del Maoismo Italiano (AMI)";
  var oggi = new Date();
  var iso = oggi.getFullYear() + "-" + String(oggi.getMonth() + 1).padStart(2, "0") +
    "-" + String(oggi.getDate()).padStart(2, "0");
  var it = iso;
  try {
    it = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "long", year: "numeric" }).format(oggi);
  } catch (e) { /* resta la data ISO */ }

  // Sito web curato: il curatore al posto dell'autore ("a cura di",
  // MLA "curatore"), nessun anno di pubblicazione (non dichiarato).
  var formati = {
    chicago: "Masci, Ivan, a cura di. <em>" + TITOLO + "</em>. Consultato il " + it + ". " + URL_AMI + ".",
    mla: "Masci, Ivan, curatore. <em>" + TITOLO + "</em>, " + URL_AMI + ". Consultato il " + it + ".",
    bibtex: [
      "@misc{ami,",
      "  title = {Archivio del Maoismo Italiano ({AMI})},",
      "  editor = {Masci, Ivan},",
      "  url = {" + URL_AMI + "},",
      "  urldate = {" + iso + "}",
      "}"
    ].join("\n"),
    semplice: "Masci, Ivan (a cura di), <em>" + TITOLO + "</em>, " + URL_AMI + ", consultato il " + it + "."
  };
  var corrente = "chicago";

  function mostra(formato) {
    corrente = formato;
    testo.innerHTML = formati[formato];
    if (!schede) return;
    schede.querySelectorAll(".citazione-tab").forEach(function (b) {
      var attivo = b.dataset.formato === formato;
      b.classList.toggle("citazione-tab--active", attivo);
      b.setAttribute("aria-pressed", attivo ? "true" : "false");
    });
  }

  if (schede) {
    schede.hidden = false;
    schede.querySelectorAll(".citazione-tab").forEach(function (b) {
      b.addEventListener("click", function () { mostra(b.dataset.formato); });
    });
  }
  mostra(corrente);

  if (!pulsante || !navigator.clipboard) return;
  var etichetta = pulsante.querySelector(".citazione-copia__etichetta") || pulsante;
  var originale = etichetta.textContent;
  pulsante.hidden = false;
  pulsante.setAttribute("aria-live", "polite");

  pulsante.addEventListener("click", function () {
    var semplice = testo.innerText;
    var copia = (window.ClipboardItem && corrente !== "bibtex")
      ? navigator.clipboard.write([new ClipboardItem({
          "text/html": new Blob([testo.innerHTML], { type: "text/html" }),
          "text/plain": new Blob([semplice], { type: "text/plain" })
        })])
      : navigator.clipboard.writeText(semplice);
    copia.then(function () {
      etichetta.textContent = "Copiato";
      pulsante.classList.add("is-copiato");
      setTimeout(function () {
        etichetta.textContent = originale;
        pulsante.classList.remove("is-copiato");
      }, 1500);
    }).catch(function () {
      var range = document.createRange();
      range.selectNodeContents(testo);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    });
  });
})();
