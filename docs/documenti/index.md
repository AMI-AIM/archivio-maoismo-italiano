---
title: "Archivio"
hide:
  - navigation
  - toc
---

# Archivio

<div id="archivio-container" class="archivio-layout">

    <!-- SIDEBAR FILTRI COLLASSABILI -->
    <aside class="filtri-sidebar" id="filtri-sidebar">
        <h4>Filtri</h4>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-organizzazione">
                <span>Organizzazione</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-organizzazione-container">
                <select id="filtro-organizzazione" multiple>
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-persona">
                <span>Persona</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-persona-container">
                <select id="filtro-persona" multiple>
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-tipo">
                <span>Tipologia</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-tipo-container">
                <select id="filtro-tipo" multiple>
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-anno">
                <span>Anno</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-anno-container">
                <div class="slider-container">
                    <span id="anno-min-label">1964</span>
                    <input type="range" id="filtro-anno-min" min="1964" max="1992" value="1964">
                    <input type="range" id="filtro-anno-max" min="1964" max="1992" value="1992">
                    <span id="anno-max-label">1992</span>
                </div>
            </div>
        </div>
        
        <div class="filtro-gruppo">
            <label for="filtro-testo">Cerca nel testo</label>
            <input type="text" id="filtro-testo" placeholder="Cerca titolo, autore, keywords...">
        </div>
        
        <div class="filtri-azioni">
            <button id="reset-filtri">↺ Reset</button>
            <span id="risultati-conteggio"></span>
        </div>
    </aside>

    <!-- RISULTATI -->
    <main class="risultati-main">
        <div id="risultati-container">
            <p class="loading">Caricamento in corso...</p>
        </div>
    </main>

</div>

<script src="/archivio-maoismo-italiano/archivio-filtri.js"></script>

<style>
.archivio-layout {
    display: flex;
    gap: 2rem;
    align-items: flex-start;
    margin-top: 1rem;
}

.filtri-sidebar {
    flex: 0 0 260px;
    background: var(--md-code-bg-color);
    padding: 1.2rem 1.2rem 1.5rem 1.2rem;
    border-radius: 8px;
    border: 1px solid var(--md-default-fg-color--lightest);
    position: sticky;
    top: 1.5rem;
    max-height: 90vh;
    overflow-y: auto;
}

.filtri-sidebar h4 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    padding-bottom: 0.5rem;
}

.filtro-gruppo {
    margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
}

.filtro-toggle {
    background: none;
    border: none;
    padding: 0.5rem 0;
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--md-default-fg-color);
    cursor: pointer;
    transition: color 0.15s;
}

.filtro-toggle:hover {
    color: var(--md-primary-fg-color);
}

.filtro-toggle .toggle-icon {
    font-size: 0.6rem;
    transition: transform 0.25s ease;
}

.filtro-toggle.open .toggle-icon {
    transform: rotate(180deg);
}

.filtro-contenuto {
    padding: 0.2rem 0 0.8rem 0;
    display: none;
}

.filtro-contenuto.open {
    display: block;
}

.filtro-gruppo label {
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--md-default-fg-color--light);
    margin-bottom: 0.2rem;
}

.filtro-gruppo select,
.filtro-gruppo input[type="text"] {
    width: 100%;
    padding: 0.3rem 0.5rem;
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 4px;
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    font-size: 0.85rem;
}

.filtro-gruppo select[multiple] {
    height: auto;
    min-height: 60px;
}

.filtro-gruppo select[multiple] option {
    padding: 0.15rem 0.3rem;
}

.filtro-gruppo select[multiple] option:checked {
    background: var(--md-primary-fg-color);
    color: var(--md-primary-bg-color);
}

.slider-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-top: 0.2rem;
}

.slider-container input[type="range"] {
    flex: 1;
    min-width: 60px;
    height: 4px;
    -webkit-appearance: none;
    background: var(--md-default-fg-color--lightest);
    border-radius: 2px;
}

.slider-container input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    cursor: pointer;
}

.slider-container input[type="range"]::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    cursor: pointer;
    border: none;
}

.slider-container span {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
    min-width: 35px;
}

.filtri-azioni {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.8rem;
    flex-wrap: wrap;
    gap: 0.3rem;
    border-top: 1px solid var(--md-default-fg-color--lightest);
    padding-top: 0.8rem;
}

#reset-filtri {
    padding: 0.2rem 0.8rem;
    background: var(--md-default-fg-color--lightest);
    border: none;
    border-radius: 4px;
    color: var(--md-default-fg-color);
    font-size: 0.75rem;
    cursor: pointer;
    transition: background 0.15s;
}

#reset-filtri:hover {
    background: var(--md-default-fg-color--lighter);
}

#risultati-conteggio {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
}

.risultati-main {
    flex: 1;
    min-width: 0;
}

.risultato-card {
    display: flex;
    align-items: flex-start;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    transition: background 0.15s;
    gap: 1.5rem;
}

.risultato-card:hover {
    background: var(--md-code-bg-color);
}

.risultato-data {
    flex: 0 0 140px;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
    white-space: nowrap;
    padding-top: 0.05rem;
}

.risultato-contenuto {
    flex: 1;
    min-width: 0;
}

.risultato-titolo {
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 0.1rem;
}

.risultato-titolo a {
    text-decoration: none;
    color: var(--md-default-fg-color);
}

.risultato-titolo a:hover {
    text-decoration: underline;
    color: var(--md-primary-fg-color);
}

.risultato-sommario {
    font-size: 0.9rem;
    color: var(--md-default-fg-color--light);
    margin-bottom: 0.1rem;
}

.risultato-badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
}

.badge {
    display: inline-block;
    font-size: 0.6rem;
    font-weight: 600;
    padding: 0.05rem 0.5rem;
    border-radius: 4px;
    background: var(--md-code-bg-color);
    color: var(--md-default-fg-color--light);
    border: 1px solid var(--md-default-fg-color--lightest);
}

.org-badge {
    background: var(--md-primary-fg-color--light);
    color: var(--md-primary-fg-color);
    border-color: var(--md-primary-fg-color);
}

.tipo-badge {
    background: var(--md-primary-fg-color);
    color: var(--md-primary-bg-color);
    border-color: var(--md-primary-fg-color);
}

.nessun-risultato {
    text-align: center;
    padding: 2rem;
    color: var(--md-default-fg-color--light);
}

.loading {
    text-align: center;
    padding: 2rem;
    color: var(--md-default-fg-color--light);
}

@media (max-width: 768px) {
    .archivio-layout {
        flex-direction: column;
    }
    .filtri-sidebar {
        flex: 0 0 auto;
        position: static;
        max-height: none;
        width: 100%;
    }
    .risultato-card {
        flex-direction: column;
        gap: 0.1rem;
        padding: 0.6rem 0.4rem;
    }
    .risultato-data {
        flex: 0 0 auto;
        white-space: normal;
        font-size: 0.85rem;
    }
}
</style>
