"""Validazione di dati.xlsx (core/validator.py) su un file di prova costruito qui."""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tests import _percorsi  # noqa: F401
from core.validator import COLONNE_ATTESE, ERRORE, AVVISO, valida


def riga(foglio, **valori):
    base = {c: "" for c in COLONNE_ATTESE[foglio]}
    base.update(valori)
    return base


def catalogo_valido():
    return [
        riga("Catalogo", ID="AMI-0001", Livello="unità", Titolo="Citazioni", Titolo_attribuito="No",
             Autore="Mao Zedong", Organizzazione="Partito Comunista Cinese", Data="1968",
             Data_normalizzata="1968", Tipo="Libro", Percorsi="Libretti rossi",
             URL="https://archive.org/details/prova-uno"),
        riga("Catalogo", ID="AMI-0002", Livello="unità", Titolo="Volantino", Titolo_attribuito="Sì",
             Organizzazione="Partito Comunista Cinese", Data="14/05/1969",
             Data_normalizzata="1969-05-14", Tipo="Volantino",
             URL="https://archive.org/details/prova-due"),
    ]


def fogli_validi():
    return {
        "Catalogo": catalogo_valido(),
        "Raccolta": [riga("Raccolta", Codice_ISAD="3.1.1", Elemento="Segnatura", Valore="AMI")],
        "Persone": [riga("Persone", ID_autorita="AMI-P-001", Tipo_entita="Persona", Nome="Mao Zedong",
                         Nascita="1893", Morte="1976", Immagine="mao.webp", Wikidata="Q5816")],
        "Organizzazioni": [riga("Organizzazioni", ID_autorita="AMI-O-001", Tipo_entita="Ente",
                                Nome="Partito Comunista Cinese", Fondazione="1921")],
        "Relazioni": [riga("Relazioni", ID_relazione="AMI-R-001", ID_entita_A="AMI-P-001",
                           Entita_A="Mao Zedong", ID_entita_B="AMI-O-001",
                           Entita_B="Partito Comunista Cinese", Relazione="presidente di",
                           Categoria_ISAAR="gerarchica", Date="1943-1976")],
    }


class TestValidatore(unittest.TestCase):
    def valida_fogli(self, fogli):
        with tempfile.TemporaryDirectory() as tmp:
            percorso = Path(tmp) / "dati.xlsx"
            with pd.ExcelWriter(percorso) as w:
                for nome, righe in fogli.items():
                    pd.DataFrame(righe, columns=COLONNE_ATTESE[nome]).to_excel(w, sheet_name=nome, index=False)
            return valida(percorso)

    def messaggi(self, rapporto, gravita):
        return [f"{v['foglio']}|{v['colonna']}|{v['messaggio']}"
                for v in rapporto.voci if v["gravita"] == gravita]

    def test_dati_validi(self):
        r = self.valida_fogli(fogli_validi())
        self.assertEqual(self.messaggi(r, ERRORE), [])
        self.assertEqual(self.messaggi(r, AVVISO), [])

    def test_id_duplicato_e_errore(self):
        fogli = fogli_validi()
        fogli["Catalogo"][1]["ID"] = "AMI-0001"
        errori = self.messaggi(self.valida_fogli(fogli), ERRORE)
        self.assertTrue(any("duplicato" in e for e in errori), errori)

    def test_immagine_mancante_e_errore(self):
        fogli = fogli_validi()
        fogli["Persone"][0]["Immagine"] = "inesistente.webp"
        errori = self.messaggi(self.valida_fogli(fogli), ERRORE)
        self.assertTrue(any("inesistente.webp" in e for e in errori), errori)

    def test_relazione_verso_id_inesistente_e_errore(self):
        fogli = fogli_validi()
        fogli["Relazioni"][0]["ID_entita_B"] = "AMI-O-999"
        errori = self.messaggi(self.valida_fogli(fogli), ERRORE)
        self.assertTrue(any("AMI-O-999" in e for e in errori), errori)

    def test_colonna_rinominata_e_errore(self):
        fogli = fogli_validi()
        validi = self.valida_fogli(fogli)
        self.assertTrue(validi.valido)
        fogli["Organizzazioni"][0]["Storia_x"] = "testo"
        with tempfile.TemporaryDirectory() as tmp:
            percorso = Path(tmp) / "dati.xlsx"
            with pd.ExcelWriter(percorso) as w:
                for nome, righe in fogli.items():
                    colonne = [c if not (nome == "Organizzazioni" and c == "Storia") else "Storia_x"
                               for c in COLONNE_ATTESE[nome]]
                    pd.DataFrame(righe).reindex(columns=colonne).to_excel(w, sheet_name=nome, index=False)
            r = valida(percorso)
        self.assertTrue(any("Storia" in e for e in self.messaggi(r, ERRORE)))

    def test_avvisi(self):
        fogli = fogli_validi()
        fogli["Catalogo"][0]["Autore"] = "Mao Tse-tung"          # forma variante
        fogli["Catalogo"][1]["Data"] = "primavera 1969"            # data non riconosciuta
        fogli["Catalogo"][1]["Percorsi"] = "Percorso inventato"    # percorso senza immagine
        fogli["Relazioni"][0]["Categoria_ISAAR"] = "da definire"   # categoria non valida
        fogli["Persone"][0]["Forme_varianti"] = "Mao Tse-tung"
        r = self.valida_fogli(fogli)
        avvisi = " ".join(self.messaggi(r, AVVISO))
        self.assertEqual(self.messaggi(r, ERRORE), [])
        for atteso in ("forma variante", "non riconosciuta", "non ha un'immagine", "Categoria_ISAAR"):
            self.assertIn(atteso, avvisi)

    def test_date_incerte_accettate(self):
        fogli = fogli_validi()
        fogli["Persone"][0]["Nascita"] = "????"
        fogli["Relazioni"][0]["Date"] = "196?-1976"
        r = self.valida_fogli(fogli)
        self.assertEqual(self.messaggi(r, AVVISO), [])


if __name__ == "__main__":
    unittest.main()
