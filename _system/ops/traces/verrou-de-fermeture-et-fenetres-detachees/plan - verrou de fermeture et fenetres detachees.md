# Plan — Verrou de fermeture pendant une acquisition, et panneaux détachés visibles dans Alt+Tab

**État :** plan rédigé le 2026-11-14 sur le PC du labo, pendant une acquisition réelle. Rien n'est codé, rien n'a été lancé.
**Prochaine action :** une fois l'acquisition en cours terminée, créer `feature/verrou-fermeture-acquisition` depuis `develop` et coder l'étape 1 (le refus de fermeture avec message), testable en mode mock.

## Pourquoi

Une acquisition réelle dure des heures. Si l'application se ferme pendant qu'elle écrit son fichier d'export, la mesure est perdue ou tronquée. Deux causes possibles : un opérateur qui ferme la fenêtre, ou Windows qui redémarre pour une mise à jour.

L'humain, le 2026-11-14 :

> mettre un verrouillage sur l'application pour ne pas qu'elle soit fermée quand elle est en cours d'acquisition (si possible même par windows s'il veut faire une mise à jour, on lui refuse et il doit attendre la fin). Si un utilisateur veut fermer l'application il doit recevoir un message pop up lui expliquant qu'une acquisition est en cours et qu'il doit d'abord stopper toute acquisition avant de fermer l'application. Par acquisition j'entends une acquisition avec export en cours, pas seulement une lecture de données dans l'interface.

Et, sur les écrans multiples :

> quand je sépare les panneaux de l'interface pour les mettre sur 2 écrans, j'aimerais que windows m'affiche ces 2 écrans dans le ctrl + tab

## Partie 1 — Verrou de fermeture

### Ce qui déclenche le verrou

Le verrou est actif quand **un fichier d'export est ouvert**, et seulement alors. Une lecture continue affichée sans export armé ne verrouille rien.

Les services savent déjà qu'un export est ouvert, il n'y a pas d'état à inventer :

- le service d'export des scans (`scan_export_service.py`) garde la liste de ses fichiers ouverts, remplie au démarrage d'un scan avec export ou d'une lecture continue avec export temporel armé, et vidée à la fermeture de l'export ;
- le service du balayage en fréquence (`frequency_sweep_service.py`) garde l'emplacement de son export ouvert ;
- les caractérisations du banc d'essai (débit d'acquisition, cadence de sortie du convertisseur) exportent aussi : à inclure si elles écrivent pendant une durée longue, à vérifier au codage.

Chacun de ces services expose une question « un export est-il ouvert ? ». Une petite requête applicative les réunit et répond « acquisition avec export en cours : oui ou non, et laquelle » (scan, lecture continue, balayage). L'interface ne lit que cette réponse, par un modèle de vue, jamais les types du domaine.

```mermaid
flowchart LR
    subgraph Interface
        F["Fenêtre principale<br/>(demande de fermeture)"]
        S["Réception de la demande<br/>d'arrêt de Windows"]
        M["Modèle de vue<br/>« acquisition en cours ? »"]
    end
    subgraph Application
        Q["Requête<br/>« acquisition avec export en cours ? »"]
        E1["Export des scans<br/>et de la lecture continue"]
        E2["Balayage en fréquence"]
        E3["Caractérisations du banc<br/>(à vérifier)"]
        P(["Port « garde de session Windows »"])
    end
    subgraph Infrastructure
        W["Adaptateur Windows<br/>raison de blocage, anti-veille,<br/>style des fenêtres détachées"]
        FW["Faux adaptateur<br/>(mock et tests)"]
    end
    F --> M
    S --> M
    M --> Q
    Q --> E1
    Q --> E2
    Q -.-> E3
    Q --> P
    P --> W
    P -.-> FW
```

Le verrou suit la vie de l'export, pas celle de l'affichage :

```mermaid
stateDiagram-v2
    direction LR
    state "Libre" as Libre
    state "Lecture affichée, sans export" as Lecture
    state "Verrouillé : export ouvert" as Verrou
    [*] --> Libre
    Libre --> Lecture : démarrage d'une lecture
    Lecture --> Libre : arrêt de la lecture
    Libre --> Verrou : ouverture d'un fichier d'export
    Lecture --> Verrou : export armé puis démarré
    Verrou --> Libre : fermeture du fichier d'export (fin, arrêt ou erreur)
    note right of Verrou
        fermeture refusée avec message
        arrêt de Windows refusé avec raison
        veille empêchée
    end note
    note right of Lecture
        fermeture acceptée
    end note
```

### Étape 1 — Refuser la fermeture par l'opérateur, avec un message

La fenêtre principale (`dashboard.py`, méthode de fermeture qui sauvegarde aujourd'hui la disposition puis accepte) demande la réponse avant d'accepter :

- export ouvert : la fermeture est refusée, et une fenêtre de message s'affiche :
  « Une acquisition avec export est en cours (scan 2D, objet X). Arrêtez d'abord toute acquisition avant de fermer l'application. »
- aucun export : comportement actuel (sauvegarde de la disposition, fermeture).

```mermaid
flowchart TD
    A(["L'opérateur ferme l'application<br/>croix, Alt+F4, barre des tâches"]) --> B{"Un fichier d'export<br/>est-il ouvert ?"}
    B -- "oui" --> C["Fermeture refusée"]
    C --> D["Message : une acquisition avec export<br/>est en cours, l'arrêter d'abord"]
    D --> L1["Log : fermeture refusée,<br/>acquisition et identifiant"]
    L1 --> R(["L'application reste ouverte,<br/>l'acquisition continue"])
    B -- "non" --> G["Sauvegarde de la disposition<br/>des panneaux"]
    G --> L2["Log : fermeture acceptée"]
    L2 --> H(["L'application se ferme"])
```

Couvre la croix de la fenêtre, Alt+F4 et la fermeture depuis la barre des tâches. Vérifier au codage qu'aucun autre chemin ne quitte l'application sans passer par là (menu, raccourci, `app.quit()` direct).

Le refus est logué avec l'acquisition en cours et son identifiant ; une fermeture acceptée aussi.

Test : en mode mock, démarrer un scan avec export, cliquer la croix, vérifier le message et que l'application reste ouverte ; arrêter le scan, fermer, vérifier que l'application se ferme. Un test automatique du même parcours, avec un faux port d'export.

### Étape 2 — Refuser l'arrêt et la déconnexion de Windows

Quand Windows s'arrête, redémarre ou déconnecte la session, il demande d'abord aux applications si elles acceptent. Qt transmet cette demande à l'application ; elle peut l'annuler.

- export ouvert : l'application annule la demande, et déclare à Windows une raison de blocage (« Acquisition AEFI en cours — attendre la fin de l'export »). Windows affiche alors son écran « Cette application empêche l'arrêt » avec ce texte, et l'opérateur choisit « Annuler ».
- la raison de blocage est déclarée au début de l'export et retirée à sa fin, pour que l'écran de Windows dise toujours la vérité.

```mermaid
sequenceDiagram
    autonumber
    participant Op as Opérateur
    participant App as Application AEFI
    participant Win as Windows
    Op->>App: démarre un scan avec export
    App->>Win: déclare la raison de blocage<br/>« Acquisition AEFI en cours »
    App->>Win: demande d'empêcher la veille
    Note over Win: plus tard : mise à jour,<br/>redémarrage ou déconnexion
    Win->>App: l'application accepte-t-elle l'arrêt ?
    App-->>Win: non (export ouvert)
    Win->>Op: écran « Cette application empêche l'arrêt »<br/>avec la raison
    Op->>Win: Annuler
    Note over App: le scan continue
    App->>App: fin du scan, fermeture du fichier d'export
    App->>Win: retire la raison de blocage
    App->>Win: retire la demande anti-veille
    Win->>App: l'application accepte-t-elle l'arrêt ?
    App-->>Win: oui
```

Les appels à Windows vivent dans un adaptateur d'infrastructure derrière un port, avec un faux pour le mode mock et les tests.

Dans la même étape, empêcher la mise en veille de l'ordinateur pendant l'export (même mécanisme de Windows, demande retirée à la fin de l'export) : une veille interromprait l'acquisition aussi sûrement qu'un redémarrage.

Test au banc, une fois une acquisition réelle terminée : lancer un scan court avec export, demander un redémarrage par le menu Démarrer, vérifier que l'écran de Windows montre la raison, cliquer « Annuler », vérifier que le scan continue.

### Limite : ce qu'une application ne peut pas refuser

Une application peut refuser un arrêt normal, mais pas tout :

- sur l'écran de blocage, un clic sur « Forcer l'arrêt » ferme l'application ;
- un redémarrage de mise à jour forcé, une fois passée l'échéance que Windows s'est fixée, peut ignorer le refus.

```mermaid
flowchart LR
    subgraph app["Couvert par l'application"]
        a1["Croix, Alt+F4,<br/>barre des tâches"]
        a2["Arrêt ou redémarrage<br/>par le menu Démarrer"]
        a3["Déconnexion de la session"]
        a4["Mise en veille"]
        a5["Redémarrage de mise à jour<br/>avant son échéance"]
    end
    subgraph machine["Demande un réglage du PC (administrateur)"]
        m1["Redémarrage de mise à jour<br/>forcé après l'échéance"]
    end
    subgraph rien["Non couvert"]
        r1["Clic sur « Forcer l'arrêt »"]
        r2["Fermeture de la console<br/>de launch.bat"]
        r3["Coupure de courant"]
    end
```

Pour fermer cette porte, le réglage se fait sur la machine, pas dans l'application : par exemple la stratégie « Pas de redémarrage automatique avec des utilisateurs connectés », ou des heures d'activité couvrant les acquisitions. Ce réglage demande les droits administrateur du PC du labo : **à trancher avec l'humain** avant l'étape 2 (le faire, par qui, lequel).

L'application ne mettra pas les mises à jour en pause d'elle-même : ce serait un comportement caché.

### Point annexe — le lancement

`launch.vbs` (le raccourci) lance l'application sans fenêtre console. `launch.bat` ouvert directement garde une console : la fermer tue l'application sans aucune demande, donc sans verrou. Rappeler dans le mode d'emploi de lancer par le raccourci.

## Partie 2 — Panneaux détachés dans Alt+Tab

Sous Windows, le sélecteur de fenêtres est **Alt+Tab** (Ctrl+Tab change d'onglet à l'intérieur d'une application ; Windows+Tab ouvre la vue des tâches). La demande porte sur Alt+Tab.

C'est possible. Aujourd'hui un panneau détaché est une fenêtre « rattachée » à la fenêtre principale par la bibliothèque d'ancrage (PySide6-QtAds) ; Windows masque les fenêtres rattachées de la barre des tâches et d'Alt+Tab. Pour qu'il les montre, chaque fenêtre détachée reçoit le style Windows « fenêtre d'application ».

```mermaid
flowchart LR
    subgraph avant["Aujourd'hui"]
        direction TB
        P1["Écran 1 : fenêtre principale"]
        D1["Écran 2 : panneau détaché<br/>(fenêtre rattachée)"]
        T1["Alt+Tab montre :<br/>AEFI Acquisition"]
        P1 --- T1
        D1 -. "absent" .- T1
    end
    subgraph apres["Après"]
        direction TB
        P2["Écran 1 : fenêtre principale"]
        D2["Écran 2 : panneau détaché<br/>(fenêtre d'application)"]
        T2["Alt+Tab montre :<br/>AEFI Acquisition<br/>+ Visualisation du scan<br/>+ autres panneaux détachés"]
        P2 --- T2
        D2 --- T2
    end
    avant ==> apres
```

```mermaid
flowchart TD
    A(["Un panneau est détaché,<br/>ou la disposition est restaurée au démarrage"]) --> B["La bibliothèque d'ancrage<br/>signale la nouvelle fenêtre"]
    B --> C["Titre de la fenêtre =<br/>nom du panneau"]
    C --> D["Pose du style Windows<br/>« fenêtre d'application »"]
    D --> E{"Fenêtre déjà affichée ?"}
    E -- "oui" --> F["Masquer puis réafficher<br/>pour appliquer le style"]
    E -- "non" --> G(["Visible dans la barre des tâches<br/>et dans Alt+Tab"])
    F --> G
```

- La bibliothèque signale la création de chaque fenêtre détachée (signal `floatingWidgetCreated` du gestionnaire d'ancrage, présent dans la version installée). À ce signal, on pose le style sur la fenêtre.
- Le titre de la fenêtre dans Alt+Tab est celui du panneau (option de la bibliothèque qui reprend le titre du panneau détaché).
- Vérifier au codage que les fenêtres détachées recréées au démarrage par la restauration de la disposition émettent aussi le signal, sinon poser le style après la restauration.
- Le style Windows ne prend effet que s'il est posé avant l'affichage de la fenêtre, ou suivi d'un masquage puis réaffichage : à vérifier sur le PC.

Même adaptateur d'infrastructure Windows que la partie 1 (sans effet hors Windows).

Test au banc : détacher deux panneaux sur le second écran, Alt+Tab, vérifier que chacun apparaît avec son nom et que le choisir l'amène au premier plan ; fermer et rouvrir l'application, vérifier que les panneaux restaurés apparaissent aussi.

## Ordre et façon de travailler

```mermaid
flowchart LR
    Z(["Fin de l'acquisition<br/>en cours"]) --> B0["Branche<br/>feature/verrou-fermeture-acquisition<br/>depuis develop"]
    B0 --> S1["Étape 1<br/>refus de fermeture + message<br/>(mock)"]
    S1 --> V1{"Vérification<br/>par l'humain"}
    V1 --> S2["Étape 2<br/>panneaux détachés<br/>dans Alt+Tab"]
    S2 --> V2{"Vérification<br/>au labo"}
    V2 --> K{"Décision : réglage<br/>du PC du labo"}
    K --> S3["Étape 3<br/>refus de l'arrêt Windows<br/>+ anti-veille"]
    S3 --> V3{"Test au banc :<br/>redémarrage annulé,<br/>scan continue"}
    V3 --> MG(["Fusion dans develop"])
```

Une étape = un commit = une vérification par l'humain :

1. refus de fermeture par l'opérateur, avec message (mock d'abord) ;
2. panneaux détachés dans Alt+Tab (petit, indépendant, vérifiable vite au labo) ;
3. refus de l'arrêt Windows et de la veille, après décision sur le réglage de la machine.

Rien ne se code ni ne se teste dans `C:\Users\manip\AEFI_Acquisition` (le dossier des acquisitions réelles), et rien ne se lance pendant une acquisition.
