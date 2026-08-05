(function () {
    const container = document.getElementById('risultati-container');
    if (!container) return; // Non in pagina Archivio
    
    let allDocuments = [];
    let currentChunk = 0;
    let totalChunks = 0;
    let isLoading = false;
    let chunkMetadata = null;
    
    // ================================================================
    // CARICA METADATA CHUNK
    // ================================================================
    
    async function loadChunkMetadata() {
        try {
            const response = await fetch('/archivio-maoismo-italiano/documenti_chunks_meta.json');
            if (!response.ok) {
                console.log('[LAZY] Nessuna chunking disponibile, caricamento singolo');
                return false;
            }
            chunkMetadata = await response.json();
            totalChunks = chunkMetadata.chunks.length;
            console.log(`[LAZY] ${chunkMetadata.totale} doc in ${totalChunks} chunk`);
            return true;
        } catch (error) {
            console.log('[LAZY] Fallback: carica documenti.json completo', error);
            return false;
        }
    }
    
    // ================================================================
    // CARICA UN CHUNK
    // ================================================================
    
    async function loadChunk(chunkNum) {
        if (isLoading || chunkNum >= totalChunks) return;
        isLoading = true;
        
        try {
            const chunkPath = `/archivio-maoismo-italiano/documenti_chunk_${chunkNum}.json`;
            const response = await fetch(chunkPath);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            allDocuments = allDocuments.concat(data.documenti || []);
            currentChunk++;
            
            console.log(`[LAZY] Chunk ${chunkNum} caricato: ${data.documenti?.length || 0} doc`);
            
            // Trigger aggiornamento filtri
            if (window.archivioFilters) {
                window.archivioFilters.updateAvailableDocuments(allDocuments);
            }
        } catch (error) {
            console.error(`[LAZY] Errore caricamento chunk ${chunkNum}:`, error);
        } finally {
            isLoading = false;
        }
    }
    
    // ================================================================
    // CARICA PRIMO CHUNK ALL'INIT
    // ================================================================
    
    async function initLazyLoad() {
        const hasChunks = await loadChunkMetadata();
        if (hasChunks) {
            await loadChunk(0);
            setupInfiniteScroll();
        }
    }
    
    // ================================================================
    // INFINITE SCROLL: carica prossimo chunk a 80% scroll
    // ================================================================
    
    function setupInfiniteScroll() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        loadChunk(currentChunk);
                    }
                });
            },
            { threshold: 0.8 }
        );
        
        const sentinel = document.createElement('div');
        sentinel.id = 'lazy-load-sentinel';
        sentinel.style.height = '100px';
        container.appendChild(sentinel);
        observer.observe(sentinel);
    }
    
    // ================================================================
    // ESPORTA GLOBALE PER ARCHIVIO-FILTRI.JS
    // ================================================================
    
    window.lazyLoader = {
        allDocuments: () => allDocuments,
        init: initLazyLoad
    };
    
    // Avvia
    initLazyLoad();
})();