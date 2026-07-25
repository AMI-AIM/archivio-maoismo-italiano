// ============================================================
// CARICAMENTO DATI
// ============================================================

let documenti = [];
let annoMin = 1950;
let annoMax = 2025;

async function caricaDati() {
    try {
        const response = await fetch('/archivio-maoismo-italiano/documenti.json');
        const data = await response.json();
        documenti = data.documenti;
        annoMin = data.anno_min || 1900;
        annoMax = data.anno_max || 2025;
        inizializzaFiltri();
        precompilaRicercaDaURL();
        applicaFiltri();
    } catch (error) {
        console.error('Errore nel caricamento dei dati:', error);
        document.getElementById('risultati-container').innerHTML = '<p class="nessun-risultato">Errore nel caricamento dei dati.</p>';
    }
}

// Se si arriva da un link tipo documenti/?q=termine (es. dalla barra di
// ricerca in home), precompila il campo "Cerca nel testo" con quel valore.
function precompilaRicercaDaURL() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get('q');
    if (query) {
        const campoTesto = document.getElementById('filtro-testo');
        if (campoTesto) {
            campoTesto.value = query;
        }
    }
}

// ============================================================
// INIZIALIZZAZIONE FILTRI (collassabili)
// ============================================================

function inizializzaFiltri() {
    // ATTIVA I FILTRI COLLASSABILI
    const toggleIds = ['toggle-organizzazione', 'toggle-persona', 'toggle-tipo', 'toggle-anno'];
    
    toggleIds.forEach(id => {
        const button = document.getElementById(id);
        if (!button) return;
        
        const container = button.nextElementSibling;
        if (!container || !container.classList.contains('filtro-contenuto')) return;
        
        container.classList.remove('open');
        button.classList.remove('open');
        
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const target = this.nextElementSibling;
            if (target && target.classList.contains('filtro-contenuto')) {
                target.classList.toggle('open');
                this.classList.toggle('open');
            }
        });
    });
    
    // Popola i dropdown
    const organizzazioni = new Set();
    const persone = new Set();
    const tipi = new Set();
    
    documenti.forEach(doc => {
        doc.organizzazioni.forEach(org => organizzazioni.add(org));
        doc.persone.forEach(persona => persone.add(persona));
        if (doc.tipo) tipi.add(doc.tipo);
    });
    
    popolaSelect('filtro-organizzazione', organizzazioni);
    popolaSelect('filtro-persona', persone);
    popolaSelect('filtro-tipo', tipi);
    
    // Imposta lo slider degli anni
    const minSlider = document.getElementById('filtro-anno-min');
    const maxSlider = document.getElementById('filtro-anno-max');
    const minLabel = document.getElementById('anno-min-label');
    const maxLabel = document.getElementById('anno-max-label');
    
    minSlider.min = annoMin;
    minSlider.max = annoMax;
    minSlider.value = annoMin;
    maxSlider.min = annoMin;
    maxSlider.max = annoMax;
    maxSlider.value = annoMax;
    minLabel.textContent = annoMin;
    maxLabel.textContent = annoMax;
    
    function aggiornaTrack() {
        const min = parseInt(minSlider.value);
        const max = parseInt(maxSlider.value);
        const minVal = parseInt(minSlider.min);
        const maxVal = parseInt(maxSlider.max);
        const range = maxVal - minVal;
        
        const leftPercent = ((min - minVal) / range) * 100;
        const rightPercent = ((maxVal - max) / range) * 100;
        
        const track = document.getElementById('slider-track-fill');
        if (track) {
            track.style.left = leftPercent + '%';
            track.style.right = rightPercent + '%';
        }
    }
    
    minSlider.addEventListener('input', function() {
        const val = parseInt(this.value);
        const maxVal = parseInt(maxSlider.value);
        if (val > maxVal) {
            this.value = maxVal;
        }
        document.getElementById('anno-min-label').textContent = this.value;
        aggiornaTrack();
        applicaFiltri();
    });
    
    maxSlider.addEventListener('input', function() {
        const val = parseInt(this.value);
        const minVal = parseInt(minSlider.value);
        if (val < minVal) {
            this.value = minVal;
        }
        document.getElementById('anno-max-label').textContent = this.value;
        aggiornaTrack();
        applicaFiltri();
    });
    
    aggiornaTrack();
    
    document.querySelectorAll('select, input').forEach(el => {
        el.addEventListener('change', applicaFiltri);
    });
    
    document.getElementById('filtro-testo').addEventListener('input', applicaFiltri);
    document.getElementById('reset-filtri').addEventListener('click', resetFiltri);
}

function popolaSelect(id, items) {
    const select = document.getElementById(id);
    const sorted = Array.from(items).sort();
    const allOption = select.querySelector('option[value="all"]');
    select.innerHTML = '';
    if (allOption) {
        select.appendChild(allOption);
    } else {
        const opt = document.createElement('option');
        opt.value = 'all';
        opt.textContent = 'Tutte';
        select.appendChild(opt);
    }
    sorted.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item;
        select.appendChild(opt);
    });
}

// ============================================================
// APPLICAZIONE FILTRI (CON ORDINAMENTO CRONOLOGICO)
// ============================================================

function applicaFiltri() {
    const orgSelezionate = getSelectedValues('filtro-organizzazione');
    const personeSelezionate = getSelectedValues('filtro-persona');
    const tipiSelezionati = getSelectedValues('filtro-tipo');
    const annoMinVal = parseInt(document.getElementById('filtro-anno-min').value);
    const annoMaxVal = parseInt(document.getElementById('filtro-anno-max').value);
    const testo = document.getElementById('filtro-testo').value.toLowerCase().trim();
    
    let risultati = documenti.filter(doc => {
        if (orgSelezionate.length > 0 && !orgSelezionate.some(o => doc.organizzazioni.includes(o))) {
            return false;
        }
        if (personeSelezionate.length > 0 && !personeSelezionate.some(p => doc.persone.includes(p))) {
            return false;
        }
        if (tipiSelezionati.length > 0 && !tipiSelezionati.includes(doc.tipo)) {
            return false;
        }
        if (doc.anno && (doc.anno < annoMinVal || doc.anno > annoMaxVal)) {
            return false;
        }
        if (testo) {
            const testoDoc = (doc.titolo + ' ' + doc.autore + ' ' + doc.keywords + ' ' + doc.serie).toLowerCase();
            if (!testoDoc.includes(testo)) {
                return false;
            }
        }
        return true;
    });
    
    // ORDINA CRONOLOGICAMENTE
    risultati.sort((a, b) => {
        if (a.anno === null && b.anno === null) return a.titolo.localeCompare(b.titolo);
        if (a.anno === null) return 1;
        if (b.anno === null) return -1;
        if (a.anno !== b.anno) return a.anno - b.anno;
        return a.titolo.localeCompare(b.titolo);
    });
    
    mostraRisultati(risultati);
}

function getSelectedValues(id) {
    const select = document.getElementById(id);
    const selected = Array.from(select.selectedOptions);
    if (selected.some(opt => opt.value === 'all')) {
        return [];
    }
    return selected.map(opt => opt.value);
}

// ============================================================
// VISUALIZZAZIONE RISULTATI (stile UMD - UNA RIGA)
// ============================================================

function mostraRisultati(risultati) {
    const container = document.getElementById('risultati-container');
    const conteggio = document.getElementById('risultati-conteggio');
    
    if (risultati.length === 0) {
        container.innerHTML = '<p class="nessun-risultato">Nessun documento trovato con i filtri selezionati.</p>';
        conteggio.textContent = '0 documenti';
        return;
    }
    
    conteggio.textContent = `${risultati.length} documenti`;
    
    let html = '';
    risultati.forEach(doc => {
        // 🔥 UNA SOLA RIGA DI METADATI: Autore · Organizzazione · Tipologia
        let metaParts = [];
        if (doc.autore && doc.autore !== 'N/A' && doc.autore !== '') {
            metaParts.push(doc.autore);
        }
        if (doc.organizzazione && doc.organizzazione !== '') {
            metaParts.push(doc.organizzazione);
        }
        if (doc.tipo && doc.tipo !== '') {
            metaParts.push(doc.tipo);
        }
        let metaLine = metaParts.length > 0 ? metaParts.join(' · ') : 'N/A';
        
        // 🔥 DESCRIZIONE (se disponibile)
        let descrizione = doc.descrizione || '';
        
        html += `
        <div class="risultato-card">
            <div class="risultato-data">${doc.data || 'n.d.'}</div>
            <div class="risultato-contenuto">
                <div class="risultato-titolo">
                    <a href="/archivio-maoismo-italiano/documenti/${doc.id}/">${doc.titolo}</a>
                </div>
                <div class="risultato-meta">${metaLine}</div>
                ${descrizione ? `<div class="risultato-desc">${descrizione}</div>` : ''}
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================================
// RESET FILTRI
// ============================================================

function resetFiltri() {
    document.querySelectorAll('select').forEach(sel => {
        const allOpt = sel.querySelector('option[value="all"]');
        if (allOpt) {
            Array.from(sel.options).forEach(opt => opt.selected = false);
            allOpt.selected = true;
        }
    });
    document.getElementById('filtro-testo').value = '';
    document.getElementById('filtro-anno-min').value = annoMin;
    document.getElementById('filtro-anno-max').value = annoMax;
    document.getElementById('anno-min-label').textContent = annoMin;
    document.getElementById('anno-max-label').textContent = annoMax;
    
    const minSlider = document.getElementById('filtro-anno-min');
    const maxSlider = document.getElementById('filtro-anno-max');
    const min = parseInt(minSlider.value);
    const max = parseInt(maxSlider.value);
    const minVal = parseInt(minSlider.min);
    const maxVal = parseInt(maxSlider.max);
    const range = maxVal - minVal;
    const leftPercent = ((min - minVal) / range) * 100;
    const rightPercent = ((maxVal - max) / range) * 100;
    const track = document.getElementById('slider-track-fill');
    if (track) {
        track.style.left = leftPercent + '%';
        track.style.right = rightPercent + '%';
    }
    
    applicaFiltri();
}

// ============================================================
// AVVIO
// ============================================================

document.addEventListener('DOMContentLoaded', caricaDati);