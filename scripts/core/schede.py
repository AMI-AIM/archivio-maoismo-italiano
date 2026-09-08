import html
import os
import re
import urllib.parse
import pandas as pd
from .argomenti import build_argomenti_index, find_topic_column, get_argomento_slug
from .citazioni import (
    CITAZIONI_TEMPLATE_VERSION,
    costruisci_payload_citazione,
    json_per_script,
    sanitize_citation_id,
    yaml_value,
)
from .schema_generator import SchemaGenerator
from .site_config import site_path, site_url
from .soggetti import crea_link, link_lista
from .utils import (
    formatta_data,
    pulisci_per_meta_description,
    scarica_descrizione_ia,
    scarica_testo_ia,
    split_nomi,
)

def crea_schede(df, persone, organizzazioni, output_dir, cache_manager=None):
    """
    Crea le schede documento.
    
    Args:
        df: DataFrame catalogo.
        persone: dict persone.
        organizzazioni: dict organizzazioni.
        output_dir: directory output (build/).
        cache_manager: CacheManager opzionale.
    
    Returns:
        tuple: (schede_generate, schede_saltate)
    """
    print("📄 Creazione delle schede dei documenti...")
    documenti_dir = os.path.join(output_dir, "documenti")
    os.makedirs(documenti_dir, exist_ok=True)
    # Colonna argomenti/serie: stessa logica condivisa usata da
    # scripts/argomenti.py (core/argomenti.find_topic_column), cosi' le due
    # generazioni restano sempre sincronizzate anche se il foglio Excel
    # usa un alias diverso da 'serie'. Bug corretto: prima questa funzione
    # leggeva sempre e solo la colonna 'serie' in modo hardcoded.
    topic_column = find_topic_column(df) or 'serie'
    argomenti_index = build_argomenti_index(df, topic_column=topic_column)
    contatore_generati = 0
    contatore_saltati = 0
    
    for index, row in df.iterrows():
        ami_id = str(row.get("id", "")).strip()
        if not ami_id or pd.isna(row.get("id")):
            continue
        
        file_path = os.path.join(documenti_dir, f"{ami_id}.md")
        
        row_hash = None
        if cache_manager:
            hash_input = {
                "source": row.to_dict(),
                "template_version": CITAZIONI_TEMPLATE_VERSION,
            }
            row_hash = cache_manager.hash_data(hash_input)
        
        if cache_manager and os.path.exists(file_path):
            cached_data = cache_manager.get_doc_metadata(ami_id)
            cached_hash = (cached_data or {}).get("data", {}).get("source_hash")
            if cached_hash == row_hash:
                contatore_saltati += 1
                print(f"   ⏭️ Saltato {ami_id} (cache valido)")
                continue
        
        # =====================================================================
        # PARSING DATI DALLA RIGA EXCEL
        # =====================================================================
        titolo = str(row.get("titolo", "Senza titolo")).strip()
        if titolo in ("nan", "None", ""):
            titolo = "Senza titolo"
        
        autore_raw = str(row.get("autore", "")).strip()
        if autore_raw in ("nan", "None"):
            autore_raw = ""
        
        org_raw = str(row.get("organizzazione", "")).strip()
        if org_raw in ("nan", "None"):
            org_raw = ""
        
        luogo_raw = str(row.get("luogo", "")).strip()
        if luogo_raw in ("nan", "None"):
            luogo_raw = ""
        
        editore_raw = str(row.get("editore", "")).strip()
        if editore_raw in ("nan", "None"):
            editore_raw = ""
        
        provenienza_raw = str(row.get("provenienza", "")).strip()
        if provenienza_raw in ("nan", "None"):
            provenienza_raw = ""
        
        persone_collegate = str(row.get("persone_collegate", "")).strip()
        if persone_collegate in ("nan", "None"):
            persone_collegate = ""
        
        organizzazioni_collegate = str(row.get("organizzazioni_collegate", "")).strip()
        if organizzazioni_collegate in ("nan", "None"):
            organizzazioni_collegate = ""
        
        data_raw = str(row.get("data", row.get("anno", ""))).strip()
        if data_raw in ("nan", "None", ""):
            data_raw = ""
        
        data_formattata, data_ordine = formatta_data(data_raw)
        
        anno_pubblicazione = ""
        if data_ordine and data_ordine[0] != 9999:
            anno_pubblicazione = str(data_ordine[0])
        
        tipo_raw = str(row.get("tipo", "")).strip()
        if tipo_raw in ("nan", "None"):
            tipo_raw = ""
        
        tipo = tipo_raw.lower()
        if tipo == "fotografia":
            tipo = "foto"
        
        tipo_display = "testo" if tipo == "testo_bilingue" else tipo
        tipo_display = tipo_display.capitalize() if tipo_display else ""
        
        serie = str(row.get(topic_column, "")).strip()
        if serie in ("nan", "None"):
            serie = ""
        
        url_ia = str(row.get("url", "#")).strip()
        if url_ia in ("nan", "None", ""):
            url_ia = "#"
        
        nome_file = str(row.get("nome_file", "")).strip()
        if nome_file in ("nan", "None"):
            nome_file = ""
        
        nome_file_originale = str(row.get("nome_file_originale", "")).strip()
        if nome_file_originale in ("nan", "None"):
            nome_file_originale = ""
        
        nome_file_traduzione = str(row.get("nome_file_traduzione", "")).strip()
        if nome_file_traduzione in ("nan", "None"):
            nome_file_traduzione = ""
        
        # =====================================================================
        # IDENTIFIER INTERNET ARCHIVE
        # =====================================================================
        identifier = None
        if url_ia and url_ia != "#":
            match = re.search(r"/details/([^/?#]+)", url_ia)
            if match:
                identifier = match.group(1)
        
        # =====================================================================
        # DESCRIZIONE IA
        # =====================================================================
        descrizione_ia = None
        if identifier:
            if cache_manager:
                cached_metadata = cache_manager.get_ia_metadata(identifier)
                if cached_metadata:
                    descrizione_ia = (
                        cached_metadata
                        .get("metadata", {})
                        .get("description")
                    )
                if not descrizione_ia:
                    print(f"   📡 Descrizione {identifier} scaricata da IA (cache vuota)")
                    descrizione_ia = scarica_descrizione_ia(identifier)
            else:
                print(f"   📡 Descrizione {identifier} scaricata da IA (nessun cache manager)")
                descrizione_ia = scarica_descrizione_ia(identifier)
            
            if descrizione_ia and cache_manager:
                cache_manager.set_ia_metadata(
                    identifier,
                    {"metadata": {"description": descrizione_ia}},
                )
        
        # =====================================================================
        # META DESCRIPTION SEO
        # =====================================================================
        meta_description = (
            pulisci_per_meta_description(descrizione_ia)
            if descrizione_ia
            else ""
        )
        
        if not meta_description:
            if org_raw:
                meta_description = (
                    f"{tipo_display or tipo} su {org_raw}. "
                    "Documento conservato su Internet Archive."
                )
            else:
                meta_description = (
                    f"{tipo_display or tipo} conservato su Internet Archive."
                )
        
        # =====================================================================
        # LINK HTML PERSONE/ORGANIZZAZIONI
        # =====================================================================
        autore_links = []
        if autore_raw:
            for autore in split_nomi(autore_raw):
                link = crea_link(autore, persone, organizzazioni)
                if link:
                    autore_links.append(link)
        
        autore_html = ", ".join(autore_links) if autore_links else "N/A"
        org_html = link_lista(org_raw, persone, organizzazioni)
        persone_collegate_html = link_lista(persone_collegate, persone, organizzazioni)
        organizzazioni_collegate_html = link_lista(
            organizzazioni_collegate,
            persone,
            organizzazioni,
        )
        
        # =====================================================================
        # SERIE / ARGOMENTI
        # =====================================================================
        serie_tags = [tag.strip() for tag in serie.split(";") if tag.strip()]
        
        if serie_tags:
            argomento_links = []
            for tag in serie_tags:
                slug = get_argomento_slug(tag, argomenti_index)
                if slug:
                    url = site_path(f"argomenti/{slug}/")
                else:
                    url = (
                        site_path("documenti/")
                        + "?serie="
                        + urllib.parse.quote(tag, safe="")
                    )
                argomento_links.append(
                    f'<a href="{html.escape(url, quote=True)}">'
                    f"{html.escape(tag)}</a>"
                )
            argomento_html = ", ".join(argomento_links)
        else:
            argomento_html = "N/A"
        
        # =====================================================================
        # CITAZIONI
        # =====================================================================
        citazione_id = sanitize_citation_id(ami_id)
        payload_citazione = costruisci_payload_citazione(
            ami_id=ami_id,
            titolo=titolo,
            tipo=tipo,
            autore_raw=autore_raw,
            org_raw=org_raw,
            editore_raw=editore_raw,
            luogo_raw=luogo_raw,
            data_formattata=data_formattata,
            anno_pubblicazione=anno_pubblicazione,
            identifier=identifier or "",
            persone=persone,
            organizzazioni=organizzazioni,
        )
        
        is_bibliografico = payload_citazione.get("mode") == "bibliografica"
        citazioni_json = json_per_script(payload_citazione)
        
        citazione_bottone_html = (
            '<button class="citazione-link" type="button" '
            f'data-citazioni-id="{citazione_id}" '
            f'aria-controls="citazione-pannello-{citazione_id}" '
            'aria-expanded="false">'
            "📑 Cita questo documento</button>"
        )
        
        # =====================================================================
        # SCHEMA.ORG JSON-LD
        # =====================================================================
        autori_nomi = split_nomi(autore_raw) if autore_raw else []
        organizzazioni_nomi = split_nomi(org_raw) if org_raw else []
        
        immagine_url_schema = (
            f"https://archive.org/services/img/{identifier}"
            if identifier
            else None
        )
        
        document_schema = SchemaGenerator.document_schema(
            ami_id=ami_id,
            titolo=titolo,
            descrizione=meta_description,
            tipo=tipo,
            autori=autori_nomi,
            organizzazioni=organizzazioni_nomi,
            data_pubblicazione=anno_pubblicazione,
            keywords=serie_tags,
            url_ia=url_ia,
            immagine_url=immagine_url_schema,
        )
        document_schema_json = json_per_script(document_schema)
        
        # =====================================================================
        # FRONTMATTER
        # =====================================================================
        frontmatter = f"""---
title: {yaml_value(titolo)}
ami_id: {yaml_value(ami_id)}
organization: {yaml_value(org_raw)}
author: {yaml_value(autore_raw)}
year: {yaml_value(data_formattata)}
type: {yaml_value(tipo)}
series: {yaml_value(serie)}
description: {yaml_value(meta_description)}
hide:
  - navigation
  - toc
---
"""
        
        # =====================================================================
        # CONTENUTO
        # =====================================================================
        data_display_html = html.escape(
            data_formattata
            if data_formattata and data_formattata != "n.d."
            else "Data non disponibile"
        )
        titolo_html = html.escape(titolo)
        url_ia_attr = html.escape(url_ia, quote=True)
        
        content = f"""<script type="application/ld+json">{document_schema_json}</script>
<div class="doc-date-large">{data_display_html}</div>
<h1 class="doc-title-large">{titolo_html}</h1>
<div class="embed-container">
"""
        
        # =====================================================================
        # EMBED MULTIMEDIALE
        # =====================================================================
        if tipo in ("foto", "manifesto") and identifier:
            if nome_file:
                quoted_file = urllib.parse.quote(nome_file)
                img_url = f"https://archive.org/download/{identifier}/{quoted_file}"
                img_url_attr = html.escape(img_url, quote=True)
                img_tag = (
                    f'<img data-src="{img_url_attr}" '
                    f'alt="{titolo_html}" '
                    'class="lazy-img photo-embed">'
                )
            else:
                img_url_jpg = f"https://archive.org/download/{identifier}/{identifier}.jpg"
                img_url_png = f"https://archive.org/download/{identifier}/{identifier}.png"
                img_url_jpg_attr = html.escape(img_url_jpg, quote=True)
                img_url_png_attr = html.escape(img_url_png, quote=True)
                img_tag = (
                    f'<img data-src="{img_url_jpg_attr}" '
                    f'data-src-fallback="{img_url_png_attr}" '
                    f'alt="{titolo_html}" '
                    'class="lazy-img photo-embed">'
                )
            
            label_ia = (
                "Visualizza il manifesto su Internet Archive"
                if tipo == "manifesto"
                else "Visualizza la foto su Internet Archive"
            )
            
            content += f"""
<div class="photo-viewer">
{img_tag}
<div class="photo-fallback" style="display:none; padding:1rem; text-align:center;">
<p>🔗 <a href="{url_ia_attr}" target="_blank" rel="noopener">{label_ia}</a></p>
</div>
<div class="embed-footer">
{citazione_bottone_html}
<a href="{url_ia_attr}" target="_blank" rel="noopener">🔗 Apri su Internet Archive</a>
</div>
</div>
"""
        
        elif tipo == "testo_bilingue" and identifier:
            testo_originale = (
                scarica_testo_ia(identifier, nome_file_originale)
                if nome_file_originale
                else None
            )
            testo_traduzione = (
                scarica_testo_ia(identifier, nome_file_traduzione)
                if nome_file_traduzione
                else None
            )
            
            if testo_originale:
                testo_originale = html.escape(testo_originale)
            else:
                testo_originale = "Testo originale non disponibile."
            
            if testo_traduzione:
                testo_traduzione = html.escape(testo_traduzione)
            else:
                testo_traduzione = "Traduzione non disponibile."
            
            content += f"""
<div class="text-bilingue">
<div class="lingua-toggle" data-toggle-container>
<button class="lingua-btn lingua-btn--active" data-lingua="originale">Originale</button>
<button class="lingua-btn" data-lingua="traduzione">Traduzione</button>
</div>
<div class="lingua-content lingua-content--originale" data-lingua-content="originale">
<pre class="text-preview">{testo_originale}</pre>
</div>
<div class="lingua-content lingua-content--traduzione" data-lingua-content="traduzione" style="display:none;">
<pre class="text-preview">{testo_traduzione}</pre>
</div>
</div>
<div class="embed-footer">
{citazione_bottone_html}
<a href="{url_ia_attr}" target="_blank" rel="noopener">🔗 Apri su Internet Archive</a>
</div>
"""
        
        elif tipo in ("testo", "trascrizione") and identifier:
            testo = scarica_testo_ia(identifier, nome_file)
            if testo:
                testo = html.escape(testo)
                content += f"""
<div class="text-content">
<pre class="text-preview">{testo}</pre>
</div>
"""
            else:
                content += f"""
<div class="text-fallback">
<p>🔗 <a href="{url_ia_attr}" target="_blank" rel="noopener">Visualizza il testo su Internet Archive</a></p>
</div>
"""
            content += f"""
<div class="embed-footer">
{citazione_bottone_html}
<a href="{url_ia_attr}" target="_blank" rel="noopener">🔗 Apri su Internet Archive</a>
</div>
"""
        
        elif identifier:
            if tipo == "audio":
                embed_url = (
                    f"https://archive.org/embed/{identifier}"
                    "?ui=embed&nav=0&show_covers=1&playlist=1"
                )
            else:
                embed_url = (
                    f"https://archive.org/embed/{identifier}"
                    "?ui=embed&nav=0"
                )
            
            embed_url_attr = html.escape(embed_url, quote=True)
            fs_id = f"ia-embed-{ami_id}"
            
            content += f"""
<iframe id="{fs_id}" src="{embed_url_attr}" class="universal-embed" allowfullscreen></iframe>
<div class="embed-footer">
{citazione_bottone_html}
<button class="fullscreen-btn" data-target="{fs_id}" type="button">⛶ Schermo intero</button>
<a href="{url_ia_attr}" target="_blank" rel="noopener">🔗 Apri su Internet Archive</a>
</div>
"""
        
        else:
            content += f"""
<div class="no-embed">
<p>📄 <a href="{url_ia_attr}" target="_blank" rel="noopener">Visualizza il documento su Internet Archive</a></p>
</div>
<div class="embed-footer">
{citazione_bottone_html}
</div>
"""
        
        # Chiude .embed-container
        content += "\n</div>\n"
        
        # =====================================================================
        # PANNELLO CITAZIONI (MODIFICATO: div invece di textarea)
        # =====================================================================
        tabs_html = ""
        if is_bibliografico:
            tabs_html = """
<div class="citazione-tabs">
<button class="citazione-tab citazione-tab--active" data-formato="chicago" type="button">Chicago</button>
<button class="citazione-tab" data-formato="mla" type="button">MLA</button>
<button class="citazione-tab" data-formato="bibtex" type="button">BibTeX</button>
<button class="citazione-tab" data-formato="semplice" type="button">Semplice</button>
</div>
"""
        
        content += f"""
<div class="citazione-pannello" id="citazione-pannello-{citazione_id}" style="display:none;">
{tabs_html}
<div class="citazione-testo" id="citazione-testo-{citazione_id}" role="textbox" aria-readonly="true"></div>
<button class="citazione-copia" id="citazione-copia-{citazione_id}" type="button">📋 Copia</button>
</div>
<noscript>
<div class="citazione-pannello citazione-pannello--noscript">
<div class="citazione-testo" role="textbox" aria-readonly="true"></div>
<p class="citazione-noscript-msg">Abilita JavaScript per vedere e copiare la citazione completa con data di consultazione.</p>
</div>
</noscript>
<script type="application/json" id="citazioni-dati-{citazione_id}">{citazioni_json}</script>
"""
        
        # =====================================================================
        # ABSTRACT IA
        # =====================================================================
        if descrizione_ia:
            content += f"""
<div class="doc-abstract">
{descrizione_ia}
</div>
"""
        
        # =====================================================================
        # METADATI
        # =====================================================================
        provenienza_html = html.escape(provenienza_raw) if provenienza_raw else "N/A"
        tipo_display_html = html.escape(tipo_display) if tipo_display else "N/A"
        data_metadata_html = html.escape(data_formattata) if data_formattata else "N/A"
        
        content += f"""
<div class="doc-metadata">
<div class="metadata-grid">
<div class="metadata-item">
<span class="metadata-label">Autore</span>
<span class="metadata-value">{autore_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Organizzazione</span>
<span class="metadata-value">{org_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Persone collegate</span>
<span class="metadata-value">{persone_collegate_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Organizzazioni collegate</span>
<span class="metadata-value">{organizzazioni_collegate_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Data</span>
<span class="metadata-value">{data_metadata_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Provenienza</span>
<span class="metadata-value">{provenienza_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Tipologia</span>
<span class="metadata-value">{tipo_display_html}</span>
</div>
<div class="metadata-item">
<span class="metadata-label">Argomenti</span>
<span class="metadata-value">{argomento_html}</span>
</div>
</div>
</div>
"""
        
        # =====================================================================
        # SALVATAGGIO
        # =====================================================================
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter + content)
        
        if cache_manager:
            cache_manager.set_doc_metadata(
                ami_id,
                {
                    "titolo": titolo,
                    "data": data_formattata,
                    "tipo": tipo,
                    "source_hash": row_hash,
                    "stato": "generato",
                },
            )
        
        contatore_generati += 1
        print(f"   ✅ Creata scheda per {ami_id} (tipo: {tipo})")
    
    print(
        "\n✅ Schede documento: "
        f"{contatore_generati} generate, "
        f"{contatore_saltati} saltate (da cache)"
    )
    
    return contatore_generati, contatore_saltati