Ce que je souhaite pour ma logique controlleur - manager centralisé - interface:

- Une interface graphique a déjà été crée mais sa logique est de communiquer directement avec le controller et ne respecte pas celle avec le manager
C:\Users\manip\Dropbox\Luis\1 PROJETS\1 - THESE\Ressources\ExperimentalData_ASSOCE\Dev\ArcusPerformaxPythonController\gui\EFImagingBench_Interface_ArcusPerformax4EXStage_PRD.md
- Certaines choses de cette interface ne sont pas bien conçues ou alors inutile mais pose déjà une bonne base
- Liste de choses inutiles 
    - Bouton Connecter
    - Actualiser


- Affichage d'un rectangle/carré qui correspond au carré que je peux parcourir avec ma colonne en actionnant mes moteurs
- Affichage de la position actuelle au sein de ce carré --> Si le homing n'a pas été fait alors on affiche dans le carré un message "Homing Necessary"
- Une possibilité d'ajouter des positions mémoires (par exemple je mets la colonne à un endroit et cela garde en mémoire la position, cela sera pratique pour la suite pour la reconnaissance d'objets enfouis) --> Un point ou une croix s'affiche alors
- Possibilité de revenir en arrière d'un point et d'effacer touts les points enregistré
- Une possibilité d'exporter l'image du carré avec les points actuellement en mémoire


- On doit pouvoir afficher vitesse et position en temps réel

## Partie SCAN X-Y

On doit pouvoir configurer un scan avec les paramètres suivants :

x_min, x_max, y_min, y_max, x_nb et y_nb définissant une grille complète.

2 modes de scan, un mode en S et un mode en E

mode S : on fait l'acquisition des données lors de l'aller, et du retour
mode E : on ne fait l'acquisition que dans un seul sens

