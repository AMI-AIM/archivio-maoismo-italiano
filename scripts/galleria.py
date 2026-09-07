import pandas as pd
import os
import re
from urllib.parse import quote

def parse_year(date_str):
    """Estrae l'anno da vari formati di data. Restituisce None se non trova."""
    if pd.isna(date_str): return None
    s = str(date_str).strip()
    
    # Cerca anno a 4 cifre (19xx o 20xx)
    m = re.search(r'\b(19\d{2}|20\d{2})\b', s)
    if m: return int(m.group(1))
    
    # Cerca anno a 2 cifre (es. 68 -> 1968)
    # Assumiamo che nel contesto di questo archivio siano tutti '900
    m = re.search(r'\b(\d{2})\b', s)
    if m:
        y = int(m.group(1))
        return 1900 + y
        
    return None

def get_img_url(row):
    """Costruisce l'URL dell'immagine da Internet Archive."""
    url = row.get('URL')
    nome_file = row.get('Nome_file')
    
    if not url or pd.isna(url): return None
    
    # Estrai identifier (es. da .../details/abc-123/mode/2up -> abc-123)
    m = re.search(r'details/([^/]+)', str(url))
    if not m: return None
    identifier = m.group(1)
    
    # Se c'è il nome file specifico, usa quello (per avere il manifesto/foto esatta)
    if nome_file and not pd.isna(nome_file):
        # quote() gestisce spazi e caratteri speciali nell'URL
        return f"https://archive.org/download/{identifier}/{quote(str(nome_file))}"
    else:
        # Fallback all'immagine di copertina dell'item
        return f"https://archive.org/services/img/{identifier}"

def generate_gallery():
    print("Generazione Galleria in corso...")
    
    # 1. Carica dati
    try:
        df = pd.read_excel('data/dati.xlsx')
    except FileNotFoundError:
        print("Errore: data/dati.xlsx non trovato.")
        return

    # 2. Filtra per Foto e Manifesti
    # La colonna 'Tipo' contiene i valori
    mask = df['Tipo'].astype(str).str.contains('Foto|Manifesto', case=False, na=False)
    df_gal = df[mask].copy()
    
    if df_gal.empty:
        print("Nessun documento trovato con Tipo 'Foto' o 'Manifesto'.")
        return

    # 3. Parsing Anno e Ordinamento
    df_gal['Anno'] = df_gal['Data'].apply(parse_year)
    
    # Ordina per Anno (i None/NaN vanno in fondo)
    df_gal = df_gal.sort_values(by='Anno', na_position='last')
    
    # 4. Prepara output
    os.makedirs('build/galleria', exist_ok=True)
    
    # 5. Genera HTML
    html_content = """---
hide:
  - navigation
  - toc
---

<!-- Galleria Fotografica - Archivio Maoismo Italiano -->
<div class="galleria-wrapper">
  <header class="galleria-header">
    <h1 class="galleria-main-title">Galleria Fotografica</h1>
    <p class="galleria-subtitle">Documenti visivi dalla storia del maoismo italiano</p>
  </header>

  <div class="galleria-layout">
    <nav class="galleria-timeline" id="galleria-timeline" aria-label="Timeline anni">
      <div class="timeline-header">
        <span class="timeline-label">Anni</span>
      </div>
      <ul class="timeline-list">
"""
    
    # Genera indici timeline
    anni_unici = df_gal['Anno'].dropna().unique()
    anni_ordinati = sorted(anni_unici)
    for idx, anno in enumerate(anni_ordinati):
        year_int = int(anno)
        active_class = " active" if idx == 0 else ""
        html_content += f'        <li><a href="#anno-{year_int}" data-year="{year_int}" class="timeline-link{active_class}">{year_int}</a></li>\n'
    
    if df_gal['Anno'].isna().any():
        html_content += '        <li><a href="#anno-sd" data-year="s.d." class="timeline-link">s.d.</a></li>\n'

    html_content += """      </ul>
    </nav>

    <main class="galleria-content">
      <div class="galleria-year-badge" id="galleria-year-badge" aria-live="polite">
        <span class="badge-label">Anno</span>
        <span class="badge-year" id="badge-year-value">1968</span>
      </div>
"""

    # Genera sezioni per anno
    current_year = None
    card_count = 0
    for index, row in df_gal.iterrows():
        anno = row['Anno']
        
        # Apri nuova sezione se l'anno cambia
        if anno != current_year:
            if current_year is not None:
                html_content += "        </div>\n      </section>\n" # Chiudi griglia e sezione
            
            current_year = anno
            anno_label = str(int(anno)) if pd.notna(anno) else "Anni non definiti"
            section_id = f"anno-{int(anno)}" if pd.notna(anno) else "anno-sd"
            
            html_content += f"""
      <section id="{section_id}" class="galleria-year-section" data-year="{anno_label}">
        <h2 class="galleria-year-title">
          <span class="year-number">{anno_label}</span>
          <span class="year-divider"></span>
        </h2>
        <div class="galleria-grid">
"""
        
        # Card
        titolo = row.get('Titolo', 'Senza titolo')
        org = row.get('Organizzazione', '')
        data_str = row.get('Data', '')
        img_url = get_img_url(row)
        link_url = row.get('URL', '#') # Link a Internet Archive
        
        # Fallback immagine
        if not img_url:
            img_url = "https://archive.org/services/img/default"
        
        # Sanitizza attributi HTML
        titolo_attr = titolo.replace('"', '&quot;')
        card_count += 1

        html_content += f"""
          <article class="galleria-card" data-order="{card_count}">
            <a href="{link_url}" target="_blank" rel="noopener noreferrer" class="card-link">
              <div class="galleria-img-container">
                <img src="{img_url}" alt="{titolo_attr}" class="galleria-img" loading="lazy" decoding="async">
                <div class="img-overlay">
                  <span class="overlay-icon">🔍</span>
                </div>
              </div>
              <div class="galleria-meta">
                <h3 class="meta-title">{titolo}</h3>
                {f'<span class="meta-date">{data_str}</span>' if pd.notna(data_str) and str(data_str).strip() else ''}
                {f'<span class="meta-org">{org}</span>' if pd.notna(org) and str(org).strip() else ''}
              </div>
            </a>
          </article>
"""

    # Chiudi ultima sezione
    if current_year is not None:
        html_content += "        </div>\n      </section>\n"

    html_content += """
    </main>
  </div>
</div>

<script src="../../assets/javascripts/galleria.js"></script>
"""

    # 6. Salva file
    with open('build/galleria/index.md', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Galleria generata con successo in build/galleria/index.md")

if __name__ == "__main__":
    generate_gallery()