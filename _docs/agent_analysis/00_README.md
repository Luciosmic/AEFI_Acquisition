# Analyse PyMoDAQ pour AEFI_Acquisition

**Date:** 2025-11-16  
**Analyste:** Agent d'Analyse SOLID  
**Objectif:** Analyser PyMoDAQ pour reconstruire AEFI_Acquisition avec une architecture conforme à SOLID, DDD et ADD

---

## Vue d'Ensemble

Ce dossier contient l'analyse complète de PyMoDAQ et la stratégie de migration pour le projet AEFI_Acquisition.

**Contexte:**  
Le logiciel Legacy AEFI_Acquisition a été développé avec une approche **bottom-up** (en partant des contrôleurs hardware), ce qui viole les principes SOLID, notamment le **Dependency Inversion Principle (DIP)**. PyMoDAQ offre une architecture **top-down** qui respecte ces principes.

---

## Documents d'Analyse

### 📄 [01_PyMoDAQ_Architecture_Overview.md](./01_PyMoDAQ_Architecture_Overview.md)
**Contenu:**
- Architecture globale de PyMoDAQ (Dashboard, Control Modules, Extensions)
- Flux d'exécution d'un scan
- Analyse de conformité SOLID (4.5/5)
- Points d'extension identifiés

**Highlights:**
- ✅ Architecture en couches respectant DIP
- ✅ Système de plugins via entry points (OCP)
- ✅ Séparation claire des responsabilités (SRP)
- ✅ Scanner système modulaire et extensible

---

### 📄 [02_PyMoDAQ_Plugin_System.md](./02_PyMoDAQ_Plugin_System.md)
**Contenu:**
- Contrats d'interface pour plugins actuateurs (`DAQ_Move_base`)
- Contrats d'interface pour plugins détecteurs (`DAQ_Viewer_base`)
- Système d'entry points Python
- Checklist création de plugins
- Exemples de code complets

**Highlights:**
- ✅ Interfaces abstraites bien définies
- ✅ Documentation claire des responsabilités
- ✅ Méthodes obligatoires vs optionnelles explicites
- ✅ Support multi-axes et modes live

---

### 📄 [03_PyMoDAQ_Scanner_System.md](./03_PyMoDAQ_Scanner_System.md)
**Contenu:**
- Système de Scanner pour acquisitions multi-points
- ScannerBase: contrat d'interface abstrait
- Types de scanners implémentés (1D, 2D, Tabular, Sequential)
- Factory Pattern pour extensibilité
- Intégration avec DAQScan

**Highlights:**
- ✅ Calcul préalable de TOUTES les positions
- ✅ Format `positions[axis, step]` standardisé
- ✅ Factory Pattern pour ajouter nouveaux scanners
- ✅ Directement utilisable pour AEFI (Scan1D Linear)

---

### 📄 [04_AEFI_Migration_Strategy.md](./04_AEFI_Migration_Strategy.md)
**Contenu:**
- Analyse du Legacy AEFI_Acquisition
- Architecture cible avec PyMoDAQ
- Plan de migration en 6 phases
- Exemples de code complets pour chaque plugin
- Mapping Legacy → PyMoDAQ
- Checklist et estimation d'effort (5-8 jours)

**Highlights:**
- ✅ Template complet plugin moteur Arcus Performax
- ✅ Template complet plugin oscilloscope Agilent
- ✅ Template complet plugin sonde Narda
- ✅ Structure package `pymodaq_plugins_aefi`
- ✅ Réutilisation des drivers Legacy existants

---

## Décisions Clés

### ✅ Utiliser PyMoDAQ comme Base

**Rationale:**
- Architecture conforme SOLID (score 4.5/5)
- Système de scanner multi-points déjà implémenté
- Orchestration Dashboard + DAQScan robuste
- Sauvegarde HDF5 et visualisation incluses
- Extensibilité via plugins

**Impact:**  
Pas besoin de réimplémenter l'orchestration → focus sur les plugins matériel uniquement.

---

### ✅ Créer Package de Plugins AEFI

**Structure:**
```
pymodaq_plugins_aefi/
├── pyproject.toml
├── src/pymodaq_plugins_aefi/
│   ├── hardware/              # Drivers Legacy réutilisés
│   ├── daq_move_ArcusPerformax.py
│   ├── daq_1Dviewer_AgilentDSOX2014.py
│   ├── daq_0Dviewer_NardaEP601.py
│   └── daq_0Dviewer_LSM9DS1.py
└── tests/
```

**Rationale:**  
Envelopper les drivers Legacy dans des plugins PyMoDAQ permet de:
- Réutiliser le code hardware existant
- Bénéficier de l'orchestration PyMoDAQ
- Respecter le DIP (dépendance vers abstractions)

---

### ✅ Supprimer l'Orchestration Legacy

**À SUPPRIMER:**
- Logique de scan dans `EFImagingBench_App`
- Coordination manuelle actuateurs/détecteurs
- Implémentation custom sauvegarde/visualisation

**REMPLACÉ PAR:**
- Dashboard PyMoDAQ
- DAQScan extension
- Scanner système
- H5Saver

**Rationale:**  
Éviter la duplication de code et les bugs associés.

---

### ✅ Extraire et Isoler la Logique Métier

**Logique E-field (getE3D):**
- À extraire du Legacy
- À isoler dans un module séparé
- Optionnellement: créer extension PyMoDAQ dédiée

**Algorithmes MATLAB:**
- À conserver comme post-traitement
- Pas d'intégration dans l'acquisition temps réel

**Rationale:**  
Séparer acquisition (PyMoDAQ) du traitement (logique métier).

---

## Conformité SOLID - Comparaison

| Principe | Legacy AEFI | PyMoDAQ | Avec Plugins AEFI |
|----------|-------------|---------|-------------------|
| **SRP** | ❌ Faible | ✅ Élevé | ✅ Élevé |
| **OCP** | ❌ Faible | ✅ Élevé | ✅ Élevé |
| **LSP** | ❌ Aucune abstraction | ✅ Élevé | ✅ Élevé |
| **ISP** | ⚠️ Moyen | ✅ Élevé | ✅ Élevé |
| **DIP** | ❌ **Violation majeure** | ✅ Élevé | ✅ Élevé |

**Conclusion:** Migration vers PyMoDAQ résout les violations SOLID du Legacy.

---

## Effort de Migration Estimé

| Phase | Durée | Priorité |
|-------|-------|----------|
| Setup package | 2h | ⭐⭐⭐ |
| Plugin Arcus Performax | 1 jour | ⭐⭐⭐ |
| Plugin Agilent Scope | 1 jour | ⭐⭐⭐ |
| Plugin Narda Probe | 0.5 jour | ⭐⭐⭐ |
| Tests unitaires | 1 jour | ⭐⭐ |
| Intégration Dashboard | 0.5 jour | ⭐⭐⭐ |
| Extension E-field (optionnel) | 2-3 jours | ⭐ |
| Documentation | 1 jour | ⭐⭐ |
| **TOTAL** | **5-8 jours** | |

---

## Prochaines Actions

### 1️⃣ Actions Immédiates

- [ ] Créer repository `pymodaq_plugins_aefi`
- [ ] Setup `pyproject.toml` avec entry points
- [ ] Copier drivers Legacy dans `hardware/`
- [ ] Commencer par plugin le plus simple (Narda)

### 2️⃣ Phase Développement

- [ ] Implémenter `daq_0Dviewer_NardaEP601`
- [ ] Tester standalone
- [ ] Implémenter `daq_move_ArcusPerformax`
- [ ] Tester standalone
- [ ] Implémenter `daq_1Dviewer_AgilentDSOX2014`
- [ ] Tester standalone

### 3️⃣ Phase Intégration

- [ ] Installer package local: `pip install -e .`
- [ ] Lancer Dashboard PyMoDAQ
- [ ] Vérifier plugins détectés
- [ ] Créer preset "AEFI Rotational Scan"
- [ ] Exécuter premier scan test

### 4️⃣ Phase Validation

- [ ] Tests unitaires complets
- [ ] Tests d'intégration avec matériel réel
- [ ] Validation données vs Legacy
- [ ] Documentation utilisateur

---

## Ressources

### Documentation PyMoDAQ
- Site officiel: http://pymodaq.cnrs.fr/
- GitHub: https://github.com/PyMoDAQ/PyMoDAQ
- Tutoriels: http://pymodaq.cnrs.fr/en/latest/tutorials.html

### Plugins Exemples
- PyMoDAQ Mock Plugins: https://github.com/PyMoDAQ/pymodaq_plugins_mock
- Plugin Template: Inclus dans PyMoDAQ

### Support
- Forum: https://github.com/PyMoDAQ/PyMoDAQ/discussions
- Issues: https://github.com/PyMoDAQ/PyMoDAQ/issues

---

## Conclusion

**Analyse Complète:** ✅  
**Architecture PyMoDAQ:** Conforme SOLID (4.5/5)  
**Stratégie Migration:** Définie et documentée  
**Exemples Code:** Templates complets fournis  

**Recommandation:** Procéder à la migration vers PyMoDAQ. L'investissement initial (5-8 jours) sera rapidement rentabilisé par:
- ✅ Code maintenable et testable
- ✅ Architecture extensible
- ✅ Respect des principes SOLID, DDD, ADD
- ✅ Réutilisabilité accrue

**Prêt pour implémentation:** Les documents d'analyse fournissent tous les éléments nécessaires pour démarrer le développement.

---

**Date de complétion:** 2025-11-16  
**Status:** ✅ Analyse terminée


