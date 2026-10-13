"""Compressione dei CSS a fine build (scripts/hooks/minifica_css.py)."""
import importlib.util
import unittest

from tests._percorsi import ROOT

_spec = importlib.util.spec_from_file_location(
    "minifica_css", ROOT / "scripts" / "hooks" / "minifica_css.py")
_modulo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_modulo)
minifica = _modulo.minifica


class TestMinificaCss(unittest.TestCase):
    def test_toglie_commenti_e_spazi(self):
        css = "/* nota */\n.a {\n  color: red;\n  margin: 0 auto;\n}\n"
        self.assertEqual(minifica(css), ".a{color:red;margin:0 auto}\n")

    def test_conserva_lo_spazio_del_discendente(self):
        # ".a :first-child" e ".a:first-child" sono selettori diversi
        self.assertEqual(minifica(".a :first-child { x: 1 }"), ".a :first-child{x:1}\n")

    def test_conserva_le_stringhe(self):
        css = '.a::before { content: "/* non e\' un commento */  ;  { }"; }'
        self.assertEqual(minifica(css), '.a::before{content:"/* non e\' un commento */  ;  { }"}\n')

    def test_calc_resta_valido(self):
        self.assertEqual(minifica(".a { width: calc(100% - 2rem); }"), ".a{width:calc(100% - 2rem)}\n")

    def test_media_query(self):
        css = "@media (max-width: 600px) {\n  .a { display: none; }\n}"
        self.assertEqual(minifica(css), "@media (max-width:600px){.a{display:none}}\n")

    def test_commento_tra_due_parole(self):
        self.assertEqual(minifica(".a{margin:0/* x */auto}"), ".a{margin:0 auto}\n")


if __name__ == "__main__":
    unittest.main()
