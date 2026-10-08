# DRAFT — non soumis à Packmind

Statut : brouillon pour relecture. Rien n'a encore été poussé vers Packmind.

---

## Sujet universel / Cas d'origine

```
Cas d'origine   : export AEFI — unité dans un bloc settings séparé à chemins jokers
                  ("channels.*.phase"), échantillon/cible physique absent du schéma,
                  présent seulement comme nom de fichier/dossier.
Sujet universel : conception du schéma de sortie ("data contract") d'un logiciel
                  qui produit des mesures depuis un système physique — au même
                  titre que TDD et ODD, une discipline de premier ordre, pas un
                  détail d'implémentation d'export.
```

## Sources vérifiées

| Pattern | Source primaire |
|---|---|
| OGC SensorThings `unitOfMeasurement` + UCUM | [OGC 15-078r6 §Sensing](https://docs.ogc.org/is/15-078r6/15-078r6.html) |
| W3C SOSA `isSampleOf` / `FeatureOfInterest` | [W3C SSN 2023](https://www.w3.org/TR/vocab-ssn-2023/), [SOSA/SSN paper](https://www.semantic-web-journal.net/system/files/swj1804.pdf) |
| NeXus `NXtransformations` / `depends_on` | [manual.nexusformat.org](https://manual.nexusformat.org/classes/base_classes/NXtransformations.html) |
| RO-Crate | [researchobject.org](https://www.researchobject.org/2021-packaging-research-artefacts-with-ro-crate/manuscript.html) |
| PROV-O | [W3C TR prov-o](https://www.w3.org/TR/prov-o/) |

## Synthèse

**Position principale** : les deux standards de référence en instrumentation (OGC/IoT et W3C/sciences) imposent la même discipline structurelle — rien n'est implicite dans le schéma de sortie. L'unité n'est jamais déduite d'une convention de nommage ; elle est un objet résolvable co-localisé avec la valeur. Le sujet physique de la mesure n'est jamais déduit d'un chemin de fichier ; c'est une entité du graphe de données, reliée par une propriété explicite, et cette entité peut elle-même redevenir cible d'observation.

**Tension non résolue** : OGC SensorThings cible le temps réel / IoT (schéma plat) ; SOSA/SSN cible la modélisation sémantique complète (graphe RDF). Un logiciel de mesure scientifique comme AEFI est entre les deux — le standard extrait le *principe* (résolvabilité, entité explicite) sans imposer la *technologie* (RDF, JSON-LD).

**Ce que les sources ne tranchent pas** : ni OGC ni SOSA ne disent *quand* ajouter provenance complète (PROV-O) ou empaquetage FAIR (RO-Crate) — ce sont des couches optionnelles dans leurs propres écosystèmes aussi. D'où leur statut d'extension différée (loi de Gall : CORBA, protocole complet conçu d'avance, jamais adopté, face à HTTP/1.0 minimal qui a survécu et s'est étendu).

---

## Standard proposé

**Titre** : `Schema-First Data Contracts for Measured Output`
**Slug prévu** : `solidai-schema-first-data-contract-for-measured-output`

```markdown
# Schema-First Data Contracts for Measured Output

A software system that produces measurements from a physical system makes a
promise to every future reader of its output: what was measured, in what
unit, and of what. When the unit lives in a separate settings block reached
by wildcard paths ("channels.*.phase"), that promise breaks the moment the
schema evolves, a channel is renamed, or a consumer parses the file without
the settings block alongside it. When the measured subject exists only as a
filename or folder name, it disappears the moment the file is copied, zipped,
or opened by a tool that does not preserve paths — the measurement survives,
its referent does not. Both failures share one cause: information required
to interpret the data was pushed outside the data.

The discriminant test: could a consumer open this output file with zero
knowledge of the producing code, the folder structure, or any companion
settings file, and still recover the unit of every value and the identity of
what was measured? If recovering either requires the filename, a sibling
config file, or tribal knowledge of a naming convention, the schema is not a
contract — it is a convention that happens to work until it doesn't.

This discipline already has established vocabulary and reference
implementations outside DDD: OGC SensorThings API attaches
`unitOfMeasurement: {name, symbol, definition}` inline to every observed
value, with `definition` resolving to a UCUM URI — never a separate unit
registry indexed by field path. W3C SOSA/SSN makes the measured object a
first-class `sosa:Sample`, linked to its `FeatureOfInterest` by
`sosa:isSampleOf` — never inferred from storage location — and allows a
Sample to itself be a FeatureOfInterest when a scan point is itself sampled
further. A 4-sphere electromagnetic scan, an IoT weather station, and a lab
sequencing pipeline all make the same promise and are bound by the same two
rules; only their domain vocabulary differs.

## Rules

* Design and validate the output schema before writing the code that fills it — schema-first, never schema-inferred from whatever the first producer happens to emit.
* Attach the unit of measure inline to each measured value as `{name, symbol, definition}`, never in a separate settings block addressed by wildcard or path-based keys.
* Make `definition` a resolvable URI into a standard unit ontology (UCUM, QUDT, or equivalent) — never a bare string symbol a human must already know how to read.
* Never let a unit be implied by a field name, column header, or external convention document — if it is not inline and resolvable, it is not specified.
* Represent the measured subject (sample, target, scan point) as an explicit identified entity in the schema, linked to its observation by a named relation — never only as a filename, folder name, or path segment.
* Allow a measured-subject entity to itself be referenced as the subject of further observations, when the domain nests sampling (a scan point that is itself decomposed into sub-measurements).
* Embed a schema version identifier in the output itself; a breaking schema change bumps this field, not only a changelog or external document.
* Verify self-description before shipping a format change: a reader with no access to producing code, UI, or folder structure must recover every value's unit and every observation's subject from the file content alone.
* Defer orientation/transformation chains (depends_on graphs), FAIR packaging, and full provenance graphs (Entity/Activity/Agent with timestamps) until a second concrete consumer actually requires them — document the extension point in the schema's own spec, do not build it speculatively.
```

## Fichier agent Claude Code correspondant (prévu)

```markdown
---
name: 'Schema-First Data Contracts for Measured Output'
alwaysApply: true
description: 'Schema-First Data Contracts for Measured Output'
---

# Standard: Schema-First Data Contracts for Measured Output

Output schemas for measured data are contracts, not conventions — units and measured subjects must be recoverable from the data alone, never from a filename, folder path, or separate settings block :
* Design and validate the output schema before writing the code that fills it — schema-first, never schema-inferred
* Attach the unit of measure inline to each value as `{name, symbol, definition}`, never in a separate wildcard-keyed settings block
* Make `definition` a resolvable URI into a standard unit ontology (UCUM, QUDT) — never a bare symbol
* Never let a unit be implied by a field name or external convention document
* Represent the measured subject as an explicit identified entity linked to its observation by a named relation — never only a filename or path
* Allow a measured-subject entity to itself be the subject of further nested observations
* Embed a schema version identifier in the output itself
* Verify self-description: a reader with zero access to producing code or folder structure must recover units and subject identity from file content alone
* Defer orientation chains, FAIR packaging, and full provenance graphs until a second real consumer requires them — document the extension point, don't build it speculatively

Full standard is available here for further request: [Schema-First Data Contracts for Measured Output](../../../.packmind/standards/solidai-schema-first-data-contract-for-measured-output.md)
```

---

En attente de décision : **[A]** soumettre tel quel, **[B]** modifier le contenu d'abord, **[C]** garder comme draft.
