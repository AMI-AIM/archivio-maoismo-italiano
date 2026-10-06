"""
Controlli sul sito finito (cartella site/, dopo `mkdocs build`).

Cosa verifica
-------------
1. Pagine attese: una scheda per ogni documento del Catalogo, le pagine
   principali (home, archivio, persone, organizzazioni, percorsi, galleria,
   progetto) e la 404.
2. Sitemap: ogni indirizzo elencato in build/sitemap.xml corrisponde a una
   pagina esistente (altrimenti i motori di ricerca trovano pagine inesistenti).
3. JSON della ricerca: documenti.json e soggetti.json si leggono, e
   documenti.json contiene tanti documenti quante righe ha il Catalogo.
4. Link e immagini interni: ogni href/src/srcset che punta al sito stesso
   deve portare a un file esistente. I link esterni (Internet Archive,
   Wikidata...) non vengono controllati qui: richiederebbero la rete.

Esito (vedi core/esito.py): pagine mancanti, sitemap con indirizzi
inesistenti, JSON rotti e link interni rotti sono ERRORI; il deploy su
GitHub si ferma e resta online la versione precedente del sito.

Uso:
    mkdocs build
    python scripts/controlla_sito.py            # controlla ./site
    python scripts/controlla_sito.py percorso/site
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# I moduli del progetto (e quindi pandas) vanno importati per primi: in alcuni
# ambienti importare xml.etree prima di pandas da questa cartella fallisce.
from core import esito  # noqa: E402
from core.dati import leggi_foglio  # noqa: E402
from core.site_config import SITE_PATH, SITE_URL  # noqa: E402

import json  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402
from collections import defaultdict  # noqa: E402
from html.parser import HTMLParser  # noqa: E402
from urllib.parse import unquote, urljoin, urlparse  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT_DIR / "build"

PAGINE_PRINCIPALI = ["", "documenti/", "persone/", "organizzazioni/", "argomenti/",
                     "galleria/", "progetto/", "404.html"]
MAX_ESEMPI = 8  # quanti esempi mostrare per ogni tipo di problema


class _Link(HTMLParser):
    """Raccoglie gli URL di href, src e srcset di una pagina."""

    ATTRIBUTI = {"href", "src"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.url = []

    def handle_starttag(self, tag, attrs):
        for nome, valore in attrs:
            if not valore:
                continue
            if nome in self.ATTRIBUTI:
                # <link rel="preconnect|dns-prefetch"> non sono risorse da scaricare
                self.url.append(valore.strip())
            elif nome == "srcset":
                for parte in valore.split(","):
                    candidato = parte.strip().split(" ")[0]
                    if candidato:
                        self.url.append(candidato)


def _pagina_esiste(site_dir, percorso_relativo):
    """True se il percorso del sito (senza prefisso) corrisponde a un file."""
    p = unquote(percorso_relativo).lstrip("/")
    destinazione = site_dir / p
    if p == "" or p.endswith("/"):
        return (destinazione / "index.html").is_file()
    if destinazione.is_file():
        return True
    # URL senza barra finale ("documenti/AMI-0001"): GitHub Pages serve index.html
    return (destinazione / "index.html").is_file()


def _url_pagina(site_dir, file_html):
    rel = file_html.relative_to(site_dir).as_posix()
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    return f"{SITE_PATH}/{rel}"


def controlla_pagine_attese(site_dir):
    mancanti = [p or "(home)" for p in PAGINE_PRINCIPALI if not _pagina_esiste(site_dir, p)]
    if mancanti:
        esito.errore(f"pagine principali mancanti: {', '.join(mancanti)}")

    ids = [i.strip() for i in leggi_foglio("Catalogo")["id"] if i.strip()]
    senza_scheda = [i for i in ids if not _pagina_esiste(site_dir, f"documenti/{i}/")]
    if senza_scheda:
        esito.errore(f"{len(senza_scheda)} documenti del Catalogo senza scheda nel sito: "
                     f"{', '.join(senza_scheda[:MAX_ESEMPI])}")
    print(f"Pagine attese: {len(PAGINE_PRINCIPALI)} principali, {len(ids)} schede documento "
          f"({len(ids) - len(senza_scheda)} presenti)")
    return len(ids)


def controlla_sitemap(site_dir):
    percorso = BUILD_DIR / "sitemap.xml"
    if not percorso.is_file():
        esito.errore("build/sitemap.xml non trovata")
        return
    try:
        radice = ET.parse(percorso).getroot()
    except ET.ParseError as e:
        esito.errore(f"build/sitemap.xml non è XML valido: {e}")
        return
    indirizzi = [el.text.strip() for el in radice.iter() if el.tag.endswith("loc") and el.text]
    inesistenti = []
    for url in indirizzi:
        if not url.startswith(SITE_URL):
            inesistenti.append(url)
            continue
        if not _pagina_esiste(site_dir, url[len(SITE_URL):]):
            inesistenti.append(url[len(SITE_URL):] or "/")
    if inesistenti:
        esito.errore(f"la sitemap elenca {len(inesistenti)} indirizzi senza pagina: "
                     f"{', '.join(inesistenti[:MAX_ESEMPI])}")
    print(f"Sitemap: {len(indirizzi)} indirizzi, {len(indirizzi) - len(inesistenti)} esistenti")


def controlla_json(site_dir, n_documenti):
    for nome in ("documenti.json", "soggetti.json"):
        percorso = site_dir / nome
        if not percorso.is_file():
            esito.errore(f"{nome} mancante nel sito (la ricerca non funzionerebbe)")
            continue
        try:
            contenuto = json.loads(percorso.read_text(encoding="utf-8"))
        except ValueError as e:
            esito.errore(f"{nome} non è JSON valido: {e}")
            continue
        if nome == "documenti.json":
            documenti = contenuto.get("documenti", contenuto) if isinstance(contenuto, dict) else contenuto
            if len(documenti) != n_documenti:
                esito.errore(f"documenti.json contiene {len(documenti)} documenti, "
                             f"il Catalogo {n_documenti}")
    print("JSON della ricerca: controllati")


def controlla_link(site_dir):
    rotti = defaultdict(set)  # destinazione -> pagine che la citano
    fuori_sito = defaultdict(set)
    pagine = sorted(site_dir.rglob("*.html"))
    n_link = 0
    for file_html in pagine:
        parser = _Link()
        parser.feed(file_html.read_text(encoding="utf-8", errors="replace"))
        base = _url_pagina(site_dir, file_html)
        pagina = base[len(SITE_PATH):] or "/"
        for url in parser.url:
            if url.startswith(("#", "mailto:", "tel:", "data:", "javascript:", "{{")):
                continue
            assoluto = urlparse(urljoin(f"https://host{base}", url))
            if assoluto.netloc != "host":
                continue  # link esterno
            n_link += 1
            percorso = assoluto.path
            if not percorso.startswith(SITE_PATH + "/") and percorso != SITE_PATH:
                # "/qualcosa" fuori dal prefisso del progetto: su GitHub Pages è rotto
                fuori_sito[percorso].add(pagina)
                continue
            if not _pagina_esiste(site_dir, percorso[len(SITE_PATH):]):
                rotti[percorso[len(SITE_PATH):]].add(pagina)

    for gruppo, testo in ((rotti, "link o immagini interni rotti"),
                          (fuori_sito, f"link che escono dal sito (manca il prefisso {SITE_PATH})")):
        if gruppo:
            esempi = [f"{dest} (in {sorted(pag)[0]}{' e altre ' + str(len(pag) - 1) if len(pag) > 1 else ''})"
                      for dest, pag in sorted(gruppo.items())[:MAX_ESEMPI]]
            esito.errore(f"{len(gruppo)} {testo}: " + "; ".join(esempi))
    print(f"Link interni: {n_link} controllati in {len(pagine)} pagine, "
          f"{len(rotti) + len(fuori_sito)} destinazioni rotte")


def main():
    site_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT_DIR / "site"
    if not (site_dir / "index.html").is_file():
        esito.errore(f"{site_dir} non contiene un sito generato: eseguire prima `mkdocs build`")
        return 1
    print(f"Controllo del sito in {site_dir}")
    n_documenti = controlla_pagine_attese(site_dir)
    controlla_sitemap(site_dir)
    controlla_json(site_dir, n_documenti)
    controlla_link(site_dir)
    return 1 if esito.ci_sono_errori() else 0


if __name__ == "__main__":
    sys.exit(esito.esegui_script("controllo sito", main))
