---
type: constat::sh-agent-os
genere_par: "[[tache - corriger les deux erreurs de conformite venues du labo]]"
doc_type: constat
---
# A20 ne connaît pas le type traducteur-anti-corruption : erreur non corrigible dans le module

Constat : l'intention `acl/acquisition_parameters_translator_intention.md` porte déjà `type: traducteur-anti-corruption::solidai-hexagonal`, valide et résolu (`au_typed` : typé, closure incluant `atome`). `solidai verify` la dit pourtant non typée.

Cause : la vérification `solidai-intention-non-typee` (solidai-atome, `checks/solidai-intention-non-typee.md`) compare les types réclamés à un paramètre `types` qui liste 13 noms, sans `traducteur-anti-corruption` ; elle lit la réclamation, pas la closure (`atome_code.intention_untyped`). `solidai verify` n'accepte pas de surcharge par cible.

Options :
- A. Ajouter `traducteur-anti-corruption` au paramètre `types` de A20 (et de A3, qui a sans doute la même liste) dans solidai-atome : correction au bon endroit, hors du périmètre de cette tâche.
- B. Retyper l'intention en `atome` : le module passe à 0, mais l'intention perd son `part_of` et le type exact.

Rien n'a été modifié pour cette erreur. Recommandation : A.
