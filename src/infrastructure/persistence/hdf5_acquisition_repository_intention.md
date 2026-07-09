# hdf5_acquisition_repository — Intention

## Rationale

Implémentation HDF5 de `IAcquisitionDataRepository` pour la persistence des `AcquisitionSample` en format haute-performance. HDF5 est choisi pour sa capacité à stocker des arrays numériques compressés et à les étendre incrémentalement (append), adapté à l'accumulation de données de scan.

## Responsibility

- `save(scan_id, data)` : créer ou étendre un dataset HDF5 resizable avec les N nouveaux échantillons.
- `find_by_scan(scan_id)` : lire et désérialiser tous les échantillons pour un scan donné.
- Organiser les fichiers par scan_id dans `base_path/scan_<id>.h5`.

## Design

- **Compound dtype numpy** : 7 champs float64 (timestamp + 6 composantes) — accès vectorisé efficace.
- **Dataset resizable (maxshape=(None,), chunks=True)** : permet l'append sans réécriture du fichier.
- **Mode `'a'` ou `'w'`** selon l'existence du fichier : pas de corruption si interruption.
- Sanitisation du `scan_id` pour la création de noms de fichier safe.
