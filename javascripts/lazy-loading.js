--- assets/javascripts/lazy-loading.js (原始)


+++ assets/javascripts/lazy-loading.js (修改后)
/**
 * LAZY LOADING CON SKELETON - Archivio del Maoismo Italiano
 *
 * Sistema avanzato di lazy loading per immagini con:
 * - Skeleton placeholder durante il caricamento
 * - Intersection Observer API per performance
 * - Fade-in animation al completamento
 * - Supporto fallback per browser legacy
 * - Gestione errori robusta
 *
 * Utilizzo:
 * 1. Aggiungere classe "lazy-img" alle immagini nel Markdown/HTML
 * 2. Usare attributo "data-src" invece di "src"
 * 3. Includere questo script nella pagina
 *
 * Esempio HTML:
 * <img class="lazy-img" data-src="immagine.webp" alt="Descrizione">
 */

(function() {
    'use strict';

    // Configurazione
    const CONFIG = {
        rootMargin: '50px',      // Carica immagine 50px prima che entri in viewport
        threshold: 0.01,         // Attiva quando l'1% dell'immagine è visibile
        fadeInDuration: 300,     // Durata fade-in in ms
        skeletonClass: 'lazy-skeleton',
        loadedClass: 'lazy-loaded',
        errorClass: 'lazy-error',
        imageClass: 'lazy-img',
        srcAttribute: 'data-src',
        srcsetAttribute: 'data-srcset',
        sizesAttribute: 'data-sizes'
    };

    // Verifica supporto Intersection Observer
    const hasIntersectionObserver = 'IntersectionObserver' in window;
    const hasNativeLazyLoad = 'loading' in HTMLImageElement.prototype;

    /**
     * Crea elemento skeleton placeholder
     */
    function createSkeleton(img) {
        const skeleton = document.createElement('div');
        skeleton.className = CONFIG.skeletonClass;

        // Mantieni dimensioni proporzionali
        const width = img.getAttribute('width') || img.offsetWidth || '100%';
        const height = img.getAttribute('height') || img.offsetHeight || '200px';

        skeleton.style.width = typeof width === 'number' ? width + 'px' : width;
        skeleton.style.height = typeof height === 'number' ? height + 'px' : height;
        skeleton.style.display = 'inline-block';
        skeleton.style.verticalAlign = 'middle';
        skeleton.style.background = 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)';
        skeleton.style.backgroundSize = '200% 100%';
        skeleton.style.animation = 'skeleton-loading 1.5s infinite';
        skeleton.style.borderRadius = img.style.borderRadius || '4px';

        return skeleton;
    }

    /**
     * Carica un'immagine singola
     */
    function loadImage(img) {
        // Se già caricata o in errore, salta
        if (img.classList.contains(CONFIG.loadedClass) ||
            img.classList.contains(CONFIG.errorClass)) {
            return;
        }

        const src = img.getAttribute(CONFIG.srcAttribute);
        const srcset = img.getAttribute(CONFIG.srcsetAttribute);
        const sizes = img.getAttribute(CONFIG.sizesAttribute);

        if (!src) {
            console.warn('[LazyLoad] Immagine senza data-src:', img);
            return;
        }

        // Crea skeleton se non esiste
        if (!img.previousElementSibling ||
            !img.previousElementSibling.classList.contains(CONFIG.skeletonClass)) {
            const skeleton = createSkeleton(img);
            img.parentNode.insertBefore(skeleton, img);

            // Nascondi immagine finché non è caricata
            img.style.opacity = '0';
            img.style.transition = `opacity ${CONFIG.fadeInDuration}ms ease-in-out`;
        }

        // Crea nuova istanza Image per precaricare
        const tempImg = new Image();

        // Copia attributi
        if (srcset) tempImg.srcset = srcset;
        if (sizes) tempImg.sizes = sizes;

        tempImg.onload = function() {
            // Imposta src reale solo dopo caricamento completo
            if (srcset) img.srcset = srcset;
            img.src = src;

            // Rimuovi attributi data
            img.removeAttribute(CONFIG.srcAttribute);
            if (srcset) img.removeAttribute(CONFIG.srcsetAttribute);
            if (sizes) img.removeAttribute(CONFIG.sizesAttribute);

            // Attendi che l'immagine sia effettivamente renderizzata
            setTimeout(() => {
                img.style.opacity = '1';
                img.classList.add(CONFIG.loadedClass);

                // Rimuovi skeleton dopo fade-in
                const skeleton = img.previousElementSibling;
                if (skeleton && skeleton.classList.contains(CONFIG.skeletonClass)) {
                    setTimeout(() => {
                        skeleton.remove();
                    }, CONFIG.fadeInDuration);
                }
            }, 50);
        };

        tempImg.onerror = function() {
            console.error('[LazyLoad] Errore caricamento immagine:', src);
            img.classList.add(CONFIG.errorClass);

            // Mostra messaggio di errore o fallback
            const skeleton = img.previousElementSibling;
            if (skeleton && skeleton.classList.contains(CONFIG.skeletonClass)) {
                skeleton.style.background = '#ffebee';
                skeleton.innerHTML = '<span style="color:#d32f2f;font-size:12px;">⚠️ Img non disponibile</span>';
                skeleton.style.display = 'flex';
                skeleton.style.alignItems = 'center';
                skeleton.style.justifyContent = 'center';
                skeleton.style.textAlign = 'center';
                skeleton.style.padding = '10px';
            }

            // Nascondi immagine rotta
            img.style.display = 'none';
        };

        // Avvia caricamento
        tempImg.src = src;
    }

    /**
     * Setup Intersection Observer per lazy loading
     */
    function setupLazyLoading() {
        if (!hasIntersectionObserver) {
            // Fallback: carica tutte le immagini immediatamente
            console.warn('[LazyLoad] IntersectionObserver non supportato, caricamento immediato');
            document.querySelectorAll('.' + CONFIG.imageClass).forEach(loadImage);
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadImage(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: CONFIG.rootMargin,
            threshold: CONFIG.threshold
        });

        // Osserva tutte le immagini lazy
        document.querySelectorAll('.' + CONFIG.imageClass).forEach(img => {
            observer.observe(img);
        });
    }

    /**
     * Caricamento nativo lazy (browser moderni)
     */
    function setupNativeLazyLoad() {
        if (!hasNativeLazyLoad) return;

        document.querySelectorAll('.' + CONFIG.imageClass).forEach(img => {
            img.loading = 'lazy';

            // Aggiungi evento load per fade-in anche con native lazy
            img.addEventListener('load', () => {
                img.classList.add(CONFIG.loadedClass);
                const skeleton = img.previousElementSibling;
                if (skeleton && skeleton.classList.contains(CONFIG.skeletonClass)) {
                    skeleton.remove();
                }
            });
        });
    }

    /**
     * Inizializza sistema lazy loading
     */
    function init() {
        // Aggiungi CSS per animazioni se non esiste
        if (!document.getElementById('lazy-load-styles')) {
            const style = document.createElement('style');
            style.id = 'lazy-load-styles';
            style.textContent = `
                @keyframes skeleton-loading {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }

                .lazy-skeleton {
                    position: relative;
                    overflow: hidden;
                }

                .lazy-img {
                    transition: opacity 300ms ease-in-out;
                }

                .lazy-img.lazy-loaded {
                    /* Immagine completamente caricata */
                }

                .lazy-img.lazy-error {
                    /* Gestione errore - immagine nascosta */
                }
            `;
            document.head.appendChild(style);
        }

        // Usa native lazy load se disponibile, altrimenti IntersectionObserver
        if (hasNativeLazyLoad) {
            setupNativeLazyLoad();
        }

        // Setup sempre IntersectionObserver per skeleton
        setupLazyLoading();
    }

    /**
     * API pubblica per ricaricare immagini dinamiche
     */
    window.LazyImageLoader = {
        /**
         * Ricarica immagini in un container specifico
         * Utile per contenuti caricati dinamicamente (AJAX, etc.)
         */
        refresh: function(container) {
            const root = container || document;
            const images = root.querySelectorAll('.' + CONFIG.imageClass);

            if (hasIntersectionObserver) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            loadImage(entry.target);
                            observer.unobserve(entry.target);
                        }
                    });
                }, {
                    rootMargin: CONFIG.rootMargin,
                    threshold: CONFIG.threshold
                });

                images.forEach(img => observer.observe(img));
            } else {
                images.forEach(loadImage);
            }
        },

        /**
         * Carica immediatamente un'immagine specifica
         */
        loadNow: function(img) {
            if (img instanceof HTMLElement) {
                loadImage(img);
            } else if (typeof img === 'string') {
                const element = document.querySelector(img);
                if (element) loadImage(element);
            }
        },

        /**
         * Distrugge observer e carica tutte le immagini
         */
        loadAll: function() {
            document.querySelectorAll('.' + CONFIG.imageClass).forEach(loadImage);
        }
    };

    // Avvia quando DOM è pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
