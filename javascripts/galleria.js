/**
 * Galleria Fotografica — AMI
 * 1) Sync sticky: barra chip sotto l'header autohide via --gal-top.
 * 2) Masonry dinamico: span calcolati dalle dimensioni reali delle immagini.
 * 3) Timeline a riga unica: scrollspy + keep-visible del chip attivo.
 * 4) Lightbox COMPLETO: dialog nativo con navigazione prev/next (pulsanti e
 *    frecce), contatore, permalink #doc-<id> con deep-link, pannello
 *    citazione con copia, barra metadati compatta.
 */
(function () {
  "use strict";

  var WIDE_ASPECT = 1.45;
  var CARD_PAD = 14; // sincronizzato con --gal-gap nel CSS
  var MOBILE_MQ = "(max-width: 560px)";

  document.addEventListener("DOMContentLoaded", function () {
    if (!document.querySelector(".galleria-wrapper")) return;

    /* ============================================================
       1) SYNC STICKY HEADER / BARRA CHIP
       ============================================================ */
    var header = document.querySelector(".md-header");
    var rootEl = document.documentElement;
    var ticking = false;

    function syncStickyTop() {
      ticking = false;
      var bottom = header ? header.getBoundingClientRect().bottom : 0;
      rootEl.style.setProperty("--gal-top", (bottom > 0 ? Math.round(bottom) : 0) + "px");
    }
    function onScrollSync() {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(syncStickyTop);
      }
    }

    window.addEventListener("scroll", onScrollSync, { passive: true });
    window.addEventListener("resize", onScrollSync);
    syncStickyTop();

    /* ============================================================
       2) MASONRY DINAMICO
       ============================================================ */
    var grids = Array.prototype.slice.call(document.querySelectorAll(".galleria-grid"));

    if (grids.length) {
      var isMobile = window.matchMedia && window.matchMedia(MOBILE_MQ).matches;

      var layoutCard = function (card) {
        var media = card.querySelector(".card-media");
        var img = card.querySelector(".galleria-img");
        if (!media || !img) return;

        var aw = img.naturalWidth;
        var ah = img.naturalHeight;

        if (aw && ah) {
          card.classList.remove("card-error");
          if (!isMobile && (aw / ah) >= WIDE_ASPECT) {
            card.classList.add("h-wide");
          } else {
            card.classList.remove("h-wide");
          }
        } else if (img.complete) {
          card.classList.add("card-error");
        } else {
          return;
        }

        var h = media.getBoundingClientRect().height + CARD_PAD;
        card.style.gridRowEnd = "span " + Math.max(40, Math.round(h));
      };

      grids.forEach(function (grid) {
        grid.classList.add("is-js");
        Array.prototype.slice.call(grid.querySelectorAll(".galleria-card")).forEach(function (card) {
          var img = card.querySelector(".galleria-img");
          if (!img) return;
          if (img.complete) {
            layoutCard(card);
          }
          img.addEventListener("load", function () { layoutCard(card); }, { once: true });
          img.addEventListener("error", function () { layoutCard(card); }, { once: true });
          img.addEventListener("ami:lazy-loaded", function () {
            img.style.transition = "";
            layoutCard(card);
          }, { once: true });
          img.addEventListener("ami:lazy-error", function () {
            layoutCard(card);
          }, { once: true });
        });
      });

      var resizeTimer = null;
      window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
          isMobile = window.matchMedia && window.matchMedia(MOBILE_MQ).matches;
          Array.prototype.slice.call(document.querySelectorAll(".galleria-card")).forEach(layoutCard);
        }, 150);
      });
    }

    /* ============================================================
       3) TIMELINE A RIGA UNICA
       ============================================================ */
    var nav = document.getElementById("galleria-timeline");
    var links = nav ? Array.prototype.slice.call(nav.querySelectorAll(".timeline-link")) : [];
    var sections = Array.prototype.slice.call(document.querySelectorAll(".galleria-year-section"));

    var reduceMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (nav && links.length && sections.length) {
      var list = nav.querySelector(".timeline-list");

      var keepChipVisible = function (link) {
        if (!list) return;
        var view = list.clientWidth;
        var sl = list.scrollLeft;
        var left = link.offsetLeft;
        var right = left + link.offsetWidth;
        var behavior = reduceMotion ? "auto" : "smooth";
        if (left < sl + 10) {
          list.scrollTo({ left: Math.max(0, left - 10), behavior: behavior });
        } else if (right > sl + view - 10) {
          list.scrollTo({ left: right - view + 10, behavior: behavior });
        }
      };

      var setActive = function (activeLink) {
        links.forEach(function (l) {
          l.classList.remove("active", "is-active");
          l.removeAttribute("aria-current");
        });
        if (activeLink) {
          activeLink.classList.add("active", "is-active");
          activeLink.setAttribute("aria-current", "true");
          keepChipVisible(activeLink);
        }
      };

      links.forEach(function (link) {
        link.addEventListener("click", function (event) {
          var href = link.getAttribute("href");
          if (!href || href.charAt(0) !== "#") return;
          var target = document.getElementById(href.slice(1));
          if (!target) return;
          event.preventDefault();
          target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
          if (window.history && window.history.replaceState) {
            window.history.replaceState(null, "", href);
          }
          setActive(link);
        });
      });

      if ("IntersectionObserver" in window) {
        var linkByYear = {};
        links.forEach(function (l) {
          var y = l.getAttribute("data-year");
          if (y) linkByYear[y] = l;
        });
        var observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            var link = linkByYear[entry.target.getAttribute("data-year")];
            if (link) setActive(link);
          });
        }, { root: null, rootMargin: "-30% 0px -60% 0px", threshold: 0 });
        sections.forEach(function (s) { observer.observe(s); });
      } else {
        setActive(links[0]);
      }
    }

    /* ============================================================
       4) LIGHTBOX COMPLETO
       ============================================================ */
    var dialog = document.getElementById("galleria-lightbox");
    if (!dialog || typeof dialog.showModal !== "function") return;

    var cards = Array.prototype.slice.call(document.querySelectorAll(".galleria-card"));
    if (!cards.length) return;

    var lbImg = dialog.querySelector(".lightbox-img");
    var lbTitle = dialog.querySelector(".lightbox-title");
    var lbMeta = dialog.querySelector(".lightbox-meta");
    var lbCounter = dialog.querySelector(".lightbox-counter");
    var lbPrev = dialog.querySelector(".lightbox-nav--prev");
    var lbNext = dialog.querySelector(".lightbox-nav--next");
    var lbClose = dialog.querySelector(".lightbox-close");
    var lbScheda = dialog.querySelector(".lightbox-action--scheda");
    var lbIa = dialog.querySelector(".lightbox-action--ia");
    var lbCiteBtn = dialog.querySelector(".lightbox-action--cite");
    var lbCitePanel = dialog.getElementById ? document.getElementById("lightbox-cite-panel") : null;
    lbCitePanel = lbCitePanel || dialog.querySelector(".lightbox-cite");
    var lbCiteText = lbCitePanel.querySelector(".citazione-testo");
    var lbCiteCopy = lbCitePanel.querySelector(".citazione-copia");

    var currentIndex = -1;
    var lastTrigger = null;
    var hashBeforeOpen = "";

    function absoluteUrl(rel) {
      try {
        return new URL(rel, document.baseURI).href;
      } catch (e) {
        return rel;
      }
    }

    function buildCitation(card) {
      var titolo = card.getAttribute("data-titolo") || "Senza titolo";
      var data = card.getAttribute("data-data") || "";
      var org = card.getAttribute("data-org") || "";
      var tipo = card.getAttribute("data-tipo") || "";
      var ia = card.getAttribute("data-ia-url") || "";
      var schedaRel = card.getAttribute("data-scheda-url") || "";
      var id = card.id || "";

      var oggi = new Date();
      var accesso = oggi.getDate() + "/" + (oggi.getMonth() + 1) + "/" + oggi.getFullYear();

      var head = org ? (org + ", " + titolo) : titolo;
      var cit = head;
      if (data) cit += ", " + data;
      if (tipo) cit += " [" + tipo + "]";
      if (ia) cit += ", in Internet Archive: " + ia;
      if (schedaRel) {
        cit += "; AMI — Archivio del Maoismo Italiano, scheda " + (id || "s.i.") +
               ": " + absoluteUrl(schedaRel);
      }
      cit += " (consultato il " + accesso + ").";
      return cit;
    }

    function setHash(card) {
      if (!window.history || !window.history.replaceState) return;
      if (card && card.id) {
        window.history.replaceState(null, "", "#doc-" + card.id);
      }
    }

    function populate(index) {
      var card = cards[index];
      if (!card) return;
      currentIndex = index;

      var titolo = card.getAttribute("data-titolo") || "Senza titolo";
      var data = card.getAttribute("data-data") || "";
      var org = card.getAttribute("data-org") || "";
      var iaUrl = card.getAttribute("data-ia-url") || "#";
      var schedaUrl = card.getAttribute("data-scheda-url") || "";
      var fullSrc = card.getAttribute("data-full-src") || "";

      lbTitle.textContent = titolo;
      lbTitle.title = titolo;
      var metaText = [data, org].filter(Boolean).join(" · ");
      lbMeta.textContent = metaText;
      lbMeta.title = metaText;
      lbMeta.hidden = !metaText;

      lbCounter.textContent = (index + 1) + " / " + cards.length;

      if (schedaUrl) {
        lbScheda.href = schedaUrl;
        lbScheda.hidden = false;
      } else {
        lbScheda.hidden = true;
        lbScheda.removeAttribute("href");
      }
      lbIa.href = iaUrl;

      // Pannello citazione: rigenerato e richiuso a ogni documento
      lbCitePanel.hidden = true;
      lbCiteBtn.setAttribute("aria-expanded", "false");
      lbCiteText.value = buildCitation(card);

      lbPrev.disabled = index <= 0;
      lbNext.disabled = index >= cards.length - 1;

      dialog.classList.remove("is-error");
      dialog.classList.add("is-loading");
      lbImg.removeAttribute("src");
      lbImg.alt = titolo;
      lbImg.src = fullSrc;

      setHash(card);
    }

    function openLightbox(card, trigger) {
      var index = cards.indexOf(card);
      if (index < 0) return;
      lastTrigger = trigger || null;
      hashBeforeOpen = window.location.hash;
      dialog.showModal();
      populate(index);
    }

    function navigate(delta) {
      var target = currentIndex + delta;
      if (target < 0 || target >= cards.length) return;
      populate(target);
    }

    // Click "semplice" sulle card apre il lightbox; ctrl/meta/shift+tasto
    // medio conservano il comportamento nativo del link.
    document.addEventListener("click", function (event) {
      if (event.defaultPrevented) return;
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      var link = event.target.closest ? event.target.closest(".galleria-card .card-link") : null;
      if (!link) return;
      var card = link.closest(".galleria-card");
      if (!card || !card.getAttribute("data-full-src")) return;
      event.preventDefault();
      openLightbox(card, link);
    });

    lbPrev.addEventListener("click", function () { navigate(-1); });
    lbNext.addEventListener("click", function () { navigate(1); });
    lbClose.addEventListener("click", function () { dialog.close(); });

    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });

    // Tastiera: frecce per navigare (ESC chiude, nativo)
    dialog.addEventListener("keydown", function (event) {
      if (event.target === lbCiteText) return; // non rubare le frecce al textarea
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        navigate(-1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        navigate(1);
      }
    });

    // Pannello citazione
    lbCiteBtn.addEventListener("click", function () {
      var aperto = lbCitePanel.hidden;
      lbCitePanel.hidden = !aperto;
      lbCiteBtn.setAttribute("aria-expanded", String(aperto));
    });

    lbCiteCopy.addEventListener("click", function () {
      var testo = lbCiteText.value;
      var originale = lbCiteCopy.textContent;

      function feedback() {
        lbCiteCopy.textContent = "Copiato ✓";
        setTimeout(function () {
          lbCiteCopy.textContent = originale;
        }, 1500);
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(testo).then(feedback, function () {
          lbCiteText.select();
          document.execCommand("copy");
          feedback();
        });
      } else {
        lbCiteText.select();
        document.execCommand("copy");
        feedback();
      }
    });

    lbImg.addEventListener("load", function () {
      dialog.classList.remove("is-loading");
    });
    lbImg.addEventListener("error", function () {
      dialog.classList.remove("is-loading");
      dialog.classList.add("is-error");
    });

    dialog.addEventListener("close", function () {
      dialog.classList.remove("is-loading", "is-error");

      // Ripristina l'hash precedente (i permalink #doc- non restano in URL)
      if (window.history && window.history.replaceState) {
        var restore = hashBeforeOpen;
        if (restore.indexOf("#doc-") === 0) restore = "";
        window.history.replaceState(
          null, "",
          window.location.pathname + window.location.search + (restore || "")
        );
      }
      hashBeforeOpen = "";

      if (lastTrigger && document.contains(lastTrigger)) {
        lastTrigger.focus({ preventScroll: true });
      }
      lastTrigger = null;
    });

    // Deep-link: /galleria/#doc-AMI-xxxx apre direttamente il lightbox
    var m = window.location.hash.match(/^#doc-(.+)$/);
    if (m) {
      var targetCard = null;
      try {
        targetCard = document.getElementById(decodeURIComponent(m[1]));
      } catch (e) {
        targetCard = null;
      }
      if (targetCard && targetCard.classList.contains("galleria-card")) {
        openLightbox(targetCard, null);
      }
    }
  });
})();