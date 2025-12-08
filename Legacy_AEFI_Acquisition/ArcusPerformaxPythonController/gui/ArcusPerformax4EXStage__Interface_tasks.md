# TODO – Refonte avec Manager centralisateur (ArcusPerformax XY)

## Log des modules créés et intégrations récentes (2024-06)
- [x] Création du module de conversion géométrique : `EFImagingBench_GeometricalParametersConversion_Module.py` (conversion inc/µm/cm, gestion des bornes physiques, clamp)
- [x] Création du widget de visualisation géométrique : `EFImagingBench_GeometricalView_Widget.py` (affichage zone utile, sous-rectangle, position courante, respect du ratio, origine en bas à gauche, gestion des int pour Qt)
- [x] Intégration du widget de visualisation dans l'UI (onglet Visualisation, mise à jour dynamique via signaux, test du sous-rectangle)
- [x] Création du module de configuration de scan 2D : `EFImagingBench_Scan2D_Module.py` (classe `Scan2DConfigurator`, génération de la séquence de points, modes E/S)
- [x] Ajout de la génération de scan 2D dans le manager (`generate_scan2d`)
- [x] Ajout d'une fonction d'exécution de scan 2D (`execute_scan2d`) pour piloter le banc selon la séquence générée
- [x] Adaptation de l'UI pour afficher la position réelle après homing, afficher le sous-rectangle, et respecter le ratio physique du banc
- [x] Correction du paintEvent pour l'affichage (conversion en int, centrage, respect du ratio, inversion axe Y)
- [x] Discussion sur l'architecture future : la logique de scan 2D reste côté manager pour l'instant, mais une orchestration multi-équipements (meta-manager) est prévue pour la synchronisation acquisition/excitation
- [x] Création et adaptation du script de benchmark pour la caractérisation des butées (`benchmark/caracterisation_butee_banc_test.py`) :
  - Homing automatique, déplacement à la butée max, enregistrement de la position, export CSV (incréments et µm)
  - Ajout du timestamp, du formatage du CSV, et de la conversion inc → µm
  - Correction de la logique pour éviter les doublons de wait_move et garantir la robustesse du protocole
- [x] Intégration de l'acquisition continue de la position (X, Y) avec timestamp pendant le scan à la volée :
  - Utilisation d'un buffer (CircularBuffer/ProductionBuffer/AdaptiveDataBuffer) pour stocker les positions synchronisées
  - Acquisition via QTimer pendant le mouvement Y, interruption lors des changements de consigne
  - Export des données pour synchronisation avec les mesures capteur
- [x] Gestion du scan à la volée (mode E/S) :
  - Génération de la séquence adaptée (mode E : balayage unidirectionnel, mode S : aller-retour)
  - Exécution ligne par ligne : consigne X, lancement du mouvement Y, acquisition continue, passage à la ligne suivante
  - Synchronisation entre l'acquisition de position et les commandes moteurs

## 1. Conception du Manager [Difficulté : 7/10]
- [x] Créer le fichier du manager
- [x] Définir la classe de base
- [x] Ajouter les signaux nécessaires
- [x] Gérer les états internes
- [x] Ajouter méthodes d'ouverture/fermeture

## 2. Refactorisation de l'UI [Difficulté : 8/10]
- [x] Adapter l'UI pour utiliser le manager
- [x] Tester l'UI (fonctionnalités de base, signaux)

## 3. Gestion des commandes et états [Difficulté : 7/10]
- [x] Valider chaque commande avant exécution
- [x] Verrouiller/déverrouiller les commandes selon l'état
- [x] Retourner le résultat de chaque commande

## 4. Gestion des erreurs et notifications [Difficulté : 6/10]
- [x] Centraliser la gestion des erreurs
- [x] Définir et utiliser un signal d'erreur
- [x] Logger les actions et erreurs
- [ ] Permettre l'export du log

## 5. Synchronisation et extensibilité [Difficulté : 6/10]
- [ ] Préparer le manager pour la synchronisation avec l'acquisition (prévu, non fait)
- [ ] Ajouter des hooks pour d'autres modules (prévu, non fait)

## 6. Tests et validation [Difficulté : 5/10]
- [ ] Écrire des tests pour chaque fonctionnalité principale (en cours)
- [ ] Vérifier la propagation des signaux (en cours)
- [ ] Noter les bugs rencontrés

## 7. Documentation utilisateur [Difficulté : 4/10]
- [ ] Ajouter une note utilisateur pour chaque fonctionnalité
- [ ] Donner des exemples d'utilisation

---

## 1bis. Transition UI existante vers Manager centralisateur [Difficulté : 6/10]
- [x] Préparer le manager pour le "pass-through"
- [x] Adapter l'UI pour utiliser le manager
- [x] Tester le fonctionnement
- [ ] Documentation et nettoyage (à compléter)

## 5bis. Harmonisation des Managers (Acquisition/Stage) *7/10*
    - [ ] Refondre StageManager pour adopter l'approche worker unique + file d'attente (alignement AcquisitionManager) *8/10*
        - [x] Le worker traite les commandes une par une et met à jour le buffer de position *2/10*
            - Le worker lit la position après chaque commande et met à jour le buffer, garantissant la cohérence des données.
        - [x] Émettre les signaux Qt (position, état, erreur) depuis le worker *1/10*
            - Les signaux positionChanged, stateChanged, errorOccurred sont émis directement depuis le worker après chaque action.
        - [x] Créer un thread worker dédié à la communication série *2/10*
            - Un thread worker est lancé à l'init, dédié à la gestion séquentielle des commandes série.
        - [x] Implémenter une file d'attente (queue) pour toutes les commandes (move_to, home, stop, get_position, etc.) *2/10*
            - Toutes les commandes sont placées dans une queue, traitées séquentiellement par le worker.
        - [x] Documenter l'alignement avec AcquisitionManager et les avantages de cette architecture *1/10*
            - Un commentaire en tête de classe explique l'alignement avec AcquisitionManager et la robustesse apportée par ce modèle.
    - [x] L'acquisition (lecture de position, etc.) doit tourner en continu dans un thread/timer dédié *2/10*
        - Le worker unique gère en continu la lecture de position et la mise à jour du buffer.
    - [x] L'acquisition ne doit jamais être bloquée par les mouvements *2/10*
        - Toutes les commandes sont séquencées dans la queue, aucun blocage n'est possible.
    - [x] Tester la robustesse de l'acquisition en cas de commandes fréquentes *2/10*
        - La queue absorbe les rafales de commandes, l'acquisition reste fluide tant que le hardware suit.
    - [x] UI indépendante : l'UI ne dépend que du buffer du manager *6/10*
        - [x] L'UI lit uniquement les données du buffer interne du manager *2/10*
            - L'UI ne fait jamais d'accès direct au hardware, elle lit uniquement le buffer mis à jour par le worker.
        - [x] L'UI ne doit jamais être bloquée, même lors de mouvements longs ou d'erreurs de communication *2/10*
            - L'UI reste réactive car tout est asynchrone et bufferisé.
        - [x] Vérifier la réactivité de l'UI dans tous les cas *2/10*
            - La structure garantit la réactivité de l'UI, sauf bug externe.
    - [x] Créer le dictionnaire self._current_config *2/10*
        - Un dictionnaire centralisé _current_config a été ajouté dans StageManager pour stocker la configuration courante.
    - [x] Implémenter update_configuration et l'émission du signal *2/10*
        - La méthode update_configuration met à jour la config et émet le signal configurationChanged si modifiée.
    - [ ] Prévoir des hooks pour la synchronisation future avec d’autres managers *4/10*
        - [ ] Définir des callbacks ou signaux extensibles *2/10*
            - [ ] Ajouter des signaux/callbacks dans StageManager *1/10*
            - [ ] Prévoir la connexion externe *1/10*
        - [ ] Documenter les points d'extension *1/10*
        - [ ] Exemple d'utilisation d'un hook *1/10*
    - [ ] Valider la compatibilité UI et modules existants *6/10*
        - [ ] Tester l'intégration avec l'UI principale *2/10*
            - [ ] Vérifier le fonctionnement des boutons et feedbacks *1/10*
            - [ ] Vérifier la remontée des erreurs et statuts *1/10*
        - [ ] Adapter les modules si besoin *2/10*
            - [ ] Identifier les modules impactés *1/10*
            - [ ] Adapter les appels au StageManager *1/10*
        - [ ] Rédiger un retour d'expérience et points de vigilance *2/10*
            - [ ] Noter les difficultés rencontrées *1/10*
            - [ ] Lister les points à surveiller pour la maintenance *1/10*
        - [x] Refonte du scan 2D : séquence entièrement gérée dans le worker *3/10*
            - La logique du scan 2D est désormais entièrement gérée dans le worker, chaque commande n'est envoyée que lorsque la position cible est atteinte (tolérance 2 incréments) et que l'axe est arrêté (is_moving False), sans jamais bloquer l'UI.

