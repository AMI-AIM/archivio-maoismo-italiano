"""
Export di data/dati.xlsx in CSV e riepilogo delle modifiche.

Perché esiste
-------------
dati.xlsx è un file binario: su GitHub ogni versione appare come
"Bin 53693 -> 53683 bytes", senza modo di sapere quali schede sono cambiate.
A ogni esecuzione del Launcher questo modulo:

1. esporta ogni foglio in data/export/<foglio>.csv (UTF-8 con BOM, così Excel
   li apre con gli accenti corretti; una riga per record), che Git sa
   confrontare riga per riga: la cronologia di ogni scheda diventa leggibile
   e i dati esistono anche in un formato aperto, indipendente da Excel;
2. confronta i CSV appena scritti con quelli dell'ultimo commit (HEAD) e
   produce un riepilogo (record aggiunti, rimossi, modificati per foglio),
   usato dal Launcher come messaggio di commit.

La chiave di ogni record è la PRIMA colonna del foglio (ID, Codice_ISAD,
ID_autorita, ID_relazione). I CSV sono derivati: la fonte resta dati.xlsx,
non vanno modificati a mano.
"""

import io
import subprocess
from pathlib import Path

import pandas as pd

CARTELLA_EXPORT = Path("data") / "export"
MAX_ID_NEL_TITOLO = 5


def _nome_file(foglio):
    return f"{foglio.strip().lower().replace(' ', '_')}.csv"


def esporta_csv(root_dir):
    """Scrive data/export/<foglio>.csv per ogni foglio di dati.xlsx.

    Restituisce {nome_foglio: percorso_relativo_csv}.
    """
    root_dir = Path(root_dir)
    excel_path = root_dir / "data" / "dati.xlsx"
    out_dir = root_dir / CARTELLA_EXPORT
    out_dir.mkdir(parents=True, exist_ok=True)

    fogli = pd.read_excel(excel_path, sheet_name=None, dtype=str)
    scritti = {}
    for nome, df in fogli.items():
        df = df.fillna("")
        # Righe completamente vuote (residui di formattazione Excel): via.
        df = df[(df != "").any(axis=1)]
        rel = CARTELLA_EXPORT / _nome_file(nome)
        df.to_csv(root_dir / rel, index=False, encoding="utf-8-sig", lineterminator="\n")
        scritti[nome] = rel
    return scritti


def _leggi_csv(testo):
    return pd.read_csv(io.StringIO(testo), dtype=str, keep_default_na=False)


def _versione_in_head(root_dir, rel_path):
    """Contenuto del CSV nell'ultimo commit, o None se non esiste ancora."""
    risultato = subprocess.run(
        ["git", "show", f"HEAD:{rel_path.as_posix()}"],
        cwd=root_dir, capture_output=True,
    )
    if risultato.returncode != 0:
        return None
    return risultato.stdout.decode("utf-8-sig")


def _per_chiave(df):
    if df.empty:
        return {}
    chiave = df.columns[0]
    df = df[df[chiave].str.strip() != ""]
    return {r[chiave].strip(): r for r in df.to_dict("records")}


def confronta_con_head(root_dir, scritti):
    """Confronta i CSV appena esportati con quelli in HEAD.

    Restituisce una lista di dict, uno per foglio con modifiche:
    {'foglio', 'nuovo' (bool), 'aggiunti', 'rimossi', 'modificati'}.
    """
    root_dir = Path(root_dir)
    esiti = []
    for foglio, rel in scritti.items():
        attuale = _leggi_csv((root_dir / rel).read_text(encoding="utf-8-sig"))
        precedente_txt = _versione_in_head(root_dir, rel)
        if precedente_txt is None:
            esiti.append({"foglio": foglio, "nuovo": True,
                          "aggiunti": [], "rimossi": [], "modificati": []})
            continue
        prima = _per_chiave(_leggi_csv(precedente_txt))
        dopo = _per_chiave(attuale)
        aggiunti = [k for k in dopo if k not in prima]
        rimossi = [k for k in prima if k not in dopo]
        modificati = [k for k in dopo if k in prima and dopo[k] != prima[k]]
        if aggiunti or rimossi or modificati:
            esiti.append({"foglio": foglio, "nuovo": False, "aggiunti": aggiunti,
                          "rimossi": rimossi, "modificati": modificati})
    return esiti


def _elenco(ids, limite=None):
    if limite is None or len(ids) <= limite:
        return ", ".join(ids)
    return ", ".join(ids[:limite]) + f" e altri {len(ids) - limite}"


def componi_messaggio(esiti):
    """(titolo, corpo) per il commit; (None, None) se i dati non sono cambiati."""
    if not esiti:
        return None, None
    if all(e["nuovo"] for e in esiti):
        return ("Dati: prima esportazione CSV dei fogli",
                "Creati: " + ", ".join(e["foglio"] for e in esiti))

    parti_titolo, righe_corpo = [], []
    for e in esiti:
        if e["nuovo"]:
            parti_titolo.append(f"{e['foglio']} (nuovo foglio)")
            righe_corpo.append(f"{e['foglio']}: nuovo foglio")
            continue
        segni = []
        if e["aggiunti"]:
            segni.append(f"+{len(e['aggiunti'])}")
        if e["modificati"]:
            segni.append(f"~{len(e['modificati'])}")
        if e["rimossi"]:
            segni.append(f"-{len(e['rimossi'])}")
        parti_titolo.append(f"{e['foglio']} {' '.join(segni)}")
        for etichetta, chiave in (("aggiunti", "aggiunti"),
                                  ("modificati", "modificati"),
                                  ("rimossi", "rimossi")):
            if e[chiave]:
                righe_corpo.append(f"{e['foglio']} — {etichetta}: {_elenco(e[chiave])}")

    titolo = "Dati: " + ", ".join(parti_titolo)
    # Se c'è un solo foglio e pochi ID, li mettiamo direttamente nel titolo.
    if len(esiti) == 1 and not esiti[0]["nuovo"]:
        ids = esiti[0]["aggiunti"] + esiti[0]["modificati"] + esiti[0]["rimossi"]
        if len(ids) <= MAX_ID_NEL_TITOLO:
            titolo += f" ({_elenco(ids)})"
    return titolo, "\n".join(righe_corpo)


def esporta_e_riepiloga(root_dir):
    """Esegue export + confronto; stampa il riepilogo e restituisce (titolo, corpo)."""
    scritti = esporta_csv(root_dir)
    print(f"Esportati {len(scritti)} fogli in {CARTELLA_EXPORT.as_posix()}/: "
          + ", ".join(p.name for p in scritti.values()))
    titolo, corpo = componi_messaggio(confronta_con_head(root_dir, scritti))
    if titolo:
        print(titolo)
        if corpo:
            print(corpo)
    else:
        print("Nessuna modifica ai dati rispetto all'ultimo commit.")
    return titolo, corpo
