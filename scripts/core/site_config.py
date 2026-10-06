"""Configurazione di pubblicazione condivisa dai generatori Python.

La sorgente autorevole resta ``site_url`` in ``mkdocs.yml``: in questo modo il
repository puo' essere pubblicato sotto un percorso diverso senza modificare
ogni generatore.
"""

import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

_ROOT_DIR = Path(__file__).resolve().parents[2]
_MKDOCS_CONFIG = _ROOT_DIR / "mkdocs.yml"


def _read_site_url():
    content = _MKDOCS_CONFIG.read_text(encoding="utf-8")
    match = re.search(r"^site_url:\s*([^\s#]+)", content, re.MULTILINE)
    if not match:
        raise RuntimeError("site_url non trovato in mkdocs.yml")
    return match.group(1).rstrip("/")


SITE_URL = _read_site_url()
SITE_PATH = urlparse(SITE_URL).path.rstrip("/")


def site_path(path=""):
    """Restituisce un URL assoluto nel sito, partendo dal suo path configurato."""
    suffix = str(path).lstrip("/")
    return f"{SITE_PATH}/{suffix}" if suffix else SITE_PATH or "/"


def data_pubblicazione():
    """Data da scrivere nei file generati (lastmod della sitemap, data di
    conversione in EAD3/EAC-CPF).

    Di norma è la data di oggi. Se è impostata la variabile d'ambiente
    SOURCE_DATE_EPOCH (secondi dal 1/1/1970, convenzione standard delle
    "reproducible builds"), si usa quella: due generazioni con gli stessi
    dati producono allora file identici anche in giorni diversi. La usano i
    controlli automatici che confrontano due generazioni.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date()
    return date.today()


def site_url(path=""):
    """Restituisce un URL canonico, partendo da ``site_url`` di MkDocs."""
    suffix = str(path).lstrip("/")
    return f"{SITE_URL}/{suffix}" if suffix else SITE_URL
