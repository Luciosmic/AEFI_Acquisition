# processing — raccord vers le service de traitement

Ce dossier ne tient plus que `processing_pipeline.py`, un raccord temporaire.
L'adaptateur de l'acquisition (`src/infrastructure/aefi_post_processor_port`) importe encore `ProcessingPipeline`, et son test patche ce nom.
Le raccord garde la signature d'origine et délègue à `PostProcessingService`, câblé sans Qt par `interface/shell/headless_wiring.py`. Il sera retiré en tranche 6, quand l'adaptateur appellera le service directement.

```python
from processing import ProcessingPipeline

with ProcessingPipeline("acquisition.h5") as pipeline:
    summary = pipeline.run_full_pipeline(
        csv_path="scan_data.csv",
        rotation_angles=(0.0, 0.0, 0.0),  # (θx, θy, θz) en degrés
        skip_interpolation=False,
    )
    print(summary["steps_completed"], summary["errors"])
```

Le calcul vit dans `domain/processing/` (un dossier par étape), l'enchaînement dans `application/post_processing_service/`, la lecture du CSV et l'écriture du `.h5` dans `infrastructure/`. Voir `../Data Processing Architecture.md`.
