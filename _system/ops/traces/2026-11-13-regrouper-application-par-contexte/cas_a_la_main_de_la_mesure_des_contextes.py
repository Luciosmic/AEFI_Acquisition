"""Cas a la main : 3 dossiers (a, b, shared), domaine, interface.

Arcs de production :
  a/x.py -> b/y.py          (a vers contexte b)
  a/x.py -> shared/s/z.py   (a vers shared)
  b/y.py -> shared/s/z.py   (b vers shared)
  a/x.py -> domain/d.py     (a vers domaine)
  interface/p.py -> a/x.py  (exterieur vers a)
  shared/s/z.py -> b/y.py   (shared vers b : arc en sens inverse du noyau)
Attendu a la main :
  a : sortants_app 2 (b, shared), entrants_app 0, I_app 1.0 ; vers_domaine 1, depuis_exterieur 1, I_tout = 3/(3+1) = 0.75
  b : sortants_app 1 (shared), entrants_app 2 (a, shared), I_app = 1/3
  shared : sortants_app 1 (b), entrants_app 2 (a, b), I_app = 1/3
"""
import unittest

from mesurer_les_contextes import mesure

G = {
    "noeuds": [{"path": p} for p in [
        "src/application/a/s1/x.py", "src/application/b/s2/y.py", "src/application/shared/s/z.py",
        "src/domain/d.py", "src/interface/p.py"]],
    "arcs": [{"source": s, "cible": t} for s, t in [
        ("src/application/a/s1/x.py", "src/application/b/s2/y.py"),
        ("src/application/a/s1/x.py", "src/application/shared/s/z.py"),
        ("src/application/b/s2/y.py", "src/application/shared/s/z.py"),
        ("src/application/a/s1/x.py", "src/domain/d.py"),
        ("src/interface/p.py", "src/application/a/s1/x.py"),
        ("src/application/shared/s/z.py", "src/application/b/s2/y.py")]],
}


class MesureTest(unittest.TestCase):
    def test_cas_a_la_main(self):
        r = mesure(G)
        self.assertEqual((r["a"]["sortants_app"], r["a"]["entrants_app"], r["a"]["I_app"]), (2, 0, 1.0))
        self.assertEqual((r["a"]["vers_domaine"], r["a"]["depuis_exterieur"], r["a"]["I_tout"]), (1, 1, 0.75))
        self.assertEqual((r["b"]["sortants_app"], r["b"]["entrants_app"]), (1, 2))
        self.assertAlmostEqual(r["b"]["I_app"], 1 / 3)
        self.assertEqual((r["shared"]["sortants_app"], r["shared"]["entrants_app"]), (1, 2))
        self.assertEqual(dict(r["shared"]["depuis_contextes"]), {"a": 1, "b": 1})
        self.assertEqual(r["b"]["depuis_shared"], 1)


if __name__ == "__main__":
    unittest.main()
