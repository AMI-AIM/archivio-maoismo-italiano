"""Date, intervalli, slug e liste di nomi: le convenzioni del catalogo."""
import unittest

from tests import _percorsi  # noqa: F401
from core.utils import formatta_data, formatta_estremo, formatta_intervallo, slugify, split_nomi


class TestDate(unittest.TestCase):
    def test_anno(self):
        self.assertEqual(formatta_data("1968"), ("1968", (1968, 1, 1)))

    def test_data_incerta_diventa_ca(self):
        self.assertEqual(formatta_data("196?")[0], "ca. 1960")

    def test_senza_data(self):
        for valore in ("????", "", "s.d.", None):
            self.assertEqual(formatta_data(valore)[0], "s.d.", valore)
            self.assertEqual(formatta_data(valore)[1][0], 9999, "le date assenti vanno in fondo")

    def test_mese_e_anno(self):
        self.assertEqual(formatta_data("03/1968")[0], "marzo 1968")
        self.assertEqual(formatta_data("1968-05")[0], "maggio 1968")

    def test_giorno_preciso_in_formato_italiano(self):
        self.assertEqual(formatta_data("14/05/1968")[0], "14 maggio 1968")
        # Le celle data di Excel arrivano come "AAAA-MM-GG 00:00:00"
        self.assertEqual(formatta_data("1968-05-14 00:00:00")[0], "14 maggio 1968")

    def test_ambiguita_giorno_mese_letta_all_italiana(self):
        self.assertEqual(formatta_data("05/12/1970")[0], "5 dicembre 1970")

    def test_data_non_riconosciuta_resta_com_e(self):
        self.assertEqual(formatta_data("primavera 1968"), ("primavera 1968", (9999, 1, 1)))


class TestEstremi(unittest.TestCase):
    def test_estremi(self):
        self.assertEqual(formatta_estremo("1921"), "1921")
        self.assertEqual(formatta_estremo("196?"), "ca. 1960")
        self.assertEqual(formatta_estremo("????"), "s.d.")
        self.assertEqual(formatta_estremo("nan"), "")

    def test_intervalli(self):
        self.assertEqual(formatta_intervallo("1921", "1993"), "1921 – 1993")
        self.assertEqual(formatta_intervallo("????", "????"), "s.d.")
        self.assertEqual(formatta_intervallo("", ""), "s.d.")
        self.assertEqual(formatta_intervallo("1921", ""), "1921 – ")
        self.assertEqual(formatta_intervallo("", "1993"), "? – 1993")


class TestNomi(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slugify("Partito Comunista d'Italia (marxista-leninista)"),
                         "partito-comunista-ditalia-marxista-leninista")
        self.assertEqual(slugify("Nuova Unità"), "nuova-unita")

    def test_split_nomi(self):
        self.assertEqual(split_nomi("Fosco Dinucci; Osvaldo Pesce"), ["Fosco Dinucci", "Osvaldo Pesce"])
        self.assertEqual(split_nomi("a, b"), ["a", "b"])
        self.assertEqual(split_nomi(""), [])
        self.assertEqual(split_nomi("nan"), [])


if __name__ == "__main__":
    unittest.main()
