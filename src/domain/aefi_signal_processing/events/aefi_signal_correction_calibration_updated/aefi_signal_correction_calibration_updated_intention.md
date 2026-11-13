---
type: evenement-de-domaine::solidai-ddd
tldr: "Fait passé : la calibration de correction de signal a été mise à jour (calibration d'une étape, bascule d'activation, ou reset)."
code: ["[[src/domain/aefi_signal_processing/events/aefi_signal_correction_calibration_updated/aefi_signal_correction_calibration_updated.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/aefi_signal_processing/aefi_corrected_sample_intention]]"
---
# aefi_signal_correction_calibration_updated — Intention

## Rationale

Le presenter affiche aujourd'hui l'état de calibration en lisant directement `self._processor.state` (`aefi_continuous_reading_presenter.py::_emit_correction_states`), couplant la UI à la structure interne de `SignalPostProcessor`. Une fois la calibration déplacée dans la couche application (`AefiSignalProcessingService`), le presenter ne doit plus lire un état interne : il doit réagir à un fait publié.

## Responsibility

- Fait passé : la calibration de correction de signal a été mise à jour (calibration d'une étape, bascule d'activation, ou reset).
- Porte l'instantané complet de la calibration courante (`AefiSignalCorrectionCalibration`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par la couche application (`AefiSignalProcessingService`) après chaque commande de calibration — pas par l'agrégat `AefiCorrectedSample`, qui ne porte pas l'état de calibration entre deux échantillons. Topic : `"aefisignalcorrectioncalibrationupdated"`.
