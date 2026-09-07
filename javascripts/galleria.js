/**
 * Galleria Fotografica — AMI
 * Scrollspy + smooth scroll per la timeline.
 * Il masonry è CSS-only: questo file non misura e non modifica le card.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var nav = document.getElementById("galleria-timeline");
    if (!nav) return;

    var links = Array.prototype.slice.call(nav.querySelectorAll(".timeline-link"));
    var sections = Array.prototype.slice.call(document.querySelectorAll(".galleria-year-section"));

    if (!links.length || !sections.length) return;

    var reduceMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function setActive(activeLink) {
      links.forEach(function (link) {
        link.classList.remove("active", "is-active");
        link.removeAttribute("aria-current");
      });

      if (activeLink) {
        activeLink.classList.add("active", "is-active");
        activeLink.setAttribute("aria-current", "true");
      }
    }

    links.forEach(function (link) {
      link.addEventListener("click", function (event) {
        var href = link.getAttribute("href");
        if (!href || href.charAt(0) !== "#") return;

        var target = document.getElementById(href.slice(1));
        if (!target) return;

        event.preventDefault();

        target.scrollIntoView({
          behavior: reduceMotion ? "auto" : "smooth",
          block: "start"
        });

        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, "", href);
        }

        setActive(link);
      });
    });

    if ("IntersectionObserver" in window) {
      var linkByYear = {};

      links.forEach(function (link) {
        var year = link.getAttribute("data-year");
        if (year) {
          linkByYear[year] = link;
        }
      });

      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;

          var year = entry.target.getAttribute("data-year");
          var link = linkByYear[year];

          if (link) {
            setActive(link);
          }
        });
      }, {
        root: null,
        rootMargin: "-30% 0px -60% 0px",
        threshold: 0
      });

      sections.forEach(function (section) {
        observer.observe(section);
      });
    } else {
      setActive(links[0]);
    }
  });
})();