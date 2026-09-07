import os
import re
import html
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

    # Anno a 4 cifre
    m = re.search(r"\b(19\d{2}|20\d{2})\b", s)
    if m:
        return int(m.group(1))

    # Anno a 2 cifre: nel contesto AMI assumiamo Novecento
    m = re.search(r"\b(\d{2})\b", s)
    if m:
        return 1900 + int(m.group(1))

    return None


def normalize_columns(df):
    """Normalizza i nomi colonna per rendere lo script indipendente da maiuscole/minuscole."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df


def clean_value(value, default=""):
    """Restituisce stringa pulita, evitando nan/None."""
    if pd.isna(value):
        return default

    s = str(value).strip()
    if s.lower() in {"nan", "none", "nat"}:
        return default

    return s


def sanitize_url(url):
    """Consente solo URL http/https."""
    u = clean_value(url, "#")
    if u.lower().startswith(("http://", "https://")):
        return u
    return "#"


def get_img_url(row):
    """Costruisce l'URL dell'immagine da Internet Archive."""
    url = clean_value(row.get("url"))
    nome_file = clean_value(row.get("nome_file"))

    if not url:
        return None

    # Esempi:
    # https://archive.org/details/identificatore
    # https://archive.org/details/identificatore/mode/2up
    m = re.search(r"archive\.org/details/([^/?#]+)", url)
    if not m:
        return None

    identifier = m.group(1)

    if nome_file:
        return f"https://archive.org/download/{identifier}/{quote(nome_file, safe='')}"

    return f"https://archive.org/services/img/{identifier}"


def load_catalogo():
    """
    Carica il foglio Catalogo se presente.
    In fallback carica il primo foglio, per compatibilità con versioni precedenti.
    """
    try:
        df = pd.read_excel(DATA_PATH, sheet_name="Catalogo")
    except ValueError:
        df = pd.read_excel(DATA_PATH)
    return normalize_columns(df)


# Ciclo deterministico di altezze.
# Serve a ottenere un effetto masonry/pinterest senza JS e senza calcolare
# le dimensioni reali delle immagini remote.
LAYOUT_CYCLE = [
    "h-med",
    "h-short",
    "h-tall",
    "h-wide",
    "h-tall",
    "h-med",
    "h-short",
    "h-tall",
]


def gallery_card(row, index_in_year):
    titolo = clean_value(row.get("titolo"), "Senza titolo")
    org = clean_value(row.get("organizzazione"))
    data_str = clean_value(row.get("data"))

    img_url = get_img_url(row) or "https://archive.org/services/img/default"
    link_url = sanitize_url(row.get("url"))

    titolo_esc = html.escape(titolo)
    titolo_attr = html.escape(titolo, quote=True)
    meta_text = " · ".join(x for x in [data_str, org] if x)
    meta_esc = html.escape(meta_text)
    meta_html = f'<span class="overlay-meta">{meta_esc}</span>' if meta_text else ""

    return (
        '<article class="galleria-card">\n'
        f'  <a class="card-link" href="{html.escape(link_url, quote=True)}" target="_blank" rel="noopener noreferrer">\n'
        '    <div class="card-media">\n'
        f'      <img class="galleria-img" src="{html.escape(img_url, quote=True)}" alt="{titolo_attr}" loading="lazy" decoding="async">\n'
        '      <div class="img-overlay">\n'
        '        <span class="overlay-icon" aria-hidden="true">🔍</span>\n'
        f'        <span class="overlay-title">{titolo_esc}</span>\n'
        f"        {meta_html}\n"
        '      </div>\n'
        '    </div>\n'
        '  </a>\n'
        '</article>\n'
    )


def generate_gallery():
    print("Generazione Galleria in corso...")

    if not DATA_PATH.exists():
        print(f"Errore: {DATA_PATH} non trovato.")
        return

    try:
        df = load_catalogo()
    except Exception as e:
        print(f"Errore durante la lettura di {DATA_PATH}: {e}")
        return

    if "tipo" not in df.columns:
        print("Errore: colonna 'tipo' non trovata nel catalogo.")
        return

    if "data" not in df.columns:
        print("Errore: colonna 'data' non trovata nel catalogo.")
        return

    # Foto, fotografia, manifesti/manifesto
    mask = df["tipo"].astype(str).str.contains(
        r"\b(foto|fotografia|manifesto|manifesti)\b",
        case=False,
        na=False,
        regex=True,
    )

    df_gal = df[mask].copy()

    if df_gal.empty:
        print("Nessun documento trovato con tipo Foto/Fotografia/Manifesto.")
        return

    df_gal["anno"] = df_gal["data"].apply(parse_year)
    df_gal["anno_sort"] = df_gal["anno"].fillna(9999).astype(int)
    df_gal["titolo_sort"] = df_gal.get("titolo", "").astype(str)

    df_gal = df_gal.sort_values(
        by=["anno_sort", "titolo_sort"],
        na_position="last",
        kind="stable",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    anni_ordinati = []
    for anno in df_gal["anno"].dropna().unique():
        anno_int = int(anno)
        if anno_int not in anni_ordinati:
            anni_ordinati.append(anno_int)

    has_no_date = df_gal["anno"].isna().any()

    out = []

    # Front matter chiuso correttamente.
    # La galleria resta fuori da nav/sitemap, ma la pagina può avere layout pulito.
    out.append("---\n")
    out.append("title: Galleria Fotografica\n")
    out.append("hide:\n")
    out.append("  - navigation\n")
    out.append("  - toc\n")
    out.append("---\n\n")

    out.append('<div class="galleria-wrapper">\n')

    out.append('<header class="galleria-header">\n')
    out.append('<h1 class="galleria-main-title">Galleria Fotografica</h1>\n')
    out.append('<p class="galleria-subtitle">Documenti visivi dalla storia del maoismo italiano</p>\n')
    out.append("</header>\n")

    out.append('<nav class="galleria-timeline" id="galleria-timeline" aria-label="Timeline anni">\n')
    out.append('<ul class="timeline-list">\n')

    for idx, anno in enumerate(anni_ordinati):
        active_class = " is-active active" if idx == 0 else ""
        out.append(
            f'<li class="timeline-item">'
            f'<a href="#anno-{anno}" data-year="{anno}" class="timeline-link{active_class}">'
            f"<span>{anno}</span>"
            f"</a>"
            f"</li>\n"
        )

    if has_no_date:
        out.append(
            '<li class="timeline-item">'
            '<a href="#anno-sd" data-year="s.d." class="timeline-link">'
            "<span>s.d.</span>"
            "</a>"
            "</li>\n"
        )

    out.append("</ul>\n")
    out.append("</nav>\n")

    out.append('<main class="galleria-content">\n')

    # Sezioni datate
    for anno in anni_ordinati:
        df_year = df_gal[df_gal["anno"] == anno]

        out.append(f'<section id="anno-{anno}" class="galleria-year-section" data-year="{anno}">\n')
        out.append(f'<h2 class="galleria-year-title">{anno}</h2>\n')
        out.append('<div class="galleria-grid">\n')

        for i, (_, row) in enumerate(df_year.iterrows()):
            out.append(gallery_card(row, i))

        out.append("</div>\n")
        out.append("</section>\n")

    # Eventuali documenti senza data
    if has_no_date:
        df_sd = df_gal[df_gal["anno"].isna()]

        out.append('<section id="anno-sd" class="galleria-year-section" data-year="s.d.">\n')
        out.append('<h2 class="galleria-year-title">s.d.</h2>\n')
        out.append('<div class="galleria-grid">\n')

        for i, (_, row) in enumerate(df_sd.iterrows()):
            out.append(gallery_card(row, i))

        out.append("</div>\n")
        out.append("</section>\n")

    out.append("</main>\n")
    out.append("</div>\n")

    output_path = OUTPUT_DIR / "index.md"
    output_path.write_text("".join(out), encoding="utf-8")

    print(f"Galleria generata con successo in {output_path}")


if __name__ == "__main__":
    generate_gallery()