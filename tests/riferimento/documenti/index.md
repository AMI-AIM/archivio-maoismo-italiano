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
        <div class="filtri-testata">
            <h2 class="filtri-titolo">Filtri</h2>
            <button type="button" class="filtri-mostra" id="filtri-mostra" aria-expanded="false" aria-controls="filtri-corpo">
                <span class="filtri-mostra__etichetta">Mostra filtri</span>
                <span class="filtri-mostra__conteggio" id="filtri-mostra-conteggio"></span>
            </button>
        </div>
        
        <div class="filtro-gruppo filtro-gruppo--testo">
            <label for="filtro-testo">Cerca nel testo</label>
            <input type="search" id="filtro-testo" placeholder="Titolo, nome, segnatura…">
        </div>

        <div class="filtri-corpo" id="filtri-corpo">
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-organizzazione" aria-expanded="false" aria-controls="filtro-organizzazione-container">
                <span>Organizzazione<span class="filtro-toggle__attivi" id="attivi-organizzazione"></span></span>
                <svg class="toggle-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 10l5 5 5-5z"/></svg>
            </button>
            <div class="filtro-contenuto" id="filtro-organizzazione-container">
                <div class="filtro-spunte" id="filtro-organizzazione" role="group" aria-label="Filtra per organizzazione"></div>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-persona" aria-expanded="false" aria-controls="filtro-persona-container">
                <span>Persona<span class="filtro-toggle__attivi" id="attivi-persona"></span></span>
                <svg class="toggle-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 10l5 5 5-5z"/></svg>
            </button>
            <div class="filtro-contenuto" id="filtro-persona-container">
                <div class="filtro-spunte" id="filtro-persona" role="group" aria-label="Filtra per persona"></div>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-tipo" aria-expanded="false" aria-controls="filtro-tipo-container">
                <span>Tipologia<span class="filtro-toggle__attivi" id="attivi-tipo"></span></span>
                <svg class="toggle-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 10l5 5 5-5z"/></svg>
            </button>
            <div class="filtro-contenuto" id="filtro-tipo-container">
                <div class="filtro-spunte" id="filtro-tipo" role="group" aria-label="Filtra per tipologia"></div>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-argomento" aria-expanded="false" aria-controls="filtro-argomento-container">
                <span>Percorsi tematici<span class="filtro-toggle__attivi" id="attivi-argomento"></span></span>
                <svg class="toggle-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 10l5 5 5-5z"/></svg>
            </button>
            <div class="filtro-contenuto" id="filtro-argomento-container">
                <div class="filtro-spunte" id="filtro-argomento" role="group" aria-label="Filtra per percorso tematico"></div>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-anno" aria-expanded="false" aria-controls="filtro-anno-container">
                <span>Anno</span>
                <svg class="toggle-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 10l5 5 5-5z"/></svg>
            </button>
            <div class="filtro-contenuto" id="filtro-anno-container">
                <div class="slider-container" id="slider-container">
                    <div class="slider-histogram" id="slider-histogram"></div>
                    <div class="slider-track">
                        <div class="slider-track-fill" id="slider-track-fill"></div>
                    </div>
                    <input type="range" id="filtro-anno-min" min="1967" max="1978" value="1967" aria-label="Anno iniziale">
                    <input type="range" id="filtro-anno-max" min="1967" max="1978" value="1978" aria-label="Anno finale">
                    <div class="slider-labels">
                        <span id="anno-min-label">1967</span>
                        <span id="anno-max-label">1978</span>
                    </div>
                </div>
            </div>
        </div>
        
        </div>

        
        <div class="filtri-azioni" id="filtri-azioni" hidden>
            <button type="button" id="reset-filtri">Azzera filtri</button>
        </div>
    </aside>

    <!-- RISULTATI -->
    <div class="risultati-main">
        <!-- Testata dei risultati: quanti sono e in che ordine. Il conteggio
             stava nel pannello filtri, lontano dalla lista (e nascosto su
             mobile quando i filtri sono chiusi). -->
        <div class="risultati-testata">
            <span id="risultati-conteggio" role="status" aria-live="polite"></span>
            <div class="risultati-ordina">
                <label for="ordina-risultati">Ordina per</label>
                <select id="ordina-risultati">
                    <option value="data">Data, dalla più vecchia</option>
                    <option value="data-desc">Data, dalla più recente</option>
                    <option value="titolo">Titolo, A–Z</option>
                </select>
            </div>
        </div>
        <div id="filtri-attivi" class="filtri-attivi"></div>
        <div id="risultati-container">
            <div id="risultati-loading" class="loading">Caricamento in corso...</div>
        </div>
        <!-- PAGINAZIONE -->
        <nav id="paginazione" class="paginazione-container" aria-label="Pagine dei risultati"></nav>
    </div>

</div>
