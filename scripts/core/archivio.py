import os
import re

from .site_config import site_path
from .utils import formatta_data, scarica_descrizione_ia, split_nomi


def genera_indice(df, output_dir, cache_manager=None):
    print("\nGenerazione della pagina Archivio con filtri...")
    
    schede = []
    anni_valori = []
    
    for index, row in df.iterrows():
        ami_id = str(row.get('id', '')).strip()
        if not ami_id:
            continue
        
        titolo = str(row.get('titolo', 'Senza titolo')).strip()
        if titolo in ['nan', 'None', '']:
            titolo = 'Senza titolo'
        
        data_raw = str(row.get('data', row.get('anno', ''))).strip()
        if data_raw in ['nan', 'None', '']:
            data_raw = 'n.d.'
        data_formattata, data_ordine = formatta_data(data_raw)
        
        tipo_raw = str(row.get('tipo', '')).strip()
        if tipo_raw in ['nan', 'None']:
            tipo_raw = ''
        tipo = tipo_raw.lower()
        # tipo_display: "testo_bilingue" diventa "testo" con maiuscola
        tipo_display = 'testo' if tipo == 'testo_bilingue' else tipo
        tipo_display = tipo_display.capitalize() if tipo_display else ''
        
        org = str(row.get('organizzazione', '')).strip()
        if org in ['nan', 'None']:
            org = ''
        autore_raw = str(row.get('autore', '')).strip()
        if autore_raw in ['nan', 'None']:
            autore_raw = ''
        
        url_ia = str(row.get('url', '#')).strip()
        descrizione = None
        if url_ia and url_ia != '#':
            match = re.search(r'/details/([^/?#]+)', url_ia)
            if match:
                identifier = match.group(1)
                # Usa cache_manager se disponibile per evitare download duplicati
                if cache_manager:
                    cached_metadata = cache_manager.get_ia_metadata(identifier)
                    if cached_metadata:
                        descrizione = cached_metadata.get('metadata', {}).get('description')
                    if not descrizione:
                        descrizione = scarica_descrizione_ia(identifier)
                        # Salva in cache per riutilizzo successivo
                        if descrizione:
                            cache_manager.set_ia_metadata(identifier, {'metadata': {'description': descrizione}})
                else:
                    descrizione = scarica_descrizione_ia(identifier)
        
        if autore_raw and autore_raw not in ['nan', 'None']:
            autori = split_nomi(autore_raw)
            autore_display = autori[0] if autori else 'N/A'
        else:
            autore_display = 'N/A'
        
        if data_ordine[0] != 9999:
            anni_valori.append(data_ordine[0])
        
        schede.append({
            'id': ami_id,
            'titolo': titolo,
            'data': data_formattata,
            'data_ordine': data_ordine,
            'tipo': tipo_display,
            'organizzazione': org,
            'autore': autore_display,
            'descrizione': descrizione
        })
    
    schede.sort(key=lambda x: (x['data_ordine'], x['titolo']))
    
    anno_min = min(anni_valori) if anni_valori else 1900
    anno_max = max(anni_valori) if anni_valori else 2025
    
    # I risultati saranno generati da JavaScript (paginazione)
    risultati_html = '<div id="risultati-loading" class="loading">Caricamento in corso...</div>'
    
    index_content = f"""---
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
        
        <div class="filtri-corpo" id="filtri-corpo">
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-organizzazione" aria-expanded="false" aria-controls="filtro-organizzazione-container">
                <span>Organizzazione</span>
                <span class="toggle-icon" aria-hidden="true">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-organizzazione-container">
                <select id="filtro-organizzazione" multiple aria-label="Filtra per organizzazione">
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-persona" aria-expanded="false" aria-controls="filtro-persona-container">
                <span>Persona</span>
                <span class="toggle-icon" aria-hidden="true">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-persona-container">
                <select id="filtro-persona" multiple aria-label="Filtra per persona">
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-tipo" aria-expanded="false" aria-controls="filtro-tipo-container">
                <span>Tipologia</span>
                <span class="toggle-icon" aria-hidden="true">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-tipo-container">
                <select id="filtro-tipo" multiple aria-label="Filtra per tipologia">
                    <option value="all">Tutte</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-argomento" aria-expanded="false" aria-controls="filtro-argomento-container">
                <span>Argomenti</span>
                <span class="toggle-icon" aria-hidden="true">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-argomento-container">
                <select id="filtro-argomento" multiple aria-label="Filtra per argomenti">
                    <option value="all">Tutti</option>
                </select>
            </div>
        </div>
        
        <div class="filtro-gruppo collapsible">
            <button type="button" class="filtro-toggle" id="toggle-anno" aria-expanded="false" aria-controls="filtro-anno-container">
                <span>Anno</span>
                <span class="toggle-icon" aria-hidden="true">▼</span>
            </button>
            <div class="filtro-contenuto" id="filtro-anno-container">
                <div class="slider-container" id="slider-container">
                    <div class="slider-histogram" id="slider-histogram"></div>
                    <div class="slider-track">
                        <div class="slider-track-fill" id="slider-track-fill"></div>
                    </div>
                    <input type="range" id="filtro-anno-min" min="{anno_min}" max="{anno_max}" value="{anno_min}" aria-label="Anno iniziale">
                    <input type="range" id="filtro-anno-max" min="{anno_min}" max="{anno_max}" value="{anno_max}" aria-label="Anno finale">
                    <div class="slider-labels">
                        <span id="anno-min-label">{anno_min}</span>
                        <span id="anno-max-label">{anno_max}</span>
                    </div>
                </div>
            </div>
        </div>
        
        </div>
        
        <div class="filtro-gruppo">
            <label for="filtro-testo">Cerca nel testo</label>
            <input type="text" id="filtro-testo" placeholder="Cerca titolo, autore...">
        </div>
        
        <div class="filtri-azioni">
            <button type="button" id="reset-filtri"><span aria-hidden="true">↺</span> Reset</button>
            <span id="risultati-conteggio" role="status" aria-live="polite"></span>
        </div>
    </aside>

    <!-- RISULTATI -->
    <div class="risultati-main">
        <div id="filtri-attivi" class="filtri-attivi"></div>
        <div id="risultati-container">
            {risultati_html}
        </div>
        <!-- PAGINAZIONE -->
        <nav id="paginazione" class="paginazione-container" aria-label="Pagine dei risultati"></nav>
    </div>

</div>

<link rel="stylesheet" href="{site_path('stylesheets/archivio.css')}">
"""
    
    index_path = os.path.join(output_dir, 'documenti', 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"Pagina Archivio generata con {len(schede)} schede.")
    print(f"Intervallo anni: {anno_min} - {anno_max}")

