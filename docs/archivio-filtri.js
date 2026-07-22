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
        applicaFiltri();
    } catch (error) {
        console.error('Errore nel caricamento dei dati:', error);
        document.getElementById('risultati-container').innerHTML = '<p class="nessun-risultato">Errore nel caricamento dei dati.</p>';
    }
}

// ============================================================
// INIZIALIZZAZIONE FILTRI (con collassabilità)
// ============================================================

function inizializzaFiltri() {
    // 🔥 ATTIVA I FILTRI COLLASSABILI
    document.querySelectorAll('.filtro-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true' || false;
            this.setAttribute('aria-expanded', !expanded);
            const content = this.parentElement.querySelector('.filtro-contenuto');
            if (content) {
                content.style.display = expanded ? 'none' : 'block';
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
    const inputMin = document.getElementById('filtro-anno-min');
    const inputMax = document.getElementById('filtro-anno-max');
    const labelMin = document.getElementById('anno-min-label');
    const labelMax = document.getElementById('anno-max-label');
    
    inputMin.min = annoMin;
    inputMin.max = annoMax;
    inputMin.value = annoMin;
    inputMax.min = annoMin;
    inputMax.max = annoMax;
    inputMax.value = annoMax;
    labelMin.textContent = annoMin;
    labelMax.textContent = annoMax;
    
    // Event listeners
    inputMin.addEventListener('input', function() {
        const val = parseInt(this.value);
        const maxVal = parseInt(inputMax.value);
        if (val > maxVal) {
            inputMax.value = val;
            labelMax.textContent = val;
        }
        labelMin.textContent = val;
        applicaFiltri();
    });
    
    inputMax.addEventListener('input', function() {
        const val = parseInt(this.value);
        const minVal = parseInt(inputMin.value);
        if (val < minVal) {
            inputMin.value = val;
            labelMin.textContent = val;
        }
        labelMax.textContent = val;
        applicaFiltri();
    });
    
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
// APPLICAZIONE FILTRI
// ============================================================

function applicaFiltri() {
    const orgSelezionate = getSelectedValues('filtro-organizzazione');
    const personeSelezionate = getSelectedValues('filtro-persona');
    const tipiSelezionati = getSelectedValues('filtro-tipo');
    const annoMinVal = parseInt(document.getElementById('filtro-anno-min').value);
    const annoMaxVal = parseInt(document.getElementById('filtro-anno-max').value);
    const testo = document.getElementById('filtro-testo').value.toLowerCase().trim();
    
    const risultati = documenti.filter(doc => {
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
// VISUALIZZAZIONE RISULTATI (layout compatto)
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
        const icona = getIcona(doc.tipo);
        const personeBadge = doc.persone.map(p => `<span class="badge">${p}</span>`).join('');
        const orgBadge = doc.organizzazioni.map(o => `<span class="badge org-badge">${o}</span>`).join('');
        
        html += `
        <div class="risultato-card">
            <div class="risultato-data">${doc.data || 'n.d.'}</div>
            <div class="risultato-titolo">
                <a href="/archivio-maoismo-italiano/documenti/${doc.id}/">${icona} ${doc.titolo}</a>
            </div>
            <div class="risultato-badge-container">
                ${orgBadge}
                ${personeBadge}
                ${doc.tipo ? `<span class="badge tipo-badge">${doc.tipo}</span>` : ''}
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

function getIcona(tipo) {
    if (!tipo) return '📄';
    const t = tipo.toLowerCase();
    if (t === 'opuscolo') return '📘';
    if (t === 'manifesto') return '🖼️';
    if (t === 'foto' || t === 'fotografia') return '📷';
    if (t === 'periodico') return '📰';
    if (t === 'volantino') return '📃';
    if (t === 'libro') return '📕';
    if (t === 'audio') return '🎵';
    return '📄';
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
    applicaFiltri();
}

// ============================================================
// AVVIO
// ============================================================

document.addEventListener('DOMContentLoaded', caricaDati);