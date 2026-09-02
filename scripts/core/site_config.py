"""Configurazione di pubblicazione condivisa dai generatori Python.

La sorgente autorevole resta ``site_url`` in ``mkdocs.yml``: in questo modo il
repository puo' essere pubblicato sotto un percorso diverso senza modificare
ogni generatore.
"""

import re
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


def site_url(path=""):
    """Restituisce un URL canonico, partendo da ``site_url`` di MkDocs."""
    suffix = str(path).lstrip("/")
    return f"{SITE_URL}/{suffix}" if suffix else SITE_URL
