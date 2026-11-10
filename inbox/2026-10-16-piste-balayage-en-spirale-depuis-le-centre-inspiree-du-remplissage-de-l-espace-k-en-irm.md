# Piste : balayage en spirale depuis le centre, inspiré du remplissage de l'espace k en IRM

**Idée :** que aefi_acquisition balaie le plan en spirale en partant du centre, au lieu de lignes cartésiennes.

## Pourquoi cette note est ici

Elle vient de `GRAPHE-THESE/0_inbox/a-relire-et-renforcer-avant-integration/Notes volantes/` (2026-10-16).
Elle en a été sortie pour qu'aucune extraction ne la mine comme une source de connaissance.
C'est une piste de fonctionnalité pour le logiciel, pas un résultat.

Elle n'est pas non plus une piste PILOTAGE (`task.lead`).
Le graphe n'a pas de nœud pour aefi_acquisition à qui la rattacher, et rien ne justifie encore le travail.

## Ce qui manque avant d'implémenter

Un moyen de valoriser la technique : un résultat concret qui montrerait un gain mesurable une fois le balayage en spirale implémenté et utilisé.
Exemples à trancher :
- temps de scan
- sensibilité à la dérive pendant l'acquisition
- qualité de l'image au centre, où se trouve l'objet
- autre critère à définir

Tant que ce critère reste flou, la note reste une piste.
Quand il s'écrit, elle devient une tâche PILOTAGE ou une question ouverte du graphe.

---

# Note d'origine

MOC : [[MOC IMAGERIE]] [[MOC Banc de test]]
Projets : [[PROJET ASSOCE]]
Tags : #NoteVolante #ToProcess #i0 #p0
URL : https://mriquestions.com/k-space-trajectories.html
Date : 2024-01-11
***

Le problème du remplissage de l'espace-k (espace réciproque) se rencontre dans le contexte de l'imagerie médicale par champ magnétique. Avant acquisition, le k-space est un tableau de cellules vides qui attend l'arrivée des données. Il existe alors plusieurs façon de le remplir.

![[4421712_orig.gif]]

## La méthode traditionnel de remplissage du k-space en imagerie IRM

Les modèles cartésiens de traversée de l'espace _k_ sont les plus faciles à mettre en œuvre et constituent depuis longtemps la méthode standard pour la plupart des séquences d'imagerie IRM, EPI ou autre.

## Une évolution des séquences d'imagerie IRM vers des lectures radiales et spirales

Aujourd'hui, les lectures radiales et spirales deviennent la norme car elles offrent une sensibilité intrinsèque plus faible au mouvement et permettent des valeurs _TE_ plus courtes . Les spirales peuvent être « en spirale vers l'intérieur », « en spirale vers l'extérieur » ou combinées. Puisqu'il n'y a pas de directions de codage de fréquence et de phase distinctes dans les techniques radiales et spirales, les artefacts sont différents (ils incluent des bandes curvilignes et un flou en forme d'anneau). Les balayages en spirale sont également plus affectés par un timing de gradient incorrect et par des gradients de champ concomitants. La reconstruction d'image est également plus compliquée et peut nécessiter un « maillage » ou d'autres méthodes pour déformer les points de l'espace _k_ mesurés en une matrice rectangulaire pour un traitement numérique rapide par transformée de Fourier.
# Références

[[fourier.kspace.mezrich.1995.pdf]]