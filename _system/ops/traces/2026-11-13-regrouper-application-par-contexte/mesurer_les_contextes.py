#!/usr/bin/env python3
"""Mesure des contextes de src/application/ depuis la sortie JSON de `solidai graphe`.

usage: mesurer_les_contextes.py <graphe.json>
Un contexte = le dossier sous src/application/ (shared = noyau partage, services = ambigus restants).
Un arc = un couple (module source, module cible) du graphe d'imports de production, sans les tests.
I = sortants / (entrants + sortants) (Martin, *Agile Software Development*, ch. 20).
  I_app : seulement les arcs entre dossiers de src/application/.
  I_tout : ajoute les sortants vers src/domain et les entrants de interface, infrastructure et main.
"""
import json
import sys
from collections import defaultdict


def contexte(path):
    parts = path.split("/")
    if len(parts) >= 4 and parts[0] == "src" and parts[1] == "application":
        return parts[2]
    return None


def couche(path):
    parts = path.split("/")
    if path == "src/main.py":
        return "main"
    if len(parts) >= 2 and parts[0] == "src":
        return parts[1]
    return "hors-src"


def mesure(graphe):
    dossiers = defaultdict(set)
    for n in graphe["noeuds"]:
        c = contexte(n["path"])
        if c:
            dossiers[c].add(n["path"].split("/")[3])
    res = {c: {"dossiers": len(d), "vers_contextes": defaultdict(int), "vers_shared": 0, "depuis_contextes": defaultdict(int),
               "depuis_shared": 0, "vers_domaine": 0, "depuis_exterieur": 0} for c, d in dossiers.items()}
    for a in graphe["arcs"]:
        s, t = a["source"], a["cible"]
        cs, ct = contexte(s), contexte(t)
        if cs in res and ct is None and couche(t) == "domain":
            res[cs]["vers_domaine"] += 1
        if ct in res and cs is None and couche(s) in ("interface", "infrastructure", "main"):
            res[ct]["depuis_exterieur"] += 1
        if cs in res and ct in res and cs != ct:
            if ct == "shared":
                res[cs]["vers_shared"] += 1
            else:
                res[cs]["vers_contextes"][ct] += 1
            if cs == "shared":
                res[ct]["depuis_shared"] += 1
            else:
                res[ct]["depuis_contextes"][cs] += 1
    for c, r in res.items():
        out_app = sum(r["vers_contextes"].values()) + r["vers_shared"]
        in_app = sum(r["depuis_contextes"].values()) + r["depuis_shared"]
        r["sortants_app"], r["entrants_app"] = out_app, in_app
        r["I_app"] = out_app / (out_app + in_app) if out_app + in_app else None
        out_all, in_all = out_app + r["vers_domaine"], in_app + r["depuis_exterieur"]
        r["I_tout"] = out_all / (out_all + in_all) if out_all + in_all else None
    return res


def fmt(x):
    return "n/a" if x is None else f"{x:.2f}"


def main():
    g = json.load(open(sys.argv[1]))
    res = mesure(g)
    print("| Contexte | Dossiers | Sortants vers contextes | Sortants vers shared | Entrants depuis contextes | Entrants depuis shared | I_app | Vers domaine | Depuis interface, infra, main | I_tout |")
    print("| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |")
    for c in sorted(res):
        r = res[c]
        vc = ", ".join(f"{k} {v}" for k, v in sorted(r["vers_contextes"].items())) or "0"
        dc = ", ".join(f"{k} {v}" for k, v in sorted(r["depuis_contextes"].items())) or "0"
        print(f"| {c} | {r['dossiers']} | {vc} | {r['vers_shared']} | {dc} | {r['depuis_shared']} | {fmt(r['I_app'])} | {r['vers_domaine']} | {r['depuis_exterieur']} | {fmt(r['I_tout'])} |")


if __name__ == "__main__":
    main()
