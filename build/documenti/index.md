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
                    <div class="slider-histogram" id="slider-histogram"></div>
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
        <div id="filtri-attivi" class="filtri-attivi"></div>
        <div id="risultati-container">
            <div id="risultati-loading" class="loading">Caricamento in corso...</div>
        </div>
        <!-- PAGINAZIONE -->
        <div id="paginazione" class="paginazione-container"></div>
    </main>

</div>

<link rel="stylesheet" href="/archivio-maoismo-italiano/stylesheets/archivio.css">
