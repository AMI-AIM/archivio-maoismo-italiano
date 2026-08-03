---
title: "Archivio"
hide:
  - navigation
  - toc
---

# Archivio

<div id="archivio-container" class="archivio-layout">

    <!-- SIDEBAR FILTRI -->
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
            <button class="filtro-toggle" id="toggle-argomento">
                <span>Argomenti</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-argomento-container">
                <select id="filtro-argomento" multiple>
                    <option value="all">Tutti</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button class="filtro-toggle" id="toggle-anno">
                <span>Anno</span>
                <span class="toggle-icon">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-anno-container">
                <div class="slider-container" id="slider-container">
                    <div class="slider-track">
                        <div class="slider-track-fill" id="slider-track-fill"></div>
                    </div>
                    <input type="range" id="filtro-anno-min" min="1964" max="1993" value="1964">
                    <input type="range" id="filtro-anno-max" min="1964" max="1993" value="1993">
                    <div class="slider-labels">
                        <span id="anno-min-label">1964</span>
                        <span id="anno-max-label">1993</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="filtro-gruppo">
            <label for="filtro-testo">Cerca nel testo</label>
            <input type="text" id="filtro-testo" placeholder="Cerca titolo, autore...">
        </div>
        
        <div class="filtri-azioni">
            <button id="reset-filtri">↺ Reset</button>
            <span id="risultati-conteggio"></span>
        </div>
    </aside>

    <!-- RISULTATI -->
    <main class="risultati-main">
        <div id="risultati-container">
            <div id="risultati-loading" class="loading">Caricamento in corso...</div>
        </div>
        <div id="paginazione" class="paginazione-container"></div>
    </main>

</div>

<script src="/archivio-maoismo-italiano/javascripts/archivio-filtri.js"></script>

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
    position: relative;
    width: 100%;
    margin-top: 1.7rem;
    margin-bottom: 0.5rem;
    height: 50px;
}

.slider-track {
    position: absolute;
    width: 100%;
    height: 6px;
    top: 50%;
    transform: translateY(-50%);
    background: var(--md-default-fg-color--lightest);
    border-radius: 3px;
}

.slider-track-fill {
    position: absolute;
    height: 100%;
    background: var(--md-primary-fg-color);
    border-radius: 3px;
    left: 0%;
    right: 0%;
}

.slider-value-pill {
    position: absolute;
    bottom: 50%;
    margin-bottom: 14px;
    transform: translateX(-50%);
    background: var(--md-default-bg-color);
    border: 1.5px solid var(--md-primary-fg-color);
    border-radius: 20px;
    padding: 0.1rem 0.6rem;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--md-primary-fg-color);
    white-space: nowrap;
    pointer-events: none;
    transition: left 0.05s ease;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    z-index: 5;
    line-height: 1.4;
}

.slider-container input[type="range"] {
    position: absolute;
    width: 100%;
    top: 0;
    left: 0;
    height: 100%;
    -webkit-appearance: none;
    appearance: none;
    background: transparent;
    pointer-events: none;
    margin: 0;
    padding: 0;
    z-index: 10;
}

.slider-container input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    cursor: pointer;
    pointer-events: auto;
    border: 2px solid var(--md-default-bg-color);
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    z-index: 12;
    margin-top: -7px;
    transition: transform 0.15s, box-shadow 0.15s;
}

.slider-container input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

.slider-container input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--md-primary-fg-color);
    cursor: pointer;
    pointer-events: auto;
    border: 2px solid var(--md-default-bg-color);
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    z-index: 12;
    transition: transform 0.15s, box-shadow 0.15s;
}

.slider-container input[type="range"]::-moz-range-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

.slider-container input[type="range"]::-webkit-slider-runnable-track {
    height: 6px;
    background: transparent;
    border-radius: 3px;
}

.slider-container input[type="range"]::-moz-range-track {
    height: 6px;
    background: transparent;
    border-radius: 3px;
}

.slider-labels {
    display: none;
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
    flex-direction: column;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--md-default-fg-color--lightest);
    transition: background 0.15s;
}

.risultato-card:hover {
    background: var(--md-code-bg-color);
}

.risultato-data {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--md-primary-fg-color);
}

.risultato-titolo {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0.1rem 0;
}

.risultato-titolo a {
    text-decoration: none;
    color: var(--md-default-fg-color);
}

.risultato-titolo a:hover {
    text-decoration: underline;
    color: var(--md-primary-fg-color);
}

.risultato-meta {
    font-size: 0.85rem;
    color: var(--md-default-fg-color--light);
    margin: 0.1rem 0;
}

.risultato-desc {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    max-height: 4.5em;
    margin: 0.1rem 0 0 0;
    font-size: 0.9rem;
    color: var(--md-default-fg-color--light);
    line-height: 1.5;
}

.risultato-desc p {
    margin: 0;
}

.risultato-desc strong,
.risultato-desc b {
    font-weight: 600;
}

.risultato-desc em,
.risultato-desc i {
    font-style: italic;
}

.risultato-desc ul,
.risultato-desc ol {
    padding-left: 1.5rem;
    margin: 0.6rem 0;
}

.risultato-desc li {
    margin: 0.2rem 0;
}

.risultato-desc * {
    font-size: inherit !important;
    font-family: inherit !important;
    color: inherit !important;
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

.paginazione-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.4rem;
    margin-top: 1.5rem;
    padding: 0.5rem 0;
    flex-wrap: wrap;
}

.pag-btn {
    background: var(--md-code-bg-color);
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 4px;
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--md-default-fg-color);
    cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    min-width: 36px;
    text-align: center;
}

.pag-btn:hover:not(.pag-btn--disabled) {
    background: var(--md-primary-fg-color);
    color: #ffffff;
    border-color: var(--md-primary-fg-color);
}

.pag-btn--active {
    background: var(--md-primary-fg-color);
    color: #ffffff !important;
    border-color: var(--md-primary-fg-color);
}

.pag-btn--disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

.pag-btn--nav {
    background: transparent;
    border: none;
    font-size: 0.9rem;
    color: var(--md-default-fg-color--light);
}

.pag-btn--nav:hover:not(.pag-btn--disabled) {
    color: var(--md-primary-fg-color);
    background: transparent;
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
        padding: 0.6rem 0.4rem;
    }
    .risultato-titolo {
        font-size: 1rem;
    }
    .risultato-meta {
        font-size: 0.8rem;
    }
    .risultato-desc {
        font-size: 0.85rem;
    }
    .pag-btn {
        padding: 0.2rem 0.5rem;
        font-size: 0.75rem;
        min-width: 30px;
    }
}
</style>
