---
type: constat::sh-agent-os
genere_par: "[[tache - separer test bench calibration et configuration]]"
doc_type: constat
date: 2026-11-13
---

# Typer le noyau partagé fait monter `solidai verify` de 987 à 1 070, et la règle ne se satisfait pas aujourd'hui

**Tranché par l'humain : choix 1** (D14 ne compare plus que les utilisateurs sous `domain/`, solidai-ddd `b7f1265`, solidai-verify `7f02cf9`). Le noyau est ensuite typé avec ses 10 utilisateurs typés du domaine ; les restants sont dans `constat-restants-du-noyau-partage-et-de-detection-devices.md`. Ce qui suit garde l'essai d'origine.

**Essai d'origine.** Le typage du noyau (`domain/shared_kernel/`) est retiré (commit `f57f411`), les 12 événements et 2 objets-valeurs à plat restent non rattachés. Ni la règle ni l'outil ne sont en cause : c'est l'étendue de D14 sur ACQ.

## Ce qui a été essayé

`operation_result_intention.md` typée `noyau-partage::solidai-ddd` (`code` : `operation_result.py`, `utilise_par` : un utilisateur). Mesure : 987 → 1 070 erreurs, soit +84 `solidai-noyau-partage-utilisateurs-ecart` et −1 `intention-non-typee`. Une tentative de déclarer un utilisateur sans type (`scan_application_service_intention`) donne l'erreur d'engine `reference-target-type-mismatch` : `utilise_par` n'accepte que des notes typées `atome`.

## Pourquoi

D14 compare à `utilise_par` **tous** les modules de production qui importent le noyau, pas seulement ceux du domaine. R21 rend 85 unités (un agrégat, ou le dossier du module) :

| Couche | Unités | Dont intention typée | Non typable aujourd'hui |
| --- | --- | --- | --- |
| domaine | 11 | 10 | 1 (`detection_devices`, aucune intention dans le dossier) |
| application | 36 | 1 | 35 |
| infrastructure | 36 | 8 | 28 (dont `aefi_post_processor_port`, aucune intention) |
| interface | 2 | 0 | 2 |

Le champ dit pourtant « les éléments du domaine qui importent le noyau », ce que la décision de l'humain reprend (« quels autres éléments du domaine les utilisent »). Les deux textes ne disent pas la même étendue. Le noyau d'ACQ est importé partout (`OperationResult`, `DomainEvent`, bus, bornes de mesure), donc la règle telle qu'elle est écrite demande 85 déclarations, et 66 d'entre elles visent des intentions que les lots d'application, d'infrastructure et d'interface n'ont pas encore typées.

## Choix

1. **Restreindre D14 au domaine** (solidai-ddd, `shared_kernel_users_gap`) : seuls les modules sous `domain/` comptent, le champ dit déjà « éléments du domaine ». Le noyau d'ACQ déclare alors 11 utilisateurs, dont 10 sont typés ; `detection_devices` reste à typer. Recommandation.
2. **Garder D14 sur toutes les couches** et typer d'abord les intentions d'application, d'infrastructure et d'interface (lots hexagonaux déjà prévus), puis le noyau. Le noyau reste alors non typé tant que ces lots ne sont pas faits.
3. **Typer le noyau avec ses 11 utilisateurs du domaine maintenant** et laisser 74 erreurs D14 que les lots suivants font tomber à mesure qu'ils typent. Le total passe sous 1 031 seulement quand ces lots sont faits.

## Restants dans `shared_kernel` (dans l'état de départ, non rattachés)

- Événements à plat, `events/<nom>/` : `aefi_acquisition_control_changed`, `aefi_voltage_reading_failed`, `aefi_voltage_reading_started`, `aefi_voltage_reading_stopped`, `aefi_voltage_sample_acquired`, `hardware_configuration_control_changed`, `system_ready_event`, `system_shutdown_complete_event`, `system_shutting_down_event`, `system_startup_failed_event` (10).
- Objets-valeurs à plat, `value_objects/<nom>/` : `measurement_uncertainty`, `validation_result` (2).
- Ni événement ni objet-valeur : `events/domain_event` (classe de base) et `events/i_domain_event_bus` (port du bus), à typer `atome`.
- Un niveau de regroupement que D3 et D4 ne lisent pas, laissés en place : `excitation/events/` (4), `excitation/value_objects/` (5, fichiers sans dossier par valeur), `motion/events/` (9), `value_objects/acquisition/`, `value_objects/geometric/`, `value_objects/hardware_configuration/` (1 fichier chacun, dossier au nom du thème). Même question que le point 1 de `constat-le-noyau-partage-a-discuter.md` du dossier SOLIDAI, étendue à ces trois dossiers.

Mesures de la tentative : `run-verify-noyau-type.json` (1 070) contre `run-verify-lot-depots.json` (987).
