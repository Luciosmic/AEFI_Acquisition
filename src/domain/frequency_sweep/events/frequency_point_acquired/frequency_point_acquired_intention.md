---
type: evenement-de-domaine::solidai-ddd
tldr: "Porter, pour une fréquence d'un balayage : l'id du balayage, son rôle, le rang et la valeur de la fréquence, la mesure moyennée (moyenne et écart-type de I et Q par…"
code: ["[[src/domain/frequency_sweep/events/frequency_point_acquired/frequency_point_acquired.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/frequency_sweep/frequency_sweep_intention]]"
---
# frequency_point_acquired — Intention

## Rationale

Chaque fréquence acquise est un fait : la réponse I/Q moyenne par axe à cette fréquence, dans les conditions du balayage. Persisté dans le journal des événements, il permet de reconstruire un balayage interrompu sans le fichier d'export.

## Responsibility

- Porter, pour une fréquence d'un balayage : l'id du balayage, son rôle, le rang et la valeur de la fréquence, la mesure moyennée (moyenne et écart-type de I et Q par axe), le nombre d'échantillons, la hauteur de la table, et l'objet mesuré (identifiant du registre) pour une mesure objet.

## Design

- Instantané autonome : le rôle et la hauteur de table sont recopiés, pour que l'événement se relise sans l'agrégat.
- Unités inline en URI QUDT : Hz, V, mm.
- Émis par `FrequencySweep.record_frequency_point`, après validation.
