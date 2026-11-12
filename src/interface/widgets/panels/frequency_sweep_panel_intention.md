# frequency_sweep_panel — Intention

## Rationale

Un balayage au banc dure plusieurs minutes et pilote le matériel : l'opérateur doit voir la réponse se construire fréquence par fréquence, et pouvoir l'arrêter s'il voit que les réglages sont faux. Les champs qui conditionnent la reproductibilité (rôle, hauteur de table, grille, N, opérateur) doivent être saisis au même endroit que le lancement.

## Responsibility

- Saisir le rôle (référence instrument, fond, mesure objet), l'objet mesuré et son lift-off (mesure objet seulement, champs grisés sinon), la hauteur de la table (obligatoire, en mm, lue sur le panneau de la table), les bornes et le nombre de fréquences, N par fréquence, l'opérateur.
- Lancer et arrêter le balayage ; verrouiller les champs pendant qu'il tourne.
- Tracer en direct l'amplitude et la phase par axe en fonction de la fréquence (échelle logarithmique).
- Afficher l'étape en cours, la fin (statut, dossier d'export) ou l'erreur.

## Design

- Affichage seul : amplitude et phase arrivent calculées (`FrequencyPointViewModel`) ; aucun import `domain/`.
- Hauteur vide = non saisie : transmise telle quelle, c'est le service qui refuse et dit pourquoi.
- Sélecteurs d'opérateur et d'objet mesuré, saisie du lift-off : mêmes widgets et mêmes registres que les panneaux Scan et Continuous Reading.
- Tracé matplotlib différé au premier affichage (même raison que le widget de caractérisation du débit).
