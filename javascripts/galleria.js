/**
 * Galleria Fotografica - Interactive Timeline & Masonry Gallery
 * Features: Active year tracking, smooth scroll, badge updates
 */
document.addEventListener('DOMContentLoaded', () => {
  const sections = document.querySelectorAll('.galleria-year-section');
  const timelineLinks = document.querySelectorAll('.timeline-link');
  const yearBadge = document.getElementById('galleria-year-badge');
  const badgeYearValue = document.getElementById('badge-year-value');
  
  if (!sections.length) return;

  // Smooth scroll per i link della timeline
  timelineLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href');
      const targetSection = document.querySelector(targetId);
      
      if (targetSection) {
        targetSection.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
        
        // Aggiorna stato active immediatamente
        timelineLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
      }
    });
  });

  // Configurazione IntersectionObserver per tracking anno corrente
  // rootMargin: "-25% 0px -75% 0px" = attiva quando sezione è nel 25% superiore viewport
  const observerOptions = {
    root: null,
    rootMargin: '-25% 0px -75% 0px',
    threshold: 0
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && entry.intersectionRatio > 0) {
        const year = entry.target.getAttribute('data-year');
        
        // 1. Aggiorna Timeline Desktop
        timelineLinks.forEach(link => {
          if (link.getAttribute('data-year') === year) {
            link.classList.add('active');
            
            // Auto-scroll della timeline per mantenere anno attivo visibile
            const timeline = document.getElementById('galleria-timeline');
            if (timeline) {
              link.scrollIntoView({ 
                block: 'center', 
                behavior: 'smooth',
                inline: 'nearest'
              });
            }
          } else {
            link.classList.remove('active');
          }
        });

        // 2. Aggiorna Badge Mobile
        if (badgeYearValue) {
          badgeYearValue.textContent = year;
          
          // Animazione flash quando cambia anno
          if (yearBadge) {
            yearBadge.style.animation = 'none';
            yearBadge.offsetHeight; /* trigger reflow */
            yearBadge.style.animation = 'pulse 0.3s ease';
          }
        }
      }
    });
  }, observerOptions);

  // Osserva tutte le sezioni anno
  sections.forEach(section => {
    observer.observe(section);
  });
  
  // Imposta primo anno come attivo all'avvio
  const firstSection = sections[0];
  if (firstSection) {
    const firstYear = firstSection.getAttribute('data-year');
    const firstLink = document.querySelector(`.timeline-link[data-year="${firstYear}"]`);
    if (firstLink) {
      firstLink.classList.add('active');
    }
    if (badgeYearValue) {
      badgeYearValue.textContent = firstYear;
    }
  }
});
