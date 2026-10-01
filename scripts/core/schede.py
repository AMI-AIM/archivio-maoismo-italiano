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
from .site_config import site_path
from .soggetti import crea_link, link_lista
from .utils import (
    formatta_data,
    pulisci_per_meta_description,
    scarica_descrizione_ia,
    scarica_testo_ia,
    split_nomi,
)


# Icone delle azioni della scheda (Material Design Icons, Apache 2.0):
# SVG inline al posto delle emoji, che cambiavano aspetto da un sistema
# operativo all'altro. aria-hidden: il testo del pulsante resta l'etichetta.
_ICONE = {
    "cita": "M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z",
    "schermo": "M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z",
    "esterno": "M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z",
    "copia": "M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z",
}


def _icona(nome):
    return (
        '<svg class="ami-icona" viewBox="0 0 24 24" aria-hidden="true" '
        f'focusable="false"><path d="{_ICONE[nome]}"/></svg>'
    )


_NUOVA_SCHEDA = '<span class="ami-sr-only"> (si apre in una nuova scheda)</span>'


def _link_ia(url_attr, etichetta="Apri su Internet Archive"):
    """Azione "apri su Internet Archive" della barra sotto il visore."""
    return (
        f'<a class="embed-azione" href="{url_attr}" target="_blank" rel="noopener">'
        f'{_icona("esterno")}<span>{etichetta}</span>{_NUOVA_SCHEDA}</a>'
    )


# Versione dell'impaginazione della scheda: entra nell'hash della cache,
# cosi' un cambio di template rigenera tutte le schede anche se i dati
# della riga non sono cambiati.
SCHEDA_TEMPLATE_VERSION = "2026-10-catalogo-3"

_MAX_CORRELATI = 4


def _indice_documenti(df):
    """Dati minimi di ogni documento, per i blocchi "nell'archivio"."""
    indice = []
    for _, riga in df.iterrows():
        ami_id = str(riga.get("id", "")).strip()
        if not ami_id or pd.isna(riga.get("id")):
            continue
        titolo = str(riga.get("titolo", "")).strip()
        if titolo in ("nan", "None", ""):
            titolo = "Senza titolo"
        org = str(riga.get("organizzazione", "")).strip()
        orgs = split_nomi(org) if org not in ("nan", "None") else []
        data_raw = str(riga.get("data", riga.get("anno", ""))).strip()
        if data_raw in ("nan", "None"):
            data_raw = ""
        data_fmt, ordine = formatta_data(data_raw)
        anno = ordine[0] if ordine and ordine[0] != 9999 else None
        indice.append({
            "id": ami_id, "titolo": titolo, "org": orgs[0] if orgs else "",
            "anno": anno, "ordine": ordine, "data": data_fmt,
        })
    return indice


def _correlati(doc, indice):
    """Fino a 4 documenti della stessa organizzazione (i piu' vicini nel
    tempo) e fino a 4 dello stesso anno (esclusi quelli gia' elencati)."""
    stessa_org = []
    if doc["org"]:
        stessa_org = [d for d in indice if d["org"] == doc["org"] and d["id"] != doc["id"]]
        stessa_org.sort(key=lambda d: (
            abs(d["anno"] - doc["anno"]) if d["anno"] and doc["anno"] else 9999,
            d["ordine"], d["titolo"]))
        stessa_org = stessa_org[:_MAX_CORRELATI]
    gia = {d["id"] for d in stessa_org}
    stesso_anno = []
    if doc["anno"]:
        stesso_anno = [d for d in indice if d["anno"] == doc["anno"]
                       and d["id"] != doc["id"] and d["id"] not in gia]
        stesso_anno.sort(key=lambda d: (d["ordine"], d["titolo"]))
        stesso_anno = stesso_anno[:_MAX_CORRELATI]
    return stessa_org, stesso_anno


def _lista_correlati(docs):
    righe = []
    for d in docs:
        data = d["data"] if d["data"] and d["data"] not in ("n.d.", "s.d.") else "s.d."
        url = site_path("documenti/" + d["id"] + "/")
        righe.append(
            f'<li><span class="doc-correlati__data">{html.escape(data)}</span>'
            f'<a class="doc-correlati__titolo" href="{url}">{html.escape(d["titolo"])}</a></li>'
        )
    return '<ul class="doc-correlati__lista">' + "".join(righe) + "</ul>"


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
    print("Creazione delle schede dei documenti...")
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
    indice_documenti = _indice_documenti(df)
    indice_per_id = {d["id"]: d for d in indice_documenti}
    
    for index, row in df.iterrows():
        ami_id = str(row.get("id", "")).strip()
        if not ami_id or pd.isna(row.get("id")):
            continue
        
        file_path = os.path.join(documenti_dir, f"{ami_id}.md")
        doc_indice = indice_per_id.get(ami_id)
        correlati_org, correlati_anno = (
            _correlati(doc_indice, indice_documenti) if doc_indice else ([], [])
        )
        
        row_hash = None
        if cache_manager:
            hash_input = {
                "source": row.to_dict(),
                "template_version": CITAZIONI_TEMPLATE_VERSION,
                "scheda_version": SCHEDA_TEMPLATE_VERSION,
                # i correlati dipendono dalle ALTRE righe: se cambiano,
                # la scheda va rigenerata anche se la sua riga e' identica
                "correlati": [d["id"] for d in correlati_org + correlati_anno],
            }
            row_hash = cache_manager.hash_data(hash_input)
        
        if cache_manager and os.path.exists(file_path):
            cached_data = cache_manager.get_doc_metadata(ami_id)
            cached_hash = (cached_data or {}).get("data", {}).get("source_hash")
            if cached_hash == row_hash:
                contatore_saltati += 1
                print(f"Saltato {ami_id} (cache valido)")
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
                    print(f"Descrizione {identifier} scaricata da IA (cache vuota)")
                    descrizione_ia = scarica_descrizione_ia(identifier)
            else:
                print(f"Descrizione {identifier} scaricata da IA (nessun cache manager)")
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
            '<button class="citazione-link embed-azione" type="button" '
            f'data-citazioni-id="{citazione_id}" '
            f'aria-controls="citazione-pannello-{citazione_id}" '
            'aria-expanded="false">'
            f'{_icona("cita")}<span>Cita questo documento</span></button>'
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
            if data_formattata and data_formattata not in ("n.d.", "s.d.")
            else "Data non disponibile"
        )
        titolo_html = html.escape(titolo)
        url_ia_attr = html.escape(url_ia, quote=True)
        
        # Intestazione da catalogo: percorso, segnatura (identificativo AMI ·
        # tipologia · data) e titolo. La segnatura prima compariva solo
        # dentro il testo della citazione.
        segnatura_data = (
            html.escape(data_formattata)
            if data_formattata and data_formattata not in ("n.d.", "s.d.")
            else '<abbr title="senza data">s.d.</abbr>'
        )
        segnatura_parti = [f'<span class="doc-segnatura__id">{html.escape(ami_id)}</span>']
        if tipo_display:
            segnatura_parti.append(html.escape(tipo_display))
        segnatura_parti.append(segnatura_data)
        segnatura_html = '<span class="doc-segnatura__sep" aria-hidden="true">·</span>'.join(segnatura_parti)
        percorso_html = f'<a href="{site_path("documenti/")}">Archivio</a>'
        if tipo_display:
            url_tipo = site_path("documenti/") + "?tipo=" + urllib.parse.quote(tipo_display, safe="")
            percorso_html += (
                '<span class="doc-percorso__sep" aria-hidden="true">›</span>'
                f'<a href="{html.escape(url_tipo, quote=True)}">{html.escape(tipo_display)}</a>'
            )
        
        content = f"""<script type="application/ld+json">{document_schema_json}</script>
<nav class="doc-percorso" aria-label="Percorso">{percorso_html}</nav>
<p class="doc-segnatura">{segnatura_html}</p>
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
<p><a href="{url_ia_attr}" target="_blank" rel="noopener">{label_ia}</a></p>
</div>
<div class="embed-footer">
{citazione_bottone_html}
{_link_ia(url_ia_attr)}
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
{_link_ia(url_ia_attr)}
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
<p><a href="{url_ia_attr}" target="_blank" rel="noopener">Visualizza il testo su Internet Archive</a></p>
</div>
"""
            content += f"""
<div class="embed-footer">
{citazione_bottone_html}
{_link_ia(url_ia_attr)}
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
<iframe id="{fs_id}" src="{embed_url_attr}" class="universal-embed" title="Visore Internet Archive: {titolo_html}" loading="lazy" allowfullscreen></iframe>
<div class="embed-footer">
{citazione_bottone_html}
<button class="fullscreen-btn embed-azione" data-target="{fs_id}" type="button">{_icona("schermo")}<span>Schermo intero</span></button>
{_link_ia(url_ia_attr)}
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
<div class="citazione-tabs" role="group" aria-label="Formato della citazione">
<button class="citazione-tab citazione-tab--active" data-formato="chicago" type="button" aria-pressed="true">Chicago</button>
<button class="citazione-tab" data-formato="mla" type="button" aria-pressed="false">MLA</button>
<button class="citazione-tab" data-formato="bibtex" type="button" aria-pressed="false">BibTeX</button>
<button class="citazione-tab" data-formato="semplice" type="button" aria-pressed="false">Semplice</button>
</div>
"""
        
        content += f"""
<div class="citazione-pannello" id="citazione-pannello-{citazione_id}" role="region" aria-label="Cita questo documento" style="display:none;">
{tabs_html}
<div class="citazione-testo" id="citazione-testo-{citazione_id}" aria-live="polite"></div>
<button class="citazione-copia" id="citazione-copia-{citazione_id}" type="button">{_icona("copia")}<span class="citazione-copia__etichetta">Copia</span></button>
</div>
<noscript>
<div class="citazione-pannello citazione-pannello--noscript">
<div class="citazione-testo"></div>
<p class="citazione-noscript-msg">Abilita JavaScript per vedere e copiare la citazione completa con data di consultazione.</p>
</div>
</noscript>
<script type="application/json" id="citazioni-dati-{citazione_id}">{citazioni_json}</script>
"""
        
        # =====================================================================
        # ABSTRACT IA
        # =====================================================================
        corpo_testo = ""
        if descrizione_ia:
            corpo_testo = f"""<div class="doc-corpo__testo">
<h2 class="doc-sezione" id="descrizione-{citazione_id}">Descrizione</h2>
<div class="doc-abstract">
{descrizione_ia}
</div>
</div>
"""
        
        # =====================================================================
        # METADATI
        # =====================================================================
        # Scheda catalografica: solo i campi compilati (prima i campi vuoti
        # comparivano come "N/A", cioe' come se fossero dati).
        campi = [
            ("Autore", autore_html),
            ("Organizzazione", org_html),
            ("Persone collegate", persone_collegate_html),
            ("Organizzazioni collegate", organizzazioni_collegate_html),
            ("Data", html.escape(data_formattata) if data_formattata and data_formattata not in ("n.d.", "s.d.") else ""),
            ("Luogo", html.escape(luogo_raw)),
            ("Editore", html.escape(editore_raw)),
            ("Tipologia", html.escape(tipo_display)),
            ("Argomenti", argomento_html),
            ("Provenienza", html.escape(provenienza_raw)),
        ]
        righe_scheda = "".join(
            f'<div class="doc-scheda__campo"><dt>{etichetta}</dt><dd>{valore}</dd></div>'
            for etichetta, valore in campi
            if valore and valore != "N/A"
        )
        
        content += f"""
<div class="doc-corpo">
{corpo_testo}<aside class="doc-scheda" aria-labelledby="scheda-{citazione_id}">
<h2 class="doc-sezione" id="scheda-{citazione_id}">Scheda</h2>
<dl class="doc-scheda__campi">{righe_scheda}</dl>
</aside>
</div>
"""
        
        # Nell'archivio: documenti vicini per organizzazione e per anno
        if correlati_org or correlati_anno:
            colonne = ""
            if correlati_org:
                org_nome = doc_indice["org"]
                url_org = (site_path("documenti/") + "?organizzazione="
                           + urllib.parse.quote(urllib.parse.quote(org_nome, safe=""), safe=""))
                colonne += f"""<div class="doc-correlati__gruppo">
<h3>Stessa organizzazione <span class="doc-correlati__chiave">{html.escape(org_nome)}</span></h3>
{_lista_correlati(correlati_org)}
<a class="doc-correlati__tutti" href="{html.escape(url_org, quote=True)}">Tutti i documenti di {html.escape(org_nome)}</a>
</div>
"""
            if correlati_anno:
                anno = doc_indice["anno"]
                url_anno = site_path("documenti/") + f"?anno_min={anno}&amp;anno_max={anno}"
                colonne += f"""<div class="doc-correlati__gruppo">
<h3>Stesso anno <span class="doc-correlati__chiave">{anno}</span></h3>
{_lista_correlati(correlati_anno)}
<a class="doc-correlati__tutti" href="{url_anno}">Tutti i documenti del {anno}</a>
</div>
"""
            content += f"""
<section class="doc-correlati" aria-labelledby="correlati-{citazione_id}">
<h2 class="doc-sezione" id="correlati-{citazione_id}">Nell'archivio</h2>
<div class="doc-correlati__colonne">
{colonne}</div>
</section>
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
        print(f"Creata scheda per {ami_id} (tipo: {tipo})")
    
    print(
        "\n Schede documento: "
        f"{contatore_generati} generate, "
        f"{contatore_saltati} saltate (da cache)"
    )
    
    return contatore_generati, contatore_saltati