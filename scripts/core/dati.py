"""
Lettura unica di data/dati.xlsx.

Tutti gli script della pipeline leggono i fogli di dati.xlsx da qui, invece
di aprire l'Excel ciascuno per conto proprio. Vantaggi:

- il file viene letto UNA volta per processo (tutti i fogli insieme) e poi
  servito dalla memoria; se il file cambia su disco, viene riletto;
- le stesse regole valgono ovunque: ogni cella è testo (dtype=str, quindi
  "1968" non diventa il numero 1968.0 e gli ID non perdono zeri), le celle
  vuote sono stringhe vuote, i nomi di colonna sono ripuliti dagli spazi;
- un foglio mancante produce un errore chiaro (ErroreDati) invece di un
  DataFrame vuoto silenzioso che genererebbe pagine incomplete.

Uso:
    from core.dati import leggi_foglio
    df = leggi_foglio('Catalogo')                       # colonne minuscole
    df = leggi_foglio('Catalogo', colonne='originali')  # colonne come in Excel
    df = leggi_foglio('Raccolta', obbligatorio=False)   # vuoto se manca

Ogni chiamata restituisce una COPIA: chi la modifica non altera i dati
visti dagli altri moduli.
"""

from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
PERCORSO_EXCEL = ROOT_DIR / "data" / "dati.xlsx"

# Fogli attesi in dati.xlsx (usati anche dal validatore).
FOGLI_ATTESI = ("Catalogo", "Raccolta", "Persone", "Organizzazioni", "Relazioni")

_cache = {}  # (percorso, mtime, dimensione) -> {nome_foglio: DataFrame}


class ErroreDati(Exception):
    """dati.xlsx mancante, illeggibile o senza un foglio richiesto."""


def _chiave(percorso):
    stat = percorso.stat()
    return (str(percorso.resolve()), stat.st_mtime_ns, stat.st_size)


def fogli(percorso=None):
    """Tutti i fogli di dati.xlsx come {nome: DataFrame} (celle testo, colonne originali).

    Non modificare i DataFrame restituiti: sono condivisi. Per lavorarci
    usare leggi_foglio(), che restituisce copie.
    """
    percorso = Path(percorso) if percorso else PERCORSO_EXCEL
    if not percorso.exists():
        raise ErroreDati(f"file non trovato: {percorso}")
    chiave = _chiave(percorso)
    if chiave not in _cache:
        try:
            letti = pd.read_excel(percorso, sheet_name=None, dtype=str)
        except Exception as e:
            raise ErroreDati(
                f"impossibile leggere {percorso.name}: {e}. "
                "Se il file è aperto in Excel, salvalo e riprova."
            ) from e
        puliti = {}
        for nome, df in letti.items():
            df = df.fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            puliti[nome.strip()] = df
        _cache.clear()
        _cache[chiave] = puliti
    return _cache[chiave]


def leggi_foglio(nome, percorso=None, obbligatorio=True, colonne="minuscole"):
    """Copia del foglio `nome`.

    Args:
        nome: nome del foglio (es. 'Catalogo').
        percorso: altro file .xlsx (default: data/dati.xlsx).
        obbligatorio: se True e il foglio manca solleva ErroreDati,
            altrimenti restituisce un DataFrame vuoto.
        colonne: 'minuscole' (default, come usano i generatori) oppure
            'originali' (intestazioni come scritte in Excel).
    """
    tutti = fogli(percorso)
    if nome not in tutti:
        if obbligatorio:
            raise ErroreDati(
                f"il foglio '{nome}' non esiste in dati.xlsx "
                f"(fogli presenti: {', '.join(tutti) or 'nessuno'})"
            )
        return pd.DataFrame()
    df = tutti[nome].copy()
    if colonne == "minuscole":
        df.columns = df.columns.str.lower()
    return df
