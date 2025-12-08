MOC : 
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation : 
Tags : #NoteAtomique 
Date : 2025-07-04
***

# Problème/Contexte

Pour garantir la robustesse, la cohérence scientifique et la maintenabilité du banc d'acquisition AD9106/ADS131A04, il est essentiel de centraliser toute la logique d'acquisition dans un composant unique (AcquisitionManager) et d'interdire tout accès direct au hardware ailleurs dans le code.

# Pistes/Réponse

**Pattern d'architecture recommandé** :
- **AcquisitionManager** est le seul module à dialoguer avec le hardware (via SerialCommunicator) et à gérer le threading, la gestion d'erreur, la synchronisation des gains, etc.
- **Le buffer d'acquisition** (thread-safe) est l'unique point d'accès aux données pour le reste du système (UI, export, analyse, etc.).
- **Aucun module (UI, export, etc.) ne doit accéder directement à SerialCommunicator** ni tenter de lire un échantillon en dehors du thread d'acquisition.
- Toute lecture de données se fait via le buffer, ou via les signaux émis par AcquisitionManager.

**Schéma textuel** :
```
[Hardware ADC] ←→ [SerialCommunicator] ←→ [AcquisitionManager (thread)] ←→ [Buffer] ←→ [UI / Export / Analyse]
```

**À compléter** :
- Description détaillée de l'architecture (diagramme, séquence, etc.)
- Cas d'usage avancés (pause, reprise, export, etc.)
- Règles de synchronisation et de traçabilité

# Références
- Voir la todo [[AD9106_ADS131A04_Visualization_GUI_tasks.md]] section "Robustesse accès buffer et découplage hardware"
- Documentation du module AcquisitionManager

# Liens
[[AD9106_ADS131A04_Visualization_GUI_tasks.md]] - Checklist robustesse accès buffer et découplage hardware. 