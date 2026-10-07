"""Messaggi di commit generati dal confronto dei CSV (core/export_dati.py)."""
import unittest

from tests import _percorsi  # noqa: F401
from core.export_dati import componi_messaggio


def esito(foglio, aggiunti=(), modificati=(), rimossi=(), nuovo=False):
    return {"foglio": foglio, "nuovo": nuovo, "aggiunti": list(aggiunti),
            "modificati": list(modificati), "rimossi": list(rimossi)}


class TestMessaggi(unittest.TestCase):
    def test_nessuna_modifica(self):
        self.assertEqual(componi_messaggio([]), (None, None))

    def test_un_foglio_con_pochi_id_nel_titolo(self):
        titolo, corpo = componi_messaggio([esito("Catalogo", aggiunti=["AMI-0097"], modificati=["AMI-0034"])])
        self.assertEqual(titolo, "Dati: Catalogo +1 ~1 (AMI-0097, AMI-0034)")
        self.assertIn("Catalogo — aggiunti: AMI-0097", corpo)

    def test_piu_fogli(self):
        titolo, _ = componi_messaggio([esito("Catalogo", aggiunti=["AMI-0097"]),
                                       esito("Persone", rimossi=["AMI-P-001"])])
        self.assertEqual(titolo, "Dati: Catalogo +1, Persone -1")

    def test_prima_esportazione(self):
        titolo, _ = componi_messaggio([esito("Catalogo", nuovo=True), esito("Persone", nuovo=True)])
        self.assertEqual(titolo, "Dati: prima esportazione CSV dei fogli")


if __name__ == "__main__":
    unittest.main()
