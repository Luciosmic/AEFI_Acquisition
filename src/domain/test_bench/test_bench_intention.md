# test_bench — Intention

Contexte cohésif du banc d'essai : ce qui décrit et caractérise le banc physique sur lequel les capteurs sont montés.

## Rationale

Sans ce contexte, la calibration vivait dans son propre dossier de premier niveau, et les limites physiques du banc dans le shared kernel global. Chaque nouvel élément du banc (composant monté, angle capteur, géométrie des sources, transmission mécanique) se rangeait donc là où il avait été écrit en premier, et rien ne disait que ces éléments changent ensemble. Or ils changent ensemble : un remontage du banc fait changer à la fois les composants montés, les angles et la géométrie. Le shared kernel global, lui, ne doit garder que ce qui sert à tous les contextes, pas la description d'un banc particulier.

Un contexte cohésif n'est pas encore un bounded context. Il n'a pas de langage propre et vit dans le même `src/`. C'est le regroupement intermédiaire entre l'agrégat et le bounded context.

## Responsibility

- `calibration/` : l'agrégat `Calibration` et ses entrées de calibration. Il couvre les capteurs, la géométrie des sources, la transmission mécanique, la phase de détection synchrone et les composants matériels montés. On y trouve aussi les événements, dont `sensor_transformation_angles_updated`, ainsi que les repositories, value objects et services du domaine.
- `physical_bench_limits/` : les limites physiques de course du banc, utilisées par la configuration de scan.

## Design

- Un agrégat par dossier à l'intérieur du contexte. Chaque dossier garde son trio atomique (intention, code, `_tests/`).
- Les autres contextes, comme `scan` et `detection_devices`, peuvent importer `test_bench`. `test_bench` n'importe que le shared kernel global.
- Ce découpage est provisoire : l'agrégat `Calibration` porte encore des éléments propres au capteur AEFI (phase de détection synchrone, analyse de débit de l'ADC). Ils pourraient rejoindre `detection_devices/aefi_device/` si leur cause de changement s'avère être le capteur plutôt que le banc.
