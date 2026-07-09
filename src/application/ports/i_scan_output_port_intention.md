# i_scan_output_port (application/ports) — Intention

## Rationale

Port de sortie global (application-level) pour la présentation des résultats de scan. Distinct du `i_scan_output_port` dans `scan_application_service/` : ce fichier représente une définition partagée ou une version applicative globale accessible depuis plusieurs services.

## Responsibility

- Déclarer le contrat de présentation des résultats scan utilisé au niveau applicatif.

## Design

- **ABC** avec méthodes abstraites uniquement.
- Placé dans `application/ports/` pour usage transverse si plusieurs services partagent ce contrat.
