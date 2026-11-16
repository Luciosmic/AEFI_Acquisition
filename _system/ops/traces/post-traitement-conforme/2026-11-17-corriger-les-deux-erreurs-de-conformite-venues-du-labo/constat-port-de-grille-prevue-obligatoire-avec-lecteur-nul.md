---
type: constat::sh-agent-os
genere_par: "[[tache - corriger les deux erreurs de conformite venues du labo]]"
doc_type: constat
---
# Le lecteur de grille prévue devient un port obligatoire, avec un lecteur nul par défaut

Constat : `PostProcessingService` recevait `Optional[IScanPlanReader] = None`. Le port est bien rangé dans `ports/` du service (H2 respectée), mais H10 (`solidai-service-depend-hors-de-ses-ports`) exige que l'annotation soit exactement le nom du port : `Optional[...]` est refusé.

Choix : `scan_plan_reader: IScanPlanReader = NO_SCAN_PLAN`, où `NO_SCAN_PLAN` est un `NoScanPlanReader` (`application/post_processing_service/no_scan_plan_reader.py`) dont `planned_grid` rend `None`. Le test `if self._scan_plan_reader` disparaît.

Raison en une ligne : le comportement est identique (aucune grille prévue, grille carrée) et les tests du labo, qui construisent le service avec deux arguments, restent inchangés.

Vérifié : 170 passés + les 2 échecs connus, `golden_master_test.py` vert, 6 passés sur le port et l'intégration, erreur H10 disparue. L'intention du service cite le nouveau fichier dans `code` et dans le Design.
