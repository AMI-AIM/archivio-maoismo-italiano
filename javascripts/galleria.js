document.addEventListener('DOMContentLoaded', () => {
  const sections = document.querySelectorAll('.galleria-year-section');
  const timelineLinks = document.querySelectorAll('.galleria-timeline a');
  const yearBadge = document.getElementById('galleria-year-badge');

  if (!sections.length) return;

  // Configurazione IntersectionObserver
  // rootMargin: "-20% 0px -80% 0px" significa che l'elemento è considerato "attivo"
  // quando la sua parte superiore entra nel 20% superiore dello schermo.
  const observerOptions = {
    root: null,
    rootMargin: '-20% 0px -80% 0px',
    threshold: 0
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const year = entry.target.getAttribute('data-year');
        
        // 1. Aggiorna Timeline Desktop
        timelineLinks.forEach(link => {
          if (link.getAttribute('data-year') === year) {
            link.classList.add('active');
            // Scrolla la timeline per tenere l'anno attivo visibile
            link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
          } else {
            link.classList.remove('active');
          }
        });

        // 2. Aggiorna Badge Mobile
        if (yearBadge) {
          yearBadge.textContent = year;
        }
      }
    });
  }, observerOptions);

  // Osserva tutte le sezioni anno
  sections.forEach(section => {
    observer.observe(section);
  });
});