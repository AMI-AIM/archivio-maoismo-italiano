/**
 * Galleria Fotografica — AMI
 * 1) Sync sticky: barra chip sotto l'header autohide via --gal-top.
 * 2) Masonry dinamico: span calcolati dalle dimensioni reali delle immagini.
 * 3) Timeline a riga unica: scrollspy + keep-visible del chip attivo.
 * 4) Lightbox minimo: <dialog> nativo con immagine, metadati e azioni
 *    (Scheda archivistica / Internet Archive). Senza prev/next né permalink.
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
       4) LIGHTBOX MINIMO (dialog nativo)
       ============================================================ */
    var dialog = document.getElementById("galleria-lightbox");
    if (!dialog || typeof dialog.showModal !== "function") return;

    var lbImg = dialog.querySelector(".lightbox-img");
    var lbTitle = dialog.querySelector(".lightbox-title");
    var lbMeta = dialog.querySelector(".lightbox-meta");
    var lbScheda = dialog.querySelector(".lightbox-action--scheda");
    var lbIa = dialog.querySelector(".lightbox-action--ia");
    var lbClose = dialog.querySelector(".lightbox-close");
    var lastTrigger = null;

    lbImg.addEventListener("load", function () {
      dialog.classList.remove("is-loading");
    });
    lbImg.addEventListener("error", function () {
      dialog.classList.remove("is-loading");
      dialog.classList.add("is-error");
    });

    function openLightbox(card, trigger) {
      var titolo = card.getAttribute("data-titolo") || "Senza titolo";
      var data = card.getAttribute("data-data") || "";
      var org = card.getAttribute("data-org") || "";
      var iaUrl = card.getAttribute("data-ia-url") || "#";
      var schedaUrl = card.getAttribute("data-scheda-url") || "";
      var fullSrc = card.getAttribute("data-full-src") || "";

      lastTrigger = trigger || null;

      lbTitle.textContent = titolo;
      var metaText = [data, org].filter(Boolean).join(" · ");
      lbMeta.textContent = metaText;
      lbMeta.hidden = !metaText;

      if (schedaUrl) {
        lbScheda.href = schedaUrl;
        lbScheda.hidden = false;
      } else {
        lbScheda.hidden = true;
        lbScheda.removeAttribute("href");
      }
      lbIa.href = iaUrl;

      dialog.classList.remove("is-error");
      dialog.classList.add("is-loading");
      lbImg.removeAttribute("src");
      lbImg.alt = titolo;

      dialog.showModal();
      lbImg.src = fullSrc; // assegnato dopo showModal: misure corrette
    }

    // Intercetta il click sulle card SOLO se è un click "semplice":
    // ctrl/meta/shift+click e click col tasto destro/passano al comportamento
    // nativo del link (apri in nuova scheda ecc.).
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

    lbClose.addEventListener("click", function () {
      dialog.close();
    });

    // Click sul backdrop (il target è il dialog stesso)
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });

    dialog.addEventListener("close", function () {
      dialog.classList.remove("is-loading", "is-error");
      if (lastTrigger && document.contains(lastTrigger)) {
        lastTrigger.focus({ preventScroll: true });
      }
      lastTrigger = null;
    });
  });
})();