/**
 * Galleria Fotografica — AMI
 * 1) Sync sticky: la barra chip insegue il bordo inferiore dell'header
 *    (header.autohide) tramite --gal-top, senza sovrapposizioni né buchi.
 * 2) Masonry dinamico: span di griglia calcolati dalle dimensioni REALI
 *    delle immagini (proporzioni naturali, nessun taglio).
 * 3) Timeline a riga unica: scrollspy + keep-visible del chip attivo.
 */
(function () {
  "use strict";

  var WIDE_ASPECT = 1.45; // sopra questa proporzione la card va a tutta riga
  var CARD_PAD = 14;      // DEVE restare sincronizzato con --gal-gap nel CSS
  var MOBILE_MQ = "(max-width: 560px)";

  document.addEventListener("DOMContentLoaded", function () {
    // La galleria è l'unica pagina con questo wrapper: altrove no-op.
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
       2) MASONRY DINAMICO (griglia a span esatti)
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
          return; // immagine non ancora caricata
        }

        // Altezza reale resa dal browser + gutter verticale = span in px
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
       3) TIMELINE A RIGA UNICA: scrollspy + keep-visible
       ============================================================ */
    var nav = document.getElementById("galleria-timeline");
    if (!nav) return;

    var list = nav.querySelector(".timeline-list");
    var links = Array.prototype.slice.call(nav.querySelectorAll(".timeline-link"));
    var sections = Array.prototype.slice.call(document.querySelectorAll(".galleria-year-section"));
    if (!links.length || !sections.length) return;

    var reduceMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function keepChipVisible(link) {
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
    }

    function setActive(activeLink) {
      links.forEach(function (l) {
        l.classList.remove("active", "is-active");
        l.removeAttribute("aria-current");
      });
      if (activeLink) {
        activeLink.classList.add("active", "is-active");
        activeLink.setAttribute("aria-current", "true");
        keepChipVisible(activeLink);
      }
    }

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
  });
})();