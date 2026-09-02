/* Gestore dei chunk del catalogo. L'interfaccia e' in archivio-filtri.js. */
(function () {
    const baseUrl = (document.querySelector('meta[name="ami-base-url"]')?.content || '')
        .replace(/\/$/, '');
    let metadata = null;
    let documents = [];
    let nextChunk = 0;
    let loading = null;

    async function init() {
        if (metadata) return metadata;
        try {
            const response = await fetch(`${baseUrl}/documenti_chunks_meta.json`);
            if (!response.ok) return null;
            metadata = await response.json();
            return metadata;
        } catch (error) {
            console.warn('[AMI] Metadati chunk non disponibili:', error);
            return null;
        }
    }

    async function loadNext() {
        const manifest = await init();
        if (!manifest || nextChunk >= manifest.chunks.length) return documents;
        if (loading) return loading;

        const chunk = manifest.chunks[nextChunk];
        // Compatibilita' con manifest generati prima della correzione, che
        // contenevano il percorso assoluto della macchina di build.
        const chunkFile = String(chunk.file).split(/[\\/]/).pop();
        loading = fetch(`${baseUrl}/${chunkFile}`)
            .then((response) => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then((data) => {
                documents = documents.concat(data.documenti || []);
                nextChunk += 1;
                return documents;
            })
            .finally(() => { loading = null; });

        return loading;
    }

    window.amiLazyLoader = {
        init,
        loadNext,
        documents: () => documents,
        hasMore: () => Boolean(metadata && nextChunk < metadata.chunks.length),
        metadata: () => metadata
    };
})();
