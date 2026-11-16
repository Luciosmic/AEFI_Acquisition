---
type: constat::sh-agent-os
genere_par: "[[tache - typer les traces du post traitement]]"
---

# Le plan est typé sans enregistrements d'étapes : une alerte du générateur

`plan-de-travail::sh-agent-os` n'exige aucun champ (`etapes` est optionnel) : `au_validate` accepte le plan avec le seul `type`, et `au_diagnostics` ne rend rien sur le dossier.

Le générateur de notes a toutefois émis `alerte etape=1.5 catalogue des acquisitions et lecture d'une carte absente des étapes de plan - post-traitement conforme.md` pour la tâche `…-1-0-a-1-3` : le plan liste ses étapes en prose (1 à 3), pas en enregistrements inline `^:`, et la trace de cette tâche nomme des étapes 1.0 à 1.5.

Aucune décision prise ici : le plan n'est pas réécrit. Si l'humain veut que les notes de tâche se rattachent à des étapes du plan, la correction est de déclarer les étapes 1.0 à 1.9 de la tranche 1 en `etapes` inline dans le plan.
