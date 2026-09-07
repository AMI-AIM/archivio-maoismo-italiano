import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "dati.xlsx"
OUTPUT_DIR = ROOT_DIR / "build" / "galleria"


def parse_year(date_str):
    """Estrae l'anno da vari formati di data. Restituisce None se non trova."""
    if pd.isna(date_str):
        return None

    s = str(date_str).strip()
    if not s:
        return None

    m = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if m:
        return int(m.group(1))

    m = re.search(r"\b(\d{2})\b", s)
    if m:
        return 1900 + int(m.group(1))

    return None


def normalize_columns(df):
    """Rende lo script indipendente da maiuscole/minuscole e spazi nei header."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df


def clean_value(value, default=""):
    """Restituisce una stringa pulita, neutralizzando nan/None/NaT."""
    if pd.isna(value):
        return default
    s = str(value).strip()
    if s.lower() in {"nan", "none", "nat"}:
        return default
    return s


MESI_IT = {
    1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
    5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
    9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre",
}


def format_data(valore):
    """Riduce le date al formato esteso italiano:
    '1964-05-14 00:00:00' -> '14 maggio 1964'
    '03/1978'             -> 'marzo 1978'
    '1967'                -> '1967'
    L'orario è rimosso solo se mezzanotte (00:00:00 = orario assente).
    """
    s = clean_value(valore)
    if not s:
        return ""

    m = re.match(
        r"^(\d{4})-(\d{1,2})-(\d{1,2})"
        r"(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$",
        s,
    )
    if m:
        anno, mese, giorno = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm = int(m.group(4) or 0), int(m.group(5) or 0)
        if 1 <= mese <= 12 and 1 <= giorno <= 31:
            base = f"{giorno} {MESI_IT[mese]} {anno}"
            if (hh, mm) != (0, 0):
                base += f", ore {hh:02d}:{mm:02d}"
            return base
        return s

    m = re.match(r"^(\d{1,2})/(\d{4})$", s)
    if m:
        mese = int(m.group(1))
        if 1 <= mese <= 12:
            return f"{MESI_IT[mese]} {m.group(2)}"
        return s

    m = re.match(r"^(\d{4})-(\d{1,2})$", s)
    if m:
        mese = int(m.group(2))
        if 1 <= mese <= 12:
            return f"{MESI_IT[mese]} {m.group(1)}"
        return s

    return s


def sanitize_url(url):
    """Consente solo scheme http/https negli href (evita javascript: ecc.)."""
    u = clean_value(url, "#")
    if u.lower().startswith(("http://", "https://")):
        return u
    return "#"


def get_image_urls(row):
    """Ritorna (primary, fallback) per l'immagine su Internet Archive."""
    url = clean_value(row.get("url"))
    nome_file = clean_value(row.get("nome_file"))

    m = re.search(r"archive\.org/details/([^/?#]+)", url) if url else None
    identifier = m.group(1) if m else None

    if identifier and nome_file:
        primary = f"https://archive.org/download/{identifier}/{quote(nome_file, safe='')}"
        fallback = f"https://archive.org/services/img/{identifier}"
    elif identifier:
        primary = f"https://archive.org/services/img/{identifier}"
        fallback = ""
    else:
        primary = "https://archive.org/services/img/default"
        fallback = ""

    return primary, fallback


def gallery_card(row):
    """Card galleria: immagine a proporzioni naturali, overlay metadati,
    lazy loading con skeleton e attributi data-* per il lightbox."""
    titolo = clean_value(row.get("titolo"), "Senza titolo")
    org = clean_value(row.get("organizzazione"))
    data_str = format_data(row.get("data"))
    doc_id = clean_value(row.get("id"))

    primary, fallback = get_image_urls(row)
    link_url = sanitize_url(row.get("url"))
    scheda_url = f"../documenti/{quote(doc_id, safe='')}/" if doc_id else ""

    titolo_esc = html.escape(titolo)
    titolo_attr = html.escape(titolo, quote=True)
    primary_esc = html.escape(primary, quote=True)
    fallback_attr = f' data-src-fallback="{html.escape(fallback, quote=True)}"' if fallback else ""
    card_id = f' id="{html.escape(doc_id, quote=True)}"' if doc_id else ""

    meta_text = " · ".join(x for x in [data_str, org] if x)
    meta_html = f'<span class="overlay-meta">{html.escape(meta_text)}</span>' if meta_text else ""

    data_attrs = (
        f' data-titolo="{titolo_attr}"'
        f' data-data="{html.escape(data_str, quote=True)}"'
        f' data-org="{html.escape(org, quote=True)}"'
        f' data-ia-url="{html.escape(link_url, quote=True)}"'
        f' data-scheda-url="{html.escape(scheda_url, quote=True)}"'
        f' data-full-src="{primary_esc}"'
    )

    return (
        f'<article class="galleria-card"{card_id}{data_attrs}>\n'
        f'<a class="card-link" href="{html.escape(link_url, quote=True)}" target="_blank" rel="noopener noreferrer">\n'
        '<div class="card-media">\n'
        # src nativo = fallback senza JS; data-src = pattern skeleton/fade;
        # data-src-fallback = retry su cover IA se il file specifico è 404.
        f'<img class="galleria-img lazy-img" src="{primary_esc}" data-src="{primary_esc}"{fallback_attr} alt="{titolo_attr}" loading="lazy" decoding="async">\n'
        '<div class="img-overlay">\n'
        '<span class="overlay-icon" aria-hidden="true">🔍</span>\n'
        f'<span class="overlay-title">{titolo_esc}</span>\n'
        f"{meta_html}\n"
        '</div>\n'
        '</div>\n'
        '</a>\n'
        '</article>\n'
    )


def lightbox_dialog():
    """Visualizzatore minimo: un solo <dialog> popolato via JS."""
    return (
        '<dialog class="galleria-lightbox" id="galleria-lightbox" aria-labelledby="lightbox-title">\n'
        '<div class="lightbox-media">\n'
        '<img class="lightbox-img" alt="" decoding="async">\n'
        '<button class="lightbox-close" type="button" aria-label="Chiudi visualizzatore">✕</button>\n'
        '</div>\n'
        '<div class="lightbox-caption">\n'
        '<div class="lightbox-titles">\n'
        '<h2 class="lightbox-title" id="lightbox-title"></h2>\n'
        '<p class="lightbox-meta"></p>\n'
        '</div>\n'
        '<div class="lightbox-actions">\n'
        '<a class="lightbox-action lightbox-action--scheda" href="#">Scheda archivistica</a>\n'
        '<a class="lightbox-action lightbox-action--ia" href="#" target="_blank" rel="noopener noreferrer">Internet Archive ↗</a>\n'
        '</div>\n'
        '</div>\n'
        '</dialog>\n'
    )


def generate_gallery():
    """Genera build/galleria/index.md. Ritorna exit code: 0 ok, 1 errore fatale."""
    print("Generazione Galleria in corso...")

    if not DATA_PATH.exists():
        print(f"Errore: {DATA_PATH} non trovato.")
        return 1

    try:
        df = load_catalogo()
    except Exception as e:
        print(f"Errore durante la lettura di {DATA_PATH}: {e}")
        return 1

    for col in ("tipo", "data"):
        if col not in df.columns:
            print(f"Errore: colonna '{col}' non trovata nel catalogo.")
            return 1

    # Substring match: copre foto, fotografia, manifesto, manifesti, ecc.
    mask = df["tipo"].astype(str).str.contains("foto|manifest", case=False, na=False)
    df_gal = df[mask].copy()

    empty_state = df_gal.empty
    if empty_state:
        print("⚠️ Nessun documento con tipo Foto/Fotografia/Manifesto: pagina in stato vuoto.")
    else:
        df_gal["anno"] = df_gal["data"].apply(parse_year)
        df_gal["anno_sort"] = df_gal["anno"].fillna(9999).astype(int)
        df_gal["titolo_sort"] = (
            df_gal["titolo"].astype(str) if "titolo" in df_gal.columns else ""
        )
        df_gal = df_gal.sort_values(by=["anno_sort", "titolo_sort"], kind="stable")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    anni_ordinati = [] if empty_state else sorted(int(a) for a in df_gal["anno"].dropna().unique())
    has_sd = False if empty_state else bool(df_gal["anno"].isna().any())

    out = []
    out.append("---\n")
    out.append("title: Galleria Fotografica\n")
    out.append(
        'description: "Galleria fotografica e iconografica dell\'Archivio del '
        'Maoismo Italiano - manifesti, fotografie e documenti visivi dalle '
        'collezioni digitali su Internet Archive."\n'
    )
    out.append("hide:\n")
    out.append("  - navigation\n")
    out.append("  - toc\n")
    out.append("---\n\n")

    out.append('<div class="galleria-wrapper">\n')
    out.append('<header class="galleria-header">\n')
    out.append('<h1 class="galleria-main-title">Galleria Fotografica</h1>\n')
    out.append('<p class="galleria-subtitle">Documenti visivi dalla storia del maoismo italiano</p>\n')
    out.append('</header>\n')

    out.append('<nav class="galleria-timeline" id="galleria-timeline" aria-label="Timeline anni">\n')
    out.append('<ul class="timeline-list">\n')
    for idx, anno in enumerate(anni_ordinati):
        active = " is-active active" if idx == 0 else ""
        out.append(
            f'<li class="timeline-item"><a href="#anno-{anno}" data-year="{anno}" '
            f'class="timeline-link{active}"><span>{anno}</span></a></li>\n'
        )
    if has_sd:
        out.append(
            '<li class="timeline-item"><a href="#anno-sd" data-year="s.d." '
            'class="timeline-link"><span>s.d.</span></a></li>\n'
        )
    out.append('</ul>\n')
    out.append('</nav>\n')

    out.append('<main class="galleria-content">\n')

    if empty_state:
        out.append('<p class="galleria-empty">Nessun documento visivo disponibile al momento.</p>\n')

    for anno in anni_ordinati:
        df_year = df_gal[df_gal["anno"] == anno]
        out.append(f'<section id="anno-{anno}" class="galleria-year-section" data-year="{anno}">\n')
        out.append(f'<h2 class="galleria-year-title">{anno}</h2>\n')
        out.append('<div class="galleria-grid">\n')
        for _, row in df_year.iterrows():
            out.append(gallery_card(row))
        out.append('</div>\n')
        out.append('</section>\n')

    if has_sd:
        df_sd = df_gal[df_gal["anno"].isna()]
        out.append('<section id="anno-sd" class="galleria-year-section" data-year="s.d.">\n')
        out.append('<h2 class="galleria-year-title">s.d.</h2>\n')
        out.append('<div class="galleria-grid">\n')
        for _, row in df_sd.iterrows():
            out.append(gallery_card(row))
        out.append('</div>\n')
        out.append('</section>\n')

    out.append('</main>\n')
    out.append('</div>\n')

    # Lightbox: fuori dal wrapper, per evitare qualsiasi interferenza
    # di antenati CSS (overflow, filter, backdrop-filter) con il top layer.
    out.append(lightbox_dialog())

    output_path = OUTPUT_DIR / "index.md"
    output_path.write_text("".join(out), encoding="utf-8")
    print(f"Galleria generata con successo in {output_path} ({len(df_gal)} card, {len(anni_ordinati)} anni)")
    return 0


def load_catalogo():
    """Legge il foglio 'Catalogo'; in fallback il primo foglio disponibile."""
    try:
        df = pd.read_excel(DATA_PATH, sheet_name="Catalogo")
    except ValueError:
        df = pd.read_excel(DATA_PATH)
    return normalize_columns(df)


def main():
    try:
        return generate_gallery()
    except Exception as e:
        print(f"Errore inatteso durante la generazione della galleria: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())