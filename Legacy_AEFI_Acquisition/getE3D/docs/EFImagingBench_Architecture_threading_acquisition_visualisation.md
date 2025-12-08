# Architecture Threading & Rafraîchissement – Interface AD9106/ADS131A04

## Résumé
L'architecture logicielle sépare explicitement les tâches critiques (acquisition, export, visualisation) en différents threads/processus pour garantir la réactivité et la robustesse de l'interface.

---

## 1. Acquisition – Thread dédié
- **AcquisitionManager** lance un thread (`_acquisition_thread`) pour l'acquisition continue.
- Ce thread gère :
  - La boucle d'acquisition (lecture hardware ou simulation)
  - La pause/reprise automatique
  - L'application de la configuration
  - L'émission du signal `data_ready` à chaque nouvel échantillon
- **Aucun blocage de l'UI** : l'acquisition tourne indépendamment du thread principal Qt.

---

## 2. Export CSV – Thread séparé
- L'export des données (streaming CSV) est géré par un thread dédié (voir `csv_exporter.py`).
- Ce thread lit le buffer d'acquisition et écrit sur disque sans bloquer ni l'acquisition ni l'UI.
- Permet un flush périodique, une gestion des erreurs disque, et une robustesse accrue.

---

## 3. Visualisation UI – Thread principal + QTimer
- L'interface graphique (PyQt) tourne dans le **thread principal Qt**.
- Un **QTimer** déclenche le rafraîchissement de l'affichage à intervalle régulier (ex : 100 ms).
- Le QTimer lit le buffer d'acquisition et met à jour les widgets (affichage 8 canaux, stats, etc.).
- **Aucune opération longue ou bloquante** n'est effectuée dans le thread UI.

---

## 4. Communication entre threads
- Les signaux PyQt (`data_ready`, `status_changed`, etc.) assurent la communication thread-safe entre acquisition, export et UI.
- Le buffer d'acquisition (thread-safe) permet de partager les données sans risque de corruption.

---

## 5. Robustesse et évolutivité
- Ce découpage garantit :
  - La réactivité de l'interface, même en cas de forte charge d'acquisition/export
  - La possibilité d'ajouter d'autres tâches asynchrones (log, analyse temps réel, etc.)
  - Une gestion propre des erreurs et des transitions de mode

---

**Règle d'or : aucune opération longue ou bloquante dans le thread principal Qt.** 