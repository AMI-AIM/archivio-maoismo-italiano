"""
Crea tests/dati_prova.xlsx: un piccolo estratto di data/dati.xlsx usato dal
test di confronto (tests/test_sito.py).

Prende un documento per ogni Tipo più alcuni con date particolari, le persone
e le organizzazioni che citano, le relazioni tra loro e tutta la Raccolta.
Svuota URL e nomi file: il test non deve dipendere da Internet Archive (né
dalla rete), così il risultato è sempre identico.

Da rilanciare solo se si vuole cambiare l'estratto (poi aggiornare il
riferimento: python -m tests.confronto --aggiorna).
    python -m tests.crea_dati_prova
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.utils import split_nomi  # noqa: E402

DESTINAZIONE = ROOT / "tests" / "dati_prova.xlsx"
COLONNE_SENZA_RETE = ["URL", "Nome_file", "Nome_file_originale", "Nome_file_traduzione"]


def main():
    fogli = pd.read_excel(ROOT / "data" / "dati.xlsx", sheet_name=None, dtype=str)
    fogli = {k: v.fillna("") for k, v in fogli.items()}
    cat = fogli["Catalogo"]

    scelti = []
    for _, gruppo in cat.groupby("Tipo", sort=True):
        scelti.append(gruppo.index[0])
    # Date particolari: incerte (?), solo mese/anno, giorno preciso.
    for maschera in (cat["Data"].str.contains(r"\?", regex=True),
                     cat["Data"].str.fullmatch(r"\d{2}/\d{4}"),
                     cat["Data"].str.contains(r"\d{4}-\d{2}-\d{2}", regex=True),
                     cat["Persone_collegate"].str.count(";") >= 2):
        indici = cat.index[maschera]
        if len(indici):
            scelti.append(indici[0])
    estratto = cat.loc[sorted(set(scelti))].copy()
    for col in COLONNE_SENZA_RETE:
        if col in estratto.columns:
            estratto[col] = ""

    nomi = set()
    for col in ("Autore", "Organizzazione", "Persone_collegate", "Organizzazioni_collegate"):
        for valore in estratto[col]:
            nomi.update(split_nomi(valore))
    persone = fogli["Persone"][fogli["Persone"]["Nome"].isin(nomi)]
    org = fogli["Organizzazioni"][fogli["Organizzazioni"]["Nome"].isin(nomi)]
    ids = set(persone["ID_autorita"]) | set(org["ID_autorita"])
    rel = fogli["Relazioni"]
    rel = rel[(rel["ID_entita_A"].isin(ids) | (rel["ID_entita_A"] == ""))
              & (rel["ID_entita_B"].isin(ids) | (rel["ID_entita_B"] == ""))
              & ((rel["ID_entita_A"].isin(ids)) | (rel["ID_entita_B"].isin(ids)))]

    with pd.ExcelWriter(DESTINAZIONE) as w:
        estratto.to_excel(w, sheet_name="Catalogo", index=False)
        fogli["Raccolta"].to_excel(w, sheet_name="Raccolta", index=False)
        persone.to_excel(w, sheet_name="Persone", index=False)
        org.to_excel(w, sheet_name="Organizzazioni", index=False)
        rel.to_excel(w, sheet_name="Relazioni", index=False)
    print(f"{DESTINAZIONE.name}: {len(estratto)} documenti, {len(persone)} persone, "
          f"{len(org)} organizzazioni, {len(rel)} relazioni")


if __name__ == "__main__":
    main()
